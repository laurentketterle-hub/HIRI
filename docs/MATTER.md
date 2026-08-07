# Matter Bridge — Research & Scaffold

## Contexte

Matter (anciennement Project CHIP) est le standard de connectivite unifie pour la maison intelligente, soutenu par la Connectivity Standards Alliance (CSA), dont font partie Apple, Google, Amazon, Samsung, et plus de 500 autres societes.

## Architecture proposee

Le bridge HIRI agit comme controleur Matter, exposant les appareils enregistres vers l'ecosysteme Matter via Thread/WiFi.

### Composants cles

1. **Matter Controller** : Le bridge HIRI agit comme controleur Matter
2. **Matter Fabric** : Gestion des commissions et de la securite
3. **Device Type Mapping** : Correspondance entre les domaines HIRI et les types d'appareils Matter
4. **Commissioning** : Processus d'appairage des appareils Matter

## Mapping des types d'appareils

| Domaine HIRI      | Device Type Matter          | Cluster ID |
|--------------------|-----------------------------|------------|
| light              | Extended Color Light        | 0x010D     |
| switch             | On/Off Plug-in Unit         | 0x010A     |
| sensor             | Temperature Sensor          | 0x0302     |
| binary_sensor      | Contact Sensor              | 0x0015     |
| climate            | Thermostat                  | 0x0301     |
| cover              | Window Covering             | 0x0202     |
| lock               | Door Lock                   | 0x0101     |
| fan                | Fan                         | 0x002B     |

## Dependances techniques

- SDK Matter (connectedhomeip) : https://github.com/project-chip/connectedhomeip
- python-matter-server : Implementation Python du controleur Matter
- chip-tool : Outil CLI officiel pour le commissioning

## Prochaines etapes

1. Installer le SDK Matter et valider la compilation
2. Implementer le commissioning via BLE/WiFi
3. Ajouter le support Thread Border Router
4. Tests end-to-end avec un appareil Matter reel
5. Documentation utilisateur pour la configuration

## References

- Specification Matter : https://csa-iot.org/developer-resource/specifications-download-request/
- Project CHIP GitHub : https://github.com/project-chip/connectedhomeip
- Home Assistant Matter : https://www.home-assistant.io/integrations/matter/

## Statut

Phase actuelle : Recherche et scaffold — PR initiale avec documentation + stub
Effort estime : 100 MRG (phase 1)
