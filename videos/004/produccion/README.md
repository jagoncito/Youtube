# Producción manual de 004

No hay cron, workflow ni generación periódica. Estos programas reproducen esta entrega concreta a partir de la partitura y las muestras indicadas. No producen otras entregas.

Entorno utilizado: Linux x86-64, Python 3.12, FFmpeg 7.1.5 con libass/libx264, GCC/G++, Git; sfizz compilado en la revisión fijada en `build_sfizz.sh`. Dependencias Python fijadas en `requirements.txt`. Los medios grandes se recuperan con Git LFS. No hace falta otra copia del repositorio ni un worktree.

## Flujo reproducible

Desde `videos/004/produccion`, activar un entorno Python con las dependencias de `requirements.txt`. Se pueden guardar los archivos de trabajo fuera del repositorio, por ejemplo en `/tmp/jagoncito-004`:

```bash
python -m venv /tmp/jagoncito-004-env
source /tmp/jagoncito-004-env/bin/activate
python -m pip install -r requirements.txt
mkdir -p /tmp/jagoncito-004

python ../fuentes/partitura/validate_score.py
python create_performance.py --score-dir ../fuentes/partitura --out-dir /tmp/jagoncito-004/performance
python download_instruments.py --manifest ../fuentes/instrumentos/instrument-sources.json --dest /tmp/jagoncito-004/vsco
bash build_sfizz.sh /tmp/jagoncito-004
python render_sfizz.py --events /tmp/jagoncito-004/performance/performance.json --samples /tmp/jagoncito-004/vsco --library /tmp/jagoncito-004/sfizz/build/library/lib/libsfizz.so --out /tmp/jagoncito-004/render
python master_audio.py --render /tmp/jagoncito-004/render --out ../vivaldi-winter.wav

python animar_invierno.py --image ../imagen.png --output /tmp/jagoncito-004/escena-60s.mp4
python validar_escena.py /tmp/jagoncito-004/escena-60s.mp4 --output /tmp/jagoncito-004/validacion-escena.json
python montar_invierno.py --scene /tmp/jagoncito-004/escena-60s.mp4 --audio ../vivaldi-winter.wav --chapters capitulos.json --output-dir .. --repeats 3
python verificar_entrega.py
```

Los pasos de reconstrucción sobrescriben los medios de 004; se ejecutan solo al producir/reconstruir esa entrega. La descarga utiliza HTTPS normal y verifica tamaño y SHA-256 de 558 archivos antes de usarlos. Las muestras no son una grabación terminada del concierto. La partitura original/adaptada y el PDF sí están incluidos. Las imágenes generadas se conservan como fuentes del montaje; no se promete regenerarlas bit a bit.

## Decisiones y comprobaciones

- `performance.json`: tiempos en segundos, eventos, articulaciones, mezcla y curvas CC11. `create_performance.py` conserva los 6802 identificadores de notas fuente; realiza los trinos escritos de forma editorial. `fuentes/interpretacion-digital.midi` es la interpretación expresiva, distinta del MIDI básico de notación.
- Tempos de referencia: negra = 70 en I, negra = 38 en II, negra = 72 en III; hay curvas de fraseo y un Lento a negra = 44 dentro de III. No se han elegido para encajar 30 minutos. La base dura 550,958322 s; tres ciclos completos son 1652,874966 s de audio.
- El motor respeta mapas/afinaciones SFZ y sus muestras reales. Ataques/colas y algunas regiones sostenidas se adaptan durante el render. Los bucles de sostenimiento tienen fundidos de 120 ms: evitan que una nota ligada larga termine al agotarse la muestra. Se detallan en `render-report.json`.
- Mezcla por secciones, panoramas moderados, reverberación algorítmica original de sala corta y eliminación subsónica a 35 Hz. Ganancia global con margen de pico real, sin compresión de dinámica ni normalización independiente por movimiento. El WAV es PCM de 24 bits / 44,1 kHz; los MP4 incluyen AAC de 256 kb/s a 44,1 kHz.
- La imagen se lleva a 1920×1080 y 24 fps. Ciclo ambiental de 60 s con nieve recortada al exterior, luz local y reflejos; animales estáticos. Codificación H.264 High/yuv420p con QP 1 para reducir el cambio de textura al regresar al primer cuadro. La continuidad se comparó con cuadros vecinos sin relajar el criterio tras las correcciones.
- El montaje repite el WAV completo y codifica el audio continuamente. Conserva el decaimiento y la pausa antes del siguiente concierto; no solapa finales con nuevos comienzos. Los capítulos también están integrados en los MP4.
- `verificar_entrega.py` decodifica todos los cuadros, mide el WAV completo y compara todo el AAC de cada ciclo contra la fuente PCM. Comprueba saturación, pico real, final y duración. Al copiar H.264 con cuadros B puede conservar dos cuadros finales adicionales; la duración del audio se comprueba por separado y el redondeo del contenedor se registra.

La fidelidad de notación, las mediciones y la inspección visual no equivalen a una valoración auditiva. **No se ha realizado una escucha subjetiva del resultado.** Tampoco se ha verificado contra un facsímil histórico independiente ni se garantizan resultados de audiencia. La biblioteca no tiene legato grabado; el órgano refuerza el bajo sin realizar todos los acordes cifrados.
