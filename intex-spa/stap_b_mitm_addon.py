"""
STAP B — mitmproxy addon: onderschept Tuya/Intex localKey uit HTTPS-verkeer

INSTALLATIE (op je PC/Linux):
    pip3 install mitmproxy

GEBRUIK:
    mitmproxy --listen-host 0.0.0.0 --listen-port 8080 -s stap_b_mitm_addon.py

Of als je liever de terminal-versie wilt (geen TUI):
    mitmdump --listen-host 0.0.0.0 --listen-port 8080 -s stap_b_mitm_addon.py

Keys worden gelogd naar: gevonden_keys.log
Zodra een LOCAL KEY verschijnt, staat die ook in de terminal (grote melding).
"""

import json
import re
from datetime import datetime
from mitmproxy import http  # type: ignore  (alleen beschikbaar binnen mitmproxy)

LOGBESTAND = "gevonden_keys.log"

# Tuya-velden die we willen vangen
INTERESSANTE_VELDEN = [
    "localKey", "local_key", "localkey",
    "devId", "deviceId", "device_id",
    "productKey", "uuid", "gwId",
]

# Regex-patronen voor het extraheren van waarden (JSON-strings én getallen)
_RE_STRING = re.compile(r'"({key})"\s*:\s*"([^"]+)"')
_RE_NUMBER = re.compile(r'"({key})"\s*:\s*(\d+)')


def _extract(body: str, key: str) -> list:
    """Geeft een lijst met gevonden waarden voor 'key' in de JSON-body."""
    hits = _RE_STRING.pattern.replace("{key}", re.escape(key))
    results = re.findall(hits, body)
    results += re.findall(_RE_NUMBER.pattern.replace("{key}", re.escape(key)), body)
    return [v for _, v in results]


class IntexKeyCapture:
    def __init__(self):
        print("\n" + "=" * 60)
        print("  INTEX KEY CAPTURE — STAP B")
        print("=" * 60)
        print(f"[*] Addon geladen. Logbestand: {LOGBESTAND}")
        print("[*] Zet je telefoon-proxy in op dit PC-IP:8080")
        print("[*] Installeer het mitmproxy CA-certificaat (zie README)")
        print("[*] Open de Intex Link-app en ververs de apparaatlijst")
        print("[*] Wacht op de melding 'LOCAL KEY GEVONDEN' hieronder\n")

    # ── elke HTTPS-response passeren ────────────────────────────────────────
    def response(self, flow: http.HTTPFlow) -> None:
        url = flow.request.pretty_url

        try:
            body = flow.response.get_text(strict=False) or ""
        except Exception:
            return

        if not body:
            return

        # Snel check: zit er iets nuttigs in?
        if not any(kw in body for kw in INTERESSANTE_VELDEN):
            return

        timestamp = datetime.now().isoformat()
        log: dict = {
            "timestamp": timestamp,
            "url": url,
            "method": flow.request.method,
            "status": flow.response.status_code,
        }

        # ── JSON-body proberen te parsen ────────────────────────────────────
        try:
            log["body"] = json.loads(body)
        except json.JSONDecodeError:
            log["body_tekst"] = body[:8000]

        # ── Per veld extracten en loggen ────────────────────────────────────
        gevonden_keys = {}
        for veld in INTERESSANTE_VELDEN:
            waarden = _extract(body, veld)
            if waarden:
                gevonden_keys[veld] = waarden

        if gevonden_keys:
            log["gevonden"] = gevonden_keys

        # ── Grote melding als localKey aanwezig ─────────────────────────────
        local_key_hits = (
            gevonden_keys.get("localKey")
            or gevonden_keys.get("local_key")
            or gevonden_keys.get("localkey")
        )
        if local_key_hits:
            banner = "!" * 60
            print(f"\n{banner}")
            print("  *** LOCAL KEY GEVONDEN ***")
            for k in ["localKey", "local_key", "localkey"]:
                vals = gevonden_keys.get(k)
                if vals:
                    for v in vals:
                        print(f"  {k:12s} = {v}")
            for k in ["devId", "deviceId", "device_id", "gwId"]:
                vals = gevonden_keys.get(k)
                if vals:
                    for v in vals:
                        print(f"  {k:12s} = {v}")
            print(f"  URL        = {url}")
            print(f"  Logbestand = {LOGBESTAND}")
            print(banner + "\n")
        else:
            print(f"[+] Interessant verkeer van: {url}")
            print(f"    Velden: {list(gevonden_keys.keys())}")

        # ── Wegschrijven naar logbestand ────────────────────────────────────
        with open(LOGBESTAND, "a", encoding="utf-8") as f:
            f.write(json.dumps(log, ensure_ascii=False, indent=2))
            f.write("\n" + "-" * 40 + "\n")


# mitmproxy roept load() aan bij het inladen van de addon
def load(loader):  # noqa: ANN001
    return IntexKeyCapture()
