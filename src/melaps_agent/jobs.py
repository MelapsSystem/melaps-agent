"""Job execution: run the workload, forward logs, handle preemption.

Batch-tier jobs are preemptible: the scheduler sends SIGTERM 60 seconds
before reclaiming the GPUs. The executor forwards SIGTERM to the child
process group so training frameworks can checkpoint, then waits up to
55 seconds before SIGKILL.
"""

import os
import signal
import subprocess
import threading
from pathlib import Path

PREEMPT_GRACE_SECONDS = 55


class JobExecutor:
    def __init__(self, job_id, spec, workdir):
        self.job_id = job_id
        self.spec = spec
        self.workdir = Path(workdir) / job_id
        self.proc = None
        self.preempted = threading.Event()

    def _on_sigterm(self, *_):
        self.preempted.set()
        if self.proc is not None:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)

    def run(self, log_callback):
        """Run the job command. Returns the exit code."""
        self.workdir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env.update({k: str(v) for k, v in self.spec.get("env", {}).items()})
        cmd = self.spec["command"]
        old_handler = signal.signal(signal.SIGTERM, self._on_sigterm)
        try:
            self.proc = subprocess.Popen(
                cmd, cwd=self.workdir, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, start_new_session=True,
            )
            for line in self.proc.stdout:
                log_callback(line.rstrip())
            try:
                return self.proc.wait(timeout=PREEMPT_GRACE_SECONDS if self.preempted.is_set() else None)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                return self.proc.wait()
        finally:
            signal.signal(signal.SIGTERM, old_handler)
