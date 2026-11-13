"""GPU discovery and telemetry via ``nvidia-smi``.

The agent shells out to ``nvidia-smi --query-gpu=... --format=csv`` once per
telemetry tick. No GPU on the box is a fatal error at startup — the agent
never fabricates readings.
"""

import subprocess

QUERY_FIELDS = (
    "index,name,utilization.gpu,memory.used,memory.total,"
    "temperature.gpu,power.draw,clocks.sm"
)


class NoGpuError(RuntimeError):
    """``nvidia-smi`` is missing or reports no GPU."""


def query_gpus():
    """Return one dict per GPU: util %, memory, temperature, power, clocks."""
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={QUERY_FIELDS}", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10, check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise NoGpuError("nvidia-smi is unavailable on this node") from e
    gpus = []
    for line in out.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 8:
            continue
        idx, name, util, mem_used, mem_total, temp, power, clocks = parts
        gpus.append({
            "index": int(idx),
            "name": name,
            "utilization_gpu": float(util.split()[0]),
            "memory_used_mib": float(mem_used.split()[0]),
            "memory_total_mib": float(mem_total.split()[0]),
            "temperature_c": float(temp.split()[0]),
            "power_w": float(power.split()[0]),
            "clocks_sm_mhz": float(clocks.split()[0]),
        })
    if not gpus:
        raise NoGpuError("nvidia-smi reports no GPUs")
    return gpus
