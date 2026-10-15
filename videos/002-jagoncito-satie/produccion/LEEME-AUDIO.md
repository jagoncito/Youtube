# Música de esta entrega

**Erik Satie: Gymnopédies n.º 1 y n.º 3 (1888), completas.**

La base musical dura exactamente **6:00**. Primero se interpreta la n.º 1,
de 0:00 a 3:10; a continuación la n.º 3, de 3:10 a 6:00. Cada intervalo incluye
la resonancia final de la obra. El vídeo de treinta minutos repite esta misma
secuencia cinco veces. No contiene cinco repertorios distintos.

Se trata de interpretaciones virtuales nuevas. Python interpreta las notas
MIDI utilizando muestras individuales de un piano real; no se incorpora una
grabación de Satie interpretada por otra persona. El tempo tiene respiración
por frases, hay balance entre melodía, acordes y bajo, pedal que se renueva con
las armonías y resonancia de una habitación pequeña. Las notas, silencios,
ligaduras y repeticiones de las partituras se conservan. No se añaden melodías
inventadas. No se declara que toque un pianista humano.

La lluvia es ruido filtrado generado para esta entrega, muy tenue: su nivel
RMS global es 27 dB inferior al del piano. No contiene grabaciones de lluvia
ajenas ni truenos. La unión circular de la lluvia se prepara por separado;
las melodías de las obras no se solapan para disimular el bucle. El último
acorde se toca completo y se deja decaer antes de volver al principio.

El único archivo de audio entregado es `audio-bucle-6min.wav`: PCM de 16 bits,
estéreo, 44.100 Hz. No hay un MP3 duplicado. El MP4 lleva ya la música incorporada.

## Partituras y procedencia

Composición de Erik Satie, fallecido en 1925, publicada en 1888. Las partituras
utilizadas proceden de Mutopia Project y fueron puestas en el dominio público
por su transcriptor, **Evin Robertson**. Los archivos originales conservan sus
encabezados. Declaran como fuente reproducciones de la obra original incluidas
en una edición Dover, y excluyen las traducciones añadidas por dicha edición.

Revisión de Mutopia fijada: `2144afd6f52d56c5b6995b8b589ef1268b3139f0`.

- N.º 1, referencia **Mutopia-2014/12/14-37**:
  https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/SatieE/gymnopedie_1/gymnopedie_1.ly
- N.º 3, referencia **Mutopia-2012/12/23-39**:
  https://github.com/MutopiaProject/MutopiaProject/blob/2144afd6f52d56c5b6995b8b589ef1268b3139f0/ftp/SatieE/gymnopedie_3/gymnopedie_3.ly

`fuentes-partituras.json` conserva URLs, hashes de los originales y de los MIDI.
Las versiones `*-render.ly` separan las tres voces en pistas para controlar
su balance; eliminan únicamente los cambios de pentagrama de la voz intermedia
y sustituyen el bloque de impresión por un bloque MIDI con repeticiones
desarrolladas. No modifican las notas. La n.º 1 conserva sus dos finales
alternativos: **78 compases, 455 notas**. La n.º 3 contiene **60 compases,
326 notas**. El MIDI conserva las notas ligadas como un único evento sostenido.

Las composiciones y estas transcripciones están en dominio público en España
y en otros países donde han vencido los derechos correspondientes. No se
promete una situación jurídica mundial idéntica ni ausencia de reclamaciones
automáticas de Content ID.

## Piano CC0

**VS Chamber Orchestra 2 Community Edition**, piano vertical muestreado por
**Simon Dalzell / Ivy Audio**, biblioteca de **Versilian Studios / Sam Gossner**.
Las muestras están publicadas bajo **CC0 1.0 Universal** y permiten uso comercial.

- Biblioteca: https://github.com/sgossner/VSCO-2-CE
- Revisión: `440300901dfe9275fd84e0b7763af1f8443ae62e`.
- Carpeta: `Keys/Upright Piano`.
- Licencia original:
  https://github.com/sgossner/VSCO-2-CE/blob/440300901dfe9275fd84e0b7763af1f8443ae62e/LICENSE
- Información del instrumento:
  https://github.com/sgossner/VSCO-2-CE/blob/440300901dfe9275fd84e0b7763af1f8443ae62e/Keys/Upright%20Piano/Info.txt

`instrumento-vsco-fuentes.json` conserva la URL exacta, el SHA-256, el tamaño,
la nota raíz y la capa de intensidad de cada muestra utilizada. Se utilizan
treinta muestras estéreo de dos intensidades, con notas raíz MIDI 29–85.
Las notas intermedias se obtienen por remuestreo. La copia de la licencia está
en `VSCO-CC0-LICENSE.txt`. Las muestras se conservan en una caché fuera de Git.

## Reproducción del proceso

Herramientas utilizadas: Python 3.12.14, FFmpeg y LilyPond 2.24.4. Las
dependencias Python están fijadas en `requirements.txt`. LilyPond solo hace
falta para reconstruir los MIDI; estos ya están incluidos.

Desde la carpeta de este vídeo:

```bash
python3 -m venv /tmp/jagoncito-satie-venv
/tmp/jagoncito-satie-venv/bin/python -m pip install -r produccion/requirements.txt
/tmp/jagoncito-satie-venv/bin/python produccion/renderizar_audio.py --samples /tmp/jagoncito-piano-cache
```

El script descarga únicamente las muestras que faltan, mantiene la verificación
TLS y comprueba cada SHA-256 antes de usarlas. Se necesitan unos 124 MB de caché
y aproximadamente 2 GB de memoria disponible. Las semillas están fijadas.
Se mide el nivel con FFmpeg, se aplica una única ganancia lineal para acercarse
a −21 LUFS sin superar −1,7 dBTP, y se añade dither TPDF al pasar a 16 bits.
No se utiliza compresión dinámica para aumentar el volumen.

Para reconstruir las partituras MIDI con LilyPond instalado normalmente:

```bash
lilypond -dbackend=null -dno-print-pages -o produccion/gymnopedie-1 produccion/gymnopedie-1-render.ly
lilypond -dbackend=null -dno-print-pages -o produccion/gymnopedie-3 produccion/gymnopedie-3-render.ly
```

Para inspeccionar el archivo y medir sus niveles sin modificarlo:

```bash
ffprobe -v error -show_streams -show_format audio-bucle-6min.wav
ffmpeg -hide_banner -nostats -i audio-bucle-6min.wav -af loudnorm=I=-21:TP=-1.7:LRA=15:print_format=json -f null -
```

## Alcance de la revisión

`audio-manifiesto.json` registra duración exacta, notas por voz, tempos,
sonoridad, pico verdadero, muestras recortadas y continuidad entre el final y
el principio. La validación realizada es técnica y automatizada. No se afirma
una escucha humana ni una valoración auditiva subjetiva del resultado.
La apreciación de la interpretación debe comprobarse escuchando el WAV.
