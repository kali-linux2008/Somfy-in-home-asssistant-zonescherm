# Zonnescherm RTS — Home Assistant integratie

Eigen (herbrande) HACS-integratie, gebaseerd op
[ESPSomfy-RTS-HA](https://github.com/rstrouse/ESPSomfy-RTS-HA) (publiek domein),
voor de `Zonnescherm RTS`-firmware op je ESP32 + CC1101.

Lokale communicatie (websocket, `local_push`) — geen cloud. Je shades verschijnen
als `cover`-entiteiten, plus sensoren (wifi-signaal, geheugen), knoppen en updates.

## Eigen aanpassingen t.o.v. upstream

| Wat | Van → Naar |
|-----|-----------|
| Integratie-domein | `espsomfy_rts` → `zonnescherm_rts` |
| Weergavenaam | `ESPSomfy RTS` → `Zonnescherm RTS` |
| Fabrikant (device) | `rstrouse` → `Zonnescherm RTS` |
| Interne unique-id prefix | `espsomfy_…` → `zonnescherm_…` |
| Event op de bus | `espsomfy-rts_event` → `zonnescherm-rts_event` |
| Docs/issue-links | naar deze repo |

> **Bewust ongewijzigd:** de SSDP/zeroconf **discovery-matchers** in `manifest.json`
> (`urn:schemas-rstrouse-org:device:ESPSomfyRTS:1`, `_espsomfy_rts._tcp.local.`,
> `model: espsomfy*`). Die moeten exact matchen met wat de firmware uitzendt, anders
> wordt je apparaat niet automatisch ontdekt. De firmware-fork is op dat punt niet
> aangepast, dus dit blijft werken.

## Installeren via HACS

1. **HACS → Integraties → ⋮ → Custom repositories**
   - Repository: `https://github.com/kali-linux2008/somfy-in-home-asssistant-zonescherm`
   - Categorie: **Integration**
2. Installeer **Zonnescherm RTS** en **herstart** Home Assistant.
3. **Instellingen → Apparaten & Services**: het apparaat `Zonnescherm` wordt
   meestal automatisch ontdekt. Anders: **Integratie toevoegen → Zonnescherm RTS**
   en vul het IP van de ESP32 in.

## Handmatig installeren (zonder HACS)

Kopieer `custom_components/zonnescherm_rts/` naar de `config/custom_components/` map
van je Home Assistant en herstart.

## Let op
- Installeer **niet** tegelijk de originele `ESPSomfy RTS`-integratie én deze; ze
  ontdekken hetzelfde apparaat. Kies er één.
- Deze integratie hoort bij de firmware-fork in [`../../firmware/`](../../firmware/).
