import asyncio
import html as _html
import queue
from turtle import st
from urllib.parse import quote_plus
import gradio as gr
from datetime import date, datetime, timedelta, timezone
from dotenv import load_dotenv

from trip_planner.assets import CSS, HEAD
from trip_planner.domain import (
    CATEGORIES,
    INTERESTS,
    CategoryId,
    InterestId,
    TravelInfo,
    choices_for,
    find_interest_by_id,
)
from trip_planner.trip_planner import (
    STAGE_PROCESSING_COMPLETE,
    STAGE_SEARCH_COMPLETE,
    create_itinerary,
)
from trip_planner.validation import capitalize_destination, is_valid_destination, validate_form

load_dotenv(override=True)


_BADGE_CLASS = {category.label: f"itin-badge-{category.id.value}" for category in CATEGORIES}


def _fmt_date(start_date) -> str:
    if isinstance(start_date, (int, float)):
        return datetime.fromtimestamp(start_date, tz=timezone.utc).strftime("%Y-%m-%d")
    if hasattr(start_date, "strftime"):
        return start_date.strftime("%Y-%m-%d")
    return str(start_date)


def _travel_dates(start_date, num_days) -> list[str]:
    if isinstance(start_date, (int, float)):
        start = datetime.fromtimestamp(start_date, tz=timezone.utc).date()
    elif isinstance(start_date, datetime):
        start = start_date.date()
    elif isinstance(start_date, date):
        start = start_date
    else:
        start = datetime.strptime(str(start_date), "%Y-%m-%d").date()
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(int(num_days))]


def _to_12h(time_str: str) -> str:
    try:
        h, m = map(int, time_str.split(":"))
        suffix = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {suffix}"
    except (ValueError, AttributeError):
        return time_str


def _trip_summary_html(
    destination, start_date, num_days, num_adults, num_children, interests,
    *, button_enabled: bool = False,
) -> str:
    e = _html.escape
    date_str = _fmt_date(start_date)
    n_days = int(num_days)
    n_adults = int(num_adults)
    n_children = int(num_children)

    days_label = f"{n_days} day{'s' if n_days != 1 else ''}"
    party_parts = [f"{n_adults} adult{'s' if n_adults != 1 else ''}"]
    if n_children:
        party_parts.append(f"{n_children} child{'ren' if n_children != 1 else ''}")
    meta = f"{e(date_str)} &nbsp;·&nbsp; {days_label} &nbsp;·&nbsp; {', '.join(party_parts)}"

    interest_values = [item for group in interests for item in (group or [])]
    if interest_values:
        interest_labels = [find_interest_by_id(InterestId(v)).label for v in interest_values]
        pills = "".join(f'<span class="trip-summary-tag">{e(lbl)}</span>' for lbl in interest_labels)
    else:
        pills = '<span class="trip-summary-tag trip-summary-tag--empty">General sightseeing</span>'

    btn_disabled = "" if button_enabled else " disabled"

    return (
        f'<div class="trip-summary">'
        f'<div class="trip-summary-header">'
        f'<div class="trip-summary-left">'
        f'<div class="trip-summary-dest">{e(destination.strip())}</div>'
        f'<div class="trip-summary-meta">{meta}</div>'
        f'<div class="trip-summary-tags">{pills}</div>'
        f'</div>'
        f'<div class="trip-plan-ctrl">'
        f'<div class="trip-modify-ctrl">'
        f'<button class="trip-modify-btn"{btn_disabled} onclick="showModifyConfirm()">'
        f'Modify Trip'
        f'</button>'
        f'<div class="trip-confirm-box" style="display:none">'
        f'<span class="trip-confirm-msg">This will take you back to the form to make changes.</span>'
        f'<div class="trip-confirm-btns">'
        f'<button class="trip-confirm-yes" onclick="triggerConfirmModify()">Yes, modify trip</button>'
        f'<button class="trip-confirm-no" onclick="hideModifyConfirm()">Cancel</button>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div class="trip-reset-ctrl">'
        f'<button class="trip-new-btn"{btn_disabled} onclick="showTripConfirm()">'
        f'Plan a New Trip'
        f'</button>'
        f'<div class="trip-confirm-box" style="display:none">'
        f'<span class="trip-confirm-msg">This will clear your current itinerary.</span>'
        f'<div class="trip-confirm-btns">'
        f'<button class="trip-confirm-yes" onclick="triggerConfirmReset()">Yes, start over</button>'
        f'<button class="trip-confirm-no" onclick="hideTripConfirm()">Cancel</button>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def _render_day(day, itinerary) -> str:
    e = _html.escape
    parts = [
        '<div class="itin-day">',
        '<div class="itin-day-header">',
        f'<span class="itin-day-label">Day {day.day_number} — {e(day.date)}</span>',
        f'<span class="itin-day-cost">${day.estimated_cost_usd:,.2f}</span>',
        '</div>',
    ]
    for venue in day.venues:
        h, m = divmod(venue.duration_minutes, 60)
        duration_str = f"{h}h {m}m" if h and m else f"{h}h" if h else f"{m}m"
        badge_cls = _BADGE_CLASS.get(venue.interest_category, "itin-badge-other")

        meta_parts = []
        if venue.location:
            if venue.location_type == "PLACE" and venue.geo_location:
                maps_query = f"{venue.geo_location.latitude},{venue.geo_location.longitude}"
            else:
                maps_query = venue.location
            maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(maps_query)}"
            meta_parts.append(
                f'<a class="itin-meta-link" href="{maps_url}" target="_blank" rel="noopener noreferrer">'
                f'\U0001f4cd {e(venue.location)}</a>'
            )
        if venue.url:
            meta_parts.append(f'<a class="itin-meta-link" href="{e(venue.url)}" target="_blank" rel="noopener noreferrer">\U0001f517 Website</a>')
        if venue.hours_of_operation:
            meta_parts.append(f'<span class="itin-meta-item">\U0001f550 {e(venue.hours_of_operation)}</span>')
        meta_html = f'<div class="itin-card-meta">{"".join(meta_parts)}</div>' if meta_parts else ""
        rating_html = (
            f'<span class="itin-card-rating">⭐ {venue.rating:.1f}</span>'
            if venue.rating is not None
            else ""
        )

        parts += [
            '<div class="itin-card">',
            '<div class="itin-card-top">',
            f'<span class="itin-card-name">{e(venue.name)}{rating_html}</span>',
            f'<span class="itin-badge {badge_cls}">{e(venue.interest_category)}</span>',
            '</div>',
            '<div class="itin-card-timing">',
            f'<span class="itin-timing-detail">{e(_to_12h(venue.start_time))} &nbsp;·&nbsp; {e(duration_str)}</span>',
            f'<span class="itin-card-cost">${venue.estimated_cost_usd:,.2f}</span>',
            '</div>',
            f'<p class="itin-card-desc">{e(venue.description)}</p>',
            meta_html,
            '</div>',
        ]
    parts.append('</div>')
    return "\n".join(parts)


