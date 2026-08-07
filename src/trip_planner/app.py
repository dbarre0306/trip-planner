import os
from dotenv import load_dotenv

from trip_planner.ui.assets import CSS, HEAD
from trip_planner.ui.ui import build_ui

load_dotenv(override=True)

demo = build_ui()


def launch():
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        css=CSS, 
        head=HEAD
    )


if __name__ == "__main__":
    launch()
