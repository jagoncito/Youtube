# Producción manual de 007

Una única entrega del **Adagio cantabile**, segundo movimiento completo de la Sonata para piano n.º 8, op. 13, «Patética», de Beethoven. No incluye los otros dos movimientos de la sonata. Esta producción no crea tareas periódicas ni publica en YouTube.

Entorno utilizado: Linux x86-64, Python 3.12, NumPy 2.3.5, SciPy 1.17.0, mido 1.3.3, SoundFile 0.14.0 y FFmpeg 7.1.5 con libass/libx264. El motor sfizz se compila desde la revisión fijada en `build_sfizz.sh`, con Git, GCC/G++, make y CMake. Las fuentes de la partitura, muestras y herramientas se identifican en `../fuentes/`.

## Reconstrucción

Desde esta carpeta de producción, con FFmpeg y las herramientas de compilación disponibles:

```bash
python -m venv /tmp/jagoncito007-env
source /tmp/jagoncito007-env/bin/activate
python -m pip install -r requirements.txt
mkdir -p /tmp/jagoncito007

python ../fuentes/partitura/validate_score.py
python create_performance.py --score ../fuentes/partitura --out /tmp/jagoncito007/performance
python download_piano.py --manifest ../fuentes/instrumento/instrument-sources.json --dest /tmp/jagoncito007/piano
bash build_sfizz.sh /tmp/jagoncito007/engine
python verify_instrument.py --cache /tmp/jagoncito007/piano --manifest ../fuentes/instrumento/instrument-sources.json --library /tmp/jagoncito007/engine/sfizz/build/library/lib/libsfizz.so --renderer render_piano.py --out-dir /tmp/jagoncito007/piano-test
python render_piano.py --events /tmp/jagoncito007/performance/performance.json --sfz '/tmp/jagoncito007/piano/Salamander Grand Piano V3.sfz' --library /tmp/jagoncito007/engine/sfizz/build/library/lib/libsfizz.so --output /tmp/jagoncito007/performance/piano.float.wav
python master_piano.py --input /tmp/jagoncito007/performance/piano.float.wav --performance /tmp/jagoncito007/performance/performance.json --output ../beethoven-adagio-cantabile.wav
python validate_audio.py --audio ../beethoven-adagio-cantabile.wav --performance /tmp/jagoncito007/performance/performance.json --midi /tmp/jagoncito007/performance/interpretacion-digital.midi --score ../fuentes/partitura --output /tmp/jagoncito007/audio-validation.json

python animar_vinedo.py --image ../imagen.png --config vinedo-parametros.json --output /tmp/jagoncito007/escena-60s.mp4
python validar_vinedo.py /tmp/jagoncito007/escena-60s.mp4 --config vinedo-parametros.json --output /tmp/jagoncito007/validacion-escena.json
python montar_video.py --scene /tmp/jagoncito007/escena-60s.mp4 --audio ../beethoven-adagio-cantabile.wav --output-dir ..
python verificar_entrega.py
```

Los comandos de máster y montaje reconstruyen los medios de esta carpeta 007. Las descargas conservan HTTPS/TLS y verifican tamaños y SHA-256. El WAV flotante y las pruebas instrumentales son intermediarios fuera de la entrega; el único audio independiente entregado es el WAV final de la interpretación base.

La imagen y la miniatura generadas se conservan como fuentes del montaje. No se promete que volver a generar imágenes produzca los mismos bytes. La recompilación opcional de PDF/MIDI requiere LilyPond 2.24.4 y se explica en `../fuentes/partitura/README.md`.

## Interpretación y mezcla

La transcripción elegida tiene **73 compases de 2/4**, equivalentes a 146 negras. Los retornos temáticos están escritos completos y no quedan signos de repetición por desplegar. Los **1629 ataques de referencia** se conservan; las 17 continuaciones ligadas y los 2 unísonos simultáneos explican las 1648 notas gráficas. Las seis notas de gracia escritas permanecen identificadas. Tres grupetos gráficos, en los compases 20, 21 y 68, reciben una realización explícita de doce ataques adicionales: **1641 ataques interpretativos en total**. El vecino inferior del grupeto del compás 21 es mi natural, según el símbolo de la fuente.

