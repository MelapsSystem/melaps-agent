from unittest.mock import Mock, patch

import pytest

from melaps_agent.gpu import NoGpuError, query_gpus

SAMPLE = """0, NVIDIA H100 80GB HBM3, 87 %, 61234 MiB, 81559 MiB, 62 C, 612 W, 1980 MHz
1, NVIDIA H100 80GB HBM3, 91 %, 60112 MiB, 81559 MiB, 64 C, 640 W, 1980 MHz
"""


def test_parses_nvidia_smi_output():
    with patch("melaps_agent.gpu.subprocess.run") as run:
        run.return_value = Mock(stdout=SAMPLE)
        gpus = query_gpus()
    assert len(gpus) == 2
    assert gpus[0]["name"] == "NVIDIA H100 80GB HBM3"
    assert gpus[0]["utilization_gpu"] == 87
    assert gpus[0]["memory_total_mib"] == 81559


def test_missing_nvidia_smi_is_fatal():
    with patch("melaps_agent.gpu.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(NoGpuError):
            query_gpus()
