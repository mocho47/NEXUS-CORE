# Tutorial: Creación de Grilla de Etiquetas en CorelDRAW

Este tutorial explica paso a paso cómo crear una grilla de 100 rectángulos (etiquetas) de **18x9mm** con numeración específica (40 etiquetas con el número "50" y 60 etiquetas con el número "100").

## Método Recomendado: Panel "Transformar" (Paso y Repetición)

Este método es el más rápido y preciso para asegurar que las etiquetas queden perfectamente alineadas y sin espacios (o con el espacio que desees).

### Paso 1: Crear la Primera Etiqueta "50"
1. Abre CorelDRAW y crea un nuevo documento.
2. Selecciona la **Herramienta Rectángulo (F6)**.
3. Dibuja un rectángulo cualquiera y en la barra de propiedades (arriba), cambia sus dimensiones a:
   - **Ancho**: 18 mm
   - **Alto**: 9 mm
4. Selecciona la **Herramienta Texto (F8)**, escribe "50".
5. Centra el texto dentro del rectángulo:
   - Selecciona ambos (Texto y Rectángulo).
   - Presiona la tecla **C** (centrar verticalmente) y luego **E** (centrar horizontalmente).
6. Agrupa la etiqueta: Selecciona todo y presiona **Ctrl + G**.

### Paso 2: Duplicar las 40 etiquetas de "50"
Necesitamos 40 etiquetas. Haremos una matriz de **4 columnas x 10 filas** (o la distribución que prefieras).

1. Abre el panel de Transformar: Ve a **Ventana > Ventanas acoplables > Transformar** (o presiona **Alt + F7**).
2. Selecciona la pestaña **Posición** (icono de flecha cruzada).
3. **Para las columnas (hacia la derecha):**
   - Selecciona tu etiqueta agrupada.
   - En el panel Transformar, marca la casilla de la **derecha** (posición relativa).
   - En "Copias", escribe: **3** (para tener 4 en total).
   - Haz clic en **Aplicar**. Ahora tienes una fila de 4 etiquetas.
4. **Para las filas (hacia abajo):**
   - Selecciona las 4 etiquetas que acabas de crear.
   - En el panel Transformar, marca la casilla de **abajo**.
   - En "Copias", escribe: **9** (para tener 10 filas en total).
   - Haz clic en **Aplicar**.
   - **Resultado:** 40 etiquetas con el número "50".

### Paso 3: Crear y Duplicar las 60 etiquetas de "100"
1. Repite el Paso 1, pero esta vez escribe el número "100" dentro del rectángulo.
2. Agrupa la nueva etiqueta (**Ctrl + G**).
3. Coloca esta primera etiqueta "100" justo al lado o debajo de tu bloque anterior.
4. Usando el panel **Transformar**:
   - Genera **6 columnas** (escribe 5 copias a la derecha).
   - Genera **10 filas** (escribe 9 copias hacia abajo).
   - **Resultado:** 60 etiquetas con el número "100".

### Paso 4: Preparar para Corte
1. Selecciona todas las etiquetas (**Ctrl + A**).
2. Asegúrate de que el contorno de los rectángulos sea **Muy fino (Hairline)** y de color **Rojo** (o el color que tu láser use para corte).
3. Asegúrate de que el texto sea de color **Negro** (o el color para grabado) y que no tenga contorno.
4. Si quieres ahorrar material y que el láser corte una sola línea entre etiquetas (corte compartido):
   - Al usar el panel Transformar, las figuras quedan pegadas borde con borde.
   - Puedes usar la función "Eliminar segmentos virtuales" o simplemente dejarlo así, ya que la mayoría de los láseres pasarán dos veces por la línea compartida (lo cual es aceptable para etiquetas pequeñas).

---
**Nota:** Si necesitas márgenes de separación entre etiquetas, en el panel Transformar, ajusta las coordenadas X o Y sumando el margen deseado (ej. en lugar de mover 18mm, mueve 19mm para 1mm de separación).
