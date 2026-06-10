# Zonnescherm RTS — eigen fork van ESPSomfy RTS

Dit is een aangepaste (gevendorde) versie van
[ESPSomfy RTS](https://github.com/rstrouse/ESPSomfy-RTS) (publiek domein / Unlicense),
afgestemd op deze opstelling. Volwaardige firmware met web-UI, MQTT en
[Home Assistant-integratie](https://github.com/rstrouse/ESPSomfy-RTS-HA), die ook
**bestaande remotes (je Telis) kan meeluisteren/linken**.

## Eigen aanpassingen t.o.v. upstream

| Wat | Bestand | Van → Naar |
|-----|---------|-----------|
| RX-pin (CC1101 GDO0) | `Somfy.h` | GPIO12 → **GPIO2** |
| TX-pin (CC1101 GDO2) | `Somfy.h` | GPIO13 → **GPIO4** |
| Apparaat-hostname | `ConfigSettings.h` | `ESPSomfyRTS` → **`Zonnescherm`** |
| Web-UI titel/branding | `data/index.html` | `ESPSomfy RTS` → **`Zonnescherm RTS`** |

Frequentie stond al goed op **433,42 MHz**. SPI-pinnen (SCK 18, MOSI 23, MISO 19,
CSN 5) waren al gelijk aan je bedrading.

## Bedrading (let op: ESPSomfy gebruikt 2 GDO-lijnen!)

| CC1101 | → ESP32 | Opmerking |
|--------|---------|-----------|
| 3.3V | 3V3 | |
| GND | GND | |
| SCK | GPIO18 | |
| MOSI | GPIO23 | |
| GCD1 (=MISO) | GPIO19 | |
| CSN | GPIO5 | |
| GDO0 | GPIO2 | ontvangen (RX) — had je al |
| **GDO2** | **GPIO4** | **zenden (TX) — deze draad NIEUW toevoegen** |

> Anders dan de ESPHome-opzet (één datalijn) gebruikt ESPSomfy een aparte RX- en
> TX-lijn. Sluit daarom **GDO2 → GPIO4** aan naast de bestaande GDO0 → GPIO2.

## Bouwen & flashen (Arduino IDE)

1. **Board support**: ESP32 (esp32 by Espressif).
2. **Library**: installeer **SmartRC-CC1101-Driver-Lib** (LSatan/ELECHOUSE) en de
   overige afhankelijkheden die de IDE aangeeft (o.a. ArduinoJson).
3. Open `SomfyController.ino` in deze map.
4. Selecteer je ESP32-board, partitiescheme met genoeg ruimte + LittleFS.
5. **Upload de sketch** (firmware).
6. **Upload de `data/`-map als LittleFS-image** (web-UI). Gebruik de
   "ESP32 LittleFS Data Upload"-tool of `arduino-littlefs-upload`.
7. ESP32 verbindt met WiFi (AP-modus bij eerste keer) → open het IP in de browser.

> Liever niet compileren? Je kunt ook upstream de kant-en-klare web-installer
> gebruiken en de pinnen/naam later in de web-UI zetten. Deze fork is voor wie de
> defaults en branding in de code wil vastleggen.

## Home Assistant
Installeer de integratie via HACS:
`https://github.com/rstrouse/ESPSomfy-RTS-HA` → het apparaat `Zonnescherm` wordt
ontdekt en je shades verschijnen als `cover`-entiteiten.

## Verder rebranden (optioneel)
- **Logo**: vervang `data/icon.png`, `data/icon.svg`, `data/favicon.png` en
  `data/apple-icon.png` door je eigen afbeeldingen (zelfde bestandsnamen/afmetingen).
- **Naam**: de zichtbare naam staat in `data/index.html` (regel ~124) en de
  hostname in `ConfigSettings.h`.

Geef me een naam/logo door als je een specifieke branding wilt, dan zet ik die erin.
