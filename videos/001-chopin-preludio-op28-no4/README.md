# Chopin — una tarde de otoño

Primera entrega para Jagoncito: **Preludio en mi menor, op. 28 n.º 4**, con tres interpretaciones digitales completas y pequeñas variaciones expresivas. **Duración: 6:46.** Una escena fija nocturna acompaña la música. La lluvia que aparece en la imagen no añade sonidos de lluvia al audio.

## Archivos para publicar

- **[video.mp4](video.mp4)**: vídeo terminado en 1920 × 1080, 24 fps, H.264 y audio AAC.
- **[audio.wav](audio.wav)**: único máster de audio independiente, estéreo PCM de 16 bits a 44,1 kHz. No se entrega una copia MP3.
- **[imagen.png](imagen.png)**: imagen base sin texto.
- **[miniatura.jpg](miniatura.jpg)**: miniatura 1280 × 720, con el texto CHOPIN / QUIET PIANO.
- **[publicacion.txt](publicacion.txt)**: título, descripción, etiquetas y comentario propuesto para copiar en YouTube Studio.

El MP4 contiene el audio necesario para subirlo directamente a YouTube. El WAV permite hacer futuros montajes sin volver a extraer audio comprimido del vídeo. Subir a GitHub no publica el vídeo en YouTube.

## Procedencia

La composición de Chopin y la transcripción de Magnus Lewis-Smith en Mutopia están identificadas como dominio público. La edición de referencia de la partitura es Peters, 1879. Las notas se han interpretado y renderizado de nuevo para este proyecto; no se ha utilizado una grabación comercial de la obra.

El instrumento utiliza muestras de piano individuales de **VSCO 2 Community Edition**, publicadas bajo **CC0 1.0 Universal**. Créditos: Simon Dalzell / Ivy Audio y Versilian Studios / Sam Gossner. Las fuentes y la licencia se conservan en [produccion](produccion/). Estas muestras son el instrumento que reproduce las notas, no una grabación de este preludio.

La imagen y la miniatura se han generado con IA para esta entrega. La procedencia y licencia de las fuentes musicales no convierten automáticamente todos los elementos del paquete en dominio público mundial.

## Producción

Los scripts, la partitura y los manifiestos de fuentes están en [produccion](produccion/). Los archivos descargados para el instrumento se identifican por URL, revisión y SHA-256; no se incluye la biblioteca completa.

Para montar de nuevo el vídeo con el WAV y la imagen existentes: `bash produccion/montar_video.sh` desde esta carpeta. El script resuelve su propia ruta, por lo que puede ejecutarse desde otro directorio. Requiere FFmpeg con libx264 y AAC.

Las estadísticas privadas aportadas por el usuario y el ZIP original no están incluidos en este repositorio. La propuesta se basa en esas estadísticas; no se afirma haber visto o escuchado los vídeos originales del canal.

Comprobación de entrega: decodificación completa del MP4 sin errores, formatos y duración verificados, WAV sin saturación y miniatura dentro del límite de tamaño. El informe técnico y los SHA-256 están en [produccion/validacion.json](produccion/validacion.json). No se afirma una escucha humana de la interpretación.
