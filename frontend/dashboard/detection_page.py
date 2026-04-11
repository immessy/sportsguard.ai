import streamlit as st
import plotly.graph_objects as go
import time
from branding import COLORS, page_header, risk_badge

# ─── Mock Data ────────────────────────────────────────────────────────────────
BASE_DETECTIONS = [
    {
        "ts":          "14:27:05",
        "source_url":  "twitter.com/live_sports_vids",
        "source_id":   "ID: TW-188279",
        "content":     "NBA Finals: G4 Stream",
        "risk":        "CRITICAL",
        "status":      "Live Now",
        "status_dot":  "danger",
    },
    {
        "ts":          "14:18:40",
        "source_url":  "instagram.com/reels/XyZ88...",
        "source_id":   "ID: IG-22481",
        "content":     "Player Highlight Clips",
        "risk":        "MEDIUM",
        "status":      "Processed",
        "status_dot":  "medium",
    },
    {
        "ts":          "14:05:12",
        "source_url":  "vimeo.com/v/private-88712",
        "source_id":   "ID: VM-90823",
        "content":     "Full Game Replay (E12)",
        "risk":        "CRITICAL",
        "status":      "Live Now",
        "status_dot":  "danger",
    },
    {
        "ts":          "13:58:00",
        "source_url":  "tiktok.com/@sports_fan_3",
        "source_id":   "ID: TK-44091",
        "content":     "Fan Reaction Video",
        "risk":        "LOW",
        "status":      "Whitelisted",
        "status_dot":  "success",
    },
    {
        "ts":          "13:45:33",
        "source_url":  "iptv-leak-stream.biz",
        "source_id":   "ID: IP-77033",
        "content":     "Unofficial stream roundup",
        "risk":        "CRITICAL",
        "status":      "Live Now",
        "status_dot":  "danger",
    },
    {
        "ts":          "13:30:10",
        "source_url":  "facebook.com/watch/live...",
        "source_id":   "ID: FB-77811",
        "content":     "Screen-recorded Playback",
        "risk":        "MEDIUM",
        "status":      "Under Review",
        "status_dot":  "medium",
    },
]

SIMULATED_DETECTION = {
    "ts":          "14:29:01",
    "source_url":  "t.me/ipl_leaks_channel",
    "source_id":   "ID: TG-99201",
    "content":     "IPL Match 42 Full Stream",
    "risk":        "CRITICAL",
    "status":      "Live Now",
    "status_dot":  "danger",
}

STATUS_DOT_COLORS = {
    "danger":  "#C24A3E",
    "medium":  "#C17F3A",
    "success": "#7D9A6E",
    "info":    "#9C8B7C",
}

ACTION_BTNS = {
    "CRITICAL": '<span class="btn-takedown">Take Down</span> <span class="btn-review">Review</span> <span class="btn-ignore">Ignore</span>',
    "MEDIUM":   '<span class="btn-review">Review</span> <span class="btn-ignore">Ignore</span>',
    "LOW":      '<span class="btn-ignore">Ignore</span>',
}


def _risk_filter_color(risk):
    return {
        "CRITICAL": COLORS["danger"],
        "MEDIUM":   COLORS["medium"],
        "LOW":      COLORS["success"],
    }.get(risk, COLORS["text_secondary"])


