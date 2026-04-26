from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://root:rootpassword@localhost:5432/codeforge"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    JWT_SECRET: str = "super_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    RATE_LIMIT_PER_MINUTE: int = 100
    CORS_ORIGINS: str = "http://localhost:5173"
    class Config:
        env_file = ".env"

settings = Settings()
