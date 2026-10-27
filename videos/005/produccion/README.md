# Producción manual de 005

Esta carpeta reproduce una única entrega de Chopin, sin cron ni tareas periódicas. Entorno utilizado: Linux x86-64, Python 3.12, NumPy 2.3.5, SciPy 1.17.0, mido 1.3.3, SoundFile 0.14.0 y FFmpeg 7.1.5 con libass/libx264. El motor sfizz se compila en la revisión fijada por `build_sfizz.sh`, con Git, GCC/G++, make y CMake. Se trabaja en la copia existente del repositorio; no hace falta un worktree.

## Reconstrucción

Desde esta carpeta, con un entorno Python que tenga las dependencias de `requirements.txt`, se puede reconstruir con archivos temporales fuera del repositorio:

```bash
python -m venv /tmp/jagoncito005-env
source /tmp/jagoncito005-env/bin/activate
python -m pip install -r requirements.txt
mkdir -p /tmp/jagoncito005

python ../fuentes/partitura/validate_score.py
python create_performance.py --score ../fuentes/partitura --out /tmp/jagoncito005/performance
python download_piano.py --manifest ../fuentes/instrumento/instrument-sources.json --dest /tmp/jagoncito005/piano
bash build_sfizz.sh /tmp/jagoncito005/engine
python render_piano.py --events /tmp/jagoncito005/performance/performance.json --sfz '/tmp/jagoncito005/piano/Salamander Grand Piano V3.sfz' --library /tmp/jagoncito005/engine/sfizz/build/library/lib/libsfizz.so --output /tmp/jagoncito005/performance/piano.float.wav
python master_piano.py --input /tmp/jagoncito005/performance/piano.float.wav --performance /tmp/jagoncito005/performance/performance.json --output ../chopin-nocturne-op27-2.wav
python validate_audio.py --audio ../chopin-nocturne-op27-2.wav --performance /tmp/jagoncito005/performance/performance.json --midi /tmp/jagoncito005/performance/interpretacion-digital.midi --output /tmp/jagoncito005/audio-validation.json

python animar_jardin.py --image ../imagen.png --output /tmp/jagoncito005/escena-60s.mp4
python validar_jardin.py /tmp/jagoncito005/escena-60s.mp4 --output /tmp/jagoncito005/validacion-escena.json
python montar_jardin.py --scene /tmp/jagoncito005/escena-60s.mp4 --audio ../chopin-nocturne-op27-2.wav --output-dir .. --repeats 5
python verificar_entrega.py
```

Estos comandos sobrescriben los medios de 005 al reconstruirlos; solo se ejecutan para producir esa entrega. Las imágenes generadas se conservan como fuentes del montaje, sin prometer regenerarlas bit a bit. Las muestras de piano se recuperan mediante HTTPS con tamaño/SHA-256 fijados y verificación TLS; no se reutiliza una grabación terminada del nocturno.

## Qué se ha trabajado

La partitura digital completa se verificó contra sus notas MIDI y eventos de notación. Los 77 compases de 6/8 contienen 1806 ataques físicos, con las continuaciones ligadas y los unísonos gráficos explicados. Los 30 ataques de gracia se conservan. La versión expresiva añade la realización editorial de los ornamentos escritos y conserva cada identificador fuente; el MIDI final se vuelve a importar para comprobar pares de notas y pedal cerrado.

El punto de partida musical es negra = 42, con curvas de rubato, cadencias y crecimientos de intensidad. Las dos manos comparten reloj, mientras melodía, acordes interiores y arpegios reciben velocidades distintas. El pedal de la fuente se interpreta con verdaderos CC64 de toma/liberación y algunas renovaciones armónicas documentadas. No se afirma medio pedal continuo. [Explicación de la interpretación](LEEME-INTERPRETACION.md).

Un solo piano Salamander Grand Piano v3 comparte el pedal de ambas manos. Se conservan sus mapas, 16 capas, afinación Retuned, envolventes y muestras de liberación/resonancia. Los controles físicos y el número de voces están en `render-report.json`. Ese informe identifica expresamente el primer render exploratorio con una cola de observación generosa, que no se entrega.

El máster aplica una corrección global moderada de balance/anchura, filtro subsónico a 20 Hz y una reverberación matemática breve y tenue. La ganancia es única para toda la pieza, con medición de pico a 4×, sin compresor, limitador ni normalización por pasaje. Tras la última nota y liberación de pedal, se mide el decaimiento con ventanas de 100 ms: se conserva la resonancia y una breve respiración; el vacío sobrante se elimina. Solo se desvanece la última fracción de segundo ya por debajo del umbral técnico indicado. `mastering.json` registra ese proceso.

La imagen nueva del jardín se anima a 1920×1080/24 fps con un ciclo de 60 s: agua/reflejos en una máscara interior, dos pétalos nuevos y pequeños destellos. No se deforma a los animales ni se afirma que se muevan. H.264 High/yuv420p, QP 1 y GOP de 10 s. [Detalles de vídeo y continuidad](README-VIDEO.md).

El WAV estéreo PCM de 24 bits / 48 kHz dura 347,083333 s. Cinco copias completas de la misma interpretación son 1735,416667 s de audio. Los MP4 integran AAC a 256 kb/s y 48 kHz, capítulos de cada ciclo y metadatos de atribución; al copiar H.264 con cuadros B se conservan dos cuadros finales adicionales. La duración del audio se comprueba por separado. El nocturno es una sola obra y no se divide en movimientos ficticios.

## Comprobaciones

- `fuentes/partitura/score-validation.json`: cobertura y correspondencia de la edición elegida.
- `performance-validation.json` y `audio-validation.json`: alturas/anclajes, ornamentos, MIDI reimportado, pedal, lectura PCM, niveles por secciones y final.
- `validacion-escena.json`: decodificación de los 1440 cuadros, movimiento del agua, región de personajes y regreso al primer cuadro frente a cambios vecinos.
- `validacion-entrega.json`: lectura completa del WAV, saturación, pico real, sonoridad, decodificación completa de los dos MP4 y comparación de cada ciclo AAC con el PCM original.
- `../manifest.json`: inventario con tamaños y SHA-256 de los archivos entregados. La descarga desde GitHub se contrasta con ese inventario después de subir.

Estas comprobaciones y la inspección visual **no son una valoración auditiva subjetiva**. No se ha realizado esa escucha ni se atribuyen a las métricas preferencias del oído o resultados de audiencia. La fidelidad a esta transcripción tampoco equivale a cotejarla independientemente con el facsímil histórico. Las licencias de composición, transcripción y piano se documentan por separado en `../fuentes/`.
