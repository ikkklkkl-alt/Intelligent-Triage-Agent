from app.db.session import get_sync_db
from app.services.report import interpret_report
from app.tasks.celery_app import celery_app

@celery_app.task(name="report.interpret", bind=True, max_retries=1, default_retry_delay=15)
def interpret_lab_report(self, report_id: int) -> str:
    db = get_sync_db()
    try:
        interpret_report(db, report_id); return "ok"
    finally: db.close()
