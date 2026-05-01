"""SparkKeeper core - 定时调度"""

import threading
from apscheduler.schedulers.background import BackgroundScheduler


class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def add_daily_job(self, job_id, func, hour, minute):
        if job_id in self.jobs:
            self.remove_job(job_id)
        self.scheduler.add_job(
            func, "cron", hour=hour, minute=minute, id=job_id
        )
        self.jobs[job_id] = True

    def add_interval_job(self, job_id, func, minutes=10):
        if job_id in self.jobs:
            self.remove_job(job_id)
        self.scheduler.add_job(
            func, "interval", minutes=minutes, id=job_id
        )
        self.jobs[job_id] = True

    def remove_job(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass
        self.jobs.pop(job_id, None)

    def is_running(self):
        return self.scheduler.running
