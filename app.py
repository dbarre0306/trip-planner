import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from trip_planner.app import launch

if __name__ == "__main__":
    launch()
