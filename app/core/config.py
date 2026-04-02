from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    #App
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    
    SECRET_KEY: str
    
    #Database
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    #JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
    #Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    
    #AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_REGION: str
    
    #RazorPay
    RAZORPAY_KEY_ID: str
    RAZORPAY_SECRET: str
    
    #Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int
    
    #ElasticSearch
    ELASTICSEARCH_URL: str
    
    #Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    #Cors
    ALLOWED_ORIGINS: str
    
    #Properties
    @property
    def DATABASE_URL(self) -> str:
        return(
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
settings = Settings()