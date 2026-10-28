# Procedencia y permisos de 006

Obra: **Claude Debussy (1862–1918), Clair de lune**, tercer movimiento de *Suite bergamasque*, versión original para piano solo en re bemol mayor. La composición, la transcripción, las muestras instrumentales y la nueva interpretación son capas distintas. No se ha utilizado una grabación terminada de otro intérprete.

## Partitura

Transcripción de **Keith OHara / Mutopia Project**, referencia **Mutopia-2010/12/21-1778**, basada en la edición identificada por el transcriptor como **E. Fromont, 1905**. [Fuente exacta](https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/DebussyC/L75/debussy_Ste_Bergamesq_Clair/debussy_Ste_Bergamesq_Clair.ly), revisión `2144afd6f52d56c5b6995b8b589ef1268b3139f0`.

El encabezado y el pie de la fuente declaran **Public Domain** para esta transcripción. Se conservan íntegros en [partitura/original/clair-de-lune.ly](partitura/original/clair-de-lune.ly), junto con PDF, MIDI y comprobaciones. No se inventa una licencia CC0 ni se hereda la licencia ShareAlike de las partituras de 004/005.

La auditoría verifica correspondencia con esa transcripción digital: 72 compases, 1494 ataques MIDI y las continuaciones ligadas/unísonos explicados. No se afirma un cotejo independiente nota a nota con un facsímil histórico ni una edición crítica. [Detalle y límites](partitura/FUENTES.md).

## Piano e interpretación

**Salamander Grand Piano v3**, Yamaha C5 muestreado por **Alexander Holm**. Afinación alternativa: **Markus Fiedler**. Reconstrucción SFZ: **kinwie / sfzinstruments**. Licencia **[CC BY 3.0 Unported](https://creativecommons.org/licenses/by/3.0/)**, conservada en `licencias/CC-BY-3.0.txt` y `instrumento/original/LICENSE`.

[Revisión exacta del instrumento](https://github.com/sfzinstruments/SalamanderGrandPiano/tree/3382bf9496bba2486f5ab0de55a264d1dfc38404): `3382bf9496bba2486f5ab0de55a264d1dfc38404`. El manifiesto identifica 668 archivos —641 muestras FLAC y 27 mapas/documentos— con URL inmutable, tamaño y SHA-256. Todos se verificaron de nuevo en esta producción. Los aproximadamente 748 MB de muestras aisladas se recuperan con `../produccion/download_piano.py`; no se añade otra pista de escucha al paquete.

Se reutiliza el instrumento de 005, con 16 capas, toma estéreo de 48 kHz/24 bits y afinación Retuned. La interpretación de Debussy, su MIDI y el máster son nuevos. Se mantienen mapas y envolventes, con muestras de liberación/resonancia y controles físicos discretos documentados. No se añaden bucles artificiales para sostener notas de piano.

La fuente de la partitura no contiene eventos efectivos de pedal, aunque define macros. Por ello el pedal de la interpretación es una **realización editorial según la armonía**, con tomas y liberaciones CC64 comprobadas; no se atribuye falsamente a marcas originales ni a una simulación continua de medio pedal. Las voces, arpegios escritos, dinámicas, textos de carácter y rubato se trabajan sin añadir otras notas o piezas.

La nueva interpretación y los vídeos se comparten bajo **CC BY 3.0**, con atribución, enlace a la licencia y declaración de cambios. No se anuncian como una grabación de dominio público universal. Los créditos para publicar están en `../publicacion.txt`. No se promete ausencia de coincidencias de Content ID.

## Herramientas y visuales

Motor [sfizz](https://github.com/sfztools/sfizz/tree/f5c6e29f23b8057867c08e88f5f6ac6738baa30b), revisión `f5c6e29f23b8057867c08e88f5f6ac6738baa30b`, licencia BSD de dos cláusulas; autores y texto incluidos en `licencias/`. Se utiliza como herramienta de render y no se distribuye su binario. Python/MIDI y FFmpeg se usan para producción y comprobación; las dependencias conservan sus propias licencias. La reverberación procede de una respuesta matemática nueva, sin una grabación de sala externa.

La imagen costera se generó nueva con OpenAI Image Generation. La imagen de 005 se aportó únicamente como referencia de identidad del personaje; la cala, perspectiva, composición y microhistoria son nuevas. La miniatura se generó a partir de la nueva escena de 006. No se reutilizan imágenes ni clips anteriores como contenido del vídeo.

La animación mueve zonas interiores del mar, espuma derecha y reflejos. Los personajes, el horizonte, el espigón y el faro permanecen estáticos. No se añaden sonidos del mar o del viento. Las aportaciones nuevas se ofrecen bajo CC BY 3.0 en la medida en que existan derechos aplicables, y los materiales de terceros conservan sus licencias indicadas.

No se incluyen el compilado de los 128 informes, las síntesis privadas ni las exportaciones de YouTube Studio. Las comprobaciones técnicas y la inspección visual no equivalen a una escucha subjetiva; esa valoración no se ha realizado.
