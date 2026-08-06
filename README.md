---
title: TripPlanner
emoji: 🧳
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.22.0
app_file: app.py
pinned: false
---

# TripPlanner

TripPlanner is an itinerary generator project that calls the OpenAI API directly via the `openai` SDK to build itineraries. Given a destination, dates, and a set of interests, it searches for venues, enriches each one with an LLM, and produces an itinerary through a Gradio web UI.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

```bash
uv sync
```

### Customizing

**Add your `OPENAI_API_KEY`, `MODEL`, and `SERPER_API_KEY` into the `.env` file**

- Modify `src/trip_planner/integrations/openai_client.py` to change how OpenAI is called
- Modify `src/trip_planner/trip_planner.py` and `src/trip_planner/enrichment/venue_processing.py` to change itinerary logic
- Modify `src/trip_planner/ui/ui.py` to change the Gradio form/results UI

## Running the Project

To launch the Gradio web UI, run this from the root folder of your project:

```bash
uv run app
```

## Testing

```bash
uv run pytest
```
