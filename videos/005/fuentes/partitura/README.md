# Partitura verificada de005

Chopin: Nocturno en re bemol mayor, op.27 n.º2. Fuente, autores, licencia CC BY-SA3.0, alcance y límites: [FUENTES.md](FUENTES.md).

- `original/chopin-nocturne-8.ly`: fuente intacta de Mutopia.
- `adapted/`: conversión de compatibilidad y extractor; compilados con LilyPond2.24.4.
- `partitura.pdf`: partitura completa; `partitura.midi`: MIDI de notación, no interpretación final.
- `source-events.json`: notas, voces, adornos, ligaduras, dinámicas y pedal.
- `mapped-midi-notes.json`:1806 eventos MIDI enlazados a la notación.
- `score-validation.json`: auditoría y hashes.

Desde este directorio, con Python y `mido` instalados:

```bash
python validate_score.py
```

Con LilyPond2.24.4 instalado:

```bash
lilypond -o partitura adapted/chopin-nocturne-8.ly
python export_events.py
lilypond -dbackend=null -dno-print-pages -o events adapted/export-events.ly > events.stdout.log 2> events.stderr.log
python parse_events.py
python validate_score.py
```

Las rutas se resuelven respecto del propio directorio; no requieren rutas de la máquina original. Resultado observado:77compases6/8, manos alineadas en231negras,1870notas escritas=1806iniciosMIDI+40continuacionesligadas+24unísonos simultáneos consolidados. Las30gracias tienen correspondencia MIDI; no hay notas colgadas ni omisiones inexplicadas. La verificación no es una escucha subjetiva ni un cotejo independiente con un facsímil histórico.
