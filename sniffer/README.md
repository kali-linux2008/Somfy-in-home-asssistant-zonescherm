# Somfy RTS sniffer (ESP32 + CC1101)

Arduino-sketch om Somfy RTS-signalen te **ontvangen en decoderen**. Handig om te
testen of je CC1101 + antenne + bedrading werken, en om het **adres + rolling code +
commando** van je Telis 1 te zien.

> Dit staat los van de ESPHome-firmware. Je flasht dit tijdelijk om te testen/sniffen;
> daarna flash je weer je ESPHome-config terug.

## Nodig
- Arduino IDE met **ESP32-board support**.
- Library **"SmartRC-CC1101-Driver-Lib"** (LSatan/ELECHOUSE) via *Bibliotheken beheren*.
- Bedrading zoals in je ESPHome-opstelling (zie [`../docs/bedrading.md`](../docs/bedrading.md)).
  De ontvangen data komt binnen op **GDO0 → GPIO2**.

## Gebruiken
1. Open [`somfy_rts_sniffer.ino`](somfy_rts_sniffer.ino) in de Arduino IDE.
2. Board: **ESP32 Dev Module**. Upload de sketch.
3. Open de **Seriele Monitor** op **115200 baud**.
4. Je zou moeten zien: `CC1101 gevonden. OK.`
5. Druk op een knop van je **Telis 1**. Bij elke druk verschijnt iets als:
   ```
   ---- Somfy RTS frame ----
     Raw bytes : A7 23 01 1F 4A 8C 12
     Adres     : 0x128C4A
     Rolling   : 287
     Commando  : 0x2 (Up (omhoog/in))
     Checksum  : OK
   ```

## Wat het je vertelt
- **Zie je frames met `Checksum: OK`** → je radio, antenne en GDO0-draad werken prima.
  Je TX-probleem zit dan elders (bijv. PA/zendkant of inleer-volgorde).
- **Zie je helemaal niets** (ook geen ruis) bij het indrukken van de Telis →
  CC1101 ontvangt niet: controleer de **antenne**, de **GDO0 → GPIO2**-draad en de
  voeding (3.3V).
- **Wel rommel maar nooit `OK`** → signaal komt binnen maar decodeert niet; meestal
  antenne/afstand of timing. Probeer dichterbij de Telis.

## Let op
- `Prog button attached: NO` e.d. hoort bij ESPHome, niet bij deze sketch.
- Wil je daarna weer bedienen vanuit Home Assistant: flash gewoon je
  `zonnescherm.yaml` terug via ESPHome.
