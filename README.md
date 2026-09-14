# Android Security Lab

Laboratorio controlado para investigar y reproducir estados de seguridad de Android relacionados con ADB, provisioning, Setup Wizard y Factory Reset Protection (FRP).

## Alcance

El proyecto está destinado exclusivamente a dispositivos propios, emuladores, AOSP y cuentas de prueba. No proporciona mecanismos para evadir controles antirrobo ni recuperar acceso a dispositivos de terceros.

## Pipeline

1. Inventario
2. Identificación del dispositivo/emulador
3. Estado y autorización ADB
4. Estado de provisioning / FRP
5. Reproducción controlada
6. Captura de evidencia
7. Análisis de superficie de ataque
8. Mitigación y validación

## Estructura

- `00-governance/` — alcance, reglas y criterios del laboratorio.
- `01-environment/` — requisitos del entorno.
- `02-inventory/` — inventario técnico.
- `03-adb/` — observación del estado ADB.
- `04-emulator/` — escenarios reproducibles.
- `05-frp-analysis/` — análisis de provisioning/FRP.
- `06-tests/` — pruebas controladas.
- `07-evidence/` — evidencia reproducible.
- `12-scripts/` — automatización.
- `13-results/` — resultados crudos y normalizados.

## Principio de reproducibilidad

Cada experimento debe registrar estado inicial, procedimiento, comandos ejecutados, evidencia obtenida y resultado verificable.
