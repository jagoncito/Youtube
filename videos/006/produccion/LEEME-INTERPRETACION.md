# Interpretación de Debussy — Clair de lune

Interpretación digital nueva de la versión original para piano de *Clair de lune*, tercer movimiento de *Suite bergamasque*. Se parte del MIDI recién compilado de la transcripción de Keith OHara / Mutopia, con fuente declarada E. Fromont (1905), colocada en dominio público por el transcriptor. No se utiliza una grabación terminada ajena ni audio de entregas anteriores. Las muestras Salamander tienen una licencia independiente CC BY 3.0; no se describe el conjunto como íntegramente CC0 o de dominio público universal.

## Fidelidad y realización

La fuente verificada contiene 72 compases de 9/8, equivalentes a 324 negras. Sus 1494 ataques MIDI corresponden a 1683 notas gráficas, con 116 continuaciones ligadas y 73 unísonos consolidados explicados por la auditoría de partitura. La única nota de gracia escrita se conserva. La interpretación mantiene los 1494 identificadores y alturas, sin notas añadidas ni adornos arbitrarios.

Las voces persistentes `red`, `green`, `blue` y `grey` conservan su función aunque crucen de pentagrama. La voz superior recibe fraseo y balance de acordes; la voz interior móvil de *Calmato* puede destacar sobre los acordes largos; los arpegios y el bajo mantienen su función sin convertirse automáticamente en melodía por cambiar de registro visual. Las velocidades no se aleatorizan para simular expresividad: siguen la frase, la función de voz, los reguladores y las indicaciones escritas.

El reloj compartido de 9/8 conserva *Andante très expressif*, *Tempo rubato*, *Un poco mosso*, *En animant*, *Calmato* y el retorno *a Tempo I*. Los puntos de tempo están en `performance.json`: apertura alrededor de negra 58–63, sección móvil 70–74, crecimiento central 78–81 y retorno con el morendo final. No proceden de una duración objetivo ni del tempo de Chopin de 005.

Los 12 eventos de arpegio escritos corresponden a siete grupos de acordes. Solo las voces marcadas se despliegan de grave a agudo con 95–120 ms de separación total; no se añaden alturas ni se arpegian melodías ajenas a esas marcas. Los detalles y anclajes están en `performance-validation.json`. Las ligaduras y las duraciones largas se conservan; las pocas colisiones de una tecla con su propio reataque se limpian mediante duraciones de dedo, mientras el pedal mantiene la resonancia.

## Pedal y timbre

La edición elegida **no tiene marcas efectivas de pedal**: sus macros de pedal definidas y el contexto vacío no se presentan como instrucciones escritas. Los 305 eventos CC64 de producción constituyen una realización armónica editorial con tomas y liberaciones reales, renovada en cambios de bajo y grupos armónicos de los arpegios. Las notas largas siguen sostenidas por su dedo cuando corresponde. El pedal se libera después de cerrar el compás 72, conservando también su reposo final de 1,5 negras. No se afirma modelado continuo de medio pedal.

Un único piano Salamander Grand Piano v3 / Yamaha C5, con 16 capas y afinación Retuned, comparte el pedal entre todas las voces. Se conservan sus mapas, envolventes, afinaciones y muestras de liberación/resonancia; los ruidos físicos quedan discretos. La indicación *con sordina* se aproxima mediante ataques contenidos y capas suaves de muestra; no se afirma un mecanismo físico de una corda ni muestras específicas de ese pedal.

## Mezcla, cola y duración

El máster usa una corrección global moderada de balance y anchura, filtro subsónico a 20 Hz y una sala matemática discreta (RT60 1,40 s, difusión 0,090). El pico se mide a 4× para fijar una única ganancia con margen de −1,8 dBTP, sin compresor, limitador ni normalización de cada mano o pasaje.

Se observó primero un búfer amplio de decaimiento. La última nota se libera a 322,890493 s y el pedal al cerrar la obra a 325,565867 s. Desde 325,965875 s la señal permanece bajo −80 dBFS en ventanas de 100 ms. Se conservan 0,5 s de confirmación y 0,6 s de respiración; se redondea al cuadro y solo se desvanece la última fracción ya subaudible. El vacío excedente del primer búfer no se entrega. El máster se comprobó después usando únicamente su búfer final reducido.

**WAV final: 327,083333333 s, 15.700.000 cuadros, estéreo PCM de 24 bits / 48 kHz.** El MIDI expresivo y su JSON terminan en esa misma duración. Seis repeticiones completas dan 1962,5 s (32:42,5); cinco darían 27:15,417. Seis es el entero más cercano a 30 minutos para esta interpretación; no se cambia el tempo para evitar esa diferencia.

## Reproducción y alcance

Dependencias: Python 3.12, NumPy 2.3.5, SciPy 1.17.0, mido 1.3.3 y SoundFile 0.14.0. El motor sfizz y las muestras se recuperan según sus manifiestos. Desde la carpeta de producción, con rutas de trabajo elegidas:

```bash
python create_performance.py --score ../fuentes/partitura --out /tmp/debussy006/performance
python render_piano.py --events /tmp/debussy006/performance/performance.json --sfz '/tmp/debussy006/piano/Salamander Grand Piano V3.sfz' --library /ruta/libsfizz.so --output /tmp/debussy006/performance/piano.float.wav
python master_piano.py --input /tmp/debussy006/performance/piano.float.wav --performance /tmp/debussy006/performance/performance.json --output ../debussy-clair-de-lune.wav
python validate_audio.py --audio ../debussy-clair-de-lune.wav --performance /tmp/debussy006/performance/performance.json --midi /tmp/debussy006/performance/interpretacion-digital.midi --score ../fuentes/partitura --output /tmp/debussy006/audio-validation.json
```

El validador reimporta el MIDI y comprueba pares de notas, anclajes, cierre de pedal y todo el PCM. Las secciones del informe de niveles corresponden a indicaciones reales de la partitura; no son movimientos ni capítulos de publicación. La notación se ha cotejado con la edición digital elegida, **sin afirmar cotejo histórico independiente ni escucha subjetiva del audio**. Las mediciones no demuestran por sí mismas belleza sonora o resultados de audiencia.
