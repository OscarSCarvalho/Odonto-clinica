from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

_scheduler: BackgroundScheduler | None = None


def start_scheduler(app):
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)

    def _job():
        with app.app_context():
            from app.infrastructure.container import enviar_lembretes_uc
            uc = enviar_lembretes_uc()
            uc.executar()

    _scheduler.add_job(
        _job,
        trigger=IntervalTrigger(minutes=15),
        id='enviar_lembretes',
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
