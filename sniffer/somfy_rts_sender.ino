/*
 * Somfy RTS ZENDER voor ESP32 + CC1101 - bediening via seriele monitor
 * --------------------------------------------------------------------
 * Typ in de seriele monitor (115200 baud, "No line ending" of "Newline"):
 *     u  -> Up    (omhoog / inrollen)
 *     d  -> Down  (omlaag / uitrollen)
 *     s  -> My / Stop
 *     p  -> Prog  (inleren / koppelen)
 *     r  -> toon huidige rolling code
 *
 * Deze ESP32 gedraagt zich als een EIGEN virtuele afstandsbediening met
 * een eigen adres (REMOTE_ADDRESS). Inleren:
 *     1) Telis omdraaien, PROG ~2s -> scherm beweegt (programmeermodus).
 *     2) Typ binnen enkele seconden 'p' in de seriele monitor.
 *     3) Scherm beweegt opnieuw = gekoppeld. Daarna werken u/d/s.
 *
 * Bedrading: identiek aan de sniffer. De zenddata gaat via GDO0 -> GPIO2.
 *
 * Vereiste library: "SmartRC-CC1101-Driver-Lib" (LSatan / ELECHOUSE)
 * --------------------------------------------------------------------
 */

#include <ELECHOUSE_CC1101_SRC_DRV.h>
#include <Preferences.h>

// --- Pinnen ---
#define SCK_PIN   18
#define MISO_PIN  19
#define MOSI_PIN  23
#define CS_PIN     5
#define TX_PIN     2     // CC1101 GDO0 (data-ingang voor de zender)

// --- Eigen afstandsbediening ---
#define REMOTE_ADDRESS 0x186024UL   // uniek adres voor deze "remote"

#define SYMBOL 640                  // us, halve-symbool

Preferences prefs;
unsigned int rollingCode = 1;

// Bouwt een Somfy RTS frame (7 bytes) voor het gegeven commando.
void buildFrame(byte *frame, byte command) {
  frame[0] = 0xA7;                       // "encryption key" (vast is prima)
  frame[1] = command << 4;               // hoge nibble = commando, lage = checksum
  frame[2] = rollingCode >> 8;           // rolling code hi
  frame[3] = rollingCode & 0xFF;         // rolling code lo
  frame[4] = REMOTE_ADDRESS >> 16;       // adres
  frame[5] = REMOTE_ADDRESS >> 8;
  frame[6] = REMOTE_ADDRESS & 0xFF;

  // Checksum: XOR van alle nibbles, in lage nibble van frame[1]
  byte checksum = 0;
  for (byte i = 0; i < 7; i++) checksum ^= frame[i] ^ (frame[i] >> 4);
  frame[1] |= (checksum & 0x0F);

  // Obfuscatie: elk byte XOR vorige
  for (byte i = 1; i < 7; i++) frame[i] ^= frame[i - 1];
}

// Zendt een frame uit door GDO0 (GPIO2) te toggelen; de CC1101 moduleert dit.
void sendFrame(byte *frame, byte syncPulses) {
  if (syncPulses == 2) {                 // alleen bij het eerste frame: wake-up
    digitalWrite(TX_PIN, HIGH); delayMicroseconds(9415);
    digitalWrite(TX_PIN, LOW);  delayMicroseconds(89565);
  }

  for (byte i = 0; i < syncPulses; i++) {   // hardware sync
    digitalWrite(TX_PIN, HIGH); delayMicroseconds(4 * SYMBOL);
    digitalWrite(TX_PIN, LOW);  delayMicroseconds(4 * SYMBOL);
  }

  digitalWrite(TX_PIN, HIGH); delayMicroseconds(4550);  // software sync
  digitalWrite(TX_PIN, LOW);  delayMicroseconds(SYMBOL);

  for (byte i = 0; i < 56; i++) {           // 56 data-bits, Manchester
    if ((frame[i / 8] >> (7 - (i % 8))) & 1) {
      digitalWrite(TX_PIN, LOW);  delayMicroseconds(SYMBOL);
      digitalWrite(TX_PIN, HIGH); delayMicroseconds(SYMBOL);
    } else {
      digitalWrite(TX_PIN, HIGH); delayMicroseconds(SYMBOL);
      digitalWrite(TX_PIN, LOW);  delayMicroseconds(SYMBOL);
    }
  }

  digitalWrite(TX_PIN, LOW);
  delayMicroseconds(30415);                 // inter-frame gap
}

void sendCommand(byte command, const char *name) {
  byte frame[7];
  buildFrame(frame, command);

  Serial.print(F("Zenden: ")); Serial.print(name);
  Serial.print(F("  (rolling code ")); Serial.print(rollingCode); Serial.println(F(")"));
  Serial.print(F("  Frame: "));
  for (byte i = 0; i < 7; i++) {
    if (frame[i] < 0x10) Serial.print('0');
    Serial.print(frame[i], HEX); Serial.print(' ');
  }
  Serial.println();

  // Eerste frame met 2 hardware-sync pulsen, daarna herhalingen met 7.
  sendFrame(frame, 2);
  for (byte i = 0; i < 3; i++) sendFrame(frame, 7);

  // Rolling code ophogen en bewaren (overleeft een herstart).
  rollingCode++;
  prefs.putUInt("rolling", rollingCode);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println(F("Somfy RTS ZENDER - ESP32 + CC1101"));

  prefs.begin("somfy", false);
  rollingCode = prefs.getUInt("rolling", 1);

  ELECHOUSE_cc1101.setSpiPin(SCK_PIN, MISO_PIN, MOSI_PIN, CS_PIN);
  ELECHOUSE_cc1101.Init();
  if (!ELECHOUSE_cc1101.getCC1101()) {
    Serial.println(F("FOUT: CC1101 niet gevonden! Controleer SPI-bedrading."));
  } else {
    Serial.println(F("CC1101 gevonden. OK."));
  }

  ELECHOUSE_cc1101.setCCMode(0);       // raw / transparent
  ELECHOUSE_cc1101.setModulation(2);   // ASK/OOK
  ELECHOUSE_cc1101.setMHZ(433.42);     // Somfy RTS
  ELECHOUSE_cc1101.setPA(12);          // maximaal zendvermogen
  ELECHOUSE_cc1101.setPktFormat(3);    // async serieel: GDO0 = data-ingang
  ELECHOUSE_cc1101.SetTx();            // zender continu aan, gekeyd via GDO0

  pinMode(TX_PIN, OUTPUT);
  digitalWrite(TX_PIN, LOW);

  Serial.print(F("Eigen adres: 0x")); Serial.println(REMOTE_ADDRESS, HEX);
  Serial.print(F("Rolling code: ")); Serial.println(rollingCode);
  Serial.println(F("Commando's: u=Up  d=Down  s=Stop/My  p=Prog  r=toon code"));
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    switch (c) {
      case 'u': case 'U': sendCommand(0x2, "Up");       break;
      case 'd': case 'D': sendCommand(0x4, "Down");     break;
      case 's': case 'S': sendCommand(0x1, "Stop/My");  break;
      case 'p': case 'P': sendCommand(0x8, "Prog");     break;
      case 'r': case 'R':
        Serial.print(F("Rolling code: ")); Serial.println(rollingCode);
        break;
      default: break;   // enters/spaties negeren
    }
  }
}
