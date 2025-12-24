from smolotchi.core.jobs import JobStore


def lan_is_busy(jobstore: JobStore) -> bool:
    running = jobstore.list(limit=1, status="running")
    return bool(running)
