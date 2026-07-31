from trip_planner.assets import CSS, HEAD


def test_css_is_nonempty_string():
    assert isinstance(CSS, str)
    assert CSS.strip()


def test_head_is_nonempty_string():
    assert isinstance(HEAD, str)
    assert HEAD.strip()


def test_head_wraps_content_in_script_tags():
    assert HEAD.count("<script>") == HEAD.count("</script>")
    assert HEAD.count("<script>") >= 1


def test_head_defines_functions_wired_to_app_onclick_handlers():
    # app.py's summary HTML calls these via onclick="..."; if renamed here the
    # buttons in the rendered UI silently do nothing.
    assert "function showTripConfirm()" in HEAD
    assert "function hideTripConfirm()" in HEAD
    assert "function triggerConfirmReset()" in HEAD


def test_head_targets_elem_ids_used_by_app():
    # app.py sets these elem_ids on live components; the JS must target the same ids.
    assert 'getElementById("start-date-field")' in HEAD
    assert "getElementById('confirm-reset-trigger')" in HEAD


def test_css_defines_classes_referenced_by_app_html():
    # Classes app.py emits directly in f-string HTML (not via elem_classes=[...]),
    # so a typo here or there silently drops the styling.
    expected_classes = [
        ".trip-summary",
        ".trip-summary-dest",
        ".trip-summary-meta",
        ".trip-summary-tags",
        ".trip-summary-tag",
        ".trip-plan-ctrl",
        ".trip-new-btn",
        ".trip-confirm-box",
        ".trip-confirm-msg",
        ".trip-confirm-btns",
        ".trip-confirm-yes",
        ".trip-confirm-no",
        ".itin-wrap",
        ".itin-total",
        ".itin-days-grid",
        ".itin-day",
        ".itin-day-header",
        ".itin-day-label",
        ".itin-day-cost",
        ".itin-card",
        ".itin-card-top",
        ".itin-card-name",
        ".itin-badge",
        ".itin-badge-food",
        ".itin-badge-culture",
        ".itin-badge-outdoors",
        ".itin-badge-entertainment",
        ".itin-badge-other",
        ".itin-card-timing",
        ".itin-timing-detail",
        ".itin-card-cost",
        ".itin-card-desc",
        ".itin-card-meta",
        ".itin-meta-item",
        ".itin-meta-link",
        ".disclaimer",
        ".page-footer",
        ".field-error",
        ".hidden-trigger",
    ]
    for css_class in expected_classes:
        assert css_class in CSS, f"expected {css_class} to be defined in CSS"
