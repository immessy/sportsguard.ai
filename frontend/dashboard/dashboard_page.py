import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from branding import (
    COLORS, metric_card, section_header,
    page_header, risk_badge
)

# ─── Mock Data ────────────────────────────────────────────────────────────────
MOCK_DETECTIONS = [
    {
        "source_url":   "stream.pro/ipl-live-m42",
        "match_pct":    99.8,
        "classification": "Piracy",
        "risk":         "CRITICAL",
        "detected_at":  "14:22:01",
    },
    {
        "source_url":   "youtube.com/v=xk2mP9qL",
        "match_pct":    84.2,
        "classification": "Transformative",
        "risk":         "MEDIUM",
        "detected_at":  "14:21:44",
    },
    {
        "source_url":   "twitter.com/fan_cricket_09",
        "match_pct":    42.1,
        "classification": "Meme",
        "risk":         "LOW",
        "detected_at":  "14:20:12",
    },
    {
        "source_url":   "iptv-portal.net/channel/ipl",
        "match_pct":    94.6,
        "classification": "Piracy",
        "risk":         "CRITICAL",
        "detected_at":  "14:19:55",
    },
]

MOCK_LOGS = [
    {"ts": "14:22:05", "level": "ALERT",   "msg": "Potential frame-matching collision detected on ASN 15209."},
    {"ts": "14:21:50", "level": "INFO",    "msg": "Updating fingerprint database for 'Match 26: KKR vs MI'."},
    {"ts": "14:21:36", "level": "SUCCESS", "msg": "Takedown notice S-49203 acknowledged by provider."},
    {"ts": "14:21:22", "level": "INFO",    "msg": "Geo-fencing confirmed for Region: IN-WEST."},
    {"ts": "14:20:55", "level": "ALERT",   "msg": "3 new IPTV streams detected matching Match 42 hash cluster."},
    {"ts": "14:20:31", "level": "SUCCESS", "msg": "C++ matcher processed 10,482 hashes in 0.089s."},
]

SPREAD_DATA = {
    "hours":  ["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"],
    "violations": [1, 3, 6, 5, 9, 14, 11, 18, 28, 41, 47],
}


