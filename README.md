# FastAPI Service Template

Este es un template base para crear servicios profesionales usando FastAPI. Incluye una arquitectura modular y configuraciones listas para producción.

## Características

- ⚡ **FastAPI**: Framework moderno y de alto rendimiento.
- 🗄️ **SQLAlchemy**: ORM para bases de datos SQL.
- 🔐 **Autenticación**: Estructura base para manejo de seguridad (JWT, etc).
- 🏗️ **Arquitectura Modular**: Separación clara de responsabilitades (API, Core, Services, Schemas).
- 🐳 **Docker**: Soporte básico para contenedores (si aplica).

## Estructura del Proyecto

El proyecto sigue una arquitectura por capas dentro del directorio `app/`:

```
app/
├── api/          # Endpoints y rutas de la API (v1, routes, etc)
├── core/         # Configuraciones generales, seguridad y utilidades base
├── db/           # Configuración de base de datos y modelos base
├── middleware/   # Middlewares para interceptar peticiones (CORS, logs, etc)
├── models/       # Modelos de base de datos (SQLAlchemy)
├── schemas/      # Esquemas de Pydantic para validación de datos
├── services/     # Lógica de negocio separada de los endpoints
└── main.py       # Punto de entrada de la aplicación
```

## Requisitos Previos

- Python 3.9+
- pip

## Instalación

1. **Clonar el repositorio y entrar al directorio:**
   ```bash
   git clone <url-del-repo>
   cd fastapi-service-template
   ```

2. **Crear un entorno virtual:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Copia el archivo `.env` de ejemplo (si existe) o crea uno nuevo basándote en la configuración en `app/core/config.py`.

## Ejecución

Para levantar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload
```

O usando el comando de fastapi si está disponible:

```bash
fastapi dev app/main.py
```

La documentación interactiva estará disponible en: http://127.0.0.1:8000/docs
