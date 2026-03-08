import os
from pydantic import BaseModel

class Settings(BaseModel):
    data_root: str = os.getenv("DATA_ROOT", "/data")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "2048"))
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = Settings()