_STEPPER_STAGES = [
    "Searching for venues",
    "Researching venues and estimating costs",
    "Building your itinerary",
]

_POLL_INTERVAL_SECONDS = 0.5


def _progress_html(active_index: int) -> str:
    e = _html.escape
    steps = []
    for i, label in enumerate(_STEPPER_STAGES):
        if i < active_index:
            state, icon = "done", '<span class="trip-progress-icon trip-progress-icon--done">✓</span>'
        elif i == active_index:
            state, icon = "active", '<span class="trip-progress-icon trip-progress-icon--spinner"></span>'
        else:
            state, icon = "pending", '<span class="trip-progress-icon trip-progress-icon--pending"></span>'
        steps.append(
            f'<div class="trip-progress-step trip-progress-step--{state}">'
            f'{icon}'
            f'<span class="trip-progress-label">{e(label)}</span>'
            f'</div>'
        )
    return f'<div class="trip-progress-wrap"><div class="trip-progress">{"".join(steps)}</div></div>'


def _itinerary_to_html(itinerary) -> str:
    days = itinerary.days
    mid = (len(days) + 1) // 2
    left = "\n".join(_render_day(d, itinerary) for d in days[:mid])
    right = "\n".join(_render_day(d, itinerary) for d in days[mid:])
    total = f'<div class="itin-total">Total estimated cost: <strong>${itinerary.estimated_cost_usd:,.2f}</strong></div>'
    grid = f'<div class="itin-days-grid"><div class="itin-col">{left}</div><div class="itin-col">{right}</div></div>'
    return f'<div class="itin-wrap">{total}{grid}</div>'


