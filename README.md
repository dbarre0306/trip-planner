# TripPlanner

TripPlanner is a trip-planning project that calls the OpenAI API directly via the `openai` SDK to build itineraries.

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

- Modify `src/trip_planner/main.py` to customize the trip inputs passed to `create_itinerary`
- Modify `src/trip_planner/openai_client.py` to change how OpenAI is called
- Modify `src/trip_planner/trip_planner.py` and `src/trip_planner/venue_processing.py` to change itinerary logic

## Running the Project

To run the trip planner, run this from the root folder of your project:

```bash
uv run trip_planner
```

## Testing

```bash
uv run pytest
```
