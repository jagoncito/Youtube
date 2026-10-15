# Prueba musical — Bach, BWV 846

Fragmento de los primeros ocho compases del Preludio en do mayor de Johann Sebastian Bach. Duración aproximada: 33 segundos. Es una demostración de síntesis, no la obra completa ni una grabación de piano acústico.

- `bach-bwv846-prueba.mp3`: escucha y revisión.
- `bach-bwv846-prueba.wav`: audio estéreo PCM de 16 bits, 44,1 kHz.
- `generar.py`: notas y síntesis reproducibles; requiere Python 3 y NumPy. Ejecutar `python3 generar.py` desde cualquier directorio. Para convertir a MP3: `ffmpeg -i bach-bwv846-prueba.wav -codec:a libmp3lame -b:a 192k bach-bwv846-prueba.mp3`.

La composición de Bach es de dominio público. Esta prueba genera las ondas matemáticamente: no incorpora grabaciones comerciales, muestras ni bancos de sonido de terceros. Las notas del fragmento están escritas en el programa; no se ha descargado una edición moderna de la partitura. No se afirma dominio público mundial para los archivos generados ni se garantiza ausencia de reclamaciones automáticas. Pendiente de revisión auditiva del usuario antes de decidir su uso en un vídeo.

Validación técnica: 128 notas renderizadas, muestras finitas, audio no silencioso, pico a -1,5 dBFS y conversión MP3 correcta. Esta comprobación no sustituye una escucha crítica.