def render_detection_table(detections):
    rows_html = ""
    for d in detections:
        dot_c   = STATUS_DOT_COLORS.get(d["status_dot"], COLORS["text_muted"])
        risk_b  = risk_badge(d["risk"])
        actions = ACTION_BTNS.get(d["risk"], "")

        rows_html += f"""
        <tr>
            <td style="font-family:'Courier Prime','Courier New',monospace;font-size:11px;
                       color:{COLORS['text_secondary']};">{d['ts']}</td>
            <td>
                <div style="font-size:12px;color:{COLORS['text_primary']};
                            font-weight:500;">{d['source_url']}</div>
                <div style="font-size:10px;color:{COLORS['text_muted']};
                            font-family:'Courier Prime','Courier New',monospace;">{d['source_id']}</div>
            </td>
            <td>
                <div style="font-size:12px;color:{COLORS['text_secondary']};
                            max-width:140px;">{d['content']}</div>
            </td>
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
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Source / URL</th>
                <th>Content Match</th>
                <th>Risk Level</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
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

    # ── Top metric pills ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
        <div style="
            background:{COLORS['bg_secondary']};
            border:1px solid {COLORS['border']};
            border-radius:6px;padding:8px 18px;
            display:flex;align-items:center;gap:8px;
        ">
            <span style="font-size:10px;color:{COLORS['text_muted']};
                         letter-spacing:.1em;text-transform:uppercase;">Scanned Today</span>
            <span style="font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;
                         font-weight:700;color:{COLORS['text_primary']};">1,247</span>
        </div>
        <div style="
            background:{COLORS['bg_secondary']};
            border:1px solid {COLORS['border']};
            border-radius:6px;padding:8px 18px;
            display:flex;align-items:center;gap:8px;
        ">
            <span style="font-size:10px;color:{COLORS['text_muted']};
                         letter-spacing:.1em;text-transform:uppercase;">Flagged</span>
            <span style="font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;
                         font-weight:700;color:{COLORS['medium']};">23</span>
        </div>
        <div style="
            background:{COLORS['bg_secondary']};
            border:1px solid rgba(239,68,68,0.25);
            border-radius:6px;padding:8px 18px;
            display:flex;align-items:center;gap:8px;
        ">
            <span style="font-size:10px;color:{COLORS['text_muted']};
                         letter-spacing:.1em;text-transform:uppercase;">High Risk</span>
            <span style="font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;
                         font-weight:700;color:{COLORS['danger']};">8</span>
        </div>
        <div style="margin-left:auto;display:flex;align-items:center;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filter row ────────────────────────────────────────────────────────────
    f_col, _, btn_col = st.columns([2, 4, 1.5])
    with f_col:
        risk_filter = st.selectbox(
            "",
            ["All Risk Levels", "🔴 Critical", "🟡 Medium", "🟢 Low"],
            key="risk_filter",
            label_visibility="collapsed",
        )
    with btn_col:
        refresh = st.button("🔄  Refresh Scan", key="refresh_btn")
        if refresh:
            st.toast("⚡ Scanning 3 platforms...", icon="🔍")

    st.markdown(f"""
    <div style="font-size:11px;color:{COLORS['text_muted']};
                margin:-8px 0 12px 0;padding-left:2px;">
        Showing results for last 24 hours
    </div>
    """, unsafe_allow_html=True)

    # ── Table ─────────────────────────────────────────────────────────────────
    # Build dataset based on filter
    if "detections_list" not in st.session_state:
        st.session_state["detections_list"] = BASE_DETECTIONS.copy()

    data = st.session_state["detections_list"]
    if risk_filter == "🔴 Critical":
        data = [d for d in data if d["risk"] == "CRITICAL"]
    elif risk_filter == "🟡 Medium":
        data = [d for d in data if d["risk"] == "MEDIUM"]
    elif risk_filter == "🟢 Low":
        data = [d for d in data if d["risk"] == "LOW"]

    st.markdown(f'<div class="sg-panel" style="padding:0;overflow:hidden;">', unsafe_allow_html=True)
    render_detection_table(data)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Simulate Detection CTA ────────────────────────────────────────────────
    st.markdown(f"""
    <div style="
        border: 1.5px dashed rgba(143, 46, 46, 0.38);
        border-radius: 8px;
        padding: 2px;
    ">
    """, unsafe_allow_html=True)

    if st.button("Add practice detection", key="simulate_btn"):
        new = SIMULATED_DETECTION.copy()
        st.session_state["detections_list"] = [new] + st.session_state["detections_list"]
        st.balloons()
        st.toast("🚨 New CRITICAL detection: t.me/ipl_leaks_channel", icon="🔴")
        time.sleep(0.5)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;margin-top:10px;">
        <span style="font-size:10px;color:{COLORS['text_muted']};">
            Hand-tallied checks against the fingerprint vault (demo cadence)
        </span>
    </div>
    """, unsafe_allow_html=True)