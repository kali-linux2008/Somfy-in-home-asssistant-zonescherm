/*
 * Somfy RTS sniffer voor ESP32 + CC1101
 * ------------------------------------------------------------
 * Doel:
 *   1) Testen of de CC1101 + antenne + GDO0-draad werken (ontvang je de Telis?).
 *   2) De Somfy RTS frames van je Telis 1 decoderen:
 *        - remote-adres (24 bit)
 *        - rolling code (16 bit)
 *        - commando (Up / Down / My-Stop / Prog)
 *
 * Bedrading (zelfde als je ESPHome-opstelling):
 *   CC1101            ESP32
 *   ------            -----
 *   3.3V              3V3
 *   GND               GND
 *   SCK               GPIO18
 *   MOSI              GPIO23
 *   GCD1 (=MISO)      GPIO19
 *   CSN               GPIO5
 *   GDO0              GPIO2     <-- hier komt de ontvangen data binnen
 *   GDO2              niet nodig
 *
 * Vereiste library (Arduino IDE -> Bibliotheken beheren):
 *   "SmartRC-CC1101-Driver-Lib" van LSatan / ELECHOUSE
 *
 * Board: "ESP32 Dev Module". Seriele monitor op 115200 baud.
 * ------------------------------------------------------------
 */

#include <ELECHOUSE_CC1101_SRC_DRV.h>

// --- Pinnen ---
#define SCK_PIN   18
#define MISO_PIN  19
#define MOSI_PIN  23
#define CS_PIN     5
#define RX_PIN     2     // CC1101 GDO0 (interrupt-pin)

// --- Somfy timing (microseconden) ---
#define SYMBOL        640   // halve-symbool (~604us)
#define HW_SYNC_MIN  1500
#define HW_SYNC_MAX  2900
#define SW_SYNC_MIN  3500
#define SW_SYNC_MAX  5500
#define SHORT_MIN     300
#define SHORT_MAX     950
#define LONG_MIN      950
#define LONG_MAX     1600
#define GAP_MIN      6000   // grens tussen frames

// --- Ringbuffer voor pulsduren ---
#define BUF_SIZE 256
volatile unsigned int  pulseLen[BUF_SIZE];
volatile byte          pulseLvl[BUF_SIZE];   // niveau (1=hoog) van het segment
volatile unsigned int  bufIndex   = 0;
volatile unsigned int  frameLen   = 0;
volatile bool          frameReady = false;

void IRAM_ATTR handleInterrupt() {
  static unsigned long lastTime = 0;
  const unsigned long now = micros();
  const unsigned int  dur = now - lastTime;
  lastTime = now;

  const int level = digitalRead(RX_PIN);   // niveau NA de flank
  // het segment dat zojuist eindigde had het tegenovergestelde niveau

  if (dur > GAP_MIN) {
    // einde van een burst -> geef de tot nu toe verzamelde puls op aan loop()
    if (bufIndex > 20 && !frameReady) {
      frameLen   = bufIndex;
      frameReady = true;
    }
    bufIndex = 0;
    return;
  }

  if (bufIndex < BUF_SIZE && !frameReady) {
    pulseLen[bufIndex] = dur;
    pulseLvl[bufIndex] = !level;            // niveau van het afgelopen segment
    bufIndex++;
  }
}

const char* commandName(byte cmd) {
  switch (cmd) {
    case 0x1: return "My / Stop";
    case 0x2: return "Up (omhoog/in)";
    case 0x4: return "Down (omlaag/uit)";
    case 0x8: return "Prog";
    case 0x9: return "Sun/Flag";
    case 0xA: return "Flag";
    default:  return "onbekend";
  }
}

void decodeFrame() {
  // 1) Zoek de software-sync (lange hoge puls ~4550us). Data start erna.
  int dataStart = -1;
  int hwSync = 0;
  for (unsigned int i = 0; i < frameLen; i++) {
    unsigned int d = pulseLen[i];
    if (d > HW_SYNC_MIN && d < HW_SYNC_MAX) {
      hwSync++;
    } else if (d > SW_SYNC_MIN && d < SW_SYNC_MAX && hwSync >= 2) {
      dataStart = i + 1;
      break;
    } else if (d < SW_SYNC_MIN) {
      // korte puls voor sync -> reset teller
      if (d < HW_SYNC_MIN) hwSync = 0;
    }
  }
  if (dataStart < 0) return;   // geen geldige sync gevonden

  // 2) Bouw de half-symbool stroom op uit de segmenten.
  //    We verzamelen wat extra half-symbolen zodat we de uitlijning kunnen zoeken.
  byte halfbits[128];
  int  hbCount = 0;
  for (unsigned int i = dataStart; i < frameLen && hbCount < 124; i++) {
    unsigned int d = pulseLen[i];
    byte lvl = pulseLvl[i];
    if (d > SHORT_MIN && d < SHORT_MAX) {
      halfbits[hbCount++] = lvl;                 // 1 half-symbool
    } else if (d >= LONG_MIN && d < LONG_MAX) {
      halfbits[hbCount++] = lvl;                 // 2 half-symbolen, zelfde niveau
      if (hbCount < 124) halfbits[hbCount++] = lvl;
    } else {
      break;
    }
  }

  // 3) Probeer meerdere uitlijningen (half-bit offset) + polariteit, en kies
  //    degene waarvan de checksum klopt. Dit lost de Manchester-uitlijning op.
  byte frame[7];
  bool ok = false;
  for (int off = 0; off <= 4 && !ok; off++) {
    for (int inv = 0; inv <= 1 && !ok; inv++) {
      ok = tryDecode(halfbits, hbCount, off, inv, frame);
    }
  }

  if (!ok) {
    // Niets klopte: toon best-effort (offset 0) als FOUT.
    tryDecodeRaw(halfbits, hbCount, 0, 0, frame);
    printFrame(frame, false);
    return;
  }
  printFrame(frame, true);
}

