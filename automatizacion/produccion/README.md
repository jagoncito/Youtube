# Productor de entregas inéditas

El productor crea un programa musical completo y sus medios. Antes de generar, comprueba el historial: la imagen y la escena deben ser inéditas y el conjunto de obras no puede coincidir con otro programa publicado, aunque cambie su orden o semilla.

## Ejecutar

```bash
python -m pip install -r automatizacion/produccion/requirements.txt
python automatizacion/produccion/crear_entrega.py --slot 2026-10-27T16:00:00Z --output /tmp/entrega-jagoncito --cache /tmp/jagoncito-piano-cache
```

Requiere Python3.12 y FFmpeg con libx264 y libass. Los MIDI revisados ya están incluidos; el runner no necesita LilyPond. Las muestras se descargan en una caché externa, conservando TLS y la comprobación SHA-256.

- `--slot`: turno UTC00/04/08/12/16/20, con minutos y segundos cero.
- `--plan-only`: comprueba la disponibilidad y devuelve el plan sin crear medios.
- `--plan-id`: solicita un plan concreto, sujeto a los mismos controles de originalidad.
- `--catalog`: banco alternativo previamente revisado.
- `--history-exclude-tag`: uso interno para reintentar únicamente una reserva pendiente o fallida; no permite excluir un vídeo publicado.
- La salida no debe existir. Solo aparece como paquete completo después de superar los controles.

Sin material inédito se produce `needs_new_assets`. Cambiar el título, la semilla o el formato de imagen no permite saltarse ese bloqueo.

## Paquete

`video-30min.mp4`, `bucle-6min.mp4`, `audio-bucle-6min.wav`, `imagen.png`, `miniatura.jpg`, `publicacion.txt`, `README.md`, `manifest.json` y `fuentes/`.

El WAV dura360s y contiene dos obras completas. El vídeo de30min repite cinco veces ese programa con audio codificado continuamente; el fundido final se sitúa después del final escrito de la obra. Los dos MP4 incorporan el audio. El publicador coloca los archivos reales en `videos/NNN/` mediante Git LFS; no crea carpetas puente ni nuevas Releases.

## Banco y novedad

El banco inicial contiene las tres Gymnopédies de Satie y tres escenas revisadas. Las entregas001–003 ya consumen la habitación nocturna, el taller y los programas[1,3]y[1,2]. Queda inédito el embarcadero con el programa[2,3]. Una vez utilizado se necesitan nuevas escenas y repertorio para continuar.

El control combina SHA-256, identidad de escena, conjunto de obras sin orden y comparación perceptual de imágenes decodificadas. Compara también las carpetas históricas sin registro y las recodificaciones con metadatos distintos. No es una evaluación artística ni garantiza alcance o monetización.

Una escena nueva requiere imagen, miniatura1280×720, plantilla H.2641920×1080/24fps de12s y su manifiesto de revisión. Los hashes y los controles de periodicidad se verifican antes de usarla. La imagen principal y su miniatura se preparan expresamente; no hay un generador autónomo de ilustraciones configurado.

Las plantillas de taller y embarcadero solo animan lluvia en máscaras exteriores. No se atribuye movimiento a sus animales. Los informes guardan la comparación relativa y los límites absolutos de cuantización, junto con el control RAW de periodicidad.

## Música y comprobaciones

Las partituras Mutopia y las transcripciones para separar voces tienen hashes fijados en `fuentes.json`. Las fuentes de Evin Robertson están marcadas como dominio público. El piano VSCO2CE usa muestras CC0 y conserva su licencia y manifiesto. Un render nuevo de Satie no se describe como composición original ni ejecución humana.

Se comprueban notas y duraciones completas, sonoridad, pico verdadero, saturación, unión circular, formato y duración. Ambos MP4 se decodifican íntegramente antes de entregar. El manifiesto registra programa, escena, fuentes, parámetros, capítulos y huellas. Estos controles técnicos no se presentan como escucha humana.

Pruebas:

```bash
python -m unittest discover -s automatizacion/produccion -p 'test*.py' -v
```

Incluyen historial completo, recodificación PNG/JPEG con SHA e ID distintos, imágenes sin índice, escenas genuinamente distintas, colores planos, programa reordenado, banco agotado, integridad de fuentes y plantillas y el anterior salto geométrico de animación.
