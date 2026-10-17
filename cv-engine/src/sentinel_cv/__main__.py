"""Module entry point for python -m sentinel_cv."""

import sys
from sentinel_cv.cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
