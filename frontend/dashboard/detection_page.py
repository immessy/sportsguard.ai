# dashboard/detection_page.py
# ─────────────────────────────────────────────────────────────────────────────
# Live detection feed page.
#
# Data source:
#   - load_detections() → GET /api/scan (or MOCK_DETECTIONS)
# Loader passed via session_state from app.py.
# get_sim_detection()  → adds one new row for the demo Simulate button.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
from branding import COLORS, page_header, risk_badge

STATUS_DOT_COLORS = {
    "danger":  "#EF4444",
    "medium":  "#F97316",
    "success": "#22C55E",
    "info":    "#3B82F6",
}

ACTION_BTNS = {
    "CRITICAL": '<span class="btn-takedown">Take Down</span> <span class="btn-review">Review</span> <span class="btn-ignore">Ignore</span>',
    "MEDIUM":   '<span class="btn-review">Review</span> <span class="btn-ignore">Ignore</span>',
    "LOW":      '<span class="btn-ignore">Ignore</span>',
}


def _score_to_risk(score: int) -> str:
    if score >= 8:   return "CRITICAL"
    if score >= 5:   return "MEDIUM"
    return "LOW"


def _score_to_status(score: int) -> tuple:
    if score >= 8:   return "Live Now",   "danger"
    if score >= 5:   return "Under Review","medium"
    return "Whitelisted", "success"


def _build_display_rows(raw_detections: list) -> list:
    """Convert raw API detection dicts into display-ready dicts."""
    rows = []
    for d in raw_detections:
        score  = d.get("gemini_risk_score", 5)
        risk   = _score_to_risk(score)
        status, dot = _score_to_status(score)
        url    = d.get("source_url", "")
        ts_raw = d.get("detected_at", "")
        ts     = ts_raw.split(" ")[-1][:8] if " " in ts_raw else ts_raw[:8]
        classification = d.get("gemini_classification", "")
        content_labels = {
            "Piracy":        "Live Stream / Raw Reupload",
            "Transformative":"Highlight Clip / Edited",
            "Meme":          "Fan Reaction / Meme",
        }
        rows.append({
            "ts":          ts,
            "source_url":  url[:32] + "..." if len(url) > 32 else url,
            "source_id":   f"ID: {d.get('id', '??')}",
            "content":     content_labels.get(classification, classification),
            "risk":        risk,
            "status":      status,
            "status_dot":  dot,
            "classification": classification,
        })
    return rows


