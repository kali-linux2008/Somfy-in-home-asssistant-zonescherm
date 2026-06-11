# Zonnescherm RTS — eigen fork van ESPSomfy RTS

Dit is een aangepaste (gevendorde) versie van
[ESPSomfy RTS](https://github.com/rstrouse/ESPSomfy-RTS) (publiek domein / Unlicense),
afgestemd op deze opstelling. Volwaardige firmware met web-UI, MQTT en
[Home Assistant-integratie](https://github.com/rstrouse/ESPSomfy-RTS-HA), die ook
**bestaande remotes (je Telis) kan meeluisteren/linken**.

## Eigen aanpassingen t.o.v. upstream

Alle broncode staat in de sketchmap **`SomfyController/`**.

| Wat | Bestand | Van → Naar |
|-----|---------|-----------|
| RX-pin (CC1101 GDO0) | `SomfyController/Somfy.h` | GPIO12 → **GPIO2** |
| TX-pin (CC1101 GDO2) | `SomfyController/Somfy.h` | GPIO13 → **GPIO4** |
| Apparaat-hostname | `SomfyController/ConfigSettings.h` | `ESPSomfyRTS` → **`Zonnescherm`** |
| Web-UI titel/branding | `SomfyController/data/index.html` | `ESPSomfy RTS` → **`Zonnescherm RTS`** |

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

> **Mapstructuur:** de sketch staat in `firmware/SomfyController/`. Arduino eist dat
> het hoofd-`.ino` in een map met dezelfde naam staat — dat is nu het geval. Open
> dus **`firmware/SomfyController/SomfyController.ino`**; alle andere bestanden
> verschijnen automatisch als tabbladen.

### 1. Board support
- Installeer in de Boards Manager: **esp32 by Espressif Systems**.

### 2. Libraries (via Bibliotheken beheren)
| Library | Auteur | Let op |
|---------|--------|--------|
| **ArduinoJson** | Benoit Blanchon | **versie 6.x** — NIET v7 (code gebruikt `DynamicJsonDocument`) |
| **SmartRC-CC1101-Driver-Lib** | LSatan / ELECHOUSE | de CC1101-radio |
| **PubSubClient** | Nick O'Leary | MQTT |
| **WebSockets** | Markus Sattler (Links2004) | `WebSocketsServer` |

De overige includes (`WiFi`, `LittleFS`, `WebServer`, `ESPmDNS`, `Update`,
`HTTPClient`, `Preferences`, `SPI`, ...) zitten al in de ESP32-core.

### 3. Board-instellingen
- **Board:** ESP32 Dev Module
- **Partition Scheme:** **Huge APP (3MB No OTA/1MB SPIFFS)**
  (de firmware is ~1,3 MB → past niet in de standaard 1,2 MB-app-partitie; de
  `data/`-map is ~472 KB → past in de 1 MB filesysteempartitie)
- **Flash Size:** 4MB

### 4. Sketch flashen
- Klik **Upload**. De eerste keer via USB; daarna kan het draadloos (OTA).

### 5. Web-UI uploaden (LittleFS)
De web-interface zit in `SomfyController/data/` en moet als filesysteem-image naar
de ESP32:
- Installeer de tool **arduino-littlefs-upload** (werkt in Arduino IDE 2.x), of de
  klassieke "ESP32 Sketch Data Upload"-plugin (1.8.x).
- Kies **LittleFS** en upload de `data/`-map.

### 6. In gebruik nemen
- ESP32 maakt bij eerste start een WiFi-accesspoint (AP). Verbind, geef je WiFi op.
- Open daarna het IP-adres van de ESP32 in de browser → de "Zonnescherm RTS" web-UI.

> Liever helemaal niet compileren? Gebruik upstream de **web-installer** (flasht de
> kant-en-klare firmware vanuit de browser, geen Arduino nodig) en zet pinnen/naam
> daarna in de web-UI. Deze fork is voor wie de defaults en branding in code wil
> vastleggen.


## Home Assistant
Installeer de integratie via HACS:
`https://github.com/rstrouse/ESPSomfy-RTS-HA` → het apparaat `Zonnescherm` wordt
ontdekt en je shades verschijnen als `cover`-entiteiten.

## Verder rebranden (optioneel)
- **Logo**: vervang `SomfyController/data/icon.png`, `icon.svg`, `favicon.png` en
  `apple-icon.png` door je eigen afbeeldingen (zelfde bestandsnamen/afmetingen).
- **Naam**: de zichtbare naam staat in `SomfyController/data/index.html` (regel ~124)
  en de hostname in `SomfyController/ConfigSettings.h`.

Geef me een naam/logo door als je een specifieke branding wilt, dan zet ik die erin.
