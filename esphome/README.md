# ESPHome variant — Somfy zonnescherm

Alternatief voor ESPSomfy RTS: de ESP32 + CC1101 draait hier op **ESPHome** met de
external component **[HarmEllis/esphome-somfy-cover-remote](https://github.com/HarmEllis/esphome-somfy-cover-remote)**.
De ESP32 wordt een virtuele Somfy-afstandsbediening en verschijnt automatisch als
`cover` in Home Assistant via de standaard ESPHome-integratie.

> **Let op:** deze component kan alleen **zenden** (inleren via PROG + bedienen).
> Meeluisteren/sniffen van een bestaande Telis zit er niet in — daarvoor is
> ESPSomfy RTS nodig (zie de hoofd-[README](../README.md)).

## Bestanden

- [`zonnescherm.yaml`](zonnescherm.yaml) — de complete ESPHome-config (afgestemd op de
  bedrading uit [`../docs/bedrading.md`](../docs/bedrading.md)).
- [`secrets.yaml.example`](secrets.yaml.example) — sjabloon voor je WiFi/API/OTA
  geheimen. Kopieer naar `secrets.yaml` (wordt niet gecommit).

## Installeren

Je hebt de ESPHome-dashboard nodig (HA-add-on, of `pip install esphome`).

1. **Geheimen instellen**
   ```bash
   cp secrets.yaml.example secrets.yaml
   # vul je WiFi/AP/OTA-gegevens in
   ```
   Laat het ESPHome-dashboard een `api_encryption_key` genereren, of maak er zelf een.

2. **Eerste keer flashen via USB**
   - Sluit de ESP32 met USB aan.
   - ESPHome-dashboard → het `zonnescherm`-toestel → **Install → Plug into this computer**
     (of via CLI: `esphome run zonnescherm.yaml`).
   - Na de eerste flash gaan updates draadloos (OTA).

3. **Toevoegen aan Home Assistant**
   - Het toestel wordt meestal automatisch ontdekt: **Instellingen → Apparaten &
     Services → ESPHome**. Anders het IP handmatig invullen.
   - Je krijgt een `cover.zonnescherm` entiteit + een knop **"Zonnescherm PROG"**.

## Inleren in de motor (pairing)

1. Pak je werkende **Telis 1**, druk kort op de **PROG-knop** (klein knopje achterop).
   Het scherm "knipt" → programmeermodus actief.
2. Druk in Home Assistant op de knop **"Zonnescherm PROG (inleren)"**.
3. Het scherm beweegt kort → de ESP32 is nu ingeleerd als extra afstandsbediening.

Daarna kun je open/dicht/stop sturen vanuit Home Assistant. Je fysieke Telis blijft
gewoon werken.

## Afstellen

- **Looptijden**: meet hoelang het scherm doet over volledig in → volledig uit en pas
  `open_duration` / `close_duration` aan voor een correcte positie-indicatie.
- **Meerdere schermen**: kopieer het `somfy_rts`- en `cover`-blok, geef elk een eigen
  `remote_code` (uniek 3-byte adres) en unieke `storage_key`.
- **Richting omgekeerd**: bij een awning kan open/dicht omgedraaid aanvoelen; wissel dan
  de open/close-acties of het `device_class`.

## Problemen oplossen

| Probleem | Oplossing |
|----------|-----------|
| Compileert niet (component) | Controleer de `external_components` source-URL en internettoegang tijdens build. |
| Scherm reageert niet | Frequentie moet 433,42 MHz zijn; controleer CSN/SCK/MOSI/MISO en GDO0→GPIO2; CC1101 op 3V3. |
| ESP32 bootlust / hangt | GPIO2 is een strapping-pin. Zorg dat de CC1101 hem bij boot niet hoog trekt, of verleg de `remote_transmitter`-pin (en GDO0-draad) naar bijv. GPIO4. |
| MISO ontbreekt op module | MISO = de pin met label **SO** of **GDO1** (→ GPIO19). Zie `../docs/bedrading.md`. |
| Inleren lukt niet | Telis-PROG correct ingedrukt? Juiste shade? Probeer opnieuw, scherm moet "knippen". |
