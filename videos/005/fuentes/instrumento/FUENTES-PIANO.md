# Piano de cola para Chopin 005

**Salamander Grand Piano v3**, un **Yamaha C5** muestreado por **Alexander Holm**, grabado con dos AKG c414 cerca de las cuerdas. 16 capas de velocidad, grabación estéreo 48 kHz / 24 bits, notas muestreadas por terceras menores y extendidas mediante los mapas originales.

## Fuente y licencia

Repositorio: https://github.com/sfzinstruments/SalamanderGrandPiano

Revisión fija: `3382bf9496bba2486f5ab0de55a264d1dfc38404`.

Licencia **Creative Commons Attribution 3.0 Unported (CC BY 3.0)**: https://creativecommons.org/licenses/by/3.0/ . Texto original incluido en `original/LICENSE`. Permite reutilizar y adaptar con atribución y conservación de los avisos; no se describe esta biblioteca como CC0 ni como dominio público. La obra de Chopin, la transcripción usada y la interpretación nueva tienen derechos separados.

- Muestreo: Alexander Holm.
- Afinación alternativa: Markus Fiedler.
- Reconstrucción del mapa SFZ: kinwie / sfzinstruments.
- Fuente histórica declarada por el repositorio: https://archive.org/details/SalamanderGrandPianoV3 . Se ha verificado el contenido y licencia de la revisión de GitHub citada, sin afirmar una inspección independiente de esa página externa.

Crédito sugerido en inglés:

> Piano samples: Salamander Grand Piano v3 (Yamaha C5), Alexander Holm. Retuned mapping by Markus Fiedler; SFZ reconstruction by kinwie / sfzinstruments. CC BY 3.0: https://creativecommons.org/licenses/by/3.0/ . Source: https://github.com/sfzinstruments/SalamanderGrandPiano/tree/3382bf9496bba2486f5ab0de55a264d1dfc38404 . New digital performance; no finished third-party recording used.

## Cobertura y funcionamiento comprobados

Descargados y comprobados **668 archivos de fuente**, incluidos **641 FLAC** y 27 mapas/documentos, 748451483 bytes en total. Cada archivo coincide con su objeto Git de la revisión fija; `instrument-sources.json` conserva tamaño, URL inmutable y SHA-256. Se conserva copia original de SFZ, archivos Data, README y licencia. Las muestras aisladas suman aproximadamente 748 MB; se recuperan con `download_piano.py` sin incluir ese volumen de fuentes en la carpeta de entrega.

Se verificó el formato de las 641 muestras: todas estéreo, 48 kHz y 24 bits. Hay 480 muestras de ataque (30 notas base × 16 velocidades); las demás recogen liberación de tecla, resonancias grabadas y acción del pedal. El mapa cubre las 88 teclas MIDI 21–108. Las muestras de ataque duran entre 2,626 s (registro agudo muy suave) y 25,863 s (registro grave fuerte), con su decaimiento natural. No se añadieron bucles para mantener notas de piano artificialmente.

El mapa original advierte sobre su uso de SFZ 2 y extensiones ARIA. Se probó en el motor **sfizz**, revisión `f5c6e29f23b8057867c08e88f5f6ac6738baa30b`: cargó **1121 regiones y 641 archivos de muestra**, sin errores de carga. Las pruebas ejercitan notas y pedal reales; no se asume compatibilidad por el nombre del formato.

- El mismo acorde, con y sin CC64, conserva una cola 44,4 dB más alta con el pedal activo, medida 2,5–3,5 s frente a 8,5–9,5 s de la prueba. El pedal se libera antes del segundo acorde.
- Cuatro velocidades 35/60/82/108 produjeron ataques RMS crecientes 0,00849/0,02110/0,03825/0,07589 en la prueba auxiliar.
- Audio finito y estéreo; sin valores NaN/Inf ni errores de render.
- Esta prueba no es una valoración auditiva subjetiva ni un dictamen sobre la mezcla final.

## Uso durante la interpretación

`render_piano.py` carga el SFZ original completo, un solo piano compartido por ambas manos y 512 voces disponibles. Selecciona la afinación **Retuned** mediante la tecla de control MIDI 13, fuera del registro musical. Conserva las envolventes y los mapas de nota/velocidad originales; respeta CC64, notas, velocidades y tiempos del JSON de interpretación.

La resonancia de liberación está disponible a un nivel discreto; los ruidos de tecla y pedal se reducen mediante sus controles MIDI originales (CC20/21/22). Los ajustes exactos quedan en el informe del render. La dinámica de cada voz procede de la velocidad de ataque, sin emplear CC11 compartido para levantar una nota a costa de todas las demás.

Límites: son muestras de un piano real, con transposición entre notas base y 16 capas discretas; no una simulación física continua de cada cuerda o del medio pedal. El pedal de producción usa CC64 para sostener y soltar según la armonía. Las resonancias son muestras de liberación, sin afirmar que se modela todo el acoplamiento simpático acústico. La imagen estéreo es la toma AB original; el máster puede ajustar anchura/balance global si la medición completa lo justifica.

## Restauración y pruebas

Desde `videos/005/produccion/`, con Python 3, NumPy/SciPy y sfizz compilado según el README de producción:

```bash
python download_piano.py --manifest ../fuentes/instrumento/instrument-sources.json --dest /tmp/jagoncito005/piano
python validar_piano.py --sfz '/tmp/jagoncito005/piano/Salamander Grand Piano V3.sfz' --library /tmp/jagoncito005/engine/sfizz/build/library/lib/libsfizz.so --out-dir /tmp/jagoncito005/piano-test
python render_piano.py --events performance.json --sfz '/tmp/jagoncito005/piano/Salamander Grand Piano V3.sfz' --library /tmp/jagoncito005/engine/sfizz/build/library/lib/libsfizz.so --output /tmp/jagoncito005/piano.float.wav
```

La restauración se comprobó además mediante HTTPS normal para el SFZ, la licencia y una muestra cuyo nombre contiene #; todos coincidieron en tamaño y SHA-256. El programa mantiene la verificación TLS y las credenciales/proxy normales del entorno.

El archivo de atributos Git del proveedor se conserva como `original/gitattributes.source.txt`, con bytes originales, para impedir que sus reglas cambien los finales de línea de los demás documentos al incorporarlos a este repositorio. Su nombre original sigue registrado en el manifiesto de restauración.
