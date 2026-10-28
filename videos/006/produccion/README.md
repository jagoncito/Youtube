# Producción manual de 006

Una única entrega de **Clair de lune**, sin cron ni producción periódica. Entorno utilizado: Linux x86-64, Python 3.12, NumPy 2.3.5, SciPy 1.17.0, mido 1.3.3, SoundFile 0.14.0 y FFmpeg 7.1.5 con libass/libx264. sfizz se compila desde la revisión fijada en `build_sfizz.sh`, con Git, GCC/G++, make y CMake. Se usa la copia existente del repositorio, sin un worktree adicional.

## Reconstrucción

Desde esta carpeta, estos comandos reconstruyen 006 con archivos temporales separados:

```bash
python -m venv /tmp/jagoncito006-env
source /tmp/jagoncito006-env/bin/activate
python -m pip install -r requirements.txt
mkdir -p /tmp/jagoncito006

python ../fuentes/partitura/validate_score.py
python create_performance.py --score ../fuentes/partitura --out /tmp/jagoncito006/performance
python download_piano.py --manifest ../fuentes/instrumento/instrument-sources.json --dest /tmp/jagoncito006/piano
bash build_sfizz.sh /tmp/jagoncito006/engine
python render_piano.py --events /tmp/jagoncito006/performance/performance.json --sfz '/tmp/jagoncito006/piano/Salamander Grand Piano V3.sfz' --library /tmp/jagoncito006/engine/sfizz/build/library/lib/libsfizz.so --output /tmp/jagoncito006/performance/piano.float.wav
python master_piano.py --input /tmp/jagoncito006/performance/piano.float.wav --performance /tmp/jagoncito006/performance/performance.json --output ../debussy-clair-de-lune.wav
python validate_audio.py --audio ../debussy-clair-de-lune.wav --performance /tmp/jagoncito006/performance/performance.json --midi /tmp/jagoncito006/performance/interpretacion-digital.midi --score ../fuentes/partitura --output /tmp/jagoncito006/audio-validation.json

python animar_costa.py --image ../imagen.png --output /tmp/jagoncito006/escena-60s.mp4
python validar_costa.py /tmp/jagoncito006/escena-60s.mp4 --output /tmp/jagoncito006/validacion-escena.json
python montar_costa.py --scene /tmp/jagoncito006/escena-60s.mp4 --audio ../debussy-clair-de-lune.wav --output-dir ..
python verificar_entrega.py
```

Los comandos sobrescriben los medios de 006 al reconstruirlos; se ejecutan solo para esa producción. La descarga de muestras mantiene HTTPS/TLS y comprueba tamaño/SHA-256. Las imágenes generadas se conservan como fuentes del montaje, sin prometer regenerarlas bit a bit. El PDF/MIDI y las fuentes de partitura están incluidos; la recompilación opcional del PDF requiere LilyPond 2.24.4 y se explica en `../fuentes/partitura/`.

## Interpretación y mezcla

La fuente completa tiene 72 compases de 9/8 y cuatro voces que cruzan pentagramas. Se conservan los 1494 ataques MIDI; las 116 continuaciones ligadas y los 73 unísonos gráficos se explican por separado. La gracia y los grupos irregulares se mantienen. Los siete grupos de acordes arpegiados escritos se realizan sin añadir alturas nuevas.

El reloj de tempo sigue las seis indicaciones textuales de la edición, sin atribuir un BPM autoral que no existe en ella. Las voces de melodía, contracanto y acompañamiento se diferencian por su identidad musical, no solo por el pentagrama que ocupan en un instante. Se conservan la sección central más móvil, el crecimiento, el retorno y el *morendo* final.

El pedal es editorial porque las macros de pedal de esta fuente están definidas pero no se usan. Las tomas/liberaciones CC64 se adaptan a la armonía y se cierran al final; no se afirma medio pedal continuo. El color inicial suave se trabaja mediante dinámica y balance, sin atribuir una toma de una corda separada que el instrumento no contiene.

Se reutiliza el piano Salamander de 005, con mapas, afinación Retuned, 16 capas y resonancias verificadas; los datos interpretativos y el audio son nuevos. Un solo piano comparte el pedal entre las voces. El máster aplica ajustes globales moderados de balance/anchura, filtro subsónico y sala matemática tenue, con ganancia única y margen de pico real. No hay compresor, limitador ni normalización por frase.

La cola se mide tras la última nota y la liberación de pedal, conservando el reposo del compás final. Cuando el nivel cae estable por debajo de −80 dBFS se conserva una breve respiración. Solo se elimina el búfer quieto sobrante y se desvanece la última fracción de segundo ya tenue. El render exploratorio se identifica como tal, sin confundir su duración con el máster entregado.

El WAV final es estéreo de 48 kHz/24 bits y dura 327,083333 s. El entero más cercano a 30 minutos es **seis ciclos completos: 1962,500000 s**. Cinco serían 1635,416667 s; no se cambia el tempo para elegir una cifra más cómoda. Los MP4 incluyen AAC de 256 kb/s a 48 kHz y capítulos reales de cada ciclo.

## Imagen, vídeo y verificación

La imagen costera nueva se anima a 1920×1080/24 fps en un ciclo de 60 s. Se mueven zonas interiores del mar, espuma derecha y reflejos; animales, manta, linterna, horizonte, espigón y faro permanecen protegidos. H.264 High/yuv420p, QP 1 y GOP de 10 s. [Detalles y comandos de vídeo](README-VIDEO.md).

Los informes separan cobertura musical (`performance-validation.json` y la auditoría de partitura), lectura PCM/pedal/MIDI (`audio-validation.json`), mezcla y decaimiento (`mastering.json`), continuidad visual (`validacion-escena.json`) y entrega final (`validacion-entrega.json`). Esta última decodifica ambos MP4 completos, compara cada ciclo AAC con el WAV, comprueba formatos/picos/finales y verifica los capítulos. La copia de cuadros B puede dejar dos cuadros de vídeo finales adicionales; se registra la duración de audio por separado.

El inventario de `../manifest.json` permite contrastar tamaños y SHA-256 después de recuperar los archivos desde GitHub. Los informes técnicos y la inspección visual **no equivalen a una escucha subjetiva**: no se ha realizado esa valoración ni se predicen preferencias auditivas o resultados de audiencia. La comparación con la transcripción elegida tampoco es un cotejo histórico independiente. Derechos y créditos se documentan en `../fuentes/`.
