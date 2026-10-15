# Una noche de lluvia con Jagoncito

Nueva entrega para el canal: Jagoncito, un pequeño dragón, comparte una habitación acogedora con un gato y un ratón. La lluvia y la luz del fuego aportan movimiento suave a la escena. La música reúne las **Gymnopédies n.º 1 y n.º 3 de Erik Satie**, en una nueva interpretación digital de piano con una capa muy tenue de lluvia sintética.

La secuencia base dura **6 minutos** y el montaje la repite cinco veces hasta **30 minutos**. Las dos obras se interpretan completas en cada vuelta: la n.º 1 comienza en **00:00** y la n.º 3 en **03:10**. La lluvia del audio se ha generado mediante síntesis; su nivel es muy bajo para acompañar el piano.

| Archivo | Uso |
| --- | --- |
| `video-30min.mp4` | Vídeo de 30 minutos listo para revisar y subir. |
| `bucle-6min.mp4` | Secuencia de 6 minutos para reproducir o montar en bucle. |
| `audio-bucle-6min.wav` | Único audio independiente, de 6 minutos. Repetir cinco veces para obtener 30 minutos. Ambos MP4 ya incorporan la música. |
| `imagen.png` | Ilustración principal. |
| `miniatura.jpg` | Miniatura de YouTube. |
| `publicacion.txt` | Título, descripción, etiquetas, nombres de archivo, créditos y notas de publicación. |
| `produccion/` | Fuentes, código y documentos de la producción. |

Ambos vídeos se entregan en **1920 × 1080, 24 fps, H.264**, con audio **AAC estéreo a 192 kb/s y 44,1 kHz**. El vídeo de 30 minutos termina con un fundido de audio de tres segundos. La secuencia de seis minutos y el WAV conservan su final preparado para repetición. El proceso está explicado en [produccion/LEEME-VIDEO.md](produccion/LEEME-VIDEO.md).

`video-30min.mp4` se almacena con **Git LFS** por su tamaño. Desde la web de GitHub, utilizar **Download / Descargar** en la página del archivo para obtener el MP4. En un clon con Git LFS instalado, ejecutar `git lfs pull` desde la raíz del repositorio para descargar el vídeo real; el pequeño puntero de texto de LFS no contiene el vídeo.

La música se ha generado a partir de transcripciones de partitura identificadas por Mutopia como dominio público y muestras de piano VSCO 2 CE con licencia CC0. Los enlaces y créditos figuran en `publicacion.txt` y en la documentación de producción. Esto no constituye una garantía frente a reclamaciones automáticas ni una declaración de dominio público para todo el paquete.

El paquete está preparado para GitHub. Subirlo a YouTube y publicar comentarios son acciones independientes.