Un reloj musical compartido mantiene juntas ambas manos. La melodía, las voces internas y el acompañamiento reciben balance y articulación diferenciados. Se trabajan respiraciones de frase, los episodios contrastantes, los sforzandi, el forte-piano, el retorno con acompañamiento de tresillos y la cadencia con calderón. La cifra oculta de 36 negras/minuto pertenece al MIDI de la transcripción; no se presenta como una metronomización autoral de Beethoven.

La fuente no contiene marcas de pedal activas: las tomas y liberaciones CC64 son una realización editorial según la armonía, con limpieza de los reposos finales y liberación completa tras el calderón. El instrumento utiliza pedal conmutado; no se afirma una simulación física continua de medio pedal ni una toma separada de una corda.

Se reutiliza el piano Yamaha C5 Salamander autorizado de las entregas anteriores, con 16 capas, afinación Retuned y resonancias verificadas. La interpretación, el MIDI y el audio de Beethoven son nuevos. Un único piano comparte el pedal entre las voces. El máster aplica correcciones globales moderadas de balance y anchura, filtro subsónico de 20 Hz y una sala matemática nueva y discreta. Una única ganancia conserva los contrastes; no hay compresor, limitador ni normalización por frase.

La cola se mide después de la última nota y la liberación del pedal. Se exige que el nivel permanezca por debajo de −80 dBFS, se conserva una breve respiración y solo se elimina el búfer quieto sobrante. El desvanecimiento final actúa sobre la última fracción de segundo ya tenue. El informe de máster registra los tiempos, niveles y la duración del render final utilizado. La reconstrucción usa el búfer final ya medido, que coincide con la duración del WAV entregado.

El WAV final, estéreo de 48 kHz y 24 bits, dura **286.666666667 s**. La versión larga contiene **6 ciclos completos: 1720.000000000 s**. Seis ciclos son el entero más cercano a 30 minutos; cinco darían 1433,333333 s y siete 2006,666667 s. No se corta el movimiento ni se cambia el tempo para cuadrar una cifra. Los MP4 incorporan AAC de 256 kb/s a 48 kHz y capítulos con los inicios reales de cada ciclo.

## Imagen, vídeo y comprobaciones

La nueva terraza del viñedo se anima a 1920×1080 y 24 fps en un ciclo de 60 s. Dos pequeñas máscaras mueven hojas concretas de la parra; tres hojas secas vectoriales nuevas cruzan el aire en momentos separados. Jagoncito, el ratón, la hoja junto al dragón y la arquitectura permanecen estáticos. No hay sonido ambiental. H.264 High/yuv420p y GOP cerrados de 10 s permiten repetir la escena al montar ambas versiones. Los detalles, máscaras y comandos están en `README-ANIMACION.md` y `vinedo-parametros.json`.

La imagen de 006 se aportó únicamente como referencia de identidad de Jagoncito. La escena de 007, su composición, perspectiva y microhistoria se generaron nuevas. La miniatura se generó específicamente a partir de la nueva escena de 007 y se comprobó a tamaño móvil. `origen-visual.json` registra el proceso.

La verificación separa la correspondencia con la transcripción (`../fuentes/partitura/score-validation.json`), cobertura interpretativa (`performance-validation.json`), PCM/MIDI/pedal (`audio-validation.json`), mezcla y cola (`mastering.json`), continuidad visual (`validacion-escena.json`) y entrega final (`validacion-entrega.json`). Esta última decodifica ambos MP4 completos, compara todos los ciclos AAC con el WAV y comprueba formatos, picos, finales y capítulos. La copia de cuadros B puede dejar dos cuadros de vídeo adicionales al final; la duración de audio se verifica por separado.

`../manifest.json` registra tamaños y SHA-256 para comprobar la recuperación completa desde GitHub, incluidos los medios de Git LFS. La producción conserva intactas las entregas 001–006.

Estos controles técnicos y la inspección visual **no equivalen a una escucha subjetiva**; esa valoración no se ha realizado. La auditoría de la partitura verifica la transcripción seleccionada, sin atribuirse un cotejo independiente con un facsímil histórico. Los derechos, créditos y límites se documentan en `../fuentes/`.
