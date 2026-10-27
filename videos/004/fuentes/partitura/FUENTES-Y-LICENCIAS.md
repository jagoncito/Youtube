# Vivaldi — El invierno / Winter, RV 297, op. 8 n.º 4

## Partitura empleada

- Compositor: Antonio Vivaldi (1678–1741). Obra publicada en 1725, *Il cimento dell’armonia e dell’inventione*, concierto IV de *Las cuatro estaciones*.
- Transcripción: *L’Inverno / Winter*, Mutopia Project, referencia Mutopia-2010/02/08-351; responsable indicado públicamente: **Anonymous**. Actualización declarada: 31 de enero de 2010.
- Fuente declarada por esa transcripción: **Performers’ Facsimiles**. Esta entrega no incluye ni afirma haber cotejado nota por nota un facsímil histórico independiente.
- Repositorio: https://github.com/MutopiaProject/MutopiaProject
- Revisión fija: `2144afd6f52d56c5b6995b8b589ef1268b3139f0`.
- Directorio original: `ftp/VivaldiA/O8/winter/winter-lys`.
- Fuente precisa: https://github.com/MutopiaProject/MutopiaProject/tree/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/VivaldiA/O8/winter/winter-lys
- Licencia declarada de la transcripción: **Creative Commons Attribution-ShareAlike 3.0 Unported**, https://creativecommons.org/licenses/by-sa/3.0/ . No se presenta esta transcripción como CC0 ni como dominio público universal.

La composición histórica y la edición digital tienen derechos distintos. Que Vivaldi sea un compositor histórico cuya obra pertenece al dominio público en los territorios de plazo ordinario no elimina la licencia de la transcripción moderna. La atribución y la obligación de compartir las adaptaciones bajo la misma licencia se conservan. La entrega audiovisual y la interpretación digital que se derivan de esta transcripción se publican bajo CC BY-SA 3.0; no deben imponerse restricciones adicionales a esa licencia. Las licencias de las muestras instrumentales se documentan por separado.

Texto de licencia incluido en `CC-BY-SA-3.0.txt`, obtenido del repositorio SPDX `license-list-data`, revisión `31ba1a50e5397e00a304dbadc76531740e89ee48`, ruta `text/CC-BY-SA-3.0.txt`. Enlace: https://github.com/spdx/license-list-data/blob/31ba1a50e5397e00a304dbadc76531740e89ee48/text/CC-BY-SA-3.0.txt . El enlace oficial anterior identifica la licencia.

Atribución sugerida en inglés:

> Antonio Vivaldi — Winter, Violin Concerto in F minor, RV 297, Op. 8 No. 4. Score transcription: Anonymous / Mutopia Project, Mutopia-2010/02/08-351, based on Performers’ Facsimiles. CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/ . New digital performance, expressive editing and audiovisual adaptation for Jagoncito; no finished third-party recording used. This adaptation is shared under CC BY-SA 3.0. Score source: https://github.com/MutopiaProject/MutopiaProject/tree/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/VivaldiA/O8/winter/winter-lys .

## Qué se ha verificado

Se han descargado las fuentes LilyPond completas de una revisión inmutable del repositorio de Mutopia. Se conserva copia original byte a byte. Se han compilado los tres movimientos completos a MIDI y a un PDF legible con LilyPond 2.24.4, sin errores de compilación ni avisos de compases desalineados. El PDF mantiene créditos y licencia.

| Movimiento | Indicación | Compás | Compases completos | Negras de notación |
| --- | --- | --- | ---: | ---: |
| I | Allegro non molto | 4/4 | 63 | 252 |
| II | Largo | 4/4 | 18 | 72 |
| III | Allegro, con sección Lento | 3/8 | 153 | 229,5 |

Los cinco pentagramas instrumentales —violín principal, violín primero, violín segundo, viola y órgano/violonchelo— terminan en el mismo punto de cada movimiento. Se conserva el bajo cifrado en las fuentes. Esta edición no tiene signos de repetición de secciones que deban desplegarse adicionalmente. La repetición del concierto completo para la versión larga se realiza después, sin recortar movimientos.

