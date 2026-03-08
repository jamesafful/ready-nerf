from celery import Celery
from .config import settings

celery = Celery(
    "nerf_recon",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.update(
    task_track_started=True,
    task_time_limit=60*60*24,  # 24h hard limit
)
