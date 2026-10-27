# Interpretación de Chopin, Nocturno op. 27 n.º 2

Se parte del MIDI recién compilado de la transcripción elegida y de su extracción de notación. No se usa una interpretación grabada ajena. La auditoría de partitura mantiene ambos pentagramas hasta el final del compás 77 (231 negras):1806 ataques físicos distintos, incluidos 30 ataques de notas de adorno escritas. Las continuaciones ligadas y los unísonos gráficos que LilyPond consolida se explican en la auditoría de esa fuente.

`create_performance.py` conserva todos los identificadores de ataque fuente y sus alturas principales. El reloj de tempo común en negras permite rubato de frase, cadencias y retornos sin separar el tiempo de las dos manos. La indicación es Lento sostenuto; el punto de partida es negra = 42 (negra con puntillo = 28), con puntos de tempo documentados en `performance.json`. No se ha elegido un tempo para conseguir una duración de vídeo.

La melodía superior, las notas inferiores de los acordes, las voces interiores y los arpegios izquierdos reciben velocidades distintas; se conservan los crecimientos de intensidad. La izquierda mantiene acompañamiento ligado. Se usan indicaciones escritas de articulación, dinámica, ligaduras y reguladores; se realizan de forma editorial cinco pralls superiores, el giro con re natural impreso y el inicio del trino del compás 51, antes de su floritura ya escrita. Esta realización conserva íntegramente las tuplets, las notas pequeñas y las anticipaciones de gracia presentes en el MIDI.

Las 224 marcas de pedal de la fuente determinan el estado del pedal físico común. El pedal se toma ligeramente después del ataque del bajo. Los pocos pedales de una misma armonía que abarcan más de un compás se refrescan brevemente en barras interiores, para evitar acumulación. La salida contiene verdaderas liberaciones CC64=0 y nuevas tomas CC64=127. No se afirma modelado continuo de medio pedal. Se libera al final. Una primera captura de prueba reservó 12 segundos para medir la cola; el archivo entregado elimina únicamente ese margen ya inaudible. La comprobación localiza la primera caída estable por debajo de −80 dBFS, confirma 0,5 segundos y conserva otros 0,6 segundos de respiración antes del redondeo al fotograma. La reconstrucción usa el margen corto ya medido y vuelve a comprobarlo: si la cola sigue audible, el proceso falla en lugar de cortarla.

`render_piano.py` utiliza un único piano Salamander Grand Piano V3 con el mapa SFZ original de 16 capas y la afinación Retuned de Markus Fiedler. Se conservan los disparos de liberación, resonancia y pedal del mapa, con sus ruidos físicos a nivel discreto. No se aplican las envolventes cortas de cuerdas usadas en 004. Las muestras, el motor y la partitura conservan sus licencias documentadas por separado.

`master_piano.py` aplica una corrección global de balance entre canales, reduce moderadamente la anchura, retira energía subsónica y añade una sala corta matemática muy tenue. La ganancia de todo el programa se fija con medición de pico a 4×, sin compresor, limitador ni normalización por pasaje o mano. Solo se desvanece la última fracción de segundo después de confirmar que la cola ya cae por debajo de −80 dBFS RMS.

La comprobación cubre conservación de alturas y ataques, cierre de notas y pedal, rango de velocidades, duración, decaimiento y medidas del WAV. **No se ha realizado una escucha subjetiva del resultado.** Estas comprobaciones no prueban por sí mismas preferencia auditiva ni resultados de audiencia.

## Reproducción

Dependencias: Python 3.12, NumPy 2.3.5, SciPy 1.17.0, mido 1.3.3 y SoundFile 0.14.0. El motor sfizz y las muestras se recuperan según sus propios manifiestos.

```bash
python create_performance.py --score /ruta/fuentes/partitura --out /ruta/trabajo
python render_piano.py --events /ruta/trabajo/performance.json --sfz '/ruta/Salamander Grand Piano V3.sfz' --library /ruta/libsfizz.so --output /ruta/trabajo/piano-dry.float.wav
python master_piano.py --input /ruta/trabajo/piano-dry.float.wav --output /ruta/trabajo/chopin-op27-no2.wav
```

El MIDI expresivo usa 1000 ticks por segundo a 60 BPM como formato de intercambio temporal; el tempo musical y sus curvas están descritos en JSON. No se debe confundir ese reloj técnico con la velocidad interpretativa.