// Bouwt 7 bytes uit de half-symboolstroom met gegeven offset/polariteit,
// de-obfusceert en geeft true terug als de checksum klopt.
bool tryDecode(byte* halfbits, int hbCount, int offset, bool invert, byte* outFrame) {
  if (hbCount < 111) return false;   // minimaal ~56 bits nodig
  tryDecodeRaw(halfbits, hbCount, offset, invert, outFrame);
  byte cks = 0;
  for (int i = 0; i < 7; i++) cks ^= outFrame[i] ^ (outFrame[i] >> 4);
  return (cks & 0x0F) == 0;
}

void tryDecodeRaw(byte* halfbits, int hbCount, int offset, bool invert, byte* outFrame) {
  for (int i = 0; i < 7; i++) outFrame[i] = 0;
  for (int k = 0; k < 56; k++) {
    int idx = offset + 2 * k;
    byte bit = (idx < hbCount) ? halfbits[idx] : 0;   // eerste half = bitwaarde
    if (invert) bit = !bit;
    outFrame[k / 8] |= bit << (7 - (k % 8));
  }
  // De-obfuscatie (elk byte XOR vorige)
  for (int i = 1; i < 7; i++) outFrame[i] ^= outFrame[i - 1];
}

void printFrame(byte* frame, bool valid) {
  byte          command = frame[1] >> 4;
  unsigned int  rolling = (frame[2] << 8) | frame[3];
  unsigned long address = ((unsigned long)frame[6] << 16) |
                          ((unsigned long)frame[5] << 8)  |
                           (unsigned long)frame[4];

  Serial.println(F("---- Somfy RTS frame ----"));
  Serial.print(F("  Raw bytes : "));
  for (int i = 0; i < 7; i++) {
    if (frame[i] < 0x10) Serial.print('0');
    Serial.print(frame[i], HEX); Serial.print(' ');
  }
  Serial.println();
  Serial.print(F("  Adres     : 0x")); Serial.println(address, HEX);
  Serial.print(F("  Rolling   : ")); Serial.println(rolling);
  Serial.print(F("  Commando  : 0x")); Serial.print(command, HEX);
  Serial.print(F(" (")); Serial.print(commandName(command)); Serial.println(F(")"));
  Serial.print(F("  Checksum  : "));
  Serial.println(valid ? F("OK") : F("FOUT (geen geldige uitlijning gevonden)"));
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println(F("Somfy RTS sniffer - ESP32 + CC1101"));

  ELECHOUSE_cc1101.setSpiPin(SCK_PIN, MISO_PIN, MOSI_PIN, CS_PIN);
  ELECHOUSE_cc1101.Init();

  if (!ELECHOUSE_cc1101.getCC1101()) {
    Serial.println(F("FOUT: CC1101 niet gevonden! Controleer SPI-bedrading (incl. MISO=GCD1)."));
  } else {
    Serial.println(F("CC1101 gevonden. OK."));
  }

  ELECHOUSE_cc1101.setCCMode(0);        // raw / transparent
  ELECHOUSE_cc1101.setModulation(2);    // 2 = ASK/OOK
  ELECHOUSE_cc1101.setMHZ(433.42);      // Somfy RTS frequentie
  ELECHOUSE_cc1101.setRxBW(203);        // ontvangstbandbreedte (kHz)
  ELECHOUSE_cc1101.setPktFormat(3);     // asynchroon serieel: data op GDO0
  ELECHOUSE_cc1101.SetRx();

  pinMode(RX_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(RX_PIN), handleInterrupt, CHANGE);

  Serial.println(F("Luisteren op 433.42 MHz... druk op een knop van je Telis."));
  Serial.println();
}

void loop() {
  if (frameReady) {
    decodeFrame();
    frameReady = false;
  }
}
