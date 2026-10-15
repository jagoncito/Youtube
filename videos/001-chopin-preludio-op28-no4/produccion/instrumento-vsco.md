# Instrumento de piano y procedencia

Se generó una interpretación nueva mediante programación MIDI y un muestreador Python. No se utilizó una grabación comercial de la obra. Para convertir las notas en sonido se usaron muestras individuales de piano, publicadas bajo CC0 1.0 Universal.

## Biblioteca

- **VS Chamber Orchestra: Community Edition**, carpeta `Keys/Upright Piano`.
- Piano grabado por **Simon Dalzell / Ivy Audio**, invierno de 2015–2016. Biblioteca publicada por **Versilian Studios / Sam Gossner**.
- Repositorio: https://github.com/sgossner/VSCO-2-CE
- Revisión fijada: `440300901dfe9275fd84e0b7763af1f8443ae62e`.
- Licencia: **CC0 1.0 Universal**. Permite reutilización y uso comercial.
- Fuente de la licencia: https://github.com/sgossner/VSCO-2-CE/blob/440300901dfe9275fd84e0b7763af1f8443ae62e/LICENSE
- Información del piano: https://github.com/sgossner/VSCO-2-CE/blob/440300901dfe9275fd84e0b7763af1f8443ae62e/Keys/Upright%20Piano/Info.txt
- El archivo `Readme.txt` del repositorio también declara que la biblioteca está diseñada para fines educativos y comerciales y solicita crédito a sus autores. Se conserva ese crédito por cortesía en la documentación y en la propuesta de descripción.

## Muestras utilizadas

Se descargaron 30 muestras: `Player_dyn1_rr1_NNN.wav` y `Player_dyn2_rr1_NNN.wav`, donde `NNN` es un índice par de 004 a 032. Son dos capas de intensidad del mismo instrumento, estéreo, 44,1 kHz, PCM de 24 bits. Los anclajes cubren MIDI 29 a 85. Las notas intermedias se generan por remuestreo de la muestra más cercana.

La correspondencia original procede de `Keys/Upright Piano/MappingChart.txt`: para los índices de esta selección, la raíz es `MIDI = 21 + 2 × índice`. Ejemplo: `020` es MIDI 61, do sostenido 4. El archivo `instrumento-vsco-fuentes.json` incluye URL exacta, tamaño y SHA-256 de cada muestra, para poder recuperar y verificar las mismas fuentes sin incluir la biblioteca completa en este proyecto.

La copia de la licencia se conserva en `VSCO-CC0-LICENSE.txt`. Esta documentación acredita el instrumento; la composición y la edición de la partitura se documentan por separado.

## Crédito sugerido

Sonido de piano: VSCO 2 Community Edition — Simon Dalzell / Ivy Audio y Versilian Studios / Sam Gossner. Muestras publicadas bajo CC0 1.0. Interpretación y render nuevos realizados para Jagoncito.
