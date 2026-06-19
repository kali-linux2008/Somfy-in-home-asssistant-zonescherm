# Intex Spa → Home Assistant via LocalTuya

Stap-voor-stap handleiding voor een Tuya-gebaseerde Intex spa (2024-model, TY-variant)
in Home Assistant via de [LocalTuya-integratie (xZetsubou-fork)](https://github.com/xZetsubou/hass-localtuya).

---

## Overzicht

| Stap | Wat | Waar draai je het |
|------|-----|-------------------|
| A | Netwerk-scan → device_id + IP + versie | HA SSH of PC in zelfde netwerk |
| B | HTTPS-onderschepping → local_key | PC (mitmproxy) + telefoon |
| C | DPS uitlezen + functies bepalen | HA SSH of PC |
| D | LocalTuya-config genereren | HA SSH of PC |

---

## STAP A — Device_id, IP en protocol-versie vinden

### Vereiste
Je hebt een terminal nodig op een machine in **hetzelfde wifi-subnet** als de spa.

**Optie 1 — Home Assistant SSH Add-on:**
1. Installeer de "Terminal & SSH" add-on in HA.
2. Open een terminal in HA.
3. Voer de onderstaande commando's uit.

**Optie 2 — PC in hetzelfde wifi-netwerk:**
Gebruik je gewone terminal/cmd.

### Commando's
```bash
pip3 install tinytuya
python3 stap_a_scan.py
```

### Verwachte output
```
IP-adres:       192.168.1.42
device_id:      bf1234567890abcdef
Versie:         3.4   ← dit heb je nodig voor STAP C/D
```

**Geef mij de device_id, het IP en de versie terug.** Dan gaan we verder met STAP B.

### DHCP-reservering instellen (vaste IP)
Zo zorg je dat de spa altijd hetzelfde IP houdt:

- **FritzBox:** Heimnetz → Netzwerk → apparaat aanklikken → "Diesem Netzwerkgerät immer die gleiche IPv4-Adresse zuweisen"
- **Unifi / Ubiquiti:** Clients → spa-client → "Fixed IP"
- **Synology Router:** Netwerk → DHCP → Reserveringen
- **TP-Link / Deco:** Geavanceerd → DHCP → Adresreservering → MAC-adres + gewenst IP invullen

Het MAC-adres van de spa vind je in de scan-output (`_raw`-veld) of in je router-overzicht.

---

## STAP B — local_key onderscheppen via mitmproxy

De local_key staat **niet** in lokaal Tuya-verkeer — die is al versleuteld.
Hij zit wél in het HTTPS-verkeer tussen de Intex Link-app en de Intex-cloud.

### B1 — mitmproxy installeren op je PC

```bash
pip3 install mitmproxy
```

Controleer je PC-IP (dit wordt je proxy-adres):
```bash
# Linux/Mac:
ip addr show   # of: ifconfig
# Windows:
ipconfig
```
Noteer het IP, bijv. `192.168.1.10`.

### B2 — mitmproxy starten met de addon

```bash
mitmdump --listen-host 0.0.0.0 --listen-port 8080 -s stap_b_mitm_addon.py
```

`mitmdump` is de headless versie (terminal-output). Gebruik `mitmproxy` voor een TUI.
Laat dit venster open staan.

### B3 — CA-certificaat genereren

mitmproxy genereert automatisch een CA-certificaat bij de eerste start.
Je vindt het op: `~/.mitmproxy/mitmproxy-ca-cert.pem` (Linux/Mac)
of `%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem` (Windows).

Kopieer het naar een toegankelijke locatie, bijv. een webserver of AirDrop.
**Eenvoudigste manier — tijdelijke HTTP-server:**
```bash
# In de ~/.mitmproxy map:
cd ~/.mitmproxy
python3 -m http.server 8888
```
Daarna open je op je telefoon: `http://192.168.1.10:8888/mitmproxy-ca-cert.pem`

### B4 — CA-certificaat installeren op je Android-telefoon

1. Open de URL van stap B3 in de browser op je telefoon.
2. Het certificaat wordt gedownload.
3. Ga naar **Instellingen → Beveiliging → Meer beveiligingsinstellingen → Certificaten installeren → CA-certificaat**.
4. Selecteer het gedownloade bestand.
5. Bevestig de waarschuwing ("Installeer toch").

> Android 11+: ga naar **Instellingen → Beveiliging → Encryptie en referenties → Vertrouwde referenties installeren**

### B5 — Proxy instellen op de telefoon

1. Ga naar **Instellingen → Wifi → [jouw netwerknaam]** (lang indrukken → Netwerk wijzigen).
2. Geavanceerde opties → Proxy → **Handmatig**.
3. Proxy-hostnaam: `192.168.1.10` (jouw PC-IP).
4. Proxy-poort: `8080`.
5. Sla op.

### B6 — Intex Link-app gebruiken om de key te triggeren

Met de proxy actief en de app gesloten:
1. Open de **Intex Link-app** opnieuw (koud openen).
2. Ga naar het **apparatenoverzicht** (thuisscherm met je spa).
3. Wacht even — de app synchroniseert met de cloud en stuurt de local_key mee.
4. Optioneel: trek het scherm omlaag om te verversen.

In het mitmproxy-venster op je PC verschijnt nu (als het lukt):
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  *** LOCAL KEY GEVONDEN ***
  localKey     = a1b2c3d4e5f60718
  devId        = bf1234567890abcdef
  URL          = https://...intex.../device/list
  Logbestand   = gevonden_keys.log
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

**Geef mij de localKey terug (behandel hem als een wachtwoord — niet online posten).**

Herstel de proxy-instelling op je telefoon naar **Geen** als je klaar bent.

---

## Fallback B — Certificate Pinning bypass met Frida

Als de Intex Link-app wél verbindt maar mitmproxy niets onderschept (certificate pinning),
gebruik dan `stap_b_frida_bypass.js`.

### Vereisten
- Geroote Android-telefoon **of** een emulator (Genymotion / Android Studio AVD met Google APIs)
- `adb` geïnstalleerd op je PC

### Frida installeren
```bash
pip3 install frida-tools

# Vind je CPU-architectuur:
adb shell getprop ro.product.cpu.abi
# → bijv. arm64-v8a

# Download frida-server van https://github.com/frida/frida/releases
# Kies: frida-server-XX.X.X-android-arm64.xz

xz -d frida-server-XX.X.X-android-arm64.xz
adb push frida-server-XX.X.X-android-arm64 /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"
```

### Package-naam van de Intex-app vinden
```bash
adb shell pm list packages | grep -i intex
# → bijv. com.intexcorp.intexlink
```

### Frida bypass starten
```bash
# Mitmproxy draait al (zie B2), telefoon-proxy is ingesteld (zie B5)
frida -U -f com.intexcorp.intexlink -l stap_b_frida_bypass.js --no-pause
```
Daarna de app gebruiken zoals bij B6. Nu hoeft het CA-certificaat niet in Android vertrouwd te zijn.

---

## STAP C — DPS uitlezen en functies bepalen

Zodra je device_id, IP en local_key hebt:

```bash
python3 stap_c_poll_dps.py <device_id> <local_key> <ip> [versie]
# Voorbeeld:
python3 stap_c_poll_dps.py bf1234567890abcdef a1b2c3d4e5f60718 192.168.1.42 3.4
```

Het script vraagt daarna of je continu wilt pollen. Zeg ja, en druk dan knoppen
op de spa (verwarming aan, bubbels aan, etc.) — je ziet welk DPS-nummer verandert.

**Geef mij de DPS-tabel terug zodat ik de mapping kan controleren.**

---

## STAP D — LocalTuya-config genereren

```bash
# Vul DEVICE_ID, LOCAL_KEY, DEVICE_IP en DPS_MAP in in het script,
# of laad het JSON-bestand uit STAP C:
python3 stap_d_genereer_config.py dps_resultaat.json
```

Het script genereert `localtuya_config.yaml` én geeft instructies voor de HA-GUI.

---

## Troubleshooting

| Probleem | Oplossing |
|----------|-----------|
| Scan vindt niets | PC/HA zit op ander subnet dan spa. Gebruik PC in zelfde wifi. |
| Verbinding mislukt in STAP C | Verkeerde versie (probeer 3.3, 3.4, 3.5) of verkeerde local_key |
| mitmproxy toont niets | App gebruikt certificate pinning → gebruik Frida-bypass |
| Temperature ×10 | Pas `TEMP_FACTOR = 10` aan in stap_d |
| LocalTuya kan niet verbinden | Spa staat op ander VLAN of firewall blokkeert poort 6668 TCP |