La auditoría `score-validation.json` compara todos los inicios de nota MIDI con los eventos de la notación compilada: **6802 pares de note-on/note-off**, sin notas colgadas ni cierres huérfanos. **120 continuaciones ligadas** explican la diferencia con las 6922 notas gráficas; cada continuación coincide con el final de una nota previa del mismo tono. La auditoría acredita fidelidad al texto digital elegido y cobertura completa, no una revisión musicológica independiente de todos sus posibles errores editoriales.

## Cambios de compatibilidad y decisiones de interpretación

- Las fuentes originales son LilyPond 2.12.3. `convert-ly` las actualizó a 2.24.0 para compilarlas con LilyPond 2.24.4.
- Se eliminaron diez llamadas obsoletas a `override-auto-beam-setting` del movimiento III (dos en cada parte instrumental). Solo afectan al agrupamiento visual de corchetes, no a alturas ni duraciones.
- Las correcciones editoriales comentadas en la transcripción original —por ejemplo algunas alteraciones del movimiento III— se mantienen y siguen visibles en los archivos; no se atribuyen a una comprobación propia del manuscrito.
- Los tempos MIDI del editor son I: negra=140; II: negra=46; III: corchea=150. **No son un criterio obligatorio de interpretación**. En particular, reproducir el movimiento I mecánicamente a negra=140 no sería apropiado para la entrega solicitada. El rendimiento final utiliza decisiones de tempo y fraseo documentadas en la producción de audio.
- El movimiento III incluye «Lento Tutti / Il Vento Sirocco» desde la negra de notación 150 hasta 178,5, donde vuelve «Solo / Il Vento Borea e tutti li Venti». Esa indicación aparece como texto, no como cambio automático de tempo en el MIDI básico.
- El Largo especifica pizzicato en los dos violines de acompañamiento, viola muy suave **con arco**, y violonchelo siempre suave. No se convierte toda la cuerda en pizzicato.
- El comienzo del movimiento III indica en el bajo «Arcate lunghe, e Tasto Solo»: no se interpreta como una autorización para añadir acordes densos indiscriminadamente.

`markers.json` contiene las indicaciones textuales y sus posiciones exactas en negras. `source-events.json` recoge notas, trinos, staccato, staccatissimo, calderones, ligaduras de expresión y de prolongación. Los eventos `ART` se asocian a las notas del mismo movimiento, parte y posición; en `SLUR`/`PHRASE`, dirección -1 es inicio y +1 final. Sirven para realizar una interpretación nueva, no son una grabación.

## Archivos y reproducción de la comprobación

- `original/`: fuentes recibidas, sin modificación.
- `adapted/`: fuentes compatibles y extractores auxiliares.
- `partitura.pdf`: partitura completa compilada.
- `score.midi`, `score-1.midi`, `score-2.midi`: salidas MIDI básicas de los movimientos I, II y III. No son el audio final expresivo.
- `score-validation.json`: cobertura de las partes, conteos, rangos y hashes SHA-256.
- `validate_score.py`: comprobación de MIDI y notación. Requiere Python y `mido`; ejecutar `python validate_score.py` en este directorio.
- `export_markers.py` y `export_articulations.py`: generan los auxiliares LilyPond para la extracción de indicaciones.
- `lily.stderr.log` y `pdf.stderr.log`: compilaciones completas con resultado satisfactorio. Los avisos de compresión de páginas son de maquetación.

Para recompilar con LilyPond 2.24.4 instalado: `lilypond -o partitura adapted/winter-score.ly`. Para extraer los eventos: `lilypond -dbackend=null -dno-print-pages -o articulations adapted/export-articulations.ly`; la salida estándar contiene las líneas `NOTE`, `ART`, `TIE`, `SLUR` y `PHRASE` que se convierten en JSON. Las versiones expresivas MIDI posteriores se documentan aparte y no sustituyen la copia de partitura.

Las comprobaciones anteriores son técnicas y de estructura musical. No demuestran una escucha subjetiva del audio final ni garantizan ausencia de reclamaciones automáticas de Content ID.