# ─── Spread Chart ─────────────────────────────────────────────────────────────
def render_spread_chart():
    fig = go.Figure()

    # Filled area
    fig.add_trace(go.Scatter(
        x=SPREAD_DATA["hours"],
        y=SPREAD_DATA["violations"],
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(143, 46, 46, 0.16)",
        line=dict(color=COLORS["accent"], width=2.5, shape="spline"),
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Violations: %{y}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=130,
        xaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(size=9, color=COLORS["text_muted"], family="Courier Prime"),
            tickvals=["09:00","12:00","15:00","18:00"],
        ),
        yaxis=dict(showgrid=False, showline=False, showticklabels=False),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=COLORS["bg_secondary"],
            font_size=11,
            font_family="Courier Prime",
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── Detection Table ──────────────────────────────────────────────────────────
def render_detection_table(detections, max_rows=4):
    rows_html = ""
    for d in detections[:max_rows]:
        pct   = d["match_pct"]
        conf_cls = "conf-high" if pct >= 85 else ("conf-med" if pct >= 50 else "conf-low")
        badge    = risk_badge(d["classification"])
        risk_b   = risk_badge(d["risk"])
        url      = d["source_url"]
        rows_html += f"""
        <tr>
            <td class="url-cell">{url}</td>
            <td><span class="{conf_cls}">{pct}%</span></td>
            <td>{badge}</td>
            <td>{risk_b}</td>
            <td style="font-family:'Courier Prime','Courier New',monospace;font-size:11px;
                       color:{COLORS['text_muted']}">{d['detected_at']}</td>
        </tr>"""

    st.markdown(f"""
    <table class="sg-table">
        <thead>
            <tr>
                <th>Source URL</th>
                <th>Match %</th>
                <th>Classification</th>
                <th>Risk</th>
                <th>Detected At</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


# ─── Log Panel ────────────────────────────────────────────────────────────────
def render_log_panel(logs):
    level_map = {
        "ALERT":   ("log-alert",   "ALERT"),
        "INFO":    ("log-info",    "INFO"),
        "SUCCESS": ("log-success", "SUCCESS"),
    }
    lines = ""
    for log in logs:
        cls, lbl = level_map.get(log["level"], ("log-info", log["level"]))
        lines += f'<div><span class="log-ts">[{log["ts"]}]</span><span class="{cls}">{lbl}:</span> <span class="log-info"> {log["msg"]}</span></div>\n'

    st.markdown(f"""
    <div style="
        display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;
    ">
        <div style="
            font-family:'Cormorant Garamond',Georgia,serif;
            font-size:12px;font-weight:700;
            letter-spacing:0.12em;text-transform:uppercase;
            color:{COLORS['text_secondary']};
        ">Office logbook</div>
        <span style="
            font-size:10px;font-weight:600;
            color:{COLORS['text_secondary']};
            background:rgba(143, 46, 46, 0.12);
            padding:2px 8px;border-radius:2px;
            letter-spacing:0.04em;font-style:italic;
            border:1px solid rgba(143, 46, 46, 0.26);
        ">Routine watch</span>
    </div>
    <div class="sg-log-panel">{lines}</div>
    """, unsafe_allow_html=True)


# ─── System Integrity Panel ───────────────────────────────────────────────────
def render_integrity_panel():
    st.markdown(f"""
    <div class="sg-integrity-panel">
        <div class="sg-integrity-icon">🛡️</div>
        <div class="sg-integrity-title">Vault seal</div>
        <div class="sg-integrity-text">
            Fingerprints and tallies stay on this desk until you say otherwise.<br>
            Demo build — no outbound filings.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Main Page Render ─────────────────────────────────────────────────────────
def render():
    # Session bar
    st.markdown(f"""
    <div style="
        display:flex;justify-content:space-between;align-items:center;
        padding: 8px 0 16px 0;
        border-bottom: 1px solid {COLORS['border']};
        margin-bottom: 20px;
    ">
        <div style="font-family:'Courier Prime','Courier New',monospace;font-size:10px;
                    color:{COLORS['text_muted']};letter-spacing:0.1em;">
            Docket: <span style="color:{COLORS['accent']}">SG-2026 · IPL window</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
            <div style="
                background:{COLORS['bg_secondary']};
                border:1px solid {COLORS['border']};
                border-radius:5px;padding:5px 12px;
                font-size:11px;color:{COLORS['text_muted']};
            ">🔍 Scan hash or URL...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page_header(
        "Rights Protection Dashboard",
        "IPL Season 2026",
        show_active=True,
    )

    # ── Metric Cards ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Videos Protected",  "12",   "+2 TODAY",   "up",   "🛡️")
    with c2:
        metric_card("Violations Caught", "47",   "+8 TODAY",   "down", "⚠️")
    with c3:
        metric_card("Avg Detection Time","6.3s", "-0.48 FASTER","good","⚡")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Bottom section: feed + chart ─────────────────────────────────────────
    left_col, right_col = st.columns([3, 2], gap="medium")

    with left_col:
        st.markdown(f"""
        <div class="sg-panel">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <div class="sg-section-header" style="margin-bottom:0">
                    <div class="sg-live-dot"></div>
                    <span class="sg-section-title">Live Detection Feed</span>
                </div>
                <span class="sg-view-all">VIEW ALL →</span>
            </div>
        """, unsafe_allow_html=True)
        render_detection_table(MOCK_DETECTIONS)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown(f"""
        <div class="sg-panel">
            <div class="sg-section-header" style="margin-bottom:8px;">
                <span class="sg-section-title">Violation Spread Today</span>
            </div>
        """, unsafe_allow_html=True)
        render_spread_chart()
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown(f"""
            <div style="padding:8px 0">
                <div style="font-size:9px;color:{COLORS['text_muted']};
                            text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px;">
                    Peak Violations</div>
                <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:22px;
                            font-weight:700;color:{COLORS['text_primary']};">
                    14 <span style="font-size:11px;color:{COLORS['text_muted']}">/min</span></div>
            </div>""", unsafe_allow_html=True)
        with c_b:
            st.markdown(f"""
            <div style="padding:8px 0">
                <div style="font-size:9px;color:{COLORS['text_muted']};
                            text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px;">
                    Total Volume</div>
                <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:22px;
                            font-weight:700;color:{COLORS['text_primary']};">
                    1.2 <span style="font-size:11px;color:{COLORS['text_muted']}">GB/s</span></div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Integrity + Logs ──────────────────────────────────────────────────────
    int_col, log_col = st.columns([1, 2], gap="medium")
    with int_col:
        render_integrity_panel()
    with log_col:
        st.markdown(f'<div class="sg-panel">', unsafe_allow_html=True)
        render_log_panel(MOCK_LOGS)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── New Scan button ───────────────────────────────────────────────────────
    _, btn_col, _ = st.columns([3, 1, 3])
    with btn_col:
        if st.button("⚡ NEW SCAN", key="dash_scan"):
            st.toast("🔍 Scan initiated across 3 platforms...", icon="⚡")