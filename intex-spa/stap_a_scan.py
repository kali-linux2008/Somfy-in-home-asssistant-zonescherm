#!/usr/bin/env python3
"""
STAP A — Tuya netwerk-scan voor Intex spa
Draai dit op je Home Assistant (via SSH) of op een PC in hetzelfde wifi-netwerk als de spa.
Vereiste: Python 3.7+

Installeer en draai:
    pip3 install tinytuya
    python3 stap_a_scan.py
"""

import subprocess
import sys
import json
import socket

# ── tinytuya installeren als het nog niet aanwezig is ──────────────────────
try:
    import tinytuya
except ImportError:
    print("[*] tinytuya niet gevonden, installeren...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tinytuya", "--quiet"])
    import tinytuya

# ── hulpfunctie: eigen IP tonen zodat gebruiker subnet ziet ────────────────
def eigen_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "onbekend"

print("\n" + "=" * 60)
print("  INTEX SPA — TUYA NETWERK-SCAN (STAP A)")
print("=" * 60)
print(f"\n[*] Dit apparaat heeft IP: {eigen_ip()}")
print("[*] Scan stuurt UDP-broadcast op poort 6666/6667/7000.")
print("[*] Vereiste: scanner en spa zitten in hetzelfde subnet.")
print("[*] Duur: ~18 seconden (3 retries × 6 s)\n")

# ── scan uitvoeren ──────────────────────────────────────────────────────────
# verbose=False want we parsen de output zelf netter
devices = tinytuya.deviceScan(verbose=False, maxretry=3)

# ── resultaat tonen ─────────────────────────────────────────────────────────
if not devices:
    print("\n[!] GEEN apparaten gevonden.")
    print()
    print("Mogelijke oorzaken:")
    print("  • Scanner zit niet in hetzelfde subnet als de spa")
    print("    (bijv. HA op VLAN, PC op gastnetwerk)")
    print("  • Spa staat uit of heeft geen wifi-verbinding")
    print("  • Firewall blokkeert UDP 6666/6667/7000")
    print("  • Sommige routers blokkeren UDP-broadcast tussen apparaten")
    print()
    print("Probeer alternatieven:")
    print("  • Draai het script op de PC die wél in hetzelfde wifi-netwerk zit")
    print("  • Of probeer: python3 -m tinytuya wizard")
    sys.exit(1)

print(f"[+] {len(devices)} Tuya-apparaat/apparaten gevonden:\n")

resultaat = {}
for ip, info in devices.items():
    device_id = info.get("gwId") or info.get("devId") or "onbekend"
    versie     = info.get("version", "onbekend")
    product    = info.get("productKey", "onbekend")
    encrypted  = info.get("encrypt", False)

    print("  " + "-" * 50)
    print(f"  IP-adres:       {ip}")
    print(f"  device_id:      {device_id}")
    print(f"  Versie:         {versie}   ← Tuya-protocol (3.3 / 3.4 / 3.5)")
    print(f"  productKey:     {product}")
    print(f"  Versleuteld:    {encrypted}")
    print()

    resultaat[ip] = {
        "ip": ip,
        "device_id": device_id,
        "version": versie,
        "productKey": product,
        "encrypted": encrypted,
        "_raw": info,
    }

# ── opslaan ─────────────────────────────────────────────────────────────────
uitvoer = "tuya_scan_resultaat.json"
with open(uitvoer, "w") as f:
    json.dump(resultaat, f, indent=2)

print(f"[+] Volledig resultaat opgeslagen in: {uitvoer}")
print()
print(">>> VOLGENDE STAP:")
print("    Geef mij de device_id, het IP en de versie van de spa.")
print("    Die info plus de local_key (STAP B) hebben we nodig voor STAP C/D.")
