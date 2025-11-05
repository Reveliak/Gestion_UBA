import json
import csv
import re
from datetime import datetime
from typing import Dict, List, Tuple
import requests
from urllib.parse import urljoin, urlparse


class ESGAuditor:
    """Sistema de auditoría ESG para proveedores"""

    def __init__(self):
        self.resultados = []
        self.timeout = 10

    # ========== GOVERNANCE: Validación de CUIT ==========

    def validar_cuit(self, cuit: str) -> Dict:
        """
        Valida el formato y dígito verificador del CUIT argentino
        Formato: XX-XXXXXXXX-X
        """
        resultado = {
            "criterio": "CUIT válido",
            "resultado": "FAIL",
            "score": 0,
            "detalles": "",
            "alertas": []
        }

        # Limpiar formato
        cuit_limpio = re.sub(r'[^0-9]', '', cuit)

        # Validar longitud
        if len(cuit_limpio) != 11:
            resultado["detalles"] = "CUIT inválido: debe tener 11 dígitos"
            resultado["alertas"].append("Formato de CUIT incorrecto")
            return resultado

        # Validar dígito verificador
        multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(cuit_limpio[i]) * multiplicadores[i] for i in range(10))
        digito_calculado = 11 - (suma % 11)

        if digito_calculado == 11:
            digito_calculado = 0
        elif digito_calculado == 10:
            digito_calculado = 9

        if int(cuit_limpio[10]) == digito_calculado:
            resultado["resultado"] = "PASS"
            resultado["score"] = 100
            resultado["detalles"] = f"CUIT {cuit} verificado correctamente"
        else:
            resultado["detalles"] = "CUIT inválido: dígito verificador incorrecto"
            resultado["alertas"].append("Dígito verificador no coincide")

        return resultado

    # ========== SOCIAL: Certificaciones Laborales ==========

    def buscar_certificaciones(self, sitio_web: str, nombre_proveedor: str) -> Dict:
        """
        Busca certificaciones laborales ISO 45001 y SA8000 en el sitio del proveedor
        """
        resultado = {
            "criterio": "Certificaciones laborales",
            "resultado": "FAIL",
            "score": 0,
            "certificaciones_encontradas": [],
            "detalles": "",
            "alertas": []
        }

        if not sitio_web:
            resultado["detalles"] = "No se proporcionó sitio web"
            resultado["alertas"].append("Sitio web no disponible para verificación")
            return resultado

        # Certificaciones a buscar
        certificaciones = {
            "ISO 45001": [r"ISO[\s-]?45001", r"ISO45001"],
            "SA8000": [r"SA[\s-]?8000", r"SA8000"]
        }

        # URLs a verificar
        urls_verificar = [
            sitio_web,
            urljoin(sitio_web, '/certificaciones'),
            urljoin(sitio_web, '/calidad'),
            urljoin(sitio_web, '/sostenibilidad'),
            urljoin(sitio_web, '/about'),
            urljoin(sitio_web, '/nosotros')
        ]

        contenido_total = ""

        # Intentar obtener contenido de las URLs
        for url in urls_verificar:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=self.timeout, headers=headers, verify=False)
                if response.status_code == 200:
                    contenido_total += response.text.lower()
            except Exception as e:
                continue

        # Buscar certificaciones en el contenido
        for cert_nombre, patrones in certificaciones.items():
            for patron in patrones:
                if re.search(patron, contenido_total, re.IGNORECASE):
                    resultado["certificaciones_encontradas"].append(cert_nombre)
                    break

        # Calcular score
        num_encontradas = len(resultado["certificaciones_encontradas"])
        resultado["score"] = (num_encontradas / len(certificaciones)) * 100

        if num_encontradas == len(certificaciones):
            resultado["resultado"] = "PASS"
            resultado["detalles"] = f"Todas las certificaciones encontradas: {', '.join(resultado['certificaciones_encontradas'])}"
        elif num_encontradas > 0:
            resultado["resultado"] = "PARTIAL"
            resultado["detalles"] = f"Certificaciones encontradas: {', '.join(resultado['certificaciones_encontradas'])}"
            # Agregar alertas de las no encontradas
            for cert in certificaciones.keys():
                if cert not in resultado["certificaciones_encontradas"]:
                    resultado["alertas"].append(f"{cert} no encontrada")
        else:
            resultado["detalles"] = "No se encontraron certificaciones laborales"
            resultado["alertas"].append("Sin certificaciones laborales verificables")

        return resultado

    # ========== ENVIRONMENTAL: Reportes de Sostenibilidad ==========

    def buscar_reporte_sostenibilidad(self, sitio_web: str, nombre_proveedor: str) -> Dict:
        """
        Busca reportes de sostenibilidad publicados en el sitio del proveedor
        """
        resultado = {
            "criterio": "Reporte de sostenibilidad publicado",
            "resultado": "FAIL",
            "score": 0,
            "reportes_encontrados": [],
            "detalles": "",
            "alertas": []
        }

        if not sitio_web:
            resultado["detalles"] = "No se proporcionó sitio web"
            resultado["alertas"].append("Sitio web no disponible para verificación")
            return resultado

        # Keywords a buscar
        keywords_sostenibilidad = [
            r'reporte\s+de\s+sostenibilidad',
            r'sustainability\s+report',
            r'informe\s+de\s+responsabilidad\s+social',
            r'memoria\s+de\s+sostenibilidad',
            r'ESG\s+report',
            r'RSE',
            r'GRI\s+report'
        ]

        # URLs a verificar
        urls_verificar = [
            sitio_web,
            urljoin(sitio_web, '/sostenibilidad'),
            urljoin(sitio_web, '/sustainability'),
            urljoin(sitio_web, '/responsabilidad-social'),
            urljoin(sitio_web, '/esg'),
            urljoin(sitio_web, '/reportes'),
            urljoin(sitio_web, '/downloads')
        ]

        contenido_total = ""
        pdfs_encontrados = []

        # Buscar contenido y PDFs
        for url in urls_verificar:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=self.timeout, headers=headers, verify=False)
                if response.status_code == 200:
                    contenido = response.text.lower()
                    contenido_total += contenido

                    # Buscar enlaces a PDFs de sostenibilidad
                    pdf_pattern = r'href=["\']([^"\']*(?:sostenibilidad|sustainability|esg|rse)[^"\']*\.pdf)["\']'
                    pdfs = re.findall(pdf_pattern, contenido, re.IGNORECASE)
                    pdfs_encontrados.extend(pdfs)

            except Exception as e:
                continue

        # Verificar keywords
        keywords_found = []
        for keyword in keywords_sostenibilidad:
            if re.search(keyword, contenido_total, re.IGNORECASE):
                keywords_found.append(keyword)

        # Evaluar resultados
        if pdfs_encontrados or len(keywords_found) >= 2:
            resultado["resultado"] = "PASS"
            resultado["score"] = 100
            if pdfs_encontrados:
                resultado["reportes_encontrados"] = pdfs_encontrados[:3]  # Máximo 3
                resultado["detalles"] = f"Se encontraron {len(pdfs_encontrados)} reportes de sostenibilidad"
            else:
                resultado["detalles"] = f"Se encontró información de sostenibilidad (keywords: {len(keywords_found)})"
        elif len(keywords_found) == 1:
            resultado["resultado"] = "PARTIAL"
            resultado["score"] = 50
            resultado["detalles"] = "Información limitada de sostenibilidad encontrada"
            resultado["alertas"].append("Reporte de sostenibilidad no claramente publicado")
        else:
            resultado["detalles"] = "No se encontró reporte de sostenibilidad publicado"
            resultado["alertas"].append("Sin reporte de sostenibilidad verificable")

        return resultado

    # ========== SCORING Y CONSOLIDACIÓN ==========

    def auditar_proveedor(self, proveedor: Dict) -> Dict:
        """
        Realiza auditoría ESG completa de un proveedor
        """
        print(f"\n🔍 Auditando: {proveedor['nombre']} (ID: {proveedor['proveedor_id']})")

        # Ejecutar validaciones
        governance = self.validar_cuit(proveedor['cuit'])
        social = self.buscar_certificaciones(proveedor.get('sitio_web', ''), proveedor['nombre'])
        environmental = self.buscar_reporte_sostenibilidad(proveedor.get('sitio_web', ''), proveedor['nombre'])

        # Calcular score total (pesos: 40% Gov, 30% Social, 30% Env)
        score_total = round(
            (governance['score'] * 0.4) +
            (social['score'] * 0.3) +
            (environmental['score'] * 0.3)
        )

        # Consolidar alertas y no conformidades
        todas_alertas = []
        todas_alertas.extend(governance.get('alertas', []))
        todas_alertas.extend(social.get('alertas', []))
        todas_alertas.extend(environmental.get('alertas', []))

        # Determinar conformidad (threshold: 70%)
        conformidad = score_total >= 70

        # Generar tareas para el proveedor
        tareas_proveedor = []
        if governance['resultado'] != 'PASS':
            tareas_proveedor.append("Verificar y corregir CUIT registrado")
        if social['score'] < 100:
            tareas_proveedor.append("Obtener certificaciones laborales faltantes (ISO 45001, SA8000)")
        if environmental['score'] < 100:
            tareas_proveedor.append("Publicar reporte de sostenibilidad en sitio web corporativo")

        # Construir resultado final
        resultado_final = {
            "timestamp": datetime.now().isoformat(),
            "proveedor": {
                "id": proveedor['proveedor_id'],
                "nombre": proveedor['nombre'],
                "cuit": proveedor['cuit'],
                "sitio_web": proveedor.get('sitio_web', 'N/A')
            },
            "auditoria_esg": {
                "governance": governance,
                "social": social,
                "environmental": environmental
            },
            "score_total": score_total,
            "conformidad": conformidad,
            "no_conformidades": todas_alertas,
            "tareas_proveedor": tareas_proveedor
        }

        # Mostrar resumen
        print(f"  ✓ Governance: {governance['score']}% - {governance['resultado']}")
        print(f"  ✓ Social: {social['score']}% - {social['resultado']}")
        print(f"  ✓ Environmental: {environmental['score']}% - {environmental['resultado']}")
        print(f"  📊 Score Total: {score_total}%")
        print(f"  {'✅ CONFORME' if conformidad else '❌ NO CONFORME'}")

        return resultado_final

    def procesar_planilla(self, archivo_csv: str) -> List[Dict]:
        """
        Procesa planilla CSV de proveedores y genera auditorías
        """
        print(f"📋 Procesando planilla: {archivo_csv}")

        proveedores = []
        try:
            with open(archivo_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                proveedores = list(reader)
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {archivo_csv}")
            return []

        print(f"✓ {len(proveedores)} proveedores cargados")

        # Auditar cada proveedor
        resultados = []
        for proveedor in proveedores:
            resultado = self.auditar_proveedor(proveedor)
            resultados.append(resultado)

        return resultados

    def exportar_json(self, resultados: List[Dict], archivo_salida: str = "auditoria_esg.json"):
        """
        Exporta resultados a JSON
        """
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados exportados a: {archivo_salida}")

        # Estadísticas
        total = len(resultados)
        conformes = sum(1 for r in resultados if r['conformidad'])

        print(f"\n📈 RESUMEN GENERAL:")
        print(f"  Total proveedores auditados: {total}")
        print(f"  Conformes: {conformes} ({round(conformes/total*100)}%)")
        print(f"  No conformes: {total - conformes} ({round((total-conformes)/total*100)}%)")

    def generar_reporte_html(self, resultado: Dict, archivo_salida: str):
        """
        Genera reporte HTML individual por proveedor
        """
        proveedor = resultado['proveedor']
        auditoria = resultado['auditoria_esg']

        # Colores según conformidad
        color_conformidad = "#27ae60" if resultado['conformidad'] else "#e74c3c"
        estado_texto = "CONFORME" if resultado['conformidad'] else "NO CONFORME"

        # Generar secciones de alertas
        alertas_gov = ""
        if auditoria['governance']['alertas']:
            alertas_gov = '<div class="alertas"><h4>⚠️ Alertas</h4><ul>' + \
                "".join(f"<li>{alerta}</li>" for alerta in auditoria['governance']['alertas']) + \
                '</ul></div>'

        alertas_social = ""
        if auditoria['social']['alertas']:
            alertas_social = '<div class="alertas"><h4>⚠️ Alertas</h4><ul>' + \
                "".join(f"<li>{alerta}</li>" for alerta in auditoria['social']['alertas']) + \
                '</ul></div>'

        alertas_env = ""
        if auditoria['environmental']['alertas']:
            alertas_env = '<div class="alertas"><h4>⚠️ Alertas</h4><ul>' + \
                "".join(f"<li>{alerta}</li>" for alerta in auditoria['environmental']['alertas']) + \
                '</ul></div>'

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auditoría ESG - {proveedor['nombre']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 40px; }}
        .header {{ text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; font-size: 2em; margin-bottom: 10px; }}
        .header p {{ color: #7f8c8d; font-size: 0.9em; }}
        .proveedor-info {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .proveedor-info h2 {{ color: #2c3e50; margin-bottom: 15px; }}
        .info-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
        .info-label {{ font-weight: bold; color: #34495e; }}
        .score-total {{ text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; margin-bottom: 30px; }}
        .score-total h2 {{ font-size: 3em; margin-bottom: 10px; }}
        .conformidad {{ display: inline-block; padding: 10px 30px; background: {color_conformidad}; color: white; border-radius: 5px; font-weight: bold; font-size: 1.2em; }}
        .criterios {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .criterio {{ background: #f8f9fa; border-left: 5px solid #3498db; padding: 20px; border-radius: 5px; }}
        .criterio h3 {{ color: #2c3e50; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .badge {{ padding: 5px 15px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }}
        .badge-pass {{ background: #27ae60; color: white; }}
        .badge-partial {{ background: #f39c12; color: white; }}
        .badge-fail {{ background: #e74c3c; color: white; }}
        .score-bar {{ width: 100%; height: 30px; background: #ecf0f1; border-radius: 15px; overflow: hidden; margin: 15px 0; }}
        .score-fill {{ height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; transition: width 0.5s; }}
        .alertas {{ background: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 5px; margin-top: 15px; }}
        .alertas h4 {{ color: #856404; margin-bottom: 10px; }}
        .alertas ul {{ margin-left: 20px; color: #856404; }}
        .tareas {{ background: #d4edda; border-left: 5px solid #28a745; padding: 20px; border-radius: 5px; }}
        .tareas h3 {{ color: #155724; margin-bottom: 15px; }}
        .tareas ul {{ margin-left: 20px; color: #155724; line-height: 1.8; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #ecf0f1; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 AUDITORÍA ESG</h1>
            <p>Reporte de Trazabilidad de Proveedor</p>
        </div>

        <div class="proveedor-info">
            <h2>{proveedor['nombre']}</h2>
            <div class="info-row">
                <span class="info-label">ID Proveedor:</span>
                <span>{proveedor['id']}</span>
            </div>
            <div class="info-row">
                <span class="info-label">CUIT:</span>
                <span>{proveedor['cuit']}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Sitio Web:</span>
                <span>{proveedor['sitio_web']}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Fecha Auditoría:</span>
                <span>{resultado['timestamp'][:10]}</span>
            </div>
        </div>

        <div class="score-total">
            <h2>{resultado['score_total']}%</h2>
            <span class="conformidad">{estado_texto}</span>
        </div>

        <div class="criterios">
            <div class="criterio">
                <h3>
                    🏛️ GOVERNANCE
                    <span class="badge badge-{auditoria['governance']['resultado'].lower()}">{auditoria['governance']['resultado']}</span>
                </h3>
                <div class="score-bar">
                    <div class="score-fill" style="width: {auditoria['governance']['score']}%">{auditoria['governance']['score']}%</div>
                </div>
                <p><strong>Criterio:</strong> {auditoria['governance']['criterio']}</p>
                <p><strong>Detalle:</strong> {auditoria['governance']['detalles']}</p>
                {alertas_gov}
            </div>

            <div class="criterio">
                <h3>
                    👥 SOCIAL
                    <span class="badge badge-{auditoria['social']['resultado'].lower()}">{auditoria['social']['resultado']}</span>
                </h3>
                <div class="score-bar">
                    <div class="score-fill" style="width: {auditoria['social']['score']}%">{auditoria['social']['score']}%</div>
                </div>
                <p><strong>Criterio:</strong> {auditoria['social']['criterio']}</p>
                <p><strong>Detalle:</strong> {auditoria['social']['detalles']}</p>
                {alertas_social}
            </div>

            <div class="criterio">
                <h3>
                    🌱 ENVIRONMENTAL
                    <span class="badge badge-{auditoria['environmental']['resultado'].lower()}">{auditoria['environmental']['resultado']}</span>
                </h3>
                <div class="score-bar">
                    <div class="score-fill" style="width: {auditoria['environmental']['score']}%">{auditoria['environmental']['score']}%</div>
                </div>
                <p><strong>Criterio:</strong> {auditoria['environmental']['criterio']}</p>
                <p><strong>Detalle:</strong> {auditoria['environmental']['detalles']}</p>
                {alertas_env}
            </div>
        </div>

        <div class="tareas">
            <h3>📋 Tareas Requeridas para el Proveedor</h3>
            <ul>
                {"".join(f"<li>{tarea}</li>" for tarea in resultado['tareas_proveedor'])}
            </ul>
        </div>

        <div class="footer">
            <p>Sistema de Auditoría ESG - Trazabilidad de Proveedores</p>
            <p>Generado automáticamente el {resultado['timestamp'][:19]}</p>
        </div>
    </div>
</body>
</html>"""

        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(html)

    def generar_dashboard(self, resultados: List[Dict], archivo_salida: str = "dashboard.html"):
        """
        Genera dashboard HTML con resumen de todos los proveedores
        """
        total = len(resultados)
        conformes = sum(1 for r in resultados if r['conformidad'])
        no_conformes = total - conformes

        score_promedio = round(sum(r['score_total'] for r in resultados) / total) if total > 0 else 0

        # Estadísticas por criterio
        gov_promedio = round(sum(r['auditoria_esg']['governance']['score'] for r in resultados) / total)
        social_promedio = round(sum(r['auditoria_esg']['social']['score'] for r in resultados) / total)
        env_promedio = round(sum(r['auditoria_esg']['environmental']['score'] for r in resultados) / total)

        # Generar filas de la tabla
        filas_tabla = ""
        for r in resultados:
            color_fila = "#d4edda" if r['conformidad'] else "#f8d7da"
            filas_tabla += f"""
            <tr style="background: {color_fila}">
                <td><strong>{r['proveedor']['nombre']}</strong></td>
                <td>{r['proveedor']['cuit']}</td>
                <td><span class="score-badge">{r['score_total']}%</span></td>
                <td>{r['auditoria_esg']['governance']['score']}%</td>
                <td>{r['auditoria_esg']['social']['score']}%</td>
                <td>{r['auditoria_esg']['environmental']['score']}%</td>
                <td><span class="badge badge-{'pass' if r['conformidad'] else 'fail'}">{'✓ CONFORME' if r['conformidad'] else '✗ NO CONFORME'}</span></td>
                <td><a href="reporte_{r['proveedor']['id']}.html" target="_blank">Ver Detalle</a></td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard ESG - Auditoría de Proveedores</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card h3 {{ color: #7f8c8d; font-size: 0.9em; text-transform: uppercase; margin-bottom: 15px; }}
        .stat-card .numero {{ font-size: 3em; font-weight: bold; color: #2c3e50; }}
        .stat-card.conforme .numero {{ color: #27ae60; }}
        .stat-card.no-conforme .numero {{ color: #e74c3c; }}
        .criterios-promedio {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .criterio-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .criterio-card h3 {{ color: #2c3e50; margin-bottom: 15px; text-align: center; }}
        .criterio-bar {{ width: 100%; height: 40px; background: #ecf0f1; border-radius: 20px; overflow: hidden; }}
        .criterio-fill {{ height: 100%; background: linear-gradient(90deg, #3498db, #2980b9); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2em; }}
        .table-container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #34495e; color: white; padding: 15px; text-align: left; font-weight: 600; }}
        td {{ padding: 15px; border-bottom: 1px solid #ecf0f1; }}
        .score-badge {{ display: inline-block; padding: 5px 15px; background: #3498db; color: white; border-radius: 20px; font-weight: bold; }}
        .badge {{ padding: 8px 20px; border-radius: 5px; font-weight: bold; font-size: 0.9em; }}
        .badge-pass {{ background: #27ae60; color: white; }}
        .badge-fail {{ background: #e74c3c; color: white; }}
        a {{ color: #3498db; text-decoration: none; font-weight: bold; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 DASHBOARD ESG</h1>
            <p>Sistema de Auditoría y Trazabilidad de Proveedores</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Proveedores</h3>
                <div class="numero">{total}</div>
            </div>
            <div class="stat-card conforme">
                <h3>Conformes</h3>
                <div class="numero">{conformes}</div>
                <p>{round(conformes/total*100) if total > 0 else 0}%</p>
            </div>
            <div class="stat-card no-conforme">
                <h3>No Conformes</h3>
                <div class="numero">{no_conformes}</div>
                <p>{round(no_conformes/total*100) if total > 0 else 0}%</p>
            </div>
            <div class="stat-card">
                <h3>Score Promedio</h3>
                <div class="numero">{score_promedio}%</div>
            </div>
        </div>

        <div class="criterios-promedio">
            <div class="criterio-card">
                <h3>🏛️ GOVERNANCE</h3>
                <div class="criterio-bar">
                    <div class="criterio-fill" style="width: {gov_promedio}%">{gov_promedio}%</div>
                </div>
            </div>
            <div class="criterio-card">
                <h3>👥 SOCIAL</h3>
                <div class="criterio-bar">
                    <div class="criterio-fill" style="width: {social_promedio}%">{social_promedio}%</div>
                </div>
            </div>
            <div class="criterio-card">
                <h3>🌱 ENVIRONMENTAL</h3>
                <div class="criterio-bar">
                    <div class="criterio-fill" style="width: {env_promedio}%">{env_promedio}%</div>
                </div>
            </div>
        </div>

        <div class="table-container">
            <h2 style="margin-bottom: 20px; color: #2c3e50;">📊 Detalle por Proveedor</h2>
            <table>
                <thead>
                    <tr>
                        <th>Proveedor</th>
                        <th>CUIT</th>
                        <th>Score Total</th>
                        <th>Governance</th>
                        <th>Social</th>
                        <th>Environmental</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_tabla}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Sistema generado con Python + JSON + Requests</p>
            <p>Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""

        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"📊 Dashboard generado: {archivo_salida}")


def main():
    """Función principal"""
    print("=" * 60)
    print("🌍 SISTEMA DE AUDITORÍA ESG - TRAZABILIDAD DE PROVEEDORES")
    print("=" * 60)

    # Crear auditor
    auditor = ESGAuditor()

    # Procesar planilla
    resultados = auditor.procesar_planilla("proveedores.csv")

    # Exportar resultados
    if resultados:
        # 1. Exportar JSON
        auditor.exportar_json(resultados)

        # 2. Generar reportes HTML individuales por proveedor
        print("\n📄 Generando reportes individuales...")
        for resultado in resultados:
            archivo_html = f"reporte_{resultado['proveedor']['id']}.html"
            auditor.generar_reporte_html(resultado, archivo_html)
            print(f"  ✓ {archivo_html}")

        # 3. Generar dashboard general
        print("\n📊 Generando dashboard general...")
        auditor.generar_dashboard(resultados)

        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print("\n📂 Archivos generados:")
        print("  • auditoria_esg.json - Datos JSON completos")
        print("  • dashboard.html - Dashboard general (ABRIR ESTE)")
        print(f"  • reporte_001.html, reporte_002.html... - Reportes individuales")
        print("\n💡 Abre dashboard.html en tu navegador para ver los resultados")
    else:
        print("\n❌ No se procesaron proveedores")

if __name__ == "__main__":
    main()