def render_detection_table(rows: list):
    rows_html = ""
    for d in rows:
        dot_c   = STATUS_DOT_COLORS.get(d["status_dot"], COLORS["text_muted"])
        risk_b  = risk_badge(d["risk"])
        actions = ACTION_BTNS.get(d["risk"], "")

        rows_html += f"""
        <tr>
            <td style="font-family:'JetBrains Mono',monospace;font-size:11px;
                       color:{COLORS['text_secondary']};">{d['ts']}</td>
            <td>
                <div style="font-size:12px;color:{COLORS['text_primary']};
                            font-weight:500;">{d['source_url']}</div>
                <div style="font-size:10px;color:{COLORS['text_muted']};
                            font-family:'JetBrains Mono',monospace;">{d['source_id']}</div>
            </td>
            <td><div style="font-size:12px;color:{COLORS['text_secondary']};
                            max-width:140px;">{d['content']}</div></td>
            <td>{risk_b}</td>
            <td>
                <div style="display:flex;align-items:center;gap:5px;">
                    <div style="width:6px;height:6px;background:{dot_c};
                                border-radius:50%;flex-shrink:0;"></div>
                    <span style="font-size:11px;color:{COLORS['text_secondary']};">
                        {d['status']}</span>
                </div>
            </td>
            <td style="white-space:nowrap">{actions}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="sg-table" style="min-width:700px;">
        <thead><tr>
            <th>Timestamp</th><th>Source / URL</th>
            <th>Content Match</th><th>Risk Level</th>
            <th>Status</th><th>Actions</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)


def render():
    page_header(
        "Live Detection Feed",
        subtitle="Real-time intellectual property monitoring across global platforms.",
        show_active=False,
    )

    # ── Load detections via api_client ────────────────────────────────────────
    # TODO Phase 3 (done): load_detections already calls real API when MOCK_MODE=False
    load_detections   = st.session_state.get("load_detections",   lambda: {"detections": []})
    get_sim_detection = st.session_state.get("get_sim_detection", lambda: {})

    # On first render, populate session list
    if st.session_state.get("detections_list") is None:
        raw  = load_detections()
        rows = _build_display_rows(raw.get("detections", []))
        st.session_state["detections_list"] = rows

    # ── Top metric pills ──────────────────────────────────────────────────────
    all_rows    = st.session_state["detections_list"]
    total_crit  = sum(1 for r in all_rows if r["risk"] == "CRITICAL")

    st.markdown(f"""
    <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
        <div style="background:{COLORS['bg_secondary']};border:1px solid {COLORS['border']};
                    border-radius:6px;padding:8px 18px;display:flex;align-items:center;gap:8px;">
            <span style="font-size:10px;color:{COLORS['text_muted']};
                         letter-spacing:.1em;text-transform:uppercase;">Scanned Today</span>
            <span style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;
                         color:{COLORS['text_primary']};">1,247</span>
        </div>
        <div style="background:{COLORS['bg_secondary']};border:1px solid {COLORS['border']};
                    border-radius:6px;padding:8px 18px;display:flex;align-items:center;gap:8px;">
            <span style="font-size:10px;color:{COLORS['text_muted']};
                         letter-spacing:.1em;text-transform:uppercase;">Flagged</span>
            <span style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;
                         color:{COLORS['medium']};">{len(all_rows)}</span>
        </div>
        <div style="background:{COLORS['bg_secondary']};
                    border:1px solid rgba(239,68,68,0.25);
                    border-radius:6px;padding:8px 18px;
                    display:flex;align-items:center;gap:8px;">
            <span style="font-size:10px;color:{COLORS['text_muted']};
                         letter-spacing:.1em;text-transform:uppercase;">High Risk</span>
            <span style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;
                         color:{COLORS['danger']};">{total_crit}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filter + Refresh ──────────────────────────────────────────────────────
    f_col, _, btn_col = st.columns([2, 4, 1.5])
    with f_col:
        risk_filter = st.selectbox(
            "",
            ["All Risk Levels", "🔴 Critical", "🟡 Medium", "🟢 Low"],
            key="risk_filter",
            label_visibility="collapsed",
        )
    with btn_col:
        if st.button("🔄  Refresh Scan", key="refresh_btn"):
            # Re-fetch from API (or mock)
            raw  = load_detections()
            rows = _build_display_rows(raw.get("detections", []))
            st.session_state["detections_list"] = rows
            st.toast("⚡ Scan complete.", icon="🔍")
            st.rerun()

    st.markdown(f"""
    <div style="font-size:11px;color:{COLORS['text_muted']};margin:-8px 0 12px 0;
                padding-left:2px;">Showing results for last 24 hours</div>
    """, unsafe_allow_html=True)

    # ── Apply filter ──────────────────────────────────────────────────────────
    data = st.session_state["detections_list"]
    if risk_filter == "🔴 Critical":
        data = [d for d in data if d["risk"] == "CRITICAL"]
    elif risk_filter == "🟡 Medium":
        data = [d for d in data if d["risk"] == "MEDIUM"]
    elif risk_filter == "🟢 Low":
        data = [d for d in data if d["risk"] == "LOW"]

    # ── Table ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="sg-panel" style="padding:0;overflow:hidden;">', unsafe_allow_html=True)
    render_detection_table(data)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Simulate Detection (demo button) ──────────────────────────────────────
    st.markdown(f"""
    <div style="border:1.5px dashed rgba(245,158,11,0.3);border-radius:8px;padding:2px;">
    """, unsafe_allow_html=True)

    if st.button("⚠️  SIMULATE DETECTION", key="simulate_btn"):
        # get_sim_detection returns a fresh API-schema detection dict
        new_raw  = get_sim_detection()
        new_rows = _build_display_rows([new_raw])
        st.session_state["detections_list"] = new_rows + st.session_state["detections_list"]
        st.balloons()
        st.toast("🚨 New CRITICAL: t.me/ipl_leaks_channel", icon="🔴")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;margin-top:10px;">
        <span style="font-size:10px;color:{COLORS['text_muted']};">
            ⚙ Neural engine scanning 18,200 requests/sec across 24 nodes
        </span>
    </div>
    """, unsafe_allow_html=True)