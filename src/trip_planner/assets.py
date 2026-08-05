CSS = """
.form-section {
    background: var(--block-background-fill);
    border: 1px solid rgba(128,128,128,0.3) !important;
    border-radius: 8px !important;
    padding: 0 !important;
    gap: 0 !important;
    --block-title-text-color: #60a5fa;
}
.trip-details {
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
}
.form-section div.svelte-d5xbca {
    gap: 0 !important;
    background: transparent !important;
}
.form-section div.svelte-1p9262q {
    gap: 0 !important;
    background: transparent !important;
}
.interests-outer {
    padding: 0px !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
.interests-label {
    background: var(--block-background-fill);
    padding: 0 !important;
}
.interests-outer.field-error {
    border: 1px solid red !important;
    border-radius: 8px;
}
.form-section span.svelte-jdcl7l,
.interests-label label {
    color: #60a5fa !important;
}
.interests-outer span.svelte-jdcl7l {
    color: #4ade80 !important;
}
.field-error input,
.field-error textarea {
    border: 1px solid red !important;
}
.interests-columns .form {
    display: block !important;
    column-width: 220px;
    column-gap: 32px;
}
.interest-category {
    break-inside: avoid;
    -webkit-column-break-inside: avoid;
}
.interest-category [data-testid="checkbox-group"] label {
    border: none !important;
    box-shadow: none !important;
    padding: 4px 2px !important;
}
.interest-category [data-testid="checkbox-group"] {
    flex-direction: column !important;
}
#field-errors * {
    color: #FF6B6B !important;
}

/* ── Trip summary card ─────────────────────────────────── */
.results-panel { gap: 8px !important; }
.trip-summary-html .html-container { padding-bottom: 0 !important; }
.results-html .html-container { padding-top: 0 !important; }
.trip-summary {
    background: var(--block-background-fill);
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 10px;
    padding: 18px 22px;
}
.trip-summary-header {
    display: flex;
    align-items: flex-start;
    gap: 16px;
}
.trip-summary-left { flex: 1; min-width: 0; }
.trip-summary-dest {
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 6px;
}
.trip-summary-meta {
    font-size: 0.85rem;
    opacity: 0.65;
    margin-bottom: 12px;
}
.trip-summary-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.trip-summary-tag {
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 999px;
    background: rgba(96,165,250,0.15);
    color: #60a5fa;
    border: 1px solid rgba(96,165,250,0.3);
}
.trip-summary-tag--empty { opacity: 0.5; }

/* ── Plan a New Trip button + inline confirmation ───────── */
.trip-plan-ctrl {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
}
.trip-new-btn {
    background: #16a34a;
    color: #fff;
    border: 1px solid #16a34a;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 0.875rem;
    font-weight: 600;
    line-height: 1;
    cursor: pointer;
    white-space: nowrap;
}
.trip-new-btn:hover:not(:disabled) { background: #15803d; border-color: #15803d; }
.trip-new-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.trip-modify-btn {
    background: #2563eb;
    color: #fff;
    border: 1px solid #2563eb;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 0.875rem;
    font-weight: 600;
    line-height: 1;
    cursor: pointer;
    white-space: nowrap;
}
.trip-modify-btn:hover:not(:disabled) { background: #1d4ed8; border-color: #1d4ed8; }
.trip-modify-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.trip-modify-ctrl,
.trip-reset-ctrl {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}
.trip-confirm-box {
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
    background: rgba(239,68,68,0.07);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 8px;
    padding: 10px 14px;
    text-align: right;
}
.trip-confirm-msg {
    display: block;
    font-size: 0.82rem;
    opacity: 0.8;
    margin-bottom: 8px;
}
.trip-confirm-btns {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}
.trip-confirm-yes {
    background: #ef4444;
    color: #fff;
    border: 1px solid #ef4444;
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
}
.trip-confirm-yes:hover { background: #dc2626; border-color: #dc2626; }
.trip-confirm-no {
    background: transparent;
    color: inherit;
    border: 1px solid rgba(128,128,128,0.35);
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 0.82rem;
    cursor: pointer;
    white-space: nowrap;
}
.trip-confirm-no:hover { background: rgba(128,128,128,0.1); }

/* Hidden Gradio trigger — off-screen but NOT display:none so Gradio processes the click */
.hidden-trigger {
    position: fixed !important;
    left: -9999px !important;
    top: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    pointer-events: none !important;
}

/* ── Itinerary display ─────────────────────────────────── */
.itin-wrap { padding: 0 0 16px; }
.itin-total {
    font-size: 1rem;
    font-weight: 600;
    color: #4ade80;
    padding: 10px 0 20px;
}
.itin-days-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 28px;
    align-items: start;
}
@media (min-width: 900px) {
    .itin-days-grid {
        grid-template-columns: 1fr 1fr;
    }
}
.itin-day { margin-bottom: 28px; }
.itin-day-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding-bottom: 8px;
    border-bottom: 2px solid #60a5fa;
    margin-bottom: 12px;
}
.itin-day-label { font-weight: 700; font-size: 1.05rem; color: #60a5fa; }
.itin-day-cost {
    font-size: 0.95rem;
    font-weight: 700;
    color: #4ade80;
    background: rgba(74, 222, 128, 0.12);
    padding: 3px 10px;
    border-radius: 999px;
}
.itin-card {
    background: var(--block-background-fill);
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.07);
}
.itin-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 4px;
}
.itin-card-name { font-weight: 700; font-size: 0.975rem; line-height: 1.3; }
.itin-card-rating { font-weight: 500; font-size: 0.84rem; opacity: 0.75; margin-left: 6px; white-space: nowrap; }
.itin-badge {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #fff;
    padding: 2px 8px;
    border-radius: 999px;
    white-space: nowrap;
    flex-shrink: 0;
    margin-top: 2px;
}
.itin-badge-food          { background: #d97706; }
.itin-badge-culture       { background: #7c3aed; }
.itin-badge-outdoors      { background: #16a34a; }
.itin-badge-entertainment { background: #db2777; }
.itin-badge-other         { background: #6b7280; }
.itin-card-timing {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.itin-timing-detail { font-size: 0.84rem; opacity: 0.62; }
.itin-card-cost { font-size: 0.88rem; font-weight: 600; color: #4ade80; }
.itin-card-desc {
    font-size: 0.865rem;
    line-height: 1.55;
    opacity: 0.78;
    margin: 0 0 6px;
}
.itin-card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 14px;
    padding-top: 8px;
    border-top: 1px solid rgba(128,128,128,0.15);
}
.itin-meta-item { font-size: 0.79rem; opacity: 0.58; }
.itin-meta-link { font-size: 0.79rem; color: #60a5fa; text-decoration: none; }
.itin-meta-link:hover { text-decoration: underline; }

/* ── Itinerary generation progress stepper ─────────────── */
.trip-progress-wrap { display: flex; justify-content: center; padding: 40px 0; }
.trip-progress {
    display: flex;
    flex-direction: column;
    background: var(--block-background-fill);
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 10px;
    padding: 24px 32px;
    min-width: 280px;
}
.trip-progress-step { display: flex; align-items: center; gap: 14px; position: relative; padding: 10px 0; }
.trip-progress-step:not(:last-child)::after {
    content: ""; position: absolute; left: 11px; top: 34px; bottom: -10px; width: 2px;
    background: rgba(128,128,128,0.25);
}
.trip-progress-step--done:not(:last-child)::after { background: #4ade80; }
.trip-progress-icon {
    flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; z-index: 1;
}
.trip-progress-icon--done { background: #4ade80; color: #0b1a10; }
.trip-progress-icon--pending { border: 2px solid rgba(128,128,128,0.35); background: transparent; }
.trip-progress-icon--spinner {
    border: 2px solid rgba(96,165,250,0.25); border-top-color: #60a5fa;
    animation: trip-progress-spin 0.8s linear infinite;
}
@keyframes trip-progress-spin { to { transform: rotate(360deg); } }
.trip-progress-label { font-size: 0.92rem; opacity: 0.6; }
.trip-progress-step--active .trip-progress-label { opacity: 1; font-weight: 600; color: #60a5fa; }
.trip-progress-step--done .trip-progress-label { opacity: 0.85; }

/* ── Disclaimer banner ─────────────────────────────────── */
.disclaimer {
    background: rgba(234,179,8,0.1);
    border: 1px solid rgba(234,179,8,0.45);
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 16px;
    font-size: 0.85rem;
    color: #ca8a04;
    text-align: center;
    letter-spacing: 0.01em;
}

/* ── Page footer ───────────────────────────────────────── */
.page-footer {
    text-align: center;
    font-size: 0.78rem;
    opacity: 0.45;
    padding: 24px 0 8px;
}
.page-footer a {
    font-weight: 600;
    font-size: 0.95rem;
}
"""

