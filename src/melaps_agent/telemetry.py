"""Telemetry + heartbeat reporting to the Melaps API."""

import requests


class Reporter:
    """POSTs heartbeats and per-GPU telemetry to the control plane."""

    def __init__(self, api_base, api_key, node_id, timeout=10):
        self.api_base = api_base.rstrip("/")
        self.node_id = node_id
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Melaps-Version": "2026-06-22",
            "Content-Type": "application/json",
        })

    def heartbeat(self, status="ok"):
        return self.session.post(
            f"{self.api_base}/nodes/{self.node_id}/heartbeat",
            json={"status": status}, timeout=self.timeout,
        )

    def telemetry(self, gpus):
        return self.session.post(
            f"{self.api_base}/nodes/{self.node_id}/telemetry",
            json={"gpus": gpus}, timeout=self.timeout,
        )

    def job_status(self, job_id, status, exit_code=None):
        body = {"status": status}
        if exit_code is not None:
            body["exit_code"] = exit_code
        return self.session.post(
            f"{self.api_base}/jobs/{job_id}/status",
            json=body, timeout=self.timeout,
        )
