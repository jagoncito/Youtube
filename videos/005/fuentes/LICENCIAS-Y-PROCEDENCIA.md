# Procedencia y permisos de 005

Obra: **Frédéric Chopin (1810–1849), Nocturno en re bemol mayor, op. 27 n.º 2**. La composición histórica, la edición digital, las muestras instrumentales y la nueva interpretación tienen derechos distintos. No se ha utilizado una grabación terminada de otro intérprete.

## Partitura e interpretación

Transcripción de **Scott Horne and Keith OHara / Mutopia Project**, referencia **Mutopia-2012/02/12-486**. La edición histórica declarada por los transcriptores es **Claude Debussy, 1915**. [Fuente fijada](https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/ChopinFF/O27/chopin-nocturne-8/chopin-nocturne-8.ly), revisión `2144afd6f52d56c5b6995b8b589ef1268b3139f0`.

Licencia de esa transcripción: **[CC BY-SA 3.0 Unported](https://creativecommons.org/licenses/by-sa/3.0/)**. El texto legal se conserva en `licencias/CC-BY-SA-3.0.txt`, y las fuentes originales/adaptadas, PDF completo, MIDI y comprobaciones en [partitura/](partitura/). La auditoría demuestra correspondencia con esa transcripción, sin atribuirse un cotejo independiente con un facsímil histórico.

La nueva interpretación, el MIDI expresivo y los dos vídeos derivados se comparten bajo **CC BY-SA 3.0**, con atribución, enlace a la licencia y declaración de cambios. Se han trabajado tempo, rubato, voces, dinámica, articulación, ornamentos escritos, pedal, mezcla y escena. La licencia permite uso comercial con sus condiciones; se mantienen los permisos y no se añaden restricciones a los materiales así licenciados. Los créditos para publicar están en `../publicacion.txt`.

## Piano

**Salamander Grand Piano v3**, Yamaha C5 muestreado por **Alexander Holm**; afinación alternativa de **Markus Fiedler** y reconstrucción SFZ de **kinwie / sfzinstruments**. Licencia **[CC BY 3.0 Unported](https://creativecommons.org/licenses/by/3.0/)**, conservada en `instrumento/original/LICENSE`.

[Repositorio y revisión exacta](https://github.com/sfzinstruments/SalamanderGrandPiano/tree/3382bf9496bba2486f5ab0de55a264d1dfc38404): `3382bf9496bba2486f5ab0de55a264d1dfc38404`.

Las muestras son estéreo de 48 kHz y 24 bits, con 16 capas de intensidad. Se conservan los mapas originales, los controles de pedal y las muestras de liberación/resonancia; no se inventan bucles para mantener notas de piano. La interpretación utiliza un piano común a ambas manos y la afinación Retuned. Los ruidos físicos de tecla/pedal se mantienen a nivel discreto, con los ajustes recogidos en el informe del render.

El manifiesto de `instrumento/instrument-sources.json` identifica **668 archivos, incluidos 641 FLAC**, con URL inmutable, tamaño y SHA-256, verificados contra los objetos Git. Los mapas/documentos originales se incluyen. Los aproximadamente 748 MB de muestras aisladas se recuperan con `../produccion/download_piano.py`; no constituyen otra pista de escucha ni una grabación del nocturno.

El pedal se comprobó con CC64 y mediante liberaciones reales en la interpretación. No se afirma simulación física continua de cada cuerda, medio pedal continuo ni modelado completo de resonancia simpática. Son muestras discretas de un piano real. [Detalle y pruebas del instrumento](instrumento/FUENTES-PIANO.md).

## Herramientas y visuales

Motor [sfizz](https://github.com/sfztools/sfizz/tree/f5c6e29f23b8057867c08e88f5f6ac6738baa30b), revisión `f5c6e29f23b8057867c08e88f5f6ac6738baa30b`, licencia BSD de dos cláusulas; autores y texto conservados en `licencias/`. Se usa como herramienta; aquí no se redistribuye su binario. Python/MIDI y FFmpeg se utilizan para producir y verificar. Las dependencias conservan sus licencias.

La imagen del jardín se generó nueva con OpenAI Image Generation. La imagen de 004 se aportó exclusivamente como referencia de identidad del personaje; el jardín, composición, perspectiva y microhistoria son nuevos. La miniatura se generó a partir de la nueva escena de 005. No se reutilizan imágenes ni clips de 001–004 como contenido de esta entrega.

La animación añade ondulación suave de reflejos dentro del estanque, dos pétalos nuevos y reflejos discretos. Los animales y el pétalo ya dibujado junto al dragón permanecen estáticos. No se han añadido sonidos de lluvia, agua u otro ambiente. La reverberación musical se genera matemáticamente, sin una grabación externa de sala.

Las aportaciones nuevas se ofrecen bajo CC BY-SA 3.0 en la medida en que existan derechos aplicables; los materiales de terceros conservan sus propias licencias. La entrega no se anuncia como íntegramente CC0 ni de dominio público universal y no promete ausencia de coincidencias automáticas de Content ID. No se publican los 128 informes ni las exportaciones privadas de Studio.
