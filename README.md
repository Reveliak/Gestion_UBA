# Sistema de Auditoría ESG - Trazabilidad de Proveedores

Sistema automatizado 100% Python de validación de criterios ESG (Environmental, Social, Governance) para proveedores con generación de reportes HTML y dashboard interactivo.

**Stack tecnológico:** Python + JSON + Requests (sin dependencias externas)

## Criterios ESG Validados

### 1. GOVERNANCE (40% del score)
- **Validación de CUIT**: Verifica formato y dígito verificador del CUIT argentino
- Cumplimiento legal básico

### 2. SOCIAL (30% del score)
- **Certificaciones laborales**:
  - ISO 45001 (Seguridad y Salud Ocupacional)
  - SA8000 (Responsabilidad Social)
- Búsqueda automatizada en sitio web del proveedor

### 3. ENVIRONMENTAL (30% del score)
- **Reportes de sostenibilidad publicados**
- Búsqueda de PDFs y contenido sobre ESG/RSE
- Verificación de secciones de sostenibilidad en web corporativa

## Flujo Completo (100% Python)

```
┌─────────────────┐
│ proveedores.csv │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   Python: ESGAuditor        │
│  - Validación CUIT          │
│  - Scraping (requests)      │
│  - Scoring ESG              │
└────────┬────────────────────┘
         │
         ├──────────────┬───────────────┬─────────────────┐
         ▼              ▼               ▼                 ▼
┌──────────────┐  ┌──────────┐  ┌──────────┐   ┌──────────┐
│auditoria_esg │  │dashboard │  │reporte_  │   │reporte_  │
│   .json      │  │  .html   │  │ 001.html │...│ 004.html │
└──────────────┘  └──────────┘  └──────────┘   └──────────┘
      ↓                ↓              ↓               ↓
  Datos para      Dashboard     Reportes       Enviar a
  APIs/Make       interactivo   individuales   proveedor
```

## Estructura del Proyecto

```
pythonUBA/
├── main.py                  # Sistema completo (690 líneas)
├── proveedores.csv          # Planilla de entrada
├── auditoria_esg.json       # Output JSON (para APIs/Make)
├── dashboard.html           # Dashboard interactivo ⭐
├── reporte_001.html         # Reporte individual YPF
├── reporte_002.html         # Reporte individual Telecom
├── reporte_003.html         # Reporte individual Arcor
├── reporte_004.html         # Reporte individual Test
└── README.md
```

## Uso

### 1. Preparar planilla CSV
Edita `proveedores.csv` con tus proveedores:

```csv
proveedor_id,nombre,cuit,pais,sitio_web,email
001,YPF S.A.,30-54668997-9,AR,https://www.ypf.com,contacto@ypf.com
002,Telecom Argentina,30-63945373-8,AR,https://www.telecom.com.ar,info@telecom.com.ar
```

### 2. Ejecutar auditoría
```bash
python3 main.py
```

### 3. Ver resultados
Abre `dashboard.html` en tu navegador para ver:
- **Dashboard general**: Estadísticas globales, scores por criterio, tabla comparativa
- **Reportes individuales**: Click en "Ver Detalle" para cada proveedor
- **JSON**: Listo para integrar con APIs o Make

## Outputs Generados

### 1. JSON (auditoria_esg.json)
Datos estructurados para integración con sistemas externos:
```json
{
  "timestamp": "2025-11-04T21:21:08",
  "proveedor": {
    "id": "001",
    "nombre": "YPF S.A.",
    "cuit": "30-54668997-9"
  },
  "score_total": 55,
  "conformidad": false,
  "no_conformidades": [...],
  "tareas_proveedor": [...]
}
```

### 2. Dashboard HTML
- Métricas globales (total, conformes, no conformes)
- Score promedio por criterio ESG
- Tabla interactiva con todos los proveedores
- Enlaces a reportes individuales

### 3. Reportes HTML Individuales
- Información completa del proveedor
- Score total y badge de conformidad
- Desglose por criterio (G, S, E)
- Barras de progreso visuales
- Alertas específicas
- Lista de tareas requeridas

## Scoring

**Fórmula del Score Total:**
```
Score Total = (Governance × 0.4) + (Social × 0.3) + (Environmental × 0.3)
```

**Conformidad:**
- CONFORME: Score ≥ 70%
- NO CONFORME: Score < 70%

**Estados por criterio:**
- PASS: 100%
- PARTIAL: 1-99%
- FAIL: 0%

## Dependencias

Solo requiere Python 3.6+ con `requests`:

```bash
pip3 install requests
```

## Características

**Solo Python + JSON + Requests:**
- Sin frameworks web (Flask, Django, FastAPI)
- Sin librerías de visualización (Matplotlib, Plotly)
- Sin herramientas externas (Make, Power BI)
- HTML/CSS generado dinámicamente desde Python
- 100% portable y autónomo

**Escalable:**
- Procesa N proveedores automáticamente
- Threshold configurable
- Fácil agregar nuevos criterios ESG
- Output JSON compatible con cualquier sistema

**Interactivo:**
- Dashboard HTML responsive
- Reportes individuales por proveedor
- Navegación entre vistas
- Alertas visuales con colores

## Limitaciones

- Solo valida CUIT argentino (extensible a otros países)
- Scraping limitado a sitios HTML accesibles via `requests`
- No procesa sitios con JavaScript pesado
- Timeout: 10 segundos por request

## Próximos Pasos de Integración

1. **Make/Zapier**: Leer `auditoria_esg.json` y enviar notificaciones
2. **Email**: Adjuntar `reporte_XXX.html` al proveedor
3. **API REST**: Exponer JSON vía endpoint
4. **Base de datos**: Guardar histórico de auditorías
5. **Scheduler**: Cron job para auditorías periódicas

## Ejemplo de Resultados

```
============================================================
✅ PROCESO COMPLETADO EXITOSAMENTE
============================================================

📂 Archivos generados:
  • auditoria_esg.json - Datos JSON completos
  • dashboard.html - Dashboard general (ABRIR ESTE)
  • reporte_001.html, reporte_002.html... - Reportes individuales

📈 RESUMEN GENERAL:
  Total proveedores auditados: 4
  Conformes: 0 (0%)
  No conformes: 4 (100%)
```

## Autor

Sistema desarrollado para gestión de proveedores con trazabilidad ESG.
**Stack:** Python + JSON + Requests
