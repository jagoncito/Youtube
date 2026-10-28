# Escena costera nueva de 006

La imagen de reproducción es una ilustración nueva de una cala nocturna, vista desde una cámara baja junto a la arena. El mar abierto domina el panorama y el espigón conduce hacia un faro distante. No se reutilizan imágenes ni clips de las entregas anteriores.

`animar_costa.py` crea efectos de vídeo sobre esa imagen, sin retocar el archivo estático:

- Pequeña ondulación de textura/reflejos dentro del mar abierto, con una máscara suave que evita el horizonte y excluye la parte superior de los personajes.
- Pequeña ondulación de la espuma y los reflejos en una zona de agua a la derecha, lejos de la manta y de los animales.
- Seis reflejos vectoriales muy tenues, breves y horizontales sobre el agua.

Los personajes, la manta, el espigón, el horizonte y el faro no tienen animación independiente. No se simula una ola que avance por toda la playa ni se mueve globalmente la imagen. No se añaden sonidos de mar o viento: la banda sonora es únicamente el piano digital.

El ciclo de 60 s funciona a 24 fps y 1920×1080. Los periodos de las ondas y reflejos dividen exactamente 60 s. H.264 High/yuv420p, QP 1, GOP de 10 s. Se realizó una prueba de tamaño de 10 s antes del render completo: unos 5,10 MB, que proyectan aproximadamente 920 MB de vídeo para 30 minutos más el audio AAC. La estimación no sustituye el tamaño medido de los MP4 finales.

Desde la carpeta de producción, con FFmpeg/libass/libx264 y NumPy:

```bash
python animar_costa.py --image ../imagen.png --output /tmp/jagoncito006-scene/escena-60s.mp4
python validar_costa.py /tmp/jagoncito006-scene/escena-60s.mp4 --output /tmp/jagoncito006-scene/validacion-escena.json
python montar_costa.py --scene /tmp/jagoncito006-scene/escena-60s.mp4 --audio ../debussy-clair-de-lune.wav --output-dir ..
```

El montador mide la duración exacta del WAV y elige el número entero de repeticiones completas más próximo a 30 minutos; puede indicarse explícitamente con `--repeats N`. No modifica el tempo ni recorta una última repetición. La cola y la respiración musical ya forman parte del WAV base y se conservan en cada ciclo.

Los MP4 incluyen AAC a 256 kb/s y a la frecuencia nativa del WAV (48 kHz para el piano Salamander de esta entrega). El MP4 base lleva un capítulo que identifica la única pieza; el largo integra los inicios medidos de los ciclos. No se inventan movimientos de Clair de lune. Título, autor y atribución se incluyen también como metadatos del contenedor.

La copia directa de H.264 con cuadros B puede conservar hasta dos cuadros finales después del audio. Se registra ese pequeño redondeo y se comprueba la duración del audio por separado.

`validar_costa.py` decodifica los 1440 cuadros completos, compara el salto del último al primero con cuadros vecinos, mide movimiento en mar/espuma y verifica regiones protegidas de animales, horizonte y espigón. El criterio fijo es `boundary <= max(0.15, 4*ordinary adjacent MAE)` y no se relaja para aprobar una discontinuidad. El informe no representa una escucha subjetiva del audio ni una valoración artística automática.

Comprobación del ciclo final: 30.490.753 bytes, 1440 cuadros decodificados, MAE del cierre 0,0290 frente al límite fijo 0,15 y mediana de vecinos 0,01994. El cambio a 15 s es 3,003 en el mar y 5,274 en la espuma derecha; las regiones protegidas de animales, horizonte y espigón quedan entre 0,0014 y 0,0020, atribuibles a la codificación. Se inspeccionó también un cuadro del segundo 17. Estos valores describen cambios de píxel, no una puntuación artística.
