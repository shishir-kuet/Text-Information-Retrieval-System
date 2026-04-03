from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from threading import Lock
from uuid import uuid4

from backend.app.config.settings import settings


_executor = ThreadPoolExecutor(max_workers=max(1, settings.job_max_workers), thread_name_prefix="admin-job")
_jobs = {}
_jobs_lock = Lock()


def _now_iso():
    return datetime.utcnow().isoformat() + "Z"


def _set_job(job_id: str, **updates):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job.update(updates)


def submit_job(job_type: str, target, *args, meta: dict | None = None, **kwargs):
    job_id = uuid4().hex
    record = {
        "job_id": job_id,
        "job_type": job_type,
        "status": "queued",
        "created_at": _now_iso(),
        "started_at": None,
        "finished_at": None,
        "error": None,
        "result": None,
        "meta": meta or {},
    }

    with _jobs_lock:
        _jobs[job_id] = record

    def _runner():
        _set_job(job_id, status="running", started_at=_now_iso())
        try:
            result = target(*args, **kwargs)
            _set_job(job_id, status="completed", finished_at=_now_iso(), result=result)
        except Exception as exc:
            _set_job(job_id, status="failed", finished_at=_now_iso(), error=str(exc))

    _executor.submit(_runner)
    with _jobs_lock:
        return deepcopy(_jobs.get(job_id))


def list_jobs(limit: int = 50, status: str | None = None):
    with _jobs_lock:
        items = list(_jobs.values())

    if status:
        items = [j for j in items if j.get("status") == status]

    items.sort(key=lambda j: j.get("created_at") or "", reverse=True)
    return [deepcopy(j) for j in items[:limit]]
