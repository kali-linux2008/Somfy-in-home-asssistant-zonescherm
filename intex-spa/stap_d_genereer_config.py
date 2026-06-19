#!/usr/bin/env python3
"""
STAP D — Genereert de LocalTuya-configuratie (YAML + GUI-instructies) voor Home Assistant.

Vul de DPS-mapping in op basis van wat je in STAP C hebt gevonden.
Gebruik:
    python3 stap_d_genereer_config.py
of laad het JSON-bestand uit STAP C automatisch:
    python3 stap_d_genereer_config.py dps_resultaat.json
"""

import sys
import json
from pathlib import Path

# ── DPS-mapping (pas aan na STAP C) ────────────────────────────────────────
# Vul hier de DPS-nummers in die je hebt geïdentificeerd.
# Als je een nummer niet weet, zet hem op None.
DPS_MAP = {
    "power":       "1",    # True/False
    "target_temp": "2",    # geheel getal (°C of ×10, zie hieronder)
    "current_temp": "3",   # geheel getal (alleen lezen)
    "heater":      "4",    # True/False
    "filter":      "5",    # True/False
    "bubbles":     "6",    # True/False
    "sanitizer":   "7",    # True/False
    "lock":        "8",    # True/False  (optioneel)
    "error_code":  "11",   # string/int  (optioneel)
}

# Temperatuurschaal: sommige Tuya-spa's geven temp ×10 terug (bijv. 380 = 38,0 °C)
TEMP_FACTOR = 1   # zet op 10 als de waarden ×10 zijn

# ── Configuratiedata (vul in na STAP A + B) ─────────────────────────────────
DEVICE_ID  = "VULL_DEVICE_ID_IN"
DEVICE_IP  = "VULL_IP_IN"
LOCAL_KEY  = "VULL_LOCAL_KEY_IN"
VERSION    = "3.3"   # "3.3", "3.4" of "3.5"
NAAM       = "Intex Spa"

# ── Optioneel: laad dps_resultaat.json ──────────────────────────────────────
if len(sys.argv) == 2:
    pad = Path(sys.argv[1])
    if pad.exists():
        data = json.loads(pad.read_text())
        DEVICE_ID = data.get("device_id", DEVICE_ID)
        DEVICE_IP = data.get("ip", DEVICE_IP)
        VERSION   = str(data.get("version", VERSION))
        print(f"[*] Geladen uit {pad}: id={DEVICE_ID}, ip={DEVICE_IP}, versie={VERSION}")

# ── YAML genereren ───────────────────────────────────────────────────────────
def dps(naam: str) -> str:
    return DPS_MAP.get(naam, "??")

temp_divisor = f"\n          # Temperatuurschaal ×{TEMP_FACTOR}" if TEMP_FACTOR != 1 else ""

yaml_blok = f"""# ============================================================
# LocalTuya configuratie voor Intex Spa
# Gegenereerd door stap_d_genereer_config.py
# Kopieer dit naar je configuration.yaml of een aparte include.
# ============================================================

localtuya:
  - host: {DEVICE_IP}
    device_id: {DEVICE_ID}
    local_key: {LOCAL_KEY}
    protocol_version: "{VERSION}"
    friendly_name: {NAAM}
    entities:

      # ── Hoofd-schakelaar ──────────────────────────────────
      - platform: switch
        friendly_name: "{NAAM} Stroom"
        id: {dps("power")}

      # ── Verwarming ────────────────────────────────────────
      - platform: switch
        friendly_name: "{NAAM} Verwarming"
        id: {dps("heater")}

      # ── Filter-pomp ───────────────────────────────────────
      - platform: switch
        friendly_name: "{NAAM} Filter"
        id: {dps("filter")}

      # ── Bubbels ───────────────────────────────────────────
      - platform: switch
        friendly_name: "{NAAM} Bubbels"
        id: {dps("bubbles")}

      # ── Sanitizer / ozon ─────────────────────────────────
      - platform: switch
        friendly_name: "{NAAM} Sanitizer"
        id: {dps("sanitizer")}

      # ── Doeltemperatuur ───────────────────────────────────
      - platform: number
        friendly_name: "{NAAM} Doeltemperatuur"
        id: {dps("target_temp")}
        min_value: 20
        max_value: 40
        step_size: 1{temp_divisor}
        # Verwijder scale_factor als temp_factor 1 is:
        # scale_factor: {TEMP_FACTOR}

      # ── Huidige temperatuur ───────────────────────────────
      - platform: sensor
        friendly_name: "{NAAM} Watertemperatuur"
        id: {dps("current_temp")}
        unit_of_measurement: "°C"
        device_class: temperature
        # scale_factor: {TEMP_FACTOR}  (verwijder als temp_factor 1 is)

      # ── Foutcode (optioneel) ──────────────────────────────
      - platform: sensor
        friendly_name: "{NAAM} Foutcode"
        id: {dps("error_code")}
"""

# ── Klimaat-entiteit (volledigere integratie) ────────────────────────────────
yaml_klimaat = f"""
# ── Alternatief: climate-entiteit (één kaart in HA) ──────────────────────────
# Vereist dat target_temp en current_temp correct zijn.

climate:
  - platform: generic_thermostat
    name: "{NAAM}"
    heater: switch.{NAAM.lower().replace(" ", "_")}_verwarming
    target_sensor: sensor.{NAAM.lower().replace(" ", "_")}_watertemperatuur
    min_temp: 20
    max_temp: 40
    cold_tolerance: 0.5
    hot_tolerance: 0.5
    initial_hvac_mode: "heat"
"""

uitvoer_yaml = "localtuya_config.yaml"
Path(uitvoer_yaml).write_text(yaml_blok + yaml_klimaat, encoding="utf-8")

print("\n" + "=" * 60)
print("  LOCALTUYA CONFIGURATIE — STAP D")
print("=" * 60)
print(yaml_blok)
print(yaml_klimaat)
print(f"[+] Configuratie opgeslagen in: {uitvoer_yaml}")

print("""
=== IMPORTEREN VIA HOME ASSISTANT GUI (LocalTuya xZetsubou) ===

1. Ga naar HA → Instellingen → Apparaten & Services → LocalTuya → Configureren
2. Kies "Voeg apparaat toe"
3. Vul in:
   • Host:         """ + DEVICE_IP + """
   • Device ID:    """ + DEVICE_ID + """
   • Local Key:    """ + LOCAL_KEY + """
   • Protocol:     """ + VERSION + """
4. HA detecteert automatisch de DPS. Koppel per DPS de juiste entiteit:
   • DPS """ + dps("power")       + """ → Switch "Stroom"
   • DPS """ + dps("heater")      + """ → Switch "Verwarming"
   • DPS """ + dps("filter")      + """ → Switch "Filter"
   • DPS """ + dps("bubbles")     + """ → Switch "Bubbels"
   • DPS """ + dps("sanitizer")   + """ → Switch "Sanitizer"
   • DPS """ + dps("target_temp") + """ → Number "Doeltemperatuur"
   • DPS """ + dps("current_temp")+ """ → Sensor "Watertemperatuur"
5. Sla op — de spa verschijnt nu als apparaat in HA.
""")
