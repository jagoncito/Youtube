# Procedencia y permisos de 004

La composición es *El invierno*, RV 297, op. 8 n.º 4, de Antonio Vivaldi (1678–1741), publicada en 1725. No se ha utilizado una grabación terminada de otro intérprete. La partitura digital elegida y las muestras instrumentales tienen licencias distintas; esta entrega no se presenta como íntegramente CC0 ni de dominio público universal.

## Partitura e interpretación

Transcripción: **Anonymous / Mutopia Project**, referencia **Mutopia-2010/02/08-351**, fuente declarada *Performers’ Facsimiles*. [Revisión exacta](https://github.com/MutopiaProject/MutopiaProject/tree/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/VivaldiA/O8/winter/winter-lys): `2144afd6f52d56c5b6995b8b589ef1268b3139f0`.

Licencia: [CC BY-SA 3.0 Unported](https://creativecommons.org/licenses/by-sa/3.0/), texto incluido en [licencias/CC-BY-SA-3.0.txt](licencias/CC-BY-SA-3.0.txt). La nueva interpretación, el MIDI expresivo y los dos vídeos derivados se comparten bajo esa misma licencia, con atribución y declaración de cambios. Permite uso comercial con sus condiciones; no se deben añadir restricciones a los permisos concedidos. Los créditos para publicar están en `../publicacion.txt`.

Cambios: adaptación de compatibilidad de LilyPond, tempos y fraseo propios, articulaciones y dinámica, realización editorial de trinos escritos, sostenimiento de notas largas, mezcla, reverberación y nueva imagen/animación. Se conservan fuentes originales, fuentes compatibles, PDF completo, MIDI de notación y auditoría en [partitura/](partitura/). La verificación demuestra correspondencia con esta transcripción, sin afirmar cotejo musicológico independiente con un facsímil histórico.

## Instrumentos

**VS Chamber Orchestra Community Edition / VSCO 2 CE**. Grabación de muestras: **Sam Gossner y Simon Dalzell**; corte de muestras: **Elan Hickler / Soundemote**. Licencia **CC0 1.0**, textos originales de las dos revisiones en `licencias/VSCO-CC0.txt` y `licencias/VSCO-SFZ-CC0.txt`.

- [Muestras, revisión 440300901dfe9275fd84e0b7763af1f8443ae62e](https://github.com/sgossner/VSCO-2-CE/tree/440300901dfe9275fd84e0b7763af1f8443ae62e).
- [Mapas SFZ, revisión 6dd651d55dde97fd4028699be9d4481f26917891](https://github.com/sgossner/VSCO-2-CE/tree/6dd651d55dde97fd4028699be9d4481f26917891).
- Violín solista: arco con vibrato y spiccato; secciones de violín, viola y violonchelo: sostenido/articulaciones cortas; violines de acompañamiento del Largo en pizzicato; órgano suave como refuerzo del bajo.
- Se respetan afinación y mapas de notas originales. Los ataques y las colas se ajustan durante el render; algunas regiones sostenidas reciben un bucle con fundido de 120 ms para conservar notas que exceden la duración de una muestra.
- `instrumentos/original-sfz/` conserva los mapas originales. `instrumentos/instrument-sources.json` identifica 558 archivos de procedencia (542 muestras, 14 mapas y 2 documentos), con URL inmutable, tamaño y SHA-256. Se verificaron todos. La biblioteca de aproximadamente 493 MB se recupera mediante `../produccion/download_instruments.py`; no es otro audio de escucha ni una grabación del concierto.

La biblioteca no incluye transiciones de legato grabadas. Se ha trabajado la expresión con tempo común, ligaduras, articulaciones, velocidades y curvas CC11; no se atribuye a una orquesta humana. El órgano dobla la línea de bajo, respetando el *Tasto Solo* inicial del tercer movimiento. No se presenta como realización armónica completa de todo el bajo cifrado.

## Herramientas y visuales

Motor [sfizz](https://github.com/sfztools/sfizz/tree/f5c6e29f23b8057867c08e88f5f6ac6738baa30b), revisión `f5c6e29f23b8057867c08e88f5f6ac6738baa30b`, licencia BSD 2 cláusulas; texto y autores incluidos en `licencias/`. Se usa como herramienta de render; no se distribuye su binario aquí. Las dependencias conservan sus propias licencias. Python/MIDI y FFmpeg se utilizan para producción y comprobación.

La imagen principal y la miniatura se generaron nuevas con OpenAI Image Generation para este encargo. La miniatura se elaboró a partir de la nueva escena de 004. No se reutilizan escenas, clips ni miniaturas de 001–003. La animación ambiental es nueva: nieve exterior, variación local de luz y pequeños reflejos del arroyo. Los animales permanecen estáticos. La reverberación es una respuesta matemática propia, sin grabación externa de una sala.

Las aportaciones nuevas de esta entrega se ofrecen bajo CC BY-SA 3.0 en la medida en que existan derechos aplicables; los materiales de terceros conservan sus licencias indicadas. No se promete ausencia de coincidencias automáticas de Content ID. No se incluyen los informes privados ni las exportaciones de YouTube Studio.
