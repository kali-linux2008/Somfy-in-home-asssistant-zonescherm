# Bedrading CC1101 → ESP32

Tekstueel pinout-schema ter aanvulling op de tabel in de [README](../README.md).

```
        ESP32                         CC1101 (433 MHz)
   +--------------+                 +------------------+
   |          3V3 |---------------->| VCC   (3,3V !)   |
   |          GND |---------------->| GND              |
   |       GPIO5  |---------------->| CSN              |
   |       GPIO18 |---------------->| SCK              |
   |       GPIO23 |---------------->| MOSI / SI        |
   |       GPIO19 |<----------------| MISO / SO        |
   |       GPIO2  |<--------------->| GDO0  (data)     |
   |       GPIO4  |<----------------| GDO2  (data RX)  |
   +--------------+                 +--------+---------+
                                             |
                                          [ ANT ]  ~17,3 cm / spring-antenne
```

## Aandachtspunten

- **3,3 V, nooit 5 V** op de CC1101.
- Houd de SPI-draden kort en de antenne vrij van metaal/storing.
- De pinnen zijn de standaardwaarden van ESPSomfy RTS en zijn in de web-UI
  aanpasbaar als je andere GPIO's wilt gebruiken.
- GDO0 wordt gebruikt voor het zenden/ontvangen van de datastroom; GDO2 is
  optioneel maar wel aangeraden voor betrouwbare ontvangst.

## CC1101 pin-varianten

Veel CC1101-modules hebben de pinnen anders gelabeld. Veelvoorkomende namen:

| In deze docs | Andere labels die je kunt tegenkomen |
|--------------|--------------------------------------|
| CSN          | CS, SS, NSS                          |
| MOSI         | SI, MOSI                             |
| MISO         | SO, MISO                             |
| SCK          | SCLK, CLK                            |
| GDO0         | GD0, GDO0                            |
| GDO2         | GD2, GDO2                            |

Controleer altijd de print/datasheet van jouw specifieke module.
