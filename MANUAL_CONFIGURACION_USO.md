# MANUAL DE CONFIGURACIÓN Y USO DE NEXUS V10

Este manual detalla paso a paso cómo configurar las herramientas externas (Inkscape, Selenium) y cómo operar Nexus diariamente para producción, ventas y marketing.

---

## 1. CONFIGURACIÓN INICIAL (Solo una vez)

Para que todas las funciones nuevas (DXF y Robot de Redes) funcionen, necesitamos instalar un par de cosas en tu PC.

### A. INSTALAR INKSCAPE (Para convertir a DXF)
Nexus usa Inkscape "por detrás" para convertir imágenes a vectores.

1.  Descarga Inkscape desde: [inkscape.org](https://inkscape.org/)
2.  Instálalo en la ruta por defecto (`C:\Program Files\Inkscape`).
3.  ¡Listo! Nexus lo detectará automáticamente.
    *   *Nota: No necesitas abrir Inkscape para trabajar, Nexus lo llama solo.*

### B. INSTALAR DEPENDENCIAS DE PYTHON (Para el Robot de Redes)
Para que Nexus pueda abrir el navegador y publicar por ti:

1.  Abre una terminal en `C:\NEXUS`.
2.  Ejecuta el siguiente comando:
    ```bash
    pip install -r requirements.txt
    ```
    *(Esto instalará `selenium` y `webdriver-manager`).*

---

## 2. GUÍA DE USO DIARIO

### A. INICIAR NEXUS
1.  Ve a la carpeta `C:\NEXUS`.
2.  Ejecuta `main.py` (o usa tu acceso directo si ya lo tienes).
3.  Escucharás: "Nexus en línea".

### B. COMANDOS DE VOZ (LISTA ACTUALIZADA)

**Gestión y Taller:**
*   **"Nexus, nuevo pedido"** → Te pedirá Cliente, Producto y Hora.
    *   *Ejemplo: "Juan Taza 2 de la tarde"*
*   **"Nexus, pedidos pendientes"** → Te lee lo que hay por entregar.
*   **"Nexus, cotiza láser"** → Te pregunta minutos y calcula costo/venta.
*   **"Nexus, parámetros [material]"** → *Ej: "Parámetros acrílico 3 milímetros".*
*   **"Nexus, convierte [cantidad] a [unidad]"** → *Ej: "Convierte 25 milímetros a pulgadas".*

**Control de PC y Apps:**
*   **"Nexus, abre Corel"** (o Aspire, Silhouette, Photoshop).
*   **"Nexus, abre WhatsApp"** (o Facebook, Instagram, YouTube).
*   **"Nexus, busca [tema]"** → Busca en internet y te lee el resumen.
    *   *Ej: "Busca quién inventó el láser".*
*   **"Nexus, escritorio"** → Minimiza todo.
*   **"Nexus, silencio"** → Mutea el audio.

### C. PANEL VISUAL (PESTAÑAS)

#### 1. Pestaña PEDIDOS
*   **Nueva Comanda:** Llena los campos y dale a "AGENDAR".
*   **Tabla de Pedidos:** Muestra todo (Pendientes, Listos, Entregados).
*   **Botones:**
    *   **TERMINAR:** Marca el pedido como "LISTO".
    *   **EDITAR ENTREGA/ESTADO:** Abre ventana para cambiar fecha o poner estado "ESPERANDO COLECCION".
    *   **WHATSAPP:** Abre chat con el cliente para avisarle.

#### 2. Pestaña TALLER (Conversor DXF)
*   **Origen:** Selecciona cualquier imagen (JPG, PNG) o vector.
*   **Modo:**
    *   `AUTO`: Nexus decide.
    *   `LINEAL`: Para grabado rápido o corte de silueta.
    *   `VECTOR IMAGEN`: Para logotipos a color (varias capas).
    *   `DETALLE ALTO`: Máxima fidelidad (más lento).
*   **Botón CONVERTIR:** Genera el DXF en `C:\NEXUS\TALLER\ENTRADA`.

#### 3. Pestaña MARKETING (Robot Social)
*   **Generador:** Pon "Vehículo" (ej: Jetta A4) e "Instalación" (ej: Lupa Biled).
*   **Botón GENERAR COPY:** Crea el texto para Facebook con emojis y hashtags.
*   *(Próximamente)* **Botón PUBLICAR:** Abrirá el navegador robotizado.

---

## 3. CÓMO FUNCIONA EL ROBOT DE REDES (SELENIUM)

Como pediste **NO usar credenciales guardadas**, el sistema funciona así:

1.  Nexus abrirá una ventana de Chrome "Robotizada".
2.  **La primera vez**, tendrás que iniciar sesión tú mismo en Facebook/Instagram en esa ventana.
3.  **Nexus recordará la sesión** (si configuramos el perfil de usuario) o te pedirá login manual por seguridad.
4.  Una vez logueado, tú le darás la orden a Nexus y él:
    *   Irá a "Crear Publicación".
    *   Pegará el texto generado.
    *   Subirá la foto/video.
    *   Esperará tu confirmación final para publicar.

*Seguridad: Tus contraseñas NUNCA se escriben en código ni se guardan en Nexus.*

---

## 4. SOLUCIÓN DE PROBLEMAS

*   **¿Nexus no escucha?**
    *   Revisa que el micrófono esté activo.
    *   Di "Nexus, prueba de audio" para ver si te oye.
*   **¿Error al convertir DXF?**
    *   Asegúrate de haber instalado Inkscape.
*   **¿El panel se cierra?**
    *   Nexus intentará reabrirlo. Si no, reinicia `main.py`.

---
**SOPORTE TÉCNICO**
Cualquier duda, revisa `C:\NEXUS\nexus_logs` para ver qué pasó.
