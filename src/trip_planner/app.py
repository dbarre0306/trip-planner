from dotenv import load_dotenv

from trip_planner.ui.assets import CSS, HEAD
from trip_planner.ui.ui import build_ui

load_dotenv(override=True)

demo = build_ui()


def launch():
    demo.launch(css=CSS, head=HEAD)


if __name__ == "__main__":
    launch()
