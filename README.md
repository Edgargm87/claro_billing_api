# Claro Billing API

Esta es una API profesional desarrollada en FastAPI diseñada para procesar facturas electrónicas XML UBL de Claro y generar de forma automática la distribución contable en Excel.

## Funcionalidades
1. **Validación y Lectura de XML**: Procesa facturas UBL 2.1 e identifica valores totales y descripciones de conceptos definidos.
2. **Motor de Distribución Contable**: Cruza los conceptos de la factura con una plantilla de distribución contable interna (basada en Excel).
3. **Generación de Reporte (Excel)**: Genera y retorna un Excel validado con los valores distribuidos manteniendo las columnas iniciales y sumando la columna de distribución, totals y totales generales calculados dinámicamente.

## Requisitos Previos

- Python 3.11+
- Docker (opcional, para despliegues con contenedor)

## Instalación y Configuración

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar el servidor localmente**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Ejecutar con Docker**:
   ```bash
   docker build -t claro-billing-api .
   docker run -p 8000:8000 claro-billing-api
   ```

## Estructura del Proyecto
El proyecto respeta estrictamente la siguiente estructura para separar los conceptos de dominio de la aplicación:
- `app/api`: Definición de rutas o endpoints.
- `app/core`: Configuración global y funciones de seguridad.
- `app/db`: Configuración e inicialización de la base de datos (dummy en caso de no usar DB para procesamiento del excel).
- `app/middleware`: Interceptores de la petición, enfocado en manejo de errores global.
- `app/models`: Modelos de base de datos definidos.
- `app/schemas`: Modelos de validación con Pydantic.
- `app/services`: Lógica de negocio (procesamiento de facturas y excel).

## Endpoints Principales

- `GET /api/v1/health`
- `GET /api/v1/ready`
- `POST /api/v1/facturas/procesar`: Recibe una factura en XML `multipart/form-data` y lanza el procesamiento devolviendo un ZIP o retornando JSON en caso de error, dependiendo de lo implementado. El proceso distribuye según configuraciones de Plantilla.

## Estructura de Respuesta del Endpoint Procesar
La carga esperada del endpoint de procesar es un archivo `xml`.
Retorna un Excel y un Header/Respuesta con la cabecera correspondiente y metadata del estado o la descarga directa de un Excel procesado.
