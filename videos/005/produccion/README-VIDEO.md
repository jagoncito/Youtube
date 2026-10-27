# Escena nueva de 005

Una escena original de jardín primaveral tras la lluvia. Cámara fija ligeramente elevada y oblicua al estanque. No se reutilizan clips ni imágenes de las entregas anteriores.

`animar_jardin.py` añade tres efectos reales de vídeo sobre la nueva imagen:

- Ondulación de los reflejos en una zona interior del estanque. El desplazamiento es pequeño y se mezcla con una máscara suave de intensidad máxima 65/255. Se excluyen el borde del estanque, Jagoncito, el gatete y la mayor parte de las plantas.
- Dos pequeños pétalos vectoriales nuevos que derivan y aparecen/desaparecen suavemente, con ciclos de 30/60 s.
- Cuatro reflejos breves y muy discretos en el agua.

Los personajes permanecen estáticos. El pétalo ya dibujado cerca del dragón no se presenta como animado. No se añade sonido de lluvia, agua ni otro ambiente.

Ciclo de 60 s a 24 fps, 1920×1080, H.264 High/yuv420p, QP 1, GOP de 10 s. Los periodos de las ondulaciones (6/10/12 s) y los pétalos/reflejos dividen 60 s. La imagen estática original se conserva intacta; los efectos solo se aplican al vídeo.

Desde la carpeta de producción, con FFmpeg/libass/libx264 y NumPy:

```bash
python animar_jardin.py --image ../imagen.png --output /tmp/jagoncito005-scene/escena-60s.mp4
python validar_jardin.py /tmp/jagoncito005-scene/escena-60s.mp4 --output /tmp/jagoncito005-scene/validacion-escena.json
python montar_jardin.py --scene /tmp/jagoncito005-scene/escena-60s.mp4 --audio ../chopin-nocturne-op27-2.wav --output-dir .. --repeats N
```

Sustituir N por el número entero de interpretaciones completas más próximo a 30 minutos según la duración real del WAV. La versión larga repite esa misma interpretación, sin retocar el tempo, cortar la obra ni solapar sus finales. La cola y la pausa musical ya forman parte del WAV base. El MP4 codifica AAC de 256 kb/s a la frecuencia nativa de ese WAV (48 kHz en 005), e integra capítulos con el inicio real de cada ciclo. La base tiene un solo capítulo; el nocturno no se divide en movimientos inventados.

La copia directa de H.264 puede conservar hasta dos cuadros finales después del audio por la reordenación de cuadros B. La validación final comprueba la duración de audio por separado y registra la duración real del contenedor.

La verificación de escena decodifica todos los cuadros, compara el salto de regreso al principio con cambios vecinos, mide movimiento del agua y comprueba que la región de los personajes permanezca estática. No supone una escucha del audio ni una valoración subjetiva del movimiento completo.