# Output order for on_schedule_itinerary:
#   [form_panel, results_panel, summary_html,
#    field_errors, interests_group,
#    destination, start_date, num_days, num_adults, num_children,
#    status_md, results_html]
#   + interest_components
#   + [progress_html, schedule_itinerary_btn]
# = 14 + n_interests items
# progress_html and schedule_itinerary_btn are appended last (after
# interest_components) so existing fixed-index positions never shift when
# they're added.
# The form's inputs (destination..num_children, interest_components) and the
# submit button are disabled right when the button is clicked (see the
# `.then()` chain below) and only re-enabled here on the validation-error
# path — every other path leaves the form hidden, so re-enabling doesn't
# matter there; on_confirm_reset/on_confirm_modify re-enable when the form
# is brought back into view.

async def on_schedule_itinerary(destination, start_date, num_days, num_adults, num_children, *interests):
    errors, err_fields = validate_form(destination, start_date, num_days, num_adults, num_children, list(interests))
    n_interests = len(interests)

    def field_cls(key: str) -> list[str]:
        return ["field-error"] if key in err_fields else []

    if not errors:
        is_valid = await asyncio.to_thread(is_valid_destination, destination.strip())
        if not is_valid:
            errors = ["Unknown destination"]
            err_fields = {"destination"}
        else:
            destination = capitalize_destination(destination.strip())

    if errors:
        error_messages = "".join(f"<li>{e}</li>" for e in errors)
        err_html = f"<ul style='margin:0; padding-left:1.2em; text-align:left'>{error_messages}</ul>"
        yield (
            [gr.update(visible=True)]                            # form_panel
            + [gr.update(visible=False)]                         # results_panel
            + [gr.update()]                                      # summary_html
            + [err_html]                                         # field_errors
            + [gr.update(elem_classes=["interests-outer"] + field_cls("interests"))]  # interests_group
            + [gr.update(elem_classes=field_cls("destination"), interactive=True)]
            + [gr.update(elem_classes=field_cls("start_date"), interactive=True)]
            + [gr.update(elem_classes=field_cls("num_days"), interactive=True)]
            + [gr.update(elem_classes=field_cls("num_adults"), interactive=True)]
            + [gr.update(elem_classes=field_cls("num_children"), interactive=True)]
            + [gr.update(value="")]                              # status_md
            + [gr.update(value="")]                              # results_html
            + [gr.update(interactive=True) for _ in range(n_interests)]
            + [gr.update(value="")]                              # progress_html
            + [gr.update(interactive=True)]                      # schedule_itinerary_btn
        )
        return

    summary_loading = _trip_summary_html(destination, start_date, num_days, num_adults, num_children, interests, button_enabled=False)
    summary_ready   = _trip_summary_html(destination, start_date, num_days, num_adults, num_children, interests, button_enabled=True)

    yield (
        [gr.update(visible=False)]                               # form_panel
        + [gr.update(visible=True)]                              # results_panel
        + [gr.update(value=summary_loading)]                     # summary_html (button disabled)
        + [gr.update(value="")]                                  # field_errors
        + [gr.update(elem_classes=["interests-outer"])]         # interests_group
        + [gr.update(value=destination, elem_classes=[])]       # destination (capitalized)
        + [gr.update(elem_classes=[]) for _ in range(4)]        # clear other field error classes
        + [gr.update(value="")]                                  # status_md
        + [gr.update(value="")]                                  # results_html
        + [gr.update() for _ in range(n_interests)]
        + [gr.update(value=_progress_html(0))]                   # progress_html
        + [gr.update()]                                          # schedule_itinerary_btn
    )

    selected_values = [item for group in interests for item in (group or [])]
    travel_info = TravelInfo(
        destination = destination,
        travel_dates = _travel_dates(start_date, num_days),
        num_adults = int(num_adults),
        num_children = int(num_children),
        interest_ids=[InterestId(v) for v in selected_values]
    )

    progress_queue: queue.Queue[tuple[str, int | None]] = queue.Queue()

    def _on_stage(event: str, count: int | None = None) -> None:
        progress_queue.put_nowait((event, count))

    try:
        itinerary_task = asyncio.create_task(
            asyncio.to_thread(create_itinerary, travel_info, on_stage=_on_stage)
        )
        active_index = 0
        while not itinerary_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(itinerary_task), timeout=_POLL_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                pass
            if itinerary_task.done():
                break

            try:
                while True:
                    event, _count = progress_queue.get_nowait()
                    if event == STAGE_SEARCH_COMPLETE:
                        active_index = 1
                    elif event == STAGE_PROCESSING_COMPLETE:
                        active_index = 2
            except queue.Empty:
                pass

            yield (
                [gr.update() for _ in range(10)]
                + [gr.update()]                                  # status_md
                + [gr.update()]                                  # results_html
                + [gr.update() for _ in range(n_interests)]
                + [gr.update(value=_progress_html(active_index))]  # progress_html
                + [gr.update()]                                  # schedule_itinerary_btn
            )
        itinerary = itinerary_task.result()
    except Exception as exc:
        yield (
            [gr.update()]                                        # form_panel
            + [gr.update()]                                      # results_panel
            + [gr.update(value=summary_ready)]                   # summary_html (button enabled)
            + [gr.update(value="")]                              # field_errors
            + [gr.update()]                                      # interests_group
            + [gr.update() for _ in range(5)]
            + [gr.update(value=f"**An error occurred:** {exc}")]
            + [gr.update(value="")]
            + [gr.update() for _ in range(n_interests)]
            + [gr.update(value="")]                              # progress_html
            + [gr.update()]                                      # schedule_itinerary_btn
        )
        return

    if not any(day.venues for day in itinerary.days):
        msg = "No itinerary could be generated. Try adjusting your interests or dates."
        yield (
            [gr.update()]                                        # form_panel
            + [gr.update()]                                      # results_panel
            + [gr.update(value=summary_ready)]                   # summary_html (button enabled)
            + [gr.update(value="")]                              # field_errors
            + [gr.update()]                                      # interests_group
            + [gr.update() for _ in range(5)]
            + [gr.update(value=f"**{msg}**")]
            + [gr.update(value="")]
            + [gr.update() for _ in range(n_interests)]
            + [gr.update(value="")]                              # progress_html
            + [gr.update()]                                      # schedule_itinerary_btn
        )
        return

    yield (
        [gr.update()]                                            # form_panel
        + [gr.update()]                                          # results_panel
        + [gr.update(value=summary_ready)]                       # summary_html (button enabled)
        + [gr.update(value="")]                                  # field_errors
        + [gr.update()]                                          # interests_group
        + [gr.update() for _ in range(5)]
        + [gr.update(value="")]                                  # status_md
        + [gr.update(value=_itinerary_to_html(itinerary))]      # results_html
        + [gr.update() for _ in range(n_interests)]
        + [gr.update(value="")]                                  # progress_html
        + [gr.update()]                                          # schedule_itinerary_btn
    )


