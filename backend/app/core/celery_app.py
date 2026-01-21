from celery import Celery
from app.core.config import settings

celery_app = Celery("pickabook", include=['app.worker.tasks'])

# Fix for Upstash/Render SSL (rediss://)
redis_url = settings.REDIS_URL
if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
    redis_url += "?ssl_cert_reqs=CERT_NONE"

celery_app.conf.broker_url = redis_url
celery_app.conf.result_backend = redis_url
celery_app.conf.broker_connection_retry_on_startup = True
