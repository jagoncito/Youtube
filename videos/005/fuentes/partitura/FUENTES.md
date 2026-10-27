# Chopin — Nocturno en re bemol mayor, op. 27 n.º 2

## Fuente identificada

- Compositor: **Frédéric Chopin (1810–1849)**. Nocturno en re bemol mayor, op. 27 n.º 2, escrito en 1835 y publicado en 1836.
- Edición histórica declarada por la transcripción: **Claude Debussy, 1915**. No se ha cotejado independientemente el facsímil de esa edición; se valida la fidelidad al texto digital elegido.
- Transcripción y mantenimiento: **Scott Horne and Keith OHara**, Mutopia Project, referencia **Mutopia-2012/02/12-486**.
- Repositorio: https://github.com/MutopiaProject/MutopiaProject
- Revisión inmutable: `2144afd6f52d56c5b6995b8b589ef1268b3139f0`.
- Ruta: `ftp/ChopinFF/O27/chopin-nocturne-8/chopin-nocturne-8.ly`.
- Enlace preciso: https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/ChopinFF/O27/chopin-nocturne-8/chopin-nocturne-8.ly
- Objeto Git del original, verificado contra el repositorio: `500d79696ebe94e7d28837ca42c5e005576fcdfb`.

La composición histórica y la transcripción digital tienen derechos distintos. Esta transcripción declara expresamente **Creative Commons Attribution-ShareAlike 3.0 Unported**; no se etiqueta como CC0 o dominio público universal. Se conserva su encabezado completo y la indicación de que una versión antigua tuvo otra licencia; se usa la licencia explícita de la revisión actual.

Licencia oficial: https://creativecommons.org/licenses/by-sa/3.0/ . Texto íntegro incluido en `CC-BY-SA-3.0.txt`, procedente del repositorio SPDX `license-list-data`, revisión `31ba1a50e5397e00a304dbadc76531740e89ee48`, ruta `text/CC-BY-SA-3.0.txt`. La nueva interpretación y los vídeos adaptados se comparten bajo CC BY-SA 3.0, conservando atribución, licencia y declaración de cambios. Los instrumentos/muestras tienen sus propias licencias, documentadas por separado.

## Qué se ha comprobado

La fuente original tiene 970 líneas y se conserva byte a byte en `original/`. Se convirtió automáticamente desde LilyPond 2.14.2 a sintaxis 2.24.0 con `convert-ly`, y se compiló con **LilyPond 2.24.4** a partitura PDF completa y MIDI. Las compilaciones terminaron correctamente, sin avisos de compás ni errores de duración. Los cambios de compatibilidad no pretenden ser una nueva edición crítica.

La obra tiene **77 compases de 6/8**, equivalentes a **231 negras**. Ambas manos terminan exactamente en ese punto. No hay signos de repetición interna que deban desplegarse además; las repeticiones completas de la versión larga se realizan posteriormente en el montaje.

Se exportaron los eventos reales de LilyPond, incluidos los tiempos principales y de gracia, voces, notas y duraciones con sus factores de tuplet, dinámicas, articulaciones, ligaduras, pedal y textos. Los datos están en `source-events.json`.

| Elemento | Cantidad |
| --- | ---: |
| Notas gráficas | 1870 |
| Inicios de nota MIDI, sin notas colgadas | 1806 |
| Continuaciones ligadas sin nuevo ataque | 40 |
| Unísonos simultáneos consolidados en el MIDI | 24 |
| Notas de gracia asociadas a sus eventos MIDI | 30 |
| Eventos de pedal | 224 |
| Dinámicas explícitas | 23 |
| Eventos de crescendo/decrescendo | 123 |
| Eventos de articulación | 142 |
| Eventos de ligaduras de expresión y frase | 292 |

Cada inicio MIDI se asocia a un evento de la notación. Las 64 notas gráficas sin nuevo ataque MIDI se explican una por una en `score-validation.json`: 40 son continuaciones ligadas y 24 son unísonos de voces simultáneas ya representados por el mismo tono. No queda ninguna omisión inexplicada. Para notas ordinarias se admite la cuantización de un tick (1/384 de negra); las gracias se asocian separadamente porque LilyPond anticipa su ejecución respecto del tiempo principal.

`mapped-midi-notes.json` contiene los 1806 eventos de ejecución con identidad de fuente: `onset_quarter`, `gate_quarters`, `main_quarter`, `grace_quarter`, `staff`, `voice`, `bar`, `pitch`, `source_index`. Son una base verificable para la interpretación expresiva, no una grabación terminada.

## Decisiones que debe tomar la interpretación

- La indicación es **Lento sostenuto**. El encabezado gráfico marca negra con puntillo = 50 y contiene una nota editorial «Often performed at 30–40 beats per minute»; el bloque MIDI declara 35, que LilyPond cuantiza a negra = 52 en el archivo MIDI. **No se debe confundir ese tempo de exportación con una obligación musical ni elegir un tempo para cuadrar la duración de la entrega.**
- Las notas de gracia están ya presentes en el MIDI. Los símbolos de adorno, como el giro y el trino, se exportan como articulaciones; si se realizan explícitamente en la interpretación, documentar las notas añadidas y conservar el anclaje a la nota escrita.
- Las ligaduras deben evitar reataques artificiales. La parte derecha incluye voces interiores, acordes y melodía; no se puede asumir que toda nota de esa mano sea la voz principal.
- El pedal está marcado explícitamente. Al principio se mantiene durante cuatro compases de una misma armonía; la realización sonora puede necesitar limpieza o cambios de profundidad para evitar acumulación de resonancia. Cualquier revisión de pedal será una decisión de interpretación documentada, sin alterar la copia original.
- Se conservan los cambios de carácter, crescendos, decrescendos y el calderón final. No se aplana la dinámica para anunciar sueño uniforme.

## Reproducción de las comprobaciones

Con Python y `mido` instalados: `python validate_score.py` en este directorio. Esa comprobación vuelve a asociar los eventos y produce el mapa y la auditoría.

Con LilyPond 2.24.4 instalado: `lilypond -o partitura adapted/chopin-nocturne-8.ly`. Para regenerar eventos: `python export_events.py`, después `lilypond -dbackend=null -dno-print-pages -o events adapted/export-events.ly > events.stdout.log 2> events.stderr.log`, y `python parse_events.py`. Conservar `events.stdout.log` durante esa extracción; no es necesario para reproducir el audio una vez guardado el JSON.

Los hashes SHA-256 de las fuentes, PDF, MIDI, JSON y mapa se conservan en `score-validation.json`. Las comprobaciones demuestran cobertura y correspondencia del texto digital elegido; **no equivalen a una escucha subjetiva ni a una comparación independiente con una primera edición histórica**.

## Atribución en inglés

> Frédéric Chopin — Nocturne in D-flat major, Op. 27 No. 2. Score transcription: Scott Horne and Keith OHara / Mutopia Project, Mutopia-2012/02/12-486; based on the edition identified by the transcribers as Claude Debussy, 1915. CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/ . New digital performance and audiovisual adaptation for Jagoncito, with editorial timing, dynamics, articulation, pedal and mixing; shared under CC BY-SA 3.0. No finished third-party performance recording was used. Score: https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/ChopinFF/O27/chopin-nocturne-8/chopin-nocturne-8.ly .