def build_ui() -> gr.Blocks:

    with gr.Blocks(title="Trip Planner") as demo:
        gr.Markdown("# Trip Planner")
        gr.HTML('<div class="disclaimer">⚠️ This is a demo app only. It should not be used for planning an actual trip. Do so at your own peril.</div>', container=False)

        # ── Form phase (full-width, hidden once planning starts) ──
        with gr.Column(visible=True) as form_panel:
            with gr.Group(elem_classes=["form-section"]):
                with gr.Group(elem_classes=["trip-details"]):
                    with gr.Row():
                        destination = gr.Textbox(
                            label="Destination",
                            placeholder="e.g. Seattle, WA",
                            scale=2, min_width=0,
                            elem_id="destination-field",
                        )
                        start_date = gr.DateTime(
                            label="Start Date",
                            include_time=False,
                            scale=2, min_width=0,
                            elem_id="start-date-field",
                        )
                    with gr.Row():
                        num_days     = gr.Number(label="Days (1-4)", value=1, precision=0, scale=1, min_width=0)
                        num_adults   = gr.Number(label="Adults (1-10)",   value=1, precision=0, scale=1, min_width=0)
                        num_children = gr.Number(label="Children (0-10)", value=0, precision=0, scale=1, min_width=0)
                    field_errors = gr.HTML(value="", elem_id="field-errors")

                interest_components = []
                _category_by_id = {c.id: c for c in CATEGORIES}
                with gr.Group(elem_classes=["interests-outer"]) as interests_group:
                    gr.HTML(
                        '<label>Select from 2 to 4 interests</label>',
                        elem_classes=["interests-label"],
                    )
                    with gr.Column(elem_classes=["interests-columns"]):
                        for key in (CategoryId.FOOD, CategoryId.CULTURE, CategoryId.OUTDOORS, CategoryId.ENTERTAINMENT, CategoryId.OTHER):
                            interest_components.append(gr.CheckboxGroup(
                                choices=choices_for(key),
                                label=_category_by_id[key].label,
                                elem_classes=["interest-category"],
                            ))

            schedule_itinerary_btn = gr.Button("Schedule Itinerary", variant="primary")

        # ── Results phase (full-width, shown once planning starts) ──
        with gr.Column(visible=False, elem_classes=["results-panel"]) as results_panel:
            # summary_html contains the trip card and "Plan a New Trip" button as HTML.
            # Clicking "Yes, start over" in that inline confirmation calls
            # triggerConfirmReset() (HEAD JS), which clicks this hidden Gradio button.
            summary_html = gr.HTML(container=False, elem_classes=["trip-summary-html"])
            confirm_reset_btn = gr.Button(
                "",
                elem_id="confirm-reset-trigger",
                elem_classes=["hidden-trigger"],
            )
            # Clicking "Yes, modify trip" in the inline confirmation calls
            # triggerConfirmModify() (HEAD JS), which clicks this hidden Gradio button.
            confirm_modify_btn = gr.Button(
                "",
                elem_id="confirm-modify-trigger",
                elem_classes=["hidden-trigger"],
            )
            # Always empty in practice — kept in the output list of every handler below,
            # but taken out of flow (like the confirm buttons) so it doesn't add gap.
            status_md    = gr.Markdown(elem_classes=["hidden-trigger"])
            results_html = gr.HTML(container=False, elem_classes=["results-html"])
            progress_html = gr.HTML(container=False)

        n_interests = len(interest_components)
        form_inputs = [destination, start_date, num_days, num_adults, num_children] + interest_components

        # ── Schedule itinerary ────────────────────────────────────
        # Disable every form input (and the button itself) the instant the
        # button is clicked, via a queue=False fn that runs ahead of the
        # (queued, potentially slow) itinerary-generating handler. Re-enabling
        # happens in on_schedule_itinerary's validation-error path and in
        # on_confirm_reset/on_confirm_modify, which bring the form back into view.
        schedule_itinerary_btn.click(
            fn=lambda: [gr.update(interactive=False) for _ in range(len(form_inputs) + 1)],
            inputs=None,
            outputs=form_inputs + [schedule_itinerary_btn],
            queue=False,
        ).then(
            fn=on_schedule_itinerary,
            inputs=[destination, start_date, num_days, num_adults, num_children] + interest_components,
            outputs=[
                form_panel, results_panel, summary_html,
                field_errors, interests_group,
                destination, start_date, num_days, num_adults, num_children,
                status_md, results_html,
            ] + interest_components + [progress_html, schedule_itinerary_btn],
            show_progress="hidden",
        )

        # ── "Yes, start over" in the HTML confirmation → reset ───────
        def on_confirm_reset():
            return (
                [gr.update(visible=True)]                 # form_panel
                + [gr.update(visible=False)]              # results_panel
                + [gr.update(value="")]                   # summary_html
                + [gr.update(value="")]                   # field_errors
                + [gr.update(elem_classes=["interests-outer"])]  # interests_group
                + [gr.update(value="", elem_classes=[], interactive=True)]  # destination
                + [gr.update(value=None, interactive=True)]                 # start_date
                + [gr.update(value=1, interactive=True)]                    # num_days
                + [gr.update(value=1, interactive=True)]                    # num_adults
                + [gr.update(value=0, interactive=True)]                    # num_children
                + [gr.update(value="")]                   # status_md
                + [gr.update(value="")]                   # results_html
                + [gr.update(value=[], interactive=True) for _ in range(n_interests)]
                + [gr.update(value="")]                   # progress_html
                + [gr.update(interactive=True)]           # schedule_itinerary_btn
            )

        confirm_reset_btn.click(
            fn=on_confirm_reset,
            outputs=[
                form_panel, results_panel, summary_html,
                field_errors, interests_group,
                destination, start_date, num_days, num_adults, num_children,
                status_md, results_html,
            ] + interest_components + [progress_html, schedule_itinerary_btn],
        )

        # ── "Yes, modify trip" in the HTML confirmation → back to form ───
        # Unlike on_confirm_reset, field values are left untouched so the
        # form reappears pre-filled with the trip currently on screen.
        def on_confirm_modify():
            return (
                [gr.update(visible=True)]   # form_panel
                + [gr.update(visible=False)]  # results_panel
                + [gr.update(interactive=True) for _ in range(len(form_inputs) + 1)]
            )

        confirm_modify_btn.click(
            fn=on_confirm_modify,
            outputs=[form_panel, results_panel] + form_inputs + [schedule_itinerary_btn],
        )

        gr.HTML(
            f'<div class="page-footer">© {datetime.now().year} <a href="https://donaldbarre.com" target="_blank" rel="noopener noreferrer">Donald Barre</a> All rights reserved.</div>',
            container=False,
        )

    return demo


demo = build_ui()


def launch():
    demo.launch(css=CSS, head=HEAD)


if __name__ == "__main__":
    launch()
