"""
STAP B (herzien) — mitmproxy addon voor Intex cloud-API capture
Logt ALLE HTTPS-verkeer van de Intex Link app: auth, device-status, commando's.

GEBRUIK:
    mitmdump --listen-host 0.0.0.0 --listen-port 8080 -s stap_b2_intex_api_capture.py

Output: intex_api_log.json  (alle requests + responses)
        intex_api_commands.log  (alleen commando's / status-calls, leesbaar)
"""

import json
from datetime import datetime
from mitmproxy import http

LOGBESTAND     = "intex_api_log.json"
LEESBAAR_LOG   = "intex_api_commands.log"

# Sleutelwoorden die duiden op Intex/Tuya API-verkeer
INTERESSANTE_HOSTS = [
    "intex", "tuya", "smart", "iot", "api", "cloud",
    "device", "control", "openapi",
]

class IntexApiCapture:
    def __init__(self):
        print("\n" + "=" * 60)
        print("  INTEX CLOUD-API CAPTURE")
        print("=" * 60)
        print(f"[*] Alle API-calls worden gelogd in:")
        print(f"    {LOGBESTAND}  (volledig, JSON)")
        print(f"    {LEESBAAR_LOG}  (leesbaar overzicht)")
        print("[*] Stel telefoon-proxy in op dit PC-IP:8080")
        print("[*] Installeer mitmproxy CA-cert op je telefoon")
        print("[*] Open Intex Link app en gebruik de spa (aan/uit, temp, etc.)")
        print("[*] Druk Ctrl+C als je klaar bent\n")

    def request(self, flow: http.HTTPFlow) -> None:
        """Log uitgaande requests (commando's naar de cloud)."""
        self._verwerk(flow, richting="REQUEST")

    def response(self, flow: http.HTTPFlow) -> None:
        """Log inkomende responses (status van de cloud)."""
        self._verwerk(flow, richting="RESPONSE")

    def _verwerk(self, flow: http.HTTPFlow, richting: str) -> None:
        host = flow.request.host.lower()

        # Filter: alleen interessant verkeer loggen
        # Alles loggen als host onbekend is (veiligheidsnet)
        is_interessant = any(kw in host for kw in INTERESSANTE_HOSTS)

        # Altijd loggen als de body "device", "temp", "power" bevat
        try:
            if richting == "REQUEST":
                body_tekst = flow.request.get_text(strict=False) or ""
            else:
                if flow.response is None:
                    return
                body_tekst = flow.response.get_text(strict=False) or ""
        except Exception:
            body_tekst = ""

        bevat_device_info = any(kw in body_tekst.lower() for kw in [
            "device", "temp", "power", "status", "command",
            "switch", "heat", "bubble", "filter", "token", "uid",
        ])

        if not (is_interessant or bevat_device_info):
            return

        # Body parsen
        try:
            body_json = json.loads(body_tekst)
        except Exception:
            body_json = None

        timestamp = datetime.now().isoformat()
        url       = flow.request.pretty_url
        methode   = flow.request.method

        # Request-headers (voor auth-tokens)
        headers = dict(flow.request.headers)

        entry = {
            "timestamp": timestamp,
            "richting":  richting,
            "methode":   methode,
            "url":       url,
            "host":      flow.request.host,
            "pad":       flow.request.path,
            "headers":   headers,
        }

        if richting == "REQUEST":
            entry["body"] = body_json or body_tekst[:4000]
        else:
            entry["status"]        = flow.response.status_code
            entry["resp_headers"]  = dict(flow.response.headers)
            entry["body"]          = body_json or body_tekst[:8000]

        # ── Volledig JSON-log ────────────────────────────────────────────
        with open(LOGBESTAND, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, indent=2))
            f.write("\n" + "-" * 40 + "\n")

        # ── Leesbaar log ─────────────────────────────────────────────────
        leesbaar = (
            f"\n[{timestamp}] {richting} {methode} {url}\n"
        )
        if richting == "REQUEST" and body_tekst.strip():
            leesbaar += f"  BODY: {body_tekst[:500]}\n"
        elif richting == "RESPONSE" and flow.response:
            leesbaar += f"  STATUS: {flow.response.status_code}\n"
            if body_json:
                leesbaar += f"  RESP:   {json.dumps(body_json, ensure_ascii=False)[:800]}\n"
            elif body_tekst.strip():
                leesbaar += f"  RESP:   {body_tekst[:500]}\n"

        with open(LEESBAAR_LOG, "a", encoding="utf-8") as f:
            f.write(leesbaar)

        # Terminal-output
        print(f"[{richting}] {methode} {flow.request.host}{flow.request.path[:60]}")
        if richting == "RESPONSE" and flow.response:
            print(f"           → HTTP {flow.response.status_code}")


def load(loader):  # noqa
    return IntexApiCapture()
