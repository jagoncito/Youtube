# Productor de entregas programadas

Este programa crea archivos nuevos de vídeo y música a partir de un catálogo **finito y explícito**, sin claves de IA ni grabaciones comerciales. No es un agente de investigación autónomo ni genera una ilustración nueva cada cuatro horas.

## Contrato

```bash
python -m pip install -r automatizacion/produccion/requirements.txt
python automatizacion/produccion/crear_entrega.py \
  --slot 2026-10-27T12:00:00Z \
  --output /tmp/entrega-jagoncito \
  --cache /tmp/jagoncito-piano-cache
```

Requiere Python 3.12, FFmpeg con libx264 y libass, y las dependencias fijadas. No hace falta LilyPond en el runner: los MIDI verificados ya están incluidos. Las muestras de piano se descargan cuando faltan, con TLS y SHA-256, y quedan fuera del repositorio.

- `--slot` admite una fecha con zona UTC y hora 00/04/08/12/16/20, sin minutos ni segundos. Un reintento del mismo slot reproduce la misma selección y semilla.
- `--plan-only` devuelve la selección en JSON y no produce archivos.
- `--plan-id` permite seleccionar manualmente un programa del catálogo.
- `--catalog` admite un catálogo alternativo previamente revisado.
- El directorio de salida no debe existir. El bundle solo aparece al final: cualquier fallo limpia la producción temporal y termina con código distinto de cero.

## Contenido de una entrega

`video-30min.mp4`, `bucle-6min.mp4`, un único `audio-bucle-6min.wav`, `imagen.png`, `miniatura.jpg`, `publicacion.txt`, `README.md`, `manifest.json` y `fuentes/`.

El WAV dura 360 s. Incluye dos Gymnopédies completas, con fraseo, rubato y dinámica controlados por una semilla del slot. La interpretación se renderiza de nuevo; no se copia el MP4 de la entrega anterior. El vídeo de30min repite cinco veces ese programa. El audio largo se codifica continuamente y solo sus últimos tres segundos llevan un fundido, situado después del final escrito de la obra.

`manifest.json` contiene título, intención, slot, programa, semilla, capítulos, niveles, controles de vídeo y hashes. El publicador debe usarlo como fuente; el programa **no hace push, no crea releases y no publica en YouTube**.

## Catálogo y escenas

`catalogo.json` contiene seis programas de lectura, concentración tranquila o descanso, con las seis combinaciones ordenadas de las Gymnopédies1,2y3 de Satie. Hay un programa por slot durante el día; en días posteriores se repite el repertorio con una interpretación programada distinta. Esto no equivale a seis composiciones ni seis escenas inéditas por día.

El catálogo alterna tres familias visuales, dos programas por familia: el taller de cerámica para lectura o concentración tranquila, el cobertizo del puerto para una pausa, y el salón nocturno de la entrega002 para desconectar. Cambian el escenario, la microhistoria, el objeto focal, la proyección del espectador y la paleta; no se trata de recolorear la misma habitación. Los cinco ejes quedan registrados en cada objeto `scene` y en el manifiesto de la entrega.

Las dos nuevas escenas están en `automatizacion/assets/atelier/` y `automatizacion/assets/boathouse/`. Sus plantillas de 12 segundos solo animan lluvia en máscaras exteriores revisadas. No se atribuye movimiento a los animales ni a la luz de esas dos escenas. Se conservan la imagen, la miniatura, `lluvia.ass`, `scene-12s.mp4` y su `manifest.json` de revisión.

Cada programa incluye su escena. Se reutilizan los activos del catálogo en posteriores ejecuciones: esta automatización no genera una ilustración inédita por slot. Para añadir una escena hay que aportar su imagen y miniatura, un `scene_template` H.264 de 1920×1080, 24 fps y 12 segundos, y un `scene_manifest` con la periodicidad RAW y el cierre codificado revisados. El productor verifica los hashes de los tres activos y el resultado de la revisión antes de renderizar música. Las coordenadas del salón002 no se aplican a otras imágenes.

Las plantillas nuevas pueden reconstruirse mediante:

```bash
python automatizacion/produccion/crear_templates.py --scene all
```

El informe conserva el fallo de la comparación relativa cuando la imagen está casi inmóvil. La aceptación requiere además una fuente RAW periódica, límites absolutos de cuantización global y por región, y P99 codificado de como máximo un nivel de 8 bits. La regresión del salto geométrico original sigue rechazándose en las pruebas.

Los ficheros visuales deben permanecer dentro del repositorio y la miniatura debe ser1280×720 y menor de2MiB. Los archivos de30min se destinan a GitHub Releases, no a aumentar indefinidamente los objetos Git/LFS del repositorio.

## Fuentes e integridad

`fuentes.json` identifica cada partitura original, su transcripción derivada para separar las tres voces MIDI y sus SHA-256. Las tres transcripciones Mutopia de Evin Robertson están marcadas como dominio público; los comentarios de la fuente excluyen las traducciones modernas de la edición Dover. Los sonidos individuales de VSCO2CE se publican bajoCC0. Se conserva la licencia y el manifiesto de30muestras. No se promete dominio público universal para todos los activos ni ausencia de reclamaciones automáticas.

La nueva Gymnopédie2 se compiló con LilyPond2.24.4 desde la fuente fijada. Contiene371notas y195negras(65compases). Las otras partituras contienen455notas/234negras y326notas/180negras. Antes de renderizar se comprueban los hashes y la duración completa del MIDI.

## Controles

El productor mide LUFS/pico verdadero, comprueba ausencia de saturación y compara el salto real de la unión circular con el ruido adyacente. Verifica duración exacta y formato de ambos MP4 y **decodifica íntegramente** los dos antes de entregar el bundle. La validación es técnica; no se afirma una escucha humana.

```bash
python -m unittest discover -s automatizacion/produccion -p test_produccion.py -v
```

Las diez pruebas cubren rotación, reintentos deterministas, slots inválidos, confinamiento e integridad de activos, tres familias visuales con diferencias sustantivas, descripciones ajustadas a los movimientos implementados, el rechazo del salto geométrico original y el empaquetado de fuentes y capítulos. Este último detectó un fallo real de copia de fuentes en la primera prueba integral y se corrigió.
