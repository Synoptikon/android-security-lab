# Controlled FRP Simulator

Interfaz web para reproducir estados de seguridad de Android en un entorno controlado.

## Incluye
- Selector de versiones Android y modelos de referencia.
- Pantalla de bloqueo simulada: patrón, contraseña o cuenta Google.
- Setup Wizard modelado como máquina de estados local.
- Fases observables: `WELCOME`, `NETWORK`, `ACCOUNT_GATE`, `RESTORE_CHECK`, `FINISHED`.
- Estados simulados de Provisioning, FRP, ADB y bootloader.
- Registro y exportación de evidencia JSON.
- Alcance explícito `controlled-simulator-only`.

## Setup Wizard
El Wizard representa únicamente transiciones de estado y gates de política. `ACCOUNT_GATE` muestra la condición FRP como bloqueo simulado; no procesa credenciales ni intenta evadir el control.

## Seguridad
Este módulo no implementa bypass de FRP, extracción de credenciales, explotación de Setup Wizard, modificación de dispositivos, comunicación ADB/USB ni acceso a cuentas. Todas las transiciones son locales y reproducibles.

## Ejecución
Abrir `index.html` en un navegador moderno. No requiere backend ni dependencias externas.
