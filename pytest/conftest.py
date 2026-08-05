import os
import sys
import time

import pytest

PYTEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PYTEST_DIR)
JOBS_DIR = os.path.join(PROJECT_ROOT, "jobs")

if JOBS_DIR not in sys.path:
    sys.path.insert(0, JOBS_DIR)


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch):
    """The retry/backoff code calls the real time.sleep() (5 x 65s on HTTP 429).

    We make it a no-op in tests - otherwise the suite hangs for ~4 minutes and
    times out in CI.
    """
    monkeypatch.setattr(time, "sleep", lambda *args, **kwargs: None)
