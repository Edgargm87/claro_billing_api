import json
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from app.services.factura_service import FacturaService
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
factura_service = FacturaService()

@router.post("/procesar")
async def procesar_factura(file: UploadFile = File(...)):
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un XML.")
    return await _process_file(file, format="xml")

@router.post("/procesar_pdf")
async def procesar_factura_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")
    return await _process_file(file, format="pdf")

async def _process_file(file: UploadFile, format: str):
    try:
        # Save temporary file
        temp_dir = "/tmp/facturas"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process based on format
        if format == "xml":
            extracted_data = factura_service.procesar_xml(file_path)
            excel_path, resumen = factura_service.generar_distribucion_excel(extracted_data, use_pdf_template=False)
        else:
            extracted_data = factura_service.procesar_pdf(file_path)
            excel_path, resumen = factura_service.generar_distribucion_excel(extracted_data, use_pdf_template=True)

        headers = {
            "Access-Control-Expose-Headers": "X-Resumen-Procesamiento",
            "X-Resumen-Procesamiento": json.dumps(resumen)
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        final_filename = f"Distribucion_{format.upper()}_{timestamp}.xlsx"
        
        return FileResponse(
            excel_path, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            filename=final_filename,
            headers=headers
        )

    except Exception as e:
        logger.error(f"Error procesando {format}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup could be done in background tasks
        pass
