"""melaps-agent — heartbeat, telemetry, and job execution for one node.

Runs as a systemd service on every GPU node in a cluster. The control plane
assigns jobs; the agent pulls the spec, executes it, streams logs, and
reports GPU telemetry every 5 seconds.
"""

import logging
import signal
import sys
import time

import requests

from .config import Config
from .gpu import NoGpuError, query_gpus
from .jobs import JobExecutor
from .telemetry import Reporter

log = logging.getLogger("melaps-agent")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = Config.load()
    if not config.api_key:
        log.error("MELAPS_AGENT_KEY is not set")
        return 1
    try:
        gpus = query_gpus()
    except NoGpuError as e:
        log.error("startup failed: %s", e)
        return 1
    log.info("node %s: %d GPU(s) detected: %s", config.node_id, len(gpus), gpus[0]["name"])
    reporter = Reporter(config.api_base, config.api_key, config.node_id)
    stop = False

    def _stop(*_):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    last_heartbeat = 0
    while not stop:
        now = time.time()
        try:
            gpus = query_gpus()
            reporter.telemetry(gpus)
            if now - last_heartbeat >= config.heartbeat_interval:
                reporter.heartbeat()
                last_heartbeat = now
            job = _poll_assignment(reporter)
            if job:
                _run_job(reporter, config, job)
        except requests.RequestException as e:
            log.warning("control plane unreachable: %s", e)
        time.sleep(config.telemetry_interval)
    log.info("agent stopping")
    return 0


def _poll_assignment(reporter):
    resp = reporter.session.get(
        f"{reporter.api_base}/nodes/{reporter.node_id}/assignment", timeout=10)
    if resp.status_code == 204:
        return None
    resp.raise_for_status()
    return resp.json()


def _run_job(reporter, config, assignment):
    job_id = assignment["id"]
    log.info("starting job %s", job_id)
    reporter.job_status(job_id, "RUNNING")
    executor = JobExecutor(job_id, assignment["spec"], config.workdir)
    exit_code = executor.run(lambda line: _send_log(reporter, job_id, line))
    status = "DONE" if exit_code == 0 else ("PREEMPTED" if executor.preempted.is_set() else "FAILED")
    reporter.job_status(job_id, status, exit_code=exit_code)
    log.info("job %s finished: %s (exit %d)", job_id, status, exit_code)


def _send_log(reporter, job_id, line):
    try:
        reporter.session.post(
            f"{reporter.api_base}/jobs/{job_id}/logs",
            json={"line": line}, timeout=5,
        )
    except requests.RequestException:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
