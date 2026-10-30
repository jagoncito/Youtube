# Animación ambiental del vídeo 007

La escena se ha generado para esta entrega: terraza de piedra y viñedo otoñal
al amanecer, con Jagoncito y un ratón. La cámara permanece fija. No se ha
reutilizado un clip anterior ni se ha atribuido movimiento a los animales.

Dos máscaras pequeñas desplazan suavemente hojas concretas del borde superior
de la parra. Las oscilaciones de 20 y 30 segundos vuelven a su fase inicial al
completarse el ciclo de 60 segundos. Tres hojas secas vectoriales dibujadas para
este vídeo atraviesan discretamente el aire en los intervalos 10–20, 30–42 y
47–57 segundos; su posición, giro y transparencia se interpolan. Ninguna está
visible en la unión del bucle. La hoja que ya aparece sobre el escalón junto a
Jagoncito permanece estática. No se ha añadido audio ambiental.

Los efectos se producen con FFmpeg 7.1.5, libass y libx264. El script Python
organiza filtros y dibujos vectoriales; no retoca una imagen estática. La
configuración documenta las máscaras y las regiones protegidas en coordenadas
1920 × 1080.

Desde la carpeta de producción:

```sh
python animar_vinedo.py --image ../imagen.png --config vinedo-parametros.json --output /tmp/jagoncito007-video/escena-60s.mp4
python validar_vinedo.py /tmp/jagoncito007-video/escena-60s.mp4 --config vinedo-parametros.json --output /tmp/jagoncito007-video/validacion-escena.json
```

El ciclo de montaje contiene 1440 fotogramas a 24 fps: H.264 High, yuv420p,
1920 × 1080, sin pista de audio. El audio musical se incorpora al montar las
versiones finales. Los GOP cerrados de 10 segundos permiten repetir el ciclo
sin recodificar una entrega larga completa.

`validacion-escena.json` registra la decodificación completa, la diferencia
entre el último y el primer fotograma, el movimiento de las dos zonas de hojas,
el desplazamiento de una hoja nueva entre 15 y 16 segundos y la estabilidad de
los animales, la piedra, el tronco y el pueblo. El criterio de unión se fija
antes de la medición: MAE en gris ≤ máximo de 0,15 y cuatro veces el cambio
mediano entre fotogramas contiguos. Las regiones protegidas deben permanecer
por debajo de 0,2 MAE; se tolera la diferencia mínima de codificación.

Se han inspeccionado visualmente la imagen original y los fotogramas de 15 y
16 segundos. Esta inspección y las mediciones no equivalen a una escucha
subjetiva de la música.
