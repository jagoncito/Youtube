# Producción del vídeo

La entrega utiliza una escena animada de **12 segundos**, una secuencia musical de **6 minutos** y un montaje de **30 minutos**. La secuencia musical contiene las dos obras completas de Satie; el montaje largo repite esa secuencia cinco veces.

## Escena y animación

`animar_escena.py` parte de `imagen.png` y prepara una imagen de salida de **1920 × 1080**. La ilustración original mide 1672 × 941; se escala y se recorta ligeramente para llenar el formato 16:9.

Los efectos se generan con FFmpeg:

- Lluvia sobre los cristales mediante trayectorias ASS, con posiciones y fases reproducibles.
- Luz local de la chimenea que varía con dos funciones coseno de periodos de 3 y 1,2 segundos. Su pendiente es cero al cerrar el ciclo.
- Un desplazamiento local de hasta unos dos píxeles en el gato, con periodo de 6 segundos, para sugerir respiración. El mapa se redondea alrededor de su posición neutra y se suaviza con tres fotogramas consecutivos.

Los periodos de los efectos encajan en los **12 segundos** de la escena. El programa genera **24 segundos** y conserva únicamente el segundo ciclo de doce segundos, con su GOP cerrado. El primer ciclo sirve de preparación al codificador. Se utiliza H.264/libx264, CRF 10, formato de píxel yuv420p y 24 fotogramas por segundo.

`validacion-animacion.json` registra la comparación entre el cierre de la escena y los cambios entre fotogramas ordinarios. También recoge una comprobación independiente de la fuente sin compresión. En esta última, el fuego y el gato coinciden al cerrar el ciclo; la lluvia conserva su movimiento de un fotograma al siguiente. Es una verificación técnica de esta producción, acompañada de inspección de un fotograma decodificado.

## Montaje y audio

`montar_videos.py` repite la escena de doce segundos **30 veces** para `bucle-6min.mp4` y **150 veces** para `video-30min.mp4`. Copia la pista H.264 ya codificada, de modo que esta fase de montaje conserva sus fotogramas.

El audio se codifica por separado como **AAC estéreo de 192 kb/s a 44.100 Hz**:

- El vídeo de seis minutos utiliza una vuelta de `audio-bucle-6min.wav`.
- El vídeo de treinta minutos codifica continuamente cinco vueltas del WAV. Así se evita concatenar cinco archivos AAC codificados de forma independiente.
- Solo el vídeo de treinta minutos recibe un fundido de audio de **3 segundos**, desde **29:57** hasta el final. El WAV y el vídeo de seis minutos conservan el final destinado a repetirse.

El MP4 incluye sus metadatos de reproducción al principio del archivo mediante `+faststart`. La música, las fuentes y los parámetros de audio se documentan en [LEEME-AUDIO.md](LEEME-AUDIO.md).

## Reproducir el proceso

Se necesita Python 3 y una instalación de FFmpeg que incluya libx264, libass y el codificador AAC. Las fuentes de sistema deben permitir resolver DejaVu Sans para las pistas ASS. También deben estar presentes `imagen.png` y `audio-bucle-6min.wav` en la carpeta de esta entrega. Para reconstruir el WAV, seguir primero `LEEME-AUDIO.md`.

Desde la carpeta `videos/002-jagoncito-satie/`:

```bash
python3 produccion/animar_escena.py --output /tmp/jagoncito-escena-12s.mp4
python3 produccion/montar_videos.py --scene-template /tmp/jagoncito-escena-12s.mp4
```

El primer comando prepara la escena y escribe sus trayectorias en `produccion/lluvia.ass`. El segundo reutiliza la escena y genera `bucle-6min.mp4` y `video-30min.mp4` en la carpeta de la entrega. Los scripts sobrescriben esos archivos de salida al reconstruirlos.

## Descargar el vídeo largo

`video-30min.mp4` está gestionado por Git LFS, según `.gitattributes` en la raíz del repositorio. En la web de GitHub se descarga con **Download / Descargar** desde la página del archivo. Para un clon local con Git LFS instalado, ejecutar desde la raíz:

```bash
git lfs pull
```

El repositorio guarda un puntero pequeño en Git y el MP4 completo en el almacenamiento LFS. Los documentos y los archivos de producción permiten conservar el proceso junto al vídeo.
