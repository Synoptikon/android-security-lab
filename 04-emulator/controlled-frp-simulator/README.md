# Controlled FRP Simulator

Interfaz web para reproducir estados de seguridad de Android en un entorno controlado.

## Incluye
- Selector de versiones Android y modelos de referencia.
- Pantalla de bloqueo simulada: patrón, contraseña o cuenta Google.
- Estados simulados de Provisioning, FRP, ADB y bootloader.
- Registro y exportación de evidencia JSON.
- Alcance explícito `controlled-simulator-only`.

## Seguridad
Este módulo no implementa bypass de FRP, extracción de credenciales, explotación de Setup Wizard, modificación de dispositivos, comunicación ADB/USB ni acceso a cuentas. La interacción solo genera un evento local con resultado `BLOCKED`.

## Ejecución
Abrir `index.html` en un navegador moderno. No requiere backend ni dependencias externas.
