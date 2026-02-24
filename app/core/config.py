from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Claro Billing API"
    VERSION: str = "1.0.0"
    SECRET_KEY: str = "super_secret_key"
    EXCEL_TEMPLATE_PATH: str = "files/Distrib. Claro.xlsx"
    PDF_TEMPLATE_PATH: str = "files/plantilla.xlsx"

    class Config:
        case_sensitive = True

settings = Settings()
