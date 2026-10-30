# Fuente musical reproducible — 007

`original/` conserva el archivo Mutopia sin modificar. `adapted/` contiene la copia de compilación y el archivo de extracción generado. Consulta `FUENTES.md` para procedencia, declaración de dominio público y límites de la verificación.

Requisitos: LilyPond2.24.4 y Python3 con Mido1.3.3. El archivo `lily-install-sources.json` registra el origen de los paquetes utilizados para el compilador; el compilador es herramienta de producción, no un instrumento ni una grabación incorporada.

Desde esta carpeta, usando `lilypond` disponible en PATH:

```sh
lilypond -dno-point-and-click -o partitura adapted/pathetique-2.ly > lily.stdout.log 2> lily.stderr.log
python export_events.py
lilypond -dno-point-and-click -o analisis adapted/export-events.ly > events.stdout.log 2> events.stderr.log
python parse_events.py
python validate_score.py
```

Los nombres `upper` y `lower` del exportador se corresponden con `up` y `down` del MIDI original. `mapped-midi-notes.json` relaciona cada ataque con su voz, compás, tono, evento escrito y duración, preservando por separado las ligaduras/unísonos explicados. `source-events.json` incluye notas, articulación, fraseo, dinámicas, reguladores y texto. `expression-map.json` resume la forma e indicaciones legibles.

`ornament-realization.json` documenta tres grupetos gráficos que deben ejecutarse adicionalmente en el MIDI expresivo. El MIDI `partitura.midi` es una referencia técnica de la transcripción y no el audio ni la interpretación final. El archivo PDF ofrece la partitura completa elegida para revisar los símbolos.