HEAD = """
<script>
function showTripConfirm() {
    var ctrl = document.querySelector('.trip-reset-ctrl');
    if (!ctrl) return;
    ctrl.querySelector('.trip-new-btn').style.display = 'none';
    var box = ctrl.querySelector('.trip-confirm-box');
    box.style.display = 'flex';
}
function hideTripConfirm() {
    var ctrl = document.querySelector('.trip-reset-ctrl');
    if (!ctrl) return;
    ctrl.querySelector('.trip-new-btn').style.display = '';
    ctrl.querySelector('.trip-confirm-box').style.display = 'none';
}
function triggerConfirmReset() {
    hideTripConfirm();
    var el = document.getElementById('confirm-reset-trigger');
    if (!el) return;
    // elem_id may land on the <button> itself or on a wrapper div — handle both
    var b = el.tagName === 'BUTTON' ? el : el.querySelector('button');
    if (b) b.click();
}
function showModifyConfirm() {
    var ctrl = document.querySelector('.trip-modify-ctrl');
    if (!ctrl) return;
    ctrl.querySelector('.trip-modify-btn').style.display = 'none';
    var box = ctrl.querySelector('.trip-confirm-box');
    box.style.display = 'flex';
}
function hideModifyConfirm() {
    var ctrl = document.querySelector('.trip-modify-ctrl');
    if (!ctrl) return;
    ctrl.querySelector('.trip-modify-btn').style.display = '';
    ctrl.querySelector('.trip-confirm-box').style.display = 'none';
}
function triggerConfirmModify() {
    hideModifyConfirm();
    var el = document.getElementById('confirm-modify-trigger');
    if (!el) return;
    // elem_id may land on the <button> itself or on a wrapper div — handle both
    var b = el.tagName === 'BUTTON' ? el : el.querySelector('button');
    if (b) b.click();
}
</script>
<script>
(function () {
    function patch() {
        const el = document.getElementById("start-date-field");
        if (!el) return;
        el.querySelectorAll("input").forEach(function (input) {
            input.setAttribute("autocomplete", "off");
            input.setAttribute("data-form-type", "other");
            input.setAttribute("data-lpignore", "true");
        });
    }

    function setupCloseOnSelect() {
        document.addEventListener('click', function (e) {
            var el = document.getElementById("start-date-field");
            if (!el) return;
            var daysGrid = el.querySelector('.days');
            if (!daysGrid || !daysGrid.contains(e.target)) return;
            // Day cell clicked — auto-click the Done button
            setTimeout(function () {
                var actionsRight = el.querySelector('.picker-actions-right');
                if (!actionsRight) return;
                var doneBtn = Array.from(actionsRight.querySelectorAll('button')).find(function (b) {
                    return b.textContent.trim() === 'Done';
                });
                if (doneBtn) doneBtn.click();
            }, 0);
        });
    }

    function init() {
        patch();
        setupCloseOnSelect();
        // Keep observing so re-renders after Gradio state changes are also patched.
        new MutationObserver(patch).observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    // Re-patch after bfcache restores (back-forward cache used on some refreshes).
    window.addEventListener("pageshow", function (e) {
        if (e.persisted) patch();
    });
}());
</script>
"""
