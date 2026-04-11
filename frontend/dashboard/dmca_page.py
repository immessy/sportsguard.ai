import streamlit as st
import datetime
from branding import COLORS, page_header

# ─── Mock Violations ─────────────────────────────────────────────────────────
VIOLATIONS = [
    {
        "id":       "SG-992-K",
        "title":    "Unauthorised Twitch Restream: Premier League",
        "url":      "twitch.tv/sports_mirror_v3",
        "hash":     "b7a1c992",
        "platform": "Twitch Interactive, Inc.",
        "platform_attn": "ATTN: Copyright Agent",
        "match_pct": 94,
        "classification": "High Risk — Piracy",
        "risk_score": 9,
        "content":  "Premier League Match Day 8 — Live Feed",
        "title_work": "Premier League Match Day 8 — Live Feed",
    },
    {
        "id":       "SG-185-X",
        "title":    "Clip Distribution: F1 Grand Prix Highlights",
        "url":      "streamcloud.io/f1-monaco-full",
        "hash":     "3f92a185",
        "platform": "Streamcloud LLC.",
        "platform_attn": "ATTN: Legal Department",
        "match_pct": 88,
        "classification": "High Risk — Piracy",
        "risk_score": 8,
        "content":  "Formula 1 Monaco Grand Prix 2026 — Highlights",
        "title_work": "Formula 1 Monaco Grand Prix 2026",
    },
    {
        "id":       "SG-224-R",
        "title":    "P2P Seed Tracker: World Cup Final Replay",
        "url":      "p2p.tracker.xyz/sport/fifa_221",
        "hash":     "9d44c224",
        "platform": "P2P Tracker Network / Hosting Provider",
        "platform_attn": "ATTN: Abuse Team",
        "match_pct": 91,
        "classification": "High Risk — Piracy",
        "risk_score": 10,
        "content":  "FIFA World Cup Final 2026 — Full Replay",
        "title_work": "FIFA World Cup Final 2026",
    },
]


def build_dmca_notice(v):
    today = datetime.date.today().strftime("%B %d, %Y")
    return f"""TO: {v['platform']}, {v['platform_attn']}
DATE: {today}
SUBJECT: DMCA Copyright Infringement Notification

I, the undersigned, STATE UNDER PENALTY OF PERJURY that I am
authorised to act on behalf of SportsGuard Global Media, the owner
of certain exclusive intellectual property rights that are being
infringed.

INFRINGEMENT DETAILS:
─────────────────────────────────────────────────────
TITLE:      {v['title_work']}
URL:        https://{v['url']}
IDENTIFIER: {v['id']} / Fingerprint ref: {v['hash']}

The content identified above is being used without authorisation.
We have a good faith belief that the use of the material in the
manner complained of is not authorised by the copyright owner, its
agent, or the law.

MATCH CONFIDENCE: {v['match_pct']}%
CLASSIFIER NOTE (DEMO): {v['classification']}
RISK SCORE: {v['risk_score']} / 10

I request the immediate removal or disabling of access to the
infringing material identified above.

Submitted by:
SportsGuard AI — Rights desk (demo export)
Prepared for review only — not a filing.

Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC
"""


def render_dmca_html(notice_text):
    """Render DMCA notice with syntax highlighting."""
    lines = notice_text.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("TO:") or line.startswith("DATE:") or line.startswith("SUBJECT:"):
            key, _, val = line.partition(":")
            html_lines.append(
                f'<span class="dmca-label">{key}:</span>'
                f'<span class="dmca-value">{val}</span>'
            )
        elif line.startswith("TITLE:") or line.startswith("URL:") or line.startswith("IDENTIFIER:"):
            key, _, val = line.partition(":")
            html_lines.append(
                f'<span class="dmca-label">{key}:</span>'
                f'<span class="dmca-value">{val}</span>'
            )
        elif line.startswith("MATCH CONFIDENCE:") or line.startswith("AI CLASSIFICATION:") or line.startswith("RISK SCORE:"):
            key, _, val = line.partition(":")
            html_lines.append(
                f'<span class="dmca-label">{key}:</span>'
                f'<span style="color:{COLORS["danger"]};font-weight:700;">{val}</span>'
            )
        elif line.startswith("─") or line.startswith("INFRINGEMENT DETAILS"):
            html_lines.append(f'<span style="color:{COLORS["text_muted"]};">{line}</span>')
        elif line.strip() == "":
            html_lines.append("")
        else:
            html_lines.append(f'<span style="color:{COLORS["text_secondary"]};">{line}</span>')
    return "<br>".join(html_lines)


