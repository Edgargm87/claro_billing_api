import os
import tempfile
import xmltodict
import pandas as pd
from fastapi import HTTPException
from app.core.config import settings
import logging

import pdfplumber
import re

logger = logging.getLogger(__name__)

class FacturaService:
    def __init__(self):
        self.conceptos_objetivo = [
            "CLARO CLOUD",
            "ALIANZAS",
            "MPLS INTRANET DOMESTIC",
            "PAQUETE HOSTING",
            "INTERNET DEDICADO COMCEL"
        ]
        self.plantilla_path = settings.EXCEL_TEMPLATE_PATH
        self.pdf_template_path = settings.PDF_TEMPLATE_PATH
        
        # Mapeo de códigos a conceptos internos
        # Algunos códigos se suman para un mismo concepto
        self.codigos_pdf_map = {
            "FJE0011": "AWS_CLOUD",
            "FJE0005": "LICENCIAMIENTO",
            "FJE0000017": "LICENCIAMIENTO",
            "FJE0003": "INTERNET_DEDICADO",
            "FJE0000013": "INTERNET_DEDICADO",
            "FJE0000014": "INTERNET_DEDICADO",
            "FJE0000015": "INTERNET_DEDICADO",
            "FJE0006": "INTERNET_OFICINA_MICRO_CREDICHEVERE",
            "FJE0007": "INTERNET_OFICINA_MONTERIA" 
        }

    def _clean_currency(self, price_str: str) -> float:
        """
        Limpia un string de moneda y lo convierte a float.
        Maneja formatos US (1,234.56) y EU (1.234,56).
        """
        if not price_str:
            return 0.0
        
        # Eliminar $ y espacios
        s = price_str.replace('$', '').strip()
        
        # Lógica de detección de formato:
        # Si tiene punto y coma, el último es el separador decimal
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'):
                # Formato Europeo/Colombiano: 1.234,56 -> 1234.56
                s = s.replace('.', '').replace(',', '.')
            else:
                # Formato US: 1,234.56 -> 1234.56
                s = s.replace(',', '')
        elif ',' in s:
            # Solo coma: si tiene 2 dígitos después, es decimal, si no, es miles
            parts = s.split(',')
            if len(parts[-1]) == 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        elif '.' in s:
            # Solo punto: si tiene 2 dígitos después, es decimal, si no, es miles
            parts = s.split('.')
            if len(parts[-1]) == 2:
                pass # Ya es formato float aceptable
            else:
                s = s.replace('.', '')
        
        try:
            return float(s)
        except ValueError:
            return 0.0

    def procesar_pdf(self, pdf_path: str) -> list[dict]:
        """
        Lee la página 3 del PDF y extrae valores basados en códigos específicos.
        """
        logger.info(f"Procesando PDF {pdf_path}")
        conceptos_sumarizados = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) < 3:
                    raise ValueError("El PDF no tiene al menos 3 páginas para procesar el detalle.")
                
                # Procesar hoja 3
                page = pdf.pages[2]
                text = page.extract_text()
                
                if not text:
                    logger.warning("No se pudo extraer texto de la página 3.")
                    return []

                lines = text.split('\n')
                for line in lines:
                    line_upper = line.upper()
                    for code, concepto_name in self.codigos_pdf_map.items():
                        if code.upper() in line_upper:
                            # Buscar patrones de moneda: $ seguido de números, puntos y comas
                            # Priorizamos valores que vienen después del símbolo $
                            prices = re.findall(r"\$\s*([\d\.,]+)", line)
                            
                            if prices:
                                # El último precio de la línea suele ser el subtotal/total del ítem
                                valor = self._clean_currency(prices[-1])
                                if valor > 0:
                                    conceptos_sumarizados[concepto_name] = conceptos_sumarizados.get(concepto_name, 0.0) + valor
                                    logger.info(f"Extraído (con $): {code} -> {valor}")
                                    # Una vez encontrado un código en la línea, pasamos a la siguiente para evitar duplicar
                                    break
                            else:
                                # Fallback: buscar números grandes al final de la línea si no hay $
                                matches = re.findall(r"([\d\.,]{5,})", line)
                                if matches:
                                    valor = self._clean_currency(matches[-1])
                                    if valor > 100: # Heurística para evitar capturar IDs o fechas
                                        conceptos_sumarizados[concepto_name] = conceptos_sumarizados.get(concepto_name, 0.0) + valor
                                        logger.info(f"Extraído (fallback): {code} -> {valor}")
                                        break

            # Formatear para el motor de distribución
            res = []
            for nombre, valor in conceptos_sumarizados.items():
                res.append({
                    "id_concepto_factura": nombre,
                    "valor": valor,
                    "descripcion": f"Concepto extraído del PDF ({nombre})"
                })

            import json
            logger.info(f"RESULTADO EXTRACCIÓN PDF: {json.dumps(res, indent=2)}")
            
            return res

        except Exception as e:
            logger.error(f"Error procesando PDF: {str(e)}")
            raise ValueError(f"Error al procesar el PDF: {str(e)}")

    def procesar_xml(self, xml_path: str) -> list[dict]:
        """
        Lee el XML UBL y extrae los valores para los conceptos especificados.
        """
        logger.info(f"Procesando XML {xml_path}")
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Limpiar namespaces para facilitar el parsing
            # Aunque xmltodict los maneja, mejor iterar por los items
            doc = xmltodict.parse(xml_content, process_namespaces=False)
            
            # Buscar InvoiceLine
            invoice = doc.get('Invoice', {})
            invoice_lines = invoice.get('cac:InvoiceLine', [])
            
            if not isinstance(invoice_lines, list):
                invoice_lines = [invoice_lines]
                
            conceptos_extraidos = []
            
            for line in invoice_lines:
                item = line.get('cac:Item', {})
                descripcion = item.get('cbc:Description', '')
                
                # Clean up if nested dict or just string
                if isinstance(descripcion, dict):
                    descripcion = descripcion.get('#text', descripcion)
                    
                if descripcion in self.conceptos_objetivo:
                    # Extraer valor total
                    line_extension = line.get('cbc:LineExtensionAmount', {})
                    valor_total = float(line_extension.get('#text', 0) if isinstance(line_extension, dict) else line_extension)
                    
                    # Extraer cantidad
                    quantity_elem = line.get('cbc:InvoicedQuantity', {})
                    cantidad = float(quantity_elem.get('#text', 1) if isinstance(quantity_elem, dict) else quantity_elem)
                    
                    conceptos_extraidos.append({
                        "id_concepto_factura": descripcion,
                        "descripcion": descripcion,
                        "valor": valor_total,
                        "cantidad": cantidad
                    })
                    
            logger.info(f"Conceptos extraidos: {conceptos_extraidos}")
            return conceptos_extraidos
            
        except Exception as e:
            logger.error(f"Error parseando XML: {str(e)}")
            raise ValueError(f"No se pudo procesar el archivo XML: {str(e)}")

    def generar_distribucion_excel(self, conceptos_extraidos: list[dict], use_pdf_template: bool = False):
        """
        Ejecuta el motor de distribucion y genera el excel de salida.
        """
        path_actual = self.pdf_template_path if use_pdf_template else self.plantilla_path
        
        if not os.path.exists(path_actual):
            raise HTTPException(status_code=500, detail=f"Plantilla de distribucion no encontrada en {path_actual}")
            
        try:
            df_plantilla = pd.read_excel(path_actual)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error leyendo la plantilla de Excel: {str(e)}")

        columnas_requeridas = [
            "AREA_RESP_PPTO", "NOMBRE_CONCEPTO", "NIVEL_3_N", "PRODUCTO_N", 
            "AGENCIA", "CENTRO_COSTO", "NOMBRE_CUENTA", "NOMBRE_TERCERO", 
            "NOMBRE_AREA", "CONCEPTO_CONTABLE", "CUENTA", "EMPRESA", 
            "PORCENTAJE_DISTRIBUCION", "ID_CONCEPTO_FACTURA"
        ]
        
        # Validar columnas
        for col in columnas_requeridas:
            if col not in df_plantilla.columns:
                raise HTTPException(status_code=500, detail=f"Falta columna requerida en la plantilla: {col}")

        # Distribuir
        filas_distribuidas = []
        resumen = {"totales_por_concepto": {}, "total_general": 0}
        
        for concepto in conceptos_extraidos:
            ID = concepto["id_concepto_factura"]
            valor_total = concepto["valor"]
            
            # Filtrar plantilla
            df_concepto = df_plantilla[df_plantilla["ID_CONCEPTO_FACTURA"] == ID]
            if df_concepto.empty:
                logger.warning(f"No se encontraron reglas de distribucion para {ID}")
                continue

            # Validar sumatoria 100%
            suma_porcentajes = df_concepto["PORCENTAJE_DISTRIBUCION"].sum()
            if abs(suma_porcentajes - 100.0) > 0.01:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Los porcentajes para {ID} no suman 100%. Total actual: {suma_porcentajes}%"
                )
                
            total_distribuido_concepto = 0
            for _, row in df_concepto.iterrows():
                porcentaje = row["PORCENTAJE_DISTRIBUCION"]
                valor_distribuido = valor_total * (porcentaje / 100.0)
                
                nueva_fila = row.to_dict()
                nueva_fila["VALOR_DISTRIBUIDO"] = valor_distribuido
                filas_distribuidas.append(nueva_fila)
                total_distribuido_concepto += valor_distribuido
                
            resumen["totales_por_concepto"][ID] = total_distribuido_concepto
            resumen["total_general"] += total_distribuido_concepto

        if not filas_distribuidas:
            raise HTTPException(status_code=400, detail="No se pudo procesar ningun concepto o plantilla vacia.")

        df_final = pd.DataFrame(filas_distribuidas)
        
        # Archivo temporal para el excel a retornar
        temp_dir = "/tmp/facturas_output"
        os.makedirs(temp_dir, exist_ok=True)
        # Using a fixed temp name so it can be managed, or a random one
        _, temp_path = tempfile.mkstemp(suffix=".xlsx", dir=temp_dir)
        
        # Opcional: Generar linea de totales mediante motor normal o Excel writer
        with pd.ExcelWriter(temp_path, engine="openpyxl") as writer:
            df_final.to_excel(writer, index=False, sheet_name="Distribucion")
            
            # Accedemos a la hoja creada
            workbook = writer.book
            worksheet = writer.sheets["Distribucion"]
            
            # Fila final de totales
            max_row = len(df_final) + 1 # el indice incluye las cabezeras (index=1)
            valor_col_index = list(df_final.columns).index("VALOR_DISTRIBUIDO") + 1
            
            worksheet.cell(row=max_row + 1, column=1, value="TOTAL GENERAL")
            worksheet.cell(row=max_row + 1, column=valor_col_index, value=resumen["total_general"])

        return temp_path, resumen
