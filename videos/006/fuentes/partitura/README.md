# Partitura y comprobaciones de 006

Fuente completa de *Clair de lune*, de Claude Debussy, transcripción de Keith OHara / Mutopia, declarada Public Domain. Consulte `FUENTES.md` para los créditos, alcance de la revisión y distinción entre composición, edición, instrumento e interpretación.

Con Python y `mido` instalados, desde esta carpeta:

```bash
python validate_score.py
```

Se vuelve a asociar cada ataque MIDI a su nota gráfica y se explican las continuaciones ligadas y unísonos. Los resultados se guardan en `score-validation.json` y `mapped-midi-notes.json`. El verificador ejecutado produce 1494 ataques, 1683 notas gráficas, 116 continuaciones ligadas, 73 unísonos consolidados y una gracia, sin omisiones inexplicadas ni notas colgadas.

Con LilyPond 2.24.4 instalado normalmente:

```bash
lilypond -o partitura adapted/clair-de-lune.ly
python export_events.py
lilypond -dbackend=null -dno-print-pages -o events adapted/export-events.ly > events.stdout.log 2> events.stderr.log
python parse_events.py
python validate_score.py
```

El PDF y el MIDI ya están incluidos. `original/` conserva los bytes recibidos; `adapted/` conserva la misma fuente musical y el auxiliar que exporta eventos. El JSON contiene notas, voces, grupos irregulares, gracia, ligaduras, arpegios, dinámicas y textos musicales reales. `lily.stderr.log` y `events.stderr.log` registran compilaciones exitosas con algunos avisos de maquetación de barras, sin fallos de compás.

La compilación se realizó en Linux con LilyPond 2.24.4 y Guile 2.2, extraídos localmente de paquetes Debian. La instalación reversible verificó las firmas del índice Debian contra el llavero de archivo del sistema, el SHA-256 del índice y los SHA-256 de los paquetes antes de usarlos. Esto prepara la herramienta; no cambia los derechos de las partituras ni implica un cotejo independiente con un facsímil histórico.
