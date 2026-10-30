# Piano de cola para Beethoven 007

**Salamander Grand Piano v3**, un **Yamaha C5** muestreado por **Alexander Holm**, grabado con dos AKG c414 cerca de las cuerdas. Su toma original es estéreo, 48 kHz y 24 bits, con **16 capas de velocidad**. Se conserva el instrumento de 005–006; el MIDI y la interpretación del *Adagio cantabile*, op. 13, II, de Beethoven se producen de nuevo.

## Fuente y licencia del instrumento

Repositorio: https://github.com/sfzinstruments/SalamanderGrandPiano

Revisión fija: `3382bf9496bba2486f5ab0de55a264d1dfc38404`.

Licencia **Creative Commons Attribution 3.0 Unported (CC BY 3.0)**: https://creativecommons.org/licenses/by/3.0/ . Se conserva el texto original en `original/LICENSE` y una copia en `../licencias/CC-BY-3.0.txt`. Permite reutilizar y adaptar con atribución y conservación de los avisos. Esta biblioteca de muestras no se presenta como CC0 ni como dominio público. La composición de Beethoven, la edición utilizada, las muestras y la nueva interpretación tienen derechos separados; la licencia de la partitura debe consultarse en su propio expediente.

- Muestreo: Alexander Holm.
- Afinación alternativa: Markus Fiedler.
- Reconstrucción del mapa SFZ: kinwie / sfzinstruments.
- Fuente histórica declarada por el repositorio: https://archive.org/details/SalamanderGrandPianoV3 . Se verificaron el contenido y la licencia de la revisión de GitHub citada; no se afirma una inspección independiente de esa página externa.

Crédito sugerido en inglés:

> Piano samples: Salamander Grand Piano v3 (Yamaha C5), Alexander Holm. Retuned mapping by Markus Fiedler; SFZ reconstruction by kinwie / sfzinstruments. CC BY 3.0: https://creativecommons.org/licenses/by/3.0/ . Source: https://github.com/sfzinstruments/SalamanderGrandPiano/tree/3382bf9496bba2486f5ab0de55a264d1dfc38404 . New digital performance; no finished third-party recording used.

## Verificación realizada para 007

Se volvieron a leer y comprobar **668 archivos de fuente**, incluidos **641 FLAC** y 27 mapas/documentos, **748451483 bytes** en total. Todos coinciden en tamaño, SHA-256 y objeto Git con el manifiesto de la revisión fija. `cache-verification-007.json` registra esta comprobación actual; `instrument-sources.json` conserva cada URL inmutable, tamaño y hash.

Se conserva una copia exacta del SFZ, los archivos Data, el README y la licencia. Las muestras aisladas ocupan aproximadamente 748 MB y se restauran con `download_piano.py`; no se incluye ese volumen de fuentes de instrumento ni otro audio independiente en la entrega.

Las **641 muestras** son estéreo, **48 kHz / PCM de 24 bits**. Se identificaron **480 muestras de ataque: 30 notas base × 16 velocidades**. Las restantes corresponden a liberaciones de tecla, resonancias grabadas y acción del pedal. Los intervalos del mapa cubren sin huecos ni solapamientos las **88 teclas MIDI 21–108**; las notas intermedias se obtienen por transposición según el SFZ original. Los ataques duran entre **2,626 s y 25,863 s**, conservando sus decaimientos. Estos datos constan en `sample-format-validation.json`.

El mapa avisa de su uso de SFZ 2 y extensiones ARIA. Se probó el motor **sfizz**, revisión `f5c6e29f23b8057867c08e88f5f6ac6738baa30b`, que cargó **1121 regiones y 641 archivos de muestra**. Se comprobaron funciones efectivas del instrumento, además de la lectura de archivos:

- **Pedal CC64:** el mismo acorde mantiene una cola **44,4459 dB** más alta con pedal activo que sin él, comparando las ventanas 2,5–3,5 s y 8,5–9,5 s de una prueba de 14 s. El pedal se libera antes del segundo acorde. Audio finito y estéreo: `piano-capability-test.json`.
- **Respuesta a velocidad:** cuatro acordes idénticos, cada uno en una instancia limpia y con los controles de producción, a velocidades **35 / 60 / 82 / 108**, produjeron RMS de ataque **0,009637 / 0,026738 / 0,049305 / 0,098370**. La ventana medida fue 0,27–0,42 s, con inicio de nota en 0,25 s. Se comprobó crecimiento estricto y audio finito: `velocity-response-007.json`.

Son comprobaciones técnicas de fuentes, motor y respuesta. **No se realizó una escucha subjetiva** y estos resultados no constituyen un juicio auditivo de la interpretación o mezcla final.

## Uso y límites

El render carga el SFZ original completo en un único piano compartido por todas las voces, con 512 voces de polifonía disponibles. La tecla de control MIDI 13 selecciona la afinación **Retuned** de Markus Fiedler; está fuera del registro musical del piano. Se mantienen las envolventes y los mapas originales de nota y velocidad, sin añadir bucles artificiales de sostenimiento.

Los controles MIDI originales reducen los ruidos de tecla y pedal; la resonancia de liberación se conserva a nivel discreto. Los valores exactos usados por la interpretación quedan en su informe de render. La dinámica individual procede de velocidades de ataque, sin usar CC11 compartido para elevar una voz a costa de todas las demás.

Se trata de muestras de un piano real, con transposición entre notas base y 16 capas discretas. No se afirma una simulación física continua de cada cuerda o del medio pedal, un acoplamiento simpático completo ni una toma independiente de una corda. El pedal usa tomas y liberaciones CC64 según la realización musical documentada. La toma AB estéreo puede recibir ajustes globales de anchura o balance si las mediciones del máster lo justifican.

## Restauración y repetición de pruebas

Desde `videos/007/produccion/`, con Python 3, NumPy, SciPy, SoundFile y la biblioteca sfizz compilada según el README de producción:

```bash
python download_piano.py --manifest ../fuentes/instrumento/instrument-sources.json --dest /tmp/jagoncito007/piano
python verify_instrument.py --cache /tmp/jagoncito007/piano --manifest ../fuentes/instrumento/instrument-sources.json --library /tmp/jagoncito007/engine/sfizz/build/library/lib/libsfizz.so --renderer render_piano.py --out-dir /tmp/jagoncito007/instrument-check
python validar_piano.py --sfz '/tmp/jagoncito007/piano/Salamander Grand Piano V3.sfz' --library /tmp/jagoncito007/engine/sfizz/build/library/lib/libsfizz.so --out-dir /tmp/jagoncito007/piano-test
```

El verificador vuelve a comprobar los 668 archivos, el formato nativo de cada FLAC, las 16 capas, la cobertura de teclado y la respuesta a velocidad. Las herramientas de descarga mantienen la verificación TLS y el proxy y credenciales normales del entorno.

El archivo de atributos Git del proveedor se conserva como `original/gitattributes.source.txt`, con sus bytes originales, para que sus reglas no alteren finales de línea al incorporar las fuentes a este repositorio. Su nombre original sigue registrado en el manifiesto de restauración.
