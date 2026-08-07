# Demo End-to-End HIRI

## Video et captures d'ecran

Ce document decrit le parcours complet end-to-end de HIRI : du firmware ESP32 au dashboard web.

### Etape 1 : Broker MQTT
```
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto
```

### Etape 2 : Bridge HIRI
```
pip install -e ".[api,mqtt]"
hiri-bridge serve --host 0.0.0.0 --port 8780
```

### Etape 3 : Demo
```
hiri-bridge demo
```

### Etape 4 : Firmware ESP32
```
pio run -e esp32dev
```

### Resultat attendu
Dashboard web avec appareils regroupes par zone, recherche et controle on/off.
API REST sur http://localhost:8780 avec /health, /devices, /areas, /adapters.

Captures dans docs/screenshots/.
