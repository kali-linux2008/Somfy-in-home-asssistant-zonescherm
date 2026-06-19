#!/usr/bin/env python3
"""
STAP C — Polt alle DPS van de Intex spa en helpt bij het identificeren van functies.

Vul onderaan (of via commandoregel) de drie waarden in die je uit STAP A + B hebt:
    DEVICE_ID  — uit de scan (bijv. "bf1234567890abcdef")
    LOCAL_KEY  — 16 tekens, uit mitmproxy-log (bijv. "a1b2c3d4e5f60718")
    DEVICE_IP  — vast IP van de spa (bijv. "192.168.1.42")

Gebruik:
    python3 stap_c_poll_dps.py
of met argumenten:
    python3 stap_c_poll_dps.py bf1234 a1b2c3d4e5f60718 192.168.1.42
"""

import subprocess
import sys
import json
import time

# ── tinytuya installeren indien nodig ───────────────────────────────────────
try:
    import tinytuya
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tinytuya", "--quiet"])
    import tinytuya

# ── Configuratie (pas aan of geef als argument mee) ─────────────────────────
DEVICE_ID  = "VULL_DEVICE_ID_IN"
LOCAL_KEY  = "VULL_LOCAL_KEY_IN"
DEVICE_IP  = "VULL_IP_IN"
VERSION    = 3.3   # verander naar 3.4 of 3.5 als de scan dat teruggaf

if len(sys.argv) >= 4:
    DEVICE_ID = sys.argv[1]
    LOCAL_KEY = sys.argv[2]
    DEVICE_IP = sys.argv[3]
if len(sys.argv) == 5:
    VERSION   = float(sys.argv[4])

if "VULL_" in DEVICE_ID or "VULL_" in LOCAL_KEY or "VULL_" in DEVICE_IP:
    print("Fout: vul DEVICE_ID, LOCAL_KEY en DEVICE_IP in bovenaan het script")
    print("of geef ze mee als argument: python3 stap_c_poll_dps.py <id> <key> <ip> [versie]")
    sys.exit(1)

# ── Bekende DPS-betekenissen voor Intex/Tuya-spa's ─────────────────────────
# Dit is een geraadpleegde mapping; precieze nummers kunnen per firmware verschillen.
BEKENDE_DPS: dict[str, str] = {
    "1":  "Power (aan/uit)",
    "2":  "Target temperatuur (°C × 1 of × 10)",
    "3":  "Huidige watertemperatuur (°C × 1 of × 10)",
    "4":  "Verwarming aan/uit",
    "5":  "Filter-pomp aan/uit",
    "6":  "Bubbels / hydrojets aan/uit",
    "7":  "Sanitizer / ozon aan/uit",
    "8":  "Vergrendeling / kinderslot",
    "11": "Fout-code",
    "101": "Power",
    "102": "Doeltemperatuur",
    "103": "Watertemperatuur",
    "104": "Verwarming",
    "105": "Filter",
    "106": "Bubbels",
    "107": "Sanitizer",
    "108": "Vergrendeling",
    "115": "Fout-code",
}

print("\n" + "=" * 60)
print("  INTEX SPA — DPS POLL (STAP C)")
print("=" * 60)
print(f"[*] IP:        {DEVICE_IP}")
print(f"[*] Device ID: {DEVICE_ID}")
print(f"[*] Key:       {'*' * len(LOCAL_KEY)}  ({len(LOCAL_KEY)} tekens)")
print(f"[*] Versie:    {VERSION}\n")

# ── Verbinding maken ─────────────────────────────────────────────────────────
d = tinytuya.Device(
    dev_id=DEVICE_ID,
    address=DEVICE_IP,
    local_key=LOCAL_KEY,
    version=VERSION,
    persist=True,
)
d.set_socketTimeout(5)

# ── Eén keer alle DPS ophalen ────────────────────────────────────────────────
print("[*] Status ophalen (alle DPS in één keer)...")
status = d.status()

if "Error" in status or "error" in status:
    print(f"\n[!] Fout bij ophalen: {status}")
    print("\nMogelijke oorzaken:")
    print("  • Verkeerde local_key")
    print("  • Verkeerd protocol-versienummer (probeer 3.4 of 3.5)")
    print("  • IP niet bereikbaar of firewall blokkeert poort 6668")
    sys.exit(1)

dps = status.get("dps", {})
print(f"\n[+] {len(dps)} DPS-waarden ontvangen:\n")
print(f"  {'DPS':>5}  {'Waarde':<20}  Bekende betekenis")
print("  " + "-" * 55)
for key in sorted(dps.keys(), key=lambda x: int(x) if x.isdigit() else 9999):
    waarde    = dps[key]
    betekenis = BEKENDE_DPS.get(str(key), "onbekend — noteer waarde bij wijzigen")
    print(f"  {key:>5}  {str(waarde):<20}  {betekenis}")

print()

# ── Opslaan ──────────────────────────────────────────────────────────────────
uitvoer = "dps_resultaat.json"
with open(uitvoer, "w") as f:
    json.dump({"device_id": DEVICE_ID, "ip": DEVICE_IP, "version": VERSION, "dps": dps}, f, indent=2)
print(f"[+] DPS opgeslagen in: {uitvoer}")

# ── Continu pollen om wijzigingen te detecteren ──────────────────────────────
print()
antwoord = input("Wil je continu pollen zodat je DPS kunt identificeren door spa-knoppen te drukken? [j/N] ").strip().lower()
if antwoord not in ("j", "ja", "y", "yes"):
    print("\n>>> Kopieer de DPS-tabel hierboven en geef hem door voor STAP D.")
    sys.exit(0)

print("\n[*] Continu pollen (Ctrl+C om te stoppen). Druk knoppen op de spa en let op wijzigingen.\n")
vorige = dict(dps)
try:
    while True:
        time.sleep(2)
        status = d.status()
        huidige = status.get("dps", {})
        for k, v in huidige.items():
            if vorige.get(k) != v:
                betekenis = BEKENDE_DPS.get(str(k), "?")
                print(f"  WIJZIGING  DPS {k:>5} : {str(vorige.get(k, '?')):<15} → {v}   ({betekenis})")
        vorige = dict(huidige)
except KeyboardInterrupt:
    print("\n[*] Gestopt.")
    print(">>> Noteer de DPS-nummers per functie en geef ze door voor STAP D.")
