# Claude Debussy — Clair de lune, Suite bergamasque III

## Fuente identificada y derechos

- Compositor: **Claude Debussy (1862–1918)**.
- Obra: **Clair de lune**, tercer movimiento de *Suite bergamasque*, piano solo, re bemol mayor, compás de 9/8, indicación **Andante très expressif**.
- Transcripción y mantenimiento: **Keith OHara / Mutopia Project**, referencia **Mutopia-2010/12/21-1778**.
- Edición histórica declarada por el transcriptor: **E. Fromont (1905)**.
- Revisión fija: `2144afd6f52d56c5b6995b8b589ef1268b3139f0`.
- Ruta: `ftp/DebussyC/L75/debussy_Ste_Bergamesq_Clair/debussy_Ste_Bergamesq_Clair.ly`.
- [Fuente exacta](https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/DebussyC/L75/debussy_Ste_Bergamesq_Clair/debussy_Ste_Bergamesq_Clair.ly).

El encabezado de la revisión elegida declara **Public Domain**, y su pie afirma expresamente que el tipógrafo ha puesto esta partitura en el dominio público. La fuente original completa, con esa declaración y sus créditos, se conserva sin cambios en `original/clair-de-lune.ly`; su objeto Git y SHA-256 se verificaron. Esta declaración no es una licencia CC0 nueva inventada por esta entrega ni implica que las muestras de piano o una grabación ajena tengan los mismos derechos.

La composición histórica, la transcripción, los instrumentos y la nueva interpretación son capas distintas. En particular, la licencia del piano Salamander usado para la realización sonora se acredita por separado. La presente fuente no impone ShareAlike; no se hereda por analogía la licencia CC BY-SA de otras obras de Mutopia utilizadas en entregas anteriores. No se promete dominio público universal del máster ni ausencia de coincidencias automáticas de Content ID.

El encabezado cita como referencia una página y un archivo de IMSLP de Fromont. **No se ha realizado aquí un cotejo independiente nota a nota con ese facsímil**; se documenta esa limitación y se valida la correspondencia de la transcripción digital elegida con su compilación y exportación.

## Cobertura musical comprobada

Se compiló la fuente LilyPond **2.24.3** con LilyPond **2.24.4**, sin cambios musicales. `adapted/clair-de-lune.ly` conserva el mismo contenido que el original; el nombre de la carpeta indica su uso en la producción, no una nueva edición crítica. El PDF completo y MIDI terminaron correctamente. Los avisos de configuración de algunas barras de unión entre pentagramas son de maquetación, sin fallos de compás o duración.

La obra contiene **72 compases de 9/8**, equivalentes a **324 negras**. Ambos pentagramas MIDI terminan alineados en ese punto. La última nota termina en la negra 322,5 y queda el silencio escrito de la última parte del compás final. No hay signos de repetición interna que deban desplegarse además de la música escrita; los ciclos completos de la versión larga se montan posteriormente.

| Elemento | Cantidad |
| --- | ---: |
| Notas gráficas exportadas | 1683 |
| Ataques MIDI físicos | 1494 |
| Continuaciones ligadas sin nuevo ataque | 116 |
| Unísonos simultáneos consolidados | 73 |
| Nota de gracia asociada a su ataque MIDI | 1 |
| Ligaduras de frase | 146 |
| Ligaduras de expresión | 134 |
| Articulaciones | 105 |
| Acordes con indicación de arpegio | 12 |
| Dinámicas explícitas | 8 |
| Crescendo/decrescendo exportados | 12 |
| Cambios textuales de tempo | 6 |
| Textos adicionales | 7 |
| Eventos efectivos de pedal | 0 |

Cada ataque MIDI se asocia a su evento de notación en `mapped-midi-notes.json`. Las 189 notas gráficas que no generan un ataque nuevo se explican individualmente: 116 continuaciones ligadas y 73 unísonos ya representados por el mismo tono. No quedan omisiones inexplicadas ni notas colgadas. Se admite un tick de cuantización MIDI (1/384 de negra) y se trata la gracia por separado.

Las cuatro voces se identifican como `red`, `green`, `blue` y `grey`. Cambian de pentagrama durante los cruces de manos: `upper` y `lower` describen su colocación en ese instante, no una mano invariable. La auditoría conserva la identidad de voz y comprueba las ligaduras a través de los cambios de pentagrama. Los duplicados gráficos no se presentan como omisiones de música.

## Indicaciones para la interpretación nueva

| Posición en negras | Compás | Indicación textual |
| ---: | ---: | --- |
| 0 | 1 | Andante très expressif |
| 63 | 15 | Tempo rubato |
| 117 | 27 | Un poco mosso |
| 162 | 37 | En animant |
| 189 | 43 | Calmato |
| 225 | 51 | a Tempo 1º |

La fuente **no fija un valor metronómico numérico** para esos textos. El tempo numérico que aparece en el MIDI compilado es una decisión predeterminada del programa, no una instrucción de Debussy ni una obligación para la interpretación. Las curvas de ejecución y la duración final deben documentarse aparte.

Hay textos musicales significativos además de las dinámicas absolutas: *con sordina* al principio, *peu à peu, cresc. et animé* en el compás 19, *diminuendo molto* en el 25, *cresc.* en el 35, *più cresc.* en el 37, un **ppp** escrito como texto de dinámica en el compás 51 y *morendo jusqu'à la fin* en el 66. No deben ignorarse por estar representados como texto en vez de un evento dinámico simple.

Se definen macros de pedal `sd`, `su` y `sv` en el preámbulo, pero **no se utilizan** en la música de esta revisión; la voz llamada `pedal` está vacía. Por ello no se atribuyen al original cambios de CC64 que no contiene. La realización de pedal necesaria para la interpretación es editorial y debe declararse, con tomas y liberaciones según la armonía y las capacidades reales del instrumento. Tampoco se atribuye una simulación de medio pedal continuo que no se haya comprobado.

Los arpegios escritos aparecen en las negras 108, 111, 112,5, 115,5, 246, 255 y 319,5, distribuidos entre las voces correspondientes. `source-events.json` conserva sus eventos, así como la gracia, articulaciones, duraciones con grupos irregulares y ligaduras. No es una grabación terminada.

## Atribución sugerida en inglés

> Claude Debussy — Clair de lune, Suite bergamasque, III. Score transcription: Keith OHara / Mutopia Project, Mutopia-2010/12/21-1778; based on the edition identified by the transcriber as E. Fromont, 1905. The typesetter explicitly placed this transcription in the public domain. Score source: https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/DebussyC/L75/debussy_Ste_Bergamesq_Clair/debussy_Ste_Bergamesq_Clair.ly . New digital piano interpretation for Jagoncito; no finished third-party performance recording used. Piano samples and the new master are credited and licensed separately.

Estas comprobaciones acreditan cobertura y correspondencia con la fuente digital. No constituyen una escucha subjetiva, una edición crítica histórica ni una garantía sobre preferencias de audiencia.
