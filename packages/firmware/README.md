# HIRI-firmware (Firmware)

PlatformIO project for **ESP32** and **ESP8266**.

## Build



## TLS MQTT (securise)

Ajouter les flags de compilation pour activer TLS :



Configurer les certificats dans  :
-  : certificat CA (PEM)
-  : certificat client (optionnel)
-  : cle privee client (optionnel)

Par defaut, TLS est desactive ().

## Deep Sleep (basse consommation)

Pour les noeuds sur batterie, activer le deep sleep :



Options de configuration :
-  : active le deep sleep (defaut: 0)
-  : duree du sommeil en secondes (defaut: 300)
-  : broche de reveil (defaut: GPIO_NUM_0)

## Battery Reporting

Activer la surveillance de la batterie :



Configuration :
-  : broche ADC pour la tension batterie (defaut: 35)
-  : ratio du diviseur de tension (defaut: 2.0)
-  : topic MQTT pour le rapport de batterie

Le firmware publie la tension batterie toutes les 60 secondes sur le topic MQTT configure.
La decouverte HA cree automatiquement un capteur de tension.

## Configure

Edit  (WiFi + MQTT broker = Home Assistant Mosquitto).

Sensor hardware is configurable in  or PlatformIO
:

- , , and  enable DHT22
  temperature readings.
- , , , and
   enable calibrated soil ADC readings.

Defaults keep simulated telemetry enabled when hardware is disabled, missing, or
returns an invalid reading.

## Features

- HA MQTT discovery for switch + soil + temperature + battery
- Optional DHT22 temperature and soil ADC moisture drivers
- Optional TLS MQTT for secure communication
- Optional deep sleep for battery-powered nodes
- Optional battery voltage monitoring and reporting
- Compact telemetry loop (10s)
- Command topic for relay

## Bounties

Real sensors, OTA, deep sleep, TLS MQTT — see monorepo issues labeled .