def render():
    page_header(
        "DMCA Report Generator",
        subtitle="",
        show_active=False,
    )

    # ── Warning banner ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sg-banner-warning">
        <span style="font-size:16px;flex-shrink:0;">⚠️</span>
        <div>
            <strong style="color:{COLORS['accent']};font-size:12px;
                           text-transform:uppercase;letter-spacing:.06em;">
                Precautionary Protocol</strong><br>
            <span style="font-size:12px;">
                Only generate takedowns for High Risk items.
                Automated legal filing requires verified metadata verification.
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two-column layout ─────────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1.6], gap="large")

    # ── LEFT: Pending violations ──────────────────────────────────────────────
    with left_col:
        # Header
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:12px;">
            <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:14px;font-weight:700;
                        letter-spacing:.1em;text-transform:uppercase;
                        color:{COLORS['text_primary']};">
                Pending Violations
            </div>
            <span style="
                background:rgba(143, 46, 46, 0.16);
                color:{COLORS['accent']};
                border:1px solid rgba(143, 46, 46, 0.32);
                padding:2px 10px;border-radius:999px;
                font-size:11px;font-weight:700;
            ">{len(VIOLATIONS)} QUEUED</span>
        </div>
        """, unsafe_allow_html=True)

        # Violation cards
        selected_id = st.session_state.get("selected_violation", VIOLATIONS[0]["id"])
        for v in VIOLATIONS:
            is_active = v["id"] == selected_id
            active_cls = "active" if is_active else ""
            st.markdown(f"""
            <div class="sg-violation-card {active_cls}" id="vc-{v['id']}">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;min-width:0;">
                        <div class="sg-violation-id">{v['id']}</div>
                        <div class="sg-violation-title">{v['title']}</div>
                        <div class="sg-violation-url">{v['url']}</div>
                    </div>
                    <span style="
                        font-size:10px;color:{COLORS['accent']};font-weight:700;
                        text-transform:uppercase;letter-spacing:.08em;
                        flex-shrink:0;margin-left:10px;
                    ">Pending</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Selectbox to choose
        violation_options = {f"{v['id']} ({v['url'].split('/')[0]})": v["id"] for v in VIOLATIONS}
        choice_label = st.selectbox(
            "SELECT VIOLATION TO ACTION",
            list(violation_options.keys()),
            key="violation_select",
        )
        st.session_state["selected_violation"] = violation_options[choice_label]

    # ── RIGHT: DMCA notice ────────────────────────────────────────────────────
    with right_col:
        sel_id = st.session_state.get("selected_violation", VIOLATIONS[0]["id"])
        sel_v  = next(v for v in VIOLATIONS if v["id"] == sel_id)
        notice = build_dmca_notice(sel_v)

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:10px;">
            <div>
                <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:14px;
                            font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                            color:{COLORS['text_primary']};">
                    Formal DMCA Notice
                </div>
                <div style="font-size:10px;color:{COLORS['text_muted']};margin-top:2px;">
                    FORMAT: RFC-2022 ENHANCED
                </div>
            </div>
        </div>
        <div style="
            background:{COLORS['bg_tertiary']};
            border:1px solid {COLORS['border']};
            border-radius:8px;
            padding:20px;
            font-family:'Courier Prime','Courier New',monospace;
            font-size:11px;
            line-height:1.8;
            max-height:380px;
            overflow-y:auto;
        ">{render_dmca_html(notice)}</div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Action buttons
        btn_a, btn_b = st.columns(2)
        with btn_a:
            if st.button("▶  TRANSMIT DMCA NOTICE", key="transmit_btn"):
                st.toast(f"✅ DMCA notice for {sel_id} transmitted!", icon="📤")
        with btn_b:
            st.download_button(
                label="⎘  Copy to Clipboard",
                data=notice,
                file_name=f"dmca_{sel_id}.txt",
                mime="text/plain",
                key="copy_btn",
            )

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center;border-top:1px solid {COLORS['border']};
                padding-top:14px;">
        <div style="font-size:11px;color:{COLORS['text_secondary']};
                    letter-spacing:.03em;font-style:italic;margin-bottom:4px;">
            Google Solution Challenge 2026 · SportsGuard AI — a clerk's desk, not a bot farm.
        </div>
        <div style="font-size:10px;color:{COLORS['text_muted']};">
            Demo notices only. Have counsel review anything real.
        </div>
    </div>
    """, unsafe_allow_html=True)