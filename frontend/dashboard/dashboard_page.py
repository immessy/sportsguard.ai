# dashboard/dashboard_page.py
# ─────────────────────────────────────────────────────────────────────────────
# Home dashboard: metrics, live detection feed, spread chart, logs.
#
# Data sources:
#   - load_stats()       → GET /api/dashboard/stats  (or MOCK_STATS)
#   - load_detections()  → GET /api/scan             (or MOCK_DETECTIONS)
# Both loaders live in app.py and are passed via session_state.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from branding import COLORS, metric_card, page_header, risk_badge

# ─── Static mock data (logs + chart — not from API) ──────────────────────────
MOCK_LOGS = [
    {"ts": "14:22:05", "level": "ALERT",   "msg": "Potential frame-matching collision detected on ASN 15209."},
    {"ts": "14:21:50", "level": "INFO",    "msg": "Updating fingerprint database for 'Match 26: KKR vs MI'."},
    {"ts": "14:21:36", "level": "SUCCESS", "msg": "Takedown notice S-49203 acknowledged by provider."},
    {"ts": "14:21:22", "level": "INFO",    "msg": "Geo-fencing confirmed for Region: IN-WEST."},
    {"ts": "14:20:55", "level": "ALERT",   "msg": "3 new IPTV streams detected matching Match 42 hash cluster."},
    {"ts": "14:20:31", "level": "SUCCESS", "msg": "C++ matcher processed 10,482 hashes in 0.089s."},
]

SPREAD_DATA = {
    "hours":      ["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"],
    "violations": [1, 3, 6, 5, 9, 14, 11, 18, 28, 41, 47],
}


def _conf_class(pct):
    if pct >= 85: return "conf-high"
    if pct >= 50: return "conf-med"
    return "conf-low"


def render_spread_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=SPREAD_DATA["hours"],
        y=SPREAD_DATA["violations"],
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(132,204,22,0.08)",
        line=dict(color=COLORS["green_neon"], width=2.5, shape="spline"),
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Violations: %{y}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=130,
        xaxis=dict(
            showgrid=False, showline=False,
            tickfont=dict(size=9, color=COLORS["text_muted"], family="JetBrains Mono"),
            tickvals=["09:00","12:00","15:00","18:00"],
        ),
        yaxis=dict(showgrid=False, showline=False, showticklabels=False),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=COLORS["bg_secondary"], font_size=11),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_detection_table(detections, max_rows=4):
    rows_html = ""
    for d in detections[:max_rows]:
        pct   = round(d["c_plus_plus_confidence"] * 100, 1)
        badge = risk_badge(d["gemini_classification"])

        # Map risk score to risk level label
        score = d["gemini_risk_score"]
        if score >= 8:   risk_label = risk_badge("CRITICAL")
        elif score >= 5: risk_label = risk_badge("MEDIUM")
        else:            risk_label = risk_badge("LOW")

        # Truncate URL for display
        url = d["source_url"]
        url_display = url if len(url) <= 28 else url[:25] + "..."
        ts  = d["detected_at"].split(" ")[-1][:5] if " " in d["detected_at"] else d["detected_at"]

        rows_html += f"""
        <tr>
            <td class="url-cell">{url_display}</td>
            <td><span class="{_conf_class(pct)}">{pct}%</span></td>
            <td>{badge}</td>
            <td>{risk_label}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:11px;
                       color:{COLORS['text_muted']}">{ts}</td>
        </tr>"""

    st.markdown(f"""
    <table class="sg-table">
        <thead><tr>
            <th>Source URL</th><th>Match %</th>
            <th>Classification</th><th>Risk</th><th>Detected At</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


def render_log_panel():
    level_map = {
        "ALERT":   ("log-alert",   "ALERT"),
        "INFO":    ("log-info",    "INFO"),
        "SUCCESS": ("log-success", "SUCCESS"),
    }
    lines = ""
    for log in MOCK_LOGS:
        cls, lbl = level_map.get(log["level"], ("log-info", log["level"]))
        lines += f'<div><span class="log-ts">[{log["ts"]}]</span><span class="{cls}">{lbl}:</span> <span class="log-info"> {log["msg"]}</span></div>\n'

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <div style="font-family:'Rajdhani',sans-serif;font-size:12px;font-weight:700;
                    letter-spacing:.12em;text-transform:uppercase;
                    color:{COLORS['text_secondary']};">Neural Engine Logs</div>
        <span style="font-size:9px;font-weight:700;color:{COLORS['accent']};
                     background:rgba(245,158,11,0.12);padding:2px 8px;border-radius:3px;
                     letter-spacing:.1em;text-transform:uppercase;
                     border:1px solid rgba(245,158,11,0.25);">AUTO-SCAN ENABLED</span>
    </div>
    <div class="sg-log-panel">{lines}</div>
    """, unsafe_allow_html=True)


def render_integrity_panel():
    st.markdown(f"""
    <div class="sg-integrity-panel">
        <div class="sg-integrity-icon">🛡️</div>
        <div class="sg-integrity-title">System Integrity</div>
        <div class="sg-integrity-text">
            All defensive neural nodes are operational.<br>
            Within optimal latency parameters.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render():
    # ── Session bar ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 0 16px 0;border-bottom:1px solid {COLORS['border']};
                margin-bottom:20px;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                    color:{COLORS['text_muted']};letter-spacing:.1em;">
            SESSION ID: <span style="color:{COLORS['accent']}">SG-2026-IPL</span>
        </div>
        <div style="background:{COLORS['bg_secondary']};border:1px solid {COLORS['border']};
                    border-radius:5px;padding:5px 12px;font-size:11px;
                    color:{COLORS['text_muted']};">
            🔍 Scan hash or URL...
        </div>
    </div>
    """, unsafe_allow_html=True)

    page_header("Rights Protection Dashboard", "IPL Season 2026", show_active=True)

    # ── Load data via api_client (real or mock) ───────────────────────────────
    # TODO Phase 3: This already calls the real API when MOCK_MODE=False
    load_stats      = st.session_state.get("load_stats",      lambda: {})
    load_detections = st.session_state.get("load_detections", lambda: {"detections": []})

    stats      = load_stats()
    detections = load_detections().get("detections", [])

    # ── Metric cards ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card(
            "Videos Protected",
            str(stats.get("total_protected", 12)),
            "+2 TODAY", "up", "🛡️",
        )
    with c2:
        metric_card(
            "Violations Caught",
            str(stats.get("violations_today", 47)),
            "+8 TODAY", "down", "⚠️",
        )
    with c3:
        avg = stats.get("avg_detection_seconds", 6.3)
        metric_card(
            "Avg Detection Time",
            f"{avg}s",
            "-0.48 FASTER", "good", "⚡",
        )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Feed + chart ──────────────────────────────────────────────────────────
    left_col, right_col = st.columns([3, 2], gap="medium")

    with left_col:
        st.markdown(f"""
        <div class="sg-panel">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;margin-bottom:14px;">
                <div class="sg-section-header" style="margin-bottom:0">
                    <div class="sg-live-dot"></div>
                    <span class="sg-section-title">Live Detection Feed</span>
                </div>
                <span class="sg-view-all">VIEW ALL →</span>
            </div>
        """, unsafe_allow_html=True)
        render_detection_table(detections)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown(f'<div class="sg-panel">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="sg-section-header" style="margin-bottom:8px;">
            <span class="sg-section-title">Violation Spread Today</span>
        </div>
        """, unsafe_allow_html=True)
        render_spread_chart()
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown(f"""
            <div style="padding:8px 0">
                <div style="font-size:9px;color:{COLORS['text_muted']};text-transform:uppercase;
                            letter-spacing:.1em;margin-bottom:3px;">Peak Violations</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:20px;font-weight:700;
                            color:{COLORS['text_primary']};">
                    14 <span style="font-size:11px;color:{COLORS['text_muted']}">/min</span>
                </div>
            </div>""", unsafe_allow_html=True)
        with c_b:
            st.markdown(f"""
            <div style="padding:8px 0">
                <div style="font-size:9px;color:{COLORS['text_muted']};text-transform:uppercase;
                            letter-spacing:.1em;margin-bottom:3px;">Total Volume</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:20px;font-weight:700;
                            color:{COLORS['text_primary']};">
                    1.2 <span style="font-size:11px;color:{COLORS['text_muted']}">GB/s</span>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Integrity + Logs ──────────────────────────────────────────────────────
    int_col, log_col = st.columns([1, 2], gap="medium")
    with int_col:
        render_integrity_panel()
    with log_col:
        st.markdown(f'<div class="sg-panel">', unsafe_allow_html=True)
        render_log_panel()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    _, btn_col, _ = st.columns([3, 1, 3])
    with btn_col:
        if st.button("⚡ NEW SCAN", key="dash_scan"):
            st.toast("🔍 Scan initiated across 3 platforms...", icon="⚡")