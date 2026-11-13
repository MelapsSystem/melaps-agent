# melaps-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

Node agent for [Melaps System](https://melaps.xyz) GPU clusters. Runs as a
systemd service on every GPU node: it reports heartbeats and per-GPU
telemetry to the control plane, pulls job assignments, executes the workload,
and streams logs back.

- Website: <https://melaps.xyz>
- Documentation: <https://docs.melaps.xyz>
- X: <https://x.com/melaps_system>

## Token

**$MELAPS** — contract address: `0x49b5a9fcd24ca5083fa05f9136e7d04564647621`

## What it does

| Loop | Interval | Detail |
| --- | --- | --- |
| Heartbeat | 15 s | Node liveness to the control plane |
| Telemetry | 5 s | Per-GPU util, memory, temperature, power, clocks via `nvidia-smi` |
| Assignment poll | 5 s | Picks up the next job for this node |
| Job execution | — | Runs the job command, streams stdout, reports `DONE` / `FAILED` / `PREEMPTED` |

Batch-tier jobs are preemptible: on SIGTERM the agent forwards the signal to
the job process group so frameworks can checkpoint, then waits up to 55
seconds before SIGKILL.

## Install

```bash
pip install melaps-agent
cp config/agent.example.toml /etc/melaps/agent.toml
# set node_id, then:
echo "MELAPS_AGENT_KEY=agent_..." > /etc/melaps/agent.env
cp systemd/melaps-agent.service /etc/systemd/system/
systemctl enable --now melaps-agent
```

## Telemetry

The agent reads real readings from `nvidia-smi` — utilization, memory used /
total, temperature, power draw, and SM clocks per GPU. If `nvidia-smi` is
missing or reports no GPU, the agent refuses to start instead of reporting
made-up numbers.

## License

MIT — see [LICENSE](LICENSE).

---

**Melaps System** — GPU racks you can hold by the hour.

- Website: <https://melaps.xyz>
- Documentation: <https://docs.melaps.xyz>
- X: <https://x.com/melaps_system>
- Status: <https://melaps.xyz/status>
