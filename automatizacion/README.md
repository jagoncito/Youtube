# Producción de Jagoncito

## Organización

Los vídeos se guardan directamente en `videos/001`, `videos/002`, `videos/003` y así sucesivamente. Cada carpeta contiene el MP4 de 30 minutos, el MP4 de 6 minutos para bucle, un solo WAV de 6 minutos, imagen, miniatura, textos y fuentes. Los MP4/WAV se suben mediante Git LFS; una carpeta no se considera terminada hasta que sus objetos y su commit estén subidos.

Los registros técnicos están en `entregas/`; no representan vídeos adicionales. `estado.json` identifica la última actividad. La portada del repositorio y `ENTREGAS.md` muestran el orden.

## Regla de novedad

Antes de reservar un número o renderizar, el planificador revisa los manifiestos, los archivos y el historial completo. Rechaza:

- Una imagen o identidad de escena ya usada.
- Recompresiones, cambios de metadatos y variaciones visuales casi idénticas detectadas por la comparación perceptual.
- Un programa musical ya publicado, aunque cambie el orden de las obras o la semilla.
- Un vídeo cuyo máster ya exista.

Las reutilizaciones de los tres vídeos históricos se mantienen documentadas; no conceden permiso para repetirlas en el futuro. Las pruebas técnicas no certifican calidad artística ni éxito en YouTube.

Si no existe una escena y un programa inéditos compatibles, se guarda **`needs_new_assets`**. No se publica un sustituto, no se reserva un número y no se llama «nuevo» a un cambio cosmético.

## Calendario y alcance real

El calendario configurado revisa la cola cada 4 horas (`0 */4 * * *`, UTC); GitHub puede retrasar el inicio. Las modificaciones de código no generan un vídeo por sí solas. También se permite una ejecución manual desde Actions.

La publicación se realiza únicamente cuando hay un plan que supera los controles. El banco actual es finito: después de001–003 queda un programa y escena inéditos —embarcadero con las Gymnopédies 2 y 3—. Tras utilizarlos se necesita ampliar el material; el sistema se bloqueará en lugar de volver a usar una imagen. No hay un generador de ilustraciones con IA autónomo configurado en segundo plano. La preparación editorial de nuevas escenas y repertorio se realiza de forma expresa.

La programación prepara archivos en GitHub; no publica en YouTube. El documento original de 128informes y los datos privados de Studio se mantienen fuera del repositorio.

## Controles

- Integridad de partituras, muestras y licencias.
- Obras completas, duración exacta y audio sin saturación o saltos anómalos.
- Decodificación íntegra de ambos MP4.
- Historial de imágenes, semejanza perceptual, programa y vídeo.
- Archivos reales completos y checksums antes de publicar.
- Git LFS y recuperación de commits o subidas fallidos sin duplicar ni cambiar números.

## Uso

El workflow requiere Python 3.12, FFmpeg, Git LFS y las dependencias fijadas. GitHub proporciona su token de trabajo; no se copian credenciales del chat.

Pruebas:

```bash
python -m unittest discover -s automatizacion/tests -v
python -m unittest discover -s automatizacion/produccion -p 'test*.py' -v
```

Consultar el siguiente plan, sin crear medios:

```bash
python automatizacion/produccion/crear_entrega.py --slot 2026-10-27T16:00:00Z --output /tmp/solo-plan --cache /tmp/jagoncito-piano --plan-only
```

Para recuperar los medios al clonar: `git lfs pull`. Las muestras del instrumento se descargan en una caché externa y se verifican con SHA-256.
