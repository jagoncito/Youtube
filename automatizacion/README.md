# Producción de Jagoncito cada cuatro horas

El workflow [Jagoncito cada 4 horas](../.github/workflows/jagoncito-cada-4h.yml) crea un paquete de vídeo y lo sube a **GitHub Releases**. La frecuencia configurada es `0 */4 * * *`: 00:00, 04:00, 08:00, 12:00, 16:00 y 20:00 **UTC**. GitHub puede demorar las ejecuciones de calendario. No se publica nada en YouTube.

## Encontrar los vídeos

- [Índice por orden](ENTREGAS.md): Vídeo 001, Vídeo 002, Vídeo 003…
- Cada entrega terminada tiene una carpeta `videos/video-NNNN/` con su ficha, título, publicación y manifiesto.
- Los MP4 y el WAV se descargan de la Release enlazada desde la ficha; no se guardan medios de cientos de MB en el historial Git.
- `estado.json` muestra el último turno, su estado real y la ejecución de Actions. `entregas/` conserva el registro de cada turno.

El Vídeo 001 existente conserva su número. El siguiente número se reserva al empezar un turno y se reutiliza si ese turno debe reintentarse. Un turno ya publicado no vuelve a producir ni sobrescribe los archivos. La reserva de un turno fallido puede dejar un hueco temporal hasta que se reintente; no se renumeran los vídeos anteriores.

## Qué se ejecuta

1. Comprobar el turno UTC y si ya existe una entrega completa.
2. Registrar `running` en GitHub, con número y enlace de la ejecución.
3. Seleccionar un programa del catálogo, renderizar una interpretación nueva y crear el bucle de 6 minutos y el vídeo de 30 minutos.
4. Verificar archivos, checksums, audio y decodificación íntegra de ambos vídeos.
5. Crear o recuperar una Release **borrador**, subir los archivos y comprobar los tamaños y los hashes remotos cuando GitHub los proporciona.
6. Publicar la Release únicamente después de esas comprobaciones. Guardar su ficha, índice y estado `success`.

Si una operación falla, el trabajo termina con error y procura registrar `failure`. Un borrador incompleto no se presenta como entrega terminada. La ejecución siguiente del mismo turno puede recuperar el borrador; los estados de autenticación fallida no se confunden con una Release inexistente.

Si una corrección llega después de cambiar el turno, la ejecución automática recupera primero una entrega antigua cuyos archivos ya estén completos y verificados. Conserva su número y evita volver a renderizarla. Después procesa el turno actual. Un borrador antiguo incompleto no provoca un render adicional no solicitado; puede reintentarse indicando su turno en la ejecución manual.

Los commits de estado y fichas no coinciden con los filtros `push` del workflow, así que no disparan producción recursiva. Hay una sola ejecución de producción concurrente. Git no se fuerza ni se reescribe; se actualiza mediante avance rápido antes de guardar estados.

## Alcance creativo

La producción programada utiliza **un catálogo curado finito** de partituras de dominio público, piano de muestras CC0 y escenas preparadas para Jagoncito. Cada interpretación se renderiza con el programa y la semilla de su turno; no copia el MP4 anterior. El manifiesto identifica las obras completas, tiempos, fuentes, huellas y activos visuales reutilizados.

Esto no es un agente creativo que investigue YouTube ni genere ilustraciones nuevas con IA en segundo plano. Las escenas, el repertorio y los criterios se amplían mediante cambios revisables en el catálogo. No se requiere una clave de OpenAI para ejecutar el programa actual. Las comprobaciones automáticas no se describen como escucha humana ni garantizan crecimiento o monetización.

Los 128 estudios aportados orientan el criterio editorial; su documento original y los datos privados de Studio permanecen fuera del repositorio y de las Releases. La programación de seis entregas diarias responde a la petición del creador, no a una supuesta frecuencia óptima de YouTube.

## Ejecutar y mantener

GitHub aporta el `GITHUB_TOKEN` del trabajo, con `contents: write`; no se copia ninguna credencial del chat. Deben estar habilitados GitHub Actions y esos permisos en la configuración del repositorio. El job instala Python 3.12, FFmpeg y las dependencias fijadas, y conserva una caché de muestras verificadas.

En **Actions → Jagoncito cada 4 horas → Run workflow** se puede iniciar una ejecución manual. El turno opcional debe ser una de las seis horas UTC; si se omite, se usa el bloque UTC de cuatro horas actual. Una ejecución repetida del mismo turno publicado se omite de forma idempotente.

Para probar el programador sin red ni publicar medios reales:

```bash
python -m unittest discover -s automatizacion/tests -v
```

Las pruebas usan Git real en repositorios temporales y simulan solo la API de GitHub. Cubren numeración, reintentos de borrador, publicación completa, reserva tras fallo, autenticación, checksum y recuperación de una publicación sin índice.

Para una ejecución real desde una máquina configurada con acceso a GitHub y las dependencias:

```bash
python automatizacion/ejecutar.py --repository jagoncito/Youtube --cache /tmp/jagoncito-piano
```

El productor escribe sus medios en un directorio temporal fuera del checkout. El programador necesita un checkout limpio de `main` y permiso para guardar los estados y fichas en esa rama.
