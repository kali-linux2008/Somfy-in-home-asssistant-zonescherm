# Somfy zonnescherm in Home Assistant (ESP32 + CC1101)

Handleiding om een **Somfy RTS zonnescherm** (bediend met een **Telis 1 RTS Pure**)
in **Home Assistant** te krijgen via een **ESP32 + CC1101 433 MHz** module, met de
firmware **[ESPSomfy RTS](https://github.com/rstrouse/ESPSomfy-RTS)**.

De ESP32 wordt een *virtuele afstandsbediening* die je net als een echte Telis in de
motor inleert. Daarna bedien je het scherm vanuit Home Assistant én blijft je fysieke
Telis gewoon werken.

---

## 1. Belangrijk om vooraf te weten

- **Frequentie = 433,42 MHz**, niet de gangbare 433,92 MHz. De CC1101 stem je in
  software exact af op 433,42 MHz — daarom is dit de juiste module. Goedkope vaste
  433,92 MHz-zendertjes werken niet betrouwbaar met Somfy.
- **Rolling code**: Somfy RTS gebruikt een rollende code + remote-adres. Je kunt een
  Telis dus **niet** simpelweg opnemen en replayen. De ESP32 krijgt zijn eigen
  remote-adres en wordt ingeleerd in de motor (PROG-knop). Eventueel kun je het adres
  van je bestaande Telis "overnemen" zodat beide synchroon blijven.
- **Voeding**: de CC1101 werkt op **3,3 V**. Sluit hem **niet** op 5 V aan.

---

## 2. Benodigdheden

- ESP32 dev board (bijv. ESP32-WROOM-32)
- CC1101 433 MHz transceiver module met (spring)antenne
- Dupont-draadjes
- USB-kabel (bij voorkeur een datakabel) om te flashen
- Een browser die Web Serial ondersteunt (Chrome of Edge) voor de web-installer
- Home Assistant met [HACS](https://hacs.xyz/) geïnstalleerd

---

## 3. Bedrading CC1101 → ESP32

> ⚠️ CC1101 op **3V3**, niet 5V.

SPI-bedrading (VSPI van de ESP32). Dit zijn de standaard pinnen van ESPSomfy RTS;
je kunt ze later in de web-UI nog aanpassen.

| CC1101 pin | Functie       | ESP32 GPIO |
|------------|---------------|------------|
| VCC        | 3,3 V voeding | 3V3        |
| GND        | Massa         | GND        |
| CSN        | SPI chip sel. | GPIO5      |
| SCK        | SPI clock     | GPIO18     |
| MOSI (SI)  | SPI data in   | GPIO23     |
| MISO (SO)  | SPI data uit  | GPIO19     |
| GDO0       | Data TX/RX    | GPIO2      |
| GDO2       | Data (RX)     | GPIO4      |

**Antenne**: soldeer/koppel de spring-antenne aan de ANT-pad van de CC1101. Een
antenne afgestemd op 433 MHz is ~17,3 cm (kwartgolf). Een spring-antenne werkt prima
voor binnenshuis.

Zie [`docs/bedrading.md`](docs/bedrading.md) voor een tekstueel pinout-schema.

---

## 4. Firmware flashen (ESPSomfy RTS)

ESPSomfy RTS is kant-en-klare firmware; je hoeft niets te compileren.

1. Sluit de ESP32 met USB aan op je pc.
2. Open in **Chrome of Edge** de web-installer:
   <https://rstrouse.github.io/ESPSomfy-RTS/> (zie ook de
   [wiki](https://github.com/rstrouse/ESPSomfy-RTS/wiki) voor de actuele link).
3. Klik **Connect/Install**, kies de seriële poort van de ESP32 en flash.
4. Na het flashen maakt de ESP32 een WiFi-accesspoint aan (bijv. `ESPSomfy-xxxx`).
   Verbind ermee en geef je eigen WiFi-gegevens op.
5. De ESP32 komt nu in je netwerk. Open het IP-adres in je browser voor de web-UI.

---

## 5. Configuratie in de ESPSomfy web-UI

1. **Radio/CC1101 instellen**
   - Ga naar de instellingen → radio.
   - Controleer dat de **GPIO-pinnen** kloppen met de tabel hierboven.
   - Zet de **frequentie op 433,42 MHz** (standaard voor RTS). Gebruik eventueel de
     ingebouwde kalibratie als het bereik tegenvalt.
2. **Zonnescherm (shade) toevoegen**
   - Voeg een nieuwe *shade* toe, type **Roller/Awning** (zonnescherm).
   - Geef hem een naam, bijv. `Zonnescherm Achter`.
   - De ESP32 genereert een uniek **remote-adres** voor deze shade.

### Inleren in de motor

**Optie A — nieuw virtueel kanaal (aanbevolen, simpel):**
1. Pak je werkende Telis 1.
2. Druk kort op de **PROG-knop** (klein knopje, vaak achterop/onderaan de Telis).
   Het scherm "knipt" even ten teken dat het in programmeermodus staat.
3. Druk in de ESPSomfy web-UI bij de shade op **PROG** (of "Set/Program").
4. Het scherm beweegt kort → de ESP32 is nu ingeleerd als extra afstandsbediening.

**Optie B — bestaande Telis overnemen (sniffen):**
- ESPSomfy RTS kan een bestaande remote "linken" door mee te luisteren. Activeer in de
  shade de optie om een afstandsbediening te koppelen, druk op een knop van je Telis,
  en de ESP32 neemt het adres + rolling code over. Handig als je geen kanalen wilt
  verspillen of het scherm exact synchroon wilt houden.

> Tip: test eerst met op/neer/stop in de web-UI vóór je verder gaat met Home Assistant.

---

## 6. Home Assistant integratie

ESPSomfy RTS heeft een officiële HA-integratie via HACS. Communicatie gaat lokaal
(geen cloud).

1. **HACS → Integraties → ⋮ → Custom repositories**
   - Repository: `https://github.com/rstrouse/ESPSomfy-RTS-HA`
   - Categorie: *Integration*
2. Installeer **ESPSomfy RTS** en herstart Home Assistant.
3. **Instellingen → Apparaten & Services → Integratie toevoegen → ESPSomfy RTS**.
   - De ESP32 wordt meestal automatisch ontdekt (anders vul je het IP in).
4. Je shades verschijnen als **`cover`**-entiteiten met open/dicht/stop en
   positie (afhankelijk van het type/instelling).

Daarna kun je ze in dashboards en automatiseringen gebruiken, bijv:

```yaml
# Voorbeeld-automatisering: scherm omhoog bij harde wind
automation:
  - alias: "Zonnescherm in bij wind"
    trigger:
      - platform: numeric_state
        entity_id: sensor.windsnelheid
        above: 40
    action:
      - service: cover.open_cover   # 'open' = scherm ingerold/omhoog
        target:
          entity_id: cover.zonnescherm_achter
```

> Let op: "open" vs "dicht" betekent bij een zonnescherm soms het tegenovergestelde
> van wat je verwacht (ingerold vs uitgerold). Controleer de richting en pas zo nodig
> de inverteer-instelling van de shade aan.

---

## 7. Problemen oplossen

| Probleem | Mogelijke oorzaak / oplossing |
|----------|-------------------------------|
| Scherm reageert niet | Frequentie niet op 433,42 MHz; bedrading CSN/MISO/MOSI/SCK; CC1101 op 5V i.p.v. 3V3. |
| Kort bereik | Antenne niet (goed) gesoldeerd; verkeerde lengte; CC1101-voeding instabiel. |
| Inleren lukt niet | PROG-knop te kort/lang ingedrukt; verkeerde shade geselecteerd; probeer Optie B. |
| Niet zichtbaar in HA | ESP32 en HA in ander VLAN/subnet; vul handmatig het IP in; controleer firewall/mDNS. |
| SPI-fouten in log | Controleer GDO0/GDO2 pinnen en of de CC1101 echt 3,3V krijgt. |

---

## 8. Referenties

- ESPSomfy RTS (firmware): <https://github.com/rstrouse/ESPSomfy-RTS>
- ESPSomfy RTS Home Assistant integratie: <https://github.com/rstrouse/ESPSomfy-RTS-HA>
- Wiki met flash- en configuratiestappen: <https://github.com/rstrouse/ESPSomfy-RTS/wiki>
- Achtergrond Somfy RTS-protocol: <https://pushstack.wordpress.com/somfy-rts-protocol/>
