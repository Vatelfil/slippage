# Generador del informe de Título II (Word)

Regenera `Informe_Titulo_II_Avance_<fecha>.docx` a partir de estos módulos.

- `parte1.json`: texto del Título I (Parte I), extraído con `extract_parte1.py` desde el Word original
  (la ruta del Word está escrita dentro del script; ajustarla si cambia).
- `parte2a.js`, `parte2b.js`, `anexos.js`: contenido de la Parte II y de los anexos (aquí se actualiza cada sprint).
- `lib.js`: estilos, tablas, figuras y recuadros. `build.js`: arma el documento.
- `fig/`: figuras usadas.

Uso (desde esta carpeta, con Node instalado):

    npm install
    node build.js ../Informe_Titulo_II_Avance_AAAA-MM-DD.docx

Al abrir el Word, aceptar la actualización de campos para que el índice se complete (o clic derecho en el índice > Actualizar campo).
Las cifras de la Parte II salen de reportes del repositorio; revisarlas contra los archivos antes de entregar.
