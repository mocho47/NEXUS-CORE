# NEXUS v2 by Simplex
**Asistente de taller inteligente** — Gestión de pedidos, cotizaciones y ventas para negocios artesanales.

## Instalación rápida

```
1. Doble clic en INSTALAR_NEXUS_V2.bat
2. Agregar GROQ_API_KEY en C:\nexus\.env
3. Doble clic en INICIAR_NEXUS_V2.bat
4. Abrir http://localhost:8001
```

## Requisitos
- Windows 10/11
- Python 3.11+
- Cuenta gratuita en https://console.groq.com (para IA)

## Comandos principales (chat)

### Pedidos
```
nuevo pedido para [cliente] [descripción]
mis pedidos activos
pedido 5 listo
pedido 3 entregado
```

### Cotizaciones
```
cotiza X4
cotiza X1 para Carlos
cotiza 50 tarjetas sublimacion
cotiza laser 30x20 mdf
genera caja 20x15x8 mdf_3
```

### Pipeline de ventas
```
nuevo prospecto [nombre] atf
ver pipeline
mover [nombre] a cotizado
```

### Agenda ATF
```
agenda instalacion X4 para Juan el viernes
ver agenda atf semana
```

### Mensajes y redes
```
redacta mensaje followup para Carlos
post de instagram para atf
```

### Briefing y finanzas
```
briefing
finanzas del mes
quien no ha pagado
```

## Panel visual
- **Resumen**: cards con totales + alertas de atrasados/listos
- **Pedidos**: tabla con filtros, actualizar estado inline
- **Cotizar**: formularios directos ATF, Sublimación, Láser
- **Agenda ATF**: instalaciones próximas
- **Pipeline**: embudo de ventas con estados
- **Vendedor**: mensajes WA y publicaciones redes
- **CanbusFix**: directorio de instaladores

## Arquitectura
```
Instrucción → cerebro.pensar() → intent map (keywords) → Motor → Respuesta
                                → Groq fallback si no matchea
```

- **22 motores** especializados, cada uno independiente
- **13 endpoints REST** para el panel (sin pasar por IA)
- **SQLite local** en C:\nexus\nexus_v2.db
- **Sin datos en la nube** — todo local

## Soporte
Taller Simplex | WA: 33 2614 8674
