import os
import sys

PYTEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PYTEST_DIR)
JOBS_DIR = os.path.join(PROJECT_ROOT, "jobs")

if JOBS_DIR not in sys.path:
    sys.path.insert(0, JOBS_DIR)
