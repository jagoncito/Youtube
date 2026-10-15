# Música de este vídeo

**Frédéric Chopin: Preludio en mi menor, op. 28 n.º 4.**

El WAV contiene tres interpretaciones virtuales completas de la misma obra,
con pequeñas diferencias de tempo, intensidad y respiración entre frases.
No es una sesión de un pianista humano ni una grabación descargada de la obra.
La partitura mantiene las notas y duraciones; el tempo, el pedal, el balance entre
manos y las colas de resonancia se trabajan en el código. Los signos ornamentales
gráficos de la partitura no se desarrollan automáticamente como notas adicionales
en esta versión MIDI. Conviene considerarlo una recreación virtual de prueba.

- Formato único de audio: WAV PCM, estéreo, 44.100 Hz, 16 bits.
- Duración: 6:45,775.
- Tres pasadas: 0:00,000; 2:15,662; 4:28,761.
- Nivel integrado: −21,54 LUFS; pico verdadero: −1,50 dBTP.
- El nivel conserva la dinámica del piano. No se ha aplicado normalización
  dinámica para aumentar el volumen.
- Comprobación técnica: 1.800 notas, sin muestras recortadas, finales con
  resonancia y unión entre pasadas en silencio. No se afirma una escucha humana
  del resultado; los controles realizados son técnicos y automatizados.

## Procedencia y derechos

La composición de Chopin pertenece al dominio público en España y en los
territorios habituales de publicación donde han vencido sus derechos de autor.
Las leyes concretas pueden variar por país; aquí no se promete una declaración
de dominio público universal ni ausencia de reclamaciones automáticas.

La transcripción utilizada está marcada **Public Domain** por su transcriptor,
**Magnus Lewis-Smith**, en el proyecto Mutopia. Fuente editorial declarada:
**Peters, 1879**. Identificador Mutopia: **Mutopia-2016/10/28-468**.

Fuente fijada en el commit `2144afd6f52d56c5b6995b8b589ef1268b3139f0`:

https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/ChopinFF/O28/Chop-28-4/Chop-28-4.ly

SHA-256 de `partitura.ly`:
`d4fca574bc3c3ad810ee643d42b7299e1c97b3b8b3fa379c3d7f77edb02f6192`.
El encabezado original, incluida la declaración de dominio público, se conserva.

Los sonidos individuales de piano pertenecen a **VSCO 2 Community Edition**,
publicado bajo **CC0 1.0**. Piano muestreado por Simon Dalzell / Ivy Audio;
colección de Versilian Studios / Sam Gossner. Se usan sonidos aislados como
instrumento para interpretar notas nuevas. No se incorpora una interpretación
de Chopin realizada por otra persona. La licencia, la revisión exacta y los
SHA-256 de las 30 muestras constan en los archivos `instrumento-vsco*` y
`VSCO-CC0-LICENSE.txt`. Las muestras no se incluyen en el repositorio.

Crédito informativo sugerido, aunque CC0 no exige atribución:

> Música: Frédéric Chopin — Preludio en mi menor, op. 28 n.º 4.
> Recreación virtual producida para Jagoncito. Partitura: Magnus Lewis-Smith /
> Mutopia Project, dominio público. Instrumento: VSCO 2 Community Edition,
> Simon Dalzell / Ivy Audio y Versilian Studios / Sam Gossner, CC0.

## Volver a generar el WAV

Probado con Python 3.12.14. Crear el entorno y la caché fuera del repositorio:

```bash
python3 -m venv /tmp/jagoncito-audio-venv
/tmp/jagoncito-audio-venv/bin/python -m pip install -r produccion/requirements.txt
/tmp/jagoncito-audio-venv/bin/python produccion/renderizar_audio.py --samples /tmp/jagoncito-piano-cache
```

Ejecutar los comandos desde la carpeta de este vídeo. El script usa rutas
relativas a su propio archivo, descarga únicamente las muestras que faltan y
comprueba todas con SHA-256. Conserva la validación TLS. La caché necesita
aproximadamente 124 MB; el render usa en torno a 1 GB de RAM y tarda unos minutos.
La semilla de las variaciones está fijada. El resultado por defecto se escribe
en `audio.wav`, en la carpeta del vídeo, y el manifiesto se actualiza.

El MIDI de entrada es `partitura.mid`. Se generó con LilyPond 2.24.4 desde
`partitura.ly`, sin editar sus notas. Para reconstruirlo si se dispone de LilyPond:

```bash
lilypond -dbackend=null -dno-print-pages -o /tmp/jagoncito-partitura produccion/partitura.ly
cp /tmp/jagoncito-partitura.midi produccion/partitura.mid
```

Para reproducir el archivo localmente:

```bash
ffplay -autoexit audio.wav
```

Para comprobar el contenedor y medir el nivel integrado y el pico verdadero:

```bash
ffprobe -v error -show_streams -show_format audio.wav
ffmpeg -hide_banner -nostats -i audio.wav -af loudnorm=I=-22:TP=-1.5:LRA=12:print_format=json -f null -
```

En la segunda orden, `input_i` e `input_tp` describen el WAV entregado. La orden
solo mide y descarta el resultado; no modifica el audio.
