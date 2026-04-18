"""HTML snippets + clipboard helper for mock-aligned Streamlit UI."""

from __future__ import annotations

import html as html_lib
import json

import streamlit as st
import streamlit.components.v1 as components
from branding import COLORS


def platform_icon(platform: str) -> str:
    return {
        "twitter": "𝕏",
        "telegram": "✈",
        "youtube": "▶",
    }.get(platform, "·")


def match_pct_class(classification: str) -> str:
    c = classification.lower()
    if "piracy" in c:
        return "red"
    if "transform" in c:
        return "amber"
    return "green"


def pill_html(classification: str) -> str:
    c = classification.lower()
    if "piracy" in c:
        cls, label = "piracy", "Piracy"
    elif "transform" in c:
        cls, label = "transform", "Transformative"
    else:
        cls, label = "meme", "Meme/Fan"
    return (
        f'<span class="sg-pill {cls}"><span class="sg-pill-dot"></span>'
        f"{html_lib.escape(label)}</span>"
    )


def feed_row_html(row: dict) -> str:
    plat = platform_icon(row.get("platform", "twitter"))
    url = html_lib.escape(row.get("display_url", row.get("Source URL", "")))
    pct = int(row.get("match_pct", row.get("Match %", 0)))
    cl = row.get("classification") or row.get("Classification", "")
    mc = match_pct_class(cl)
    return f"""
<div class="sg-feed-row">
  <div class="sg-feed-url"><span class="sg-plat">{plat}</span><span>{url}</span></div>
  <div class="sg-match {mc}">{pct}%</div>
  <div>{pill_html(cl)}</div>
</div>
"""


def feed_table_html(rows: list[dict]) -> str:
    head = """
<div class="sg-feed-wrap">
  <div class="sg-feed-head">
    <div>Source URL</div>
    <div>Match %</div>
    <div>Classification</div>
  </div>
"""
    body = "".join(feed_row_html(r) for r in rows)
    return head + body + "</div>"


def pending_violations_table_html(rows: list[dict]) -> str:
    parts = [
        '<table class="sg-table-mini"><thead><tr>',
        "<th>Ref ID</th><th>URL</th><th>Platform</th><th>Match</th><th>Status</th>",
        "</tr></thead><tbody>",
    ]
    for r in rows:
        parts.append(
            "<tr>"
            f'<td><span class="sg-ref">{html_lib.escape(r["ref_id"])}</span></td>'
            f'<td>{html_lib.escape(r["display_url"])}</td>'
            f'<td style="color:#9c8b7c">{html_lib.escape(r["platform"])}</td>'
            f'<td style="color:#8f2e2e;font-weight:700">{int(r["match_pct"])}%</td>'
            '<td><span class="sg-pend-pill">⏳ Pending</span></td>'
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def render_content_type(data: dict):
    """Renders the AI Content Type Detection UI."""
    ct = data.get("content_type", "Meme")
    conf = data.get("confidence", 92)
    
    cls_map = {
        "Raw Clip": "ct-raw",
        "Meme": "ct-meme",
        "Analysis": "ct-analysis",
        "Reaction": "ct-reaction"
    }
    badge_cls = cls_map.get(ct, "ct-meme")
    
    st.markdown(f"""
    <div class="sg-feature-card">
        <div class="sg-feature-title">🎭 Content Type Detection</div>
        <div class="sg-feature-subtitle">AI classification of uploaded content</div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <span class="sg-ct-badge {badge_cls}">{ct}</span>
            <span style="color: {COLORS['text_muted']}; font-size: 13px; font-weight: 500;">
                Confidence <span style="color: {COLORS['accent']}; font-weight: 700;">{conf}%</span>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_dmca_smart_panel(data: dict):
    """Renders the Smart DMCA Generator UI."""
    risk = data.get("risk_level", "High")
    platform = data.get("platform", "YouTube")
    ts = data.get("timestamp", "02:13")
    match_pct = data.get("match_percent", 87)
    ct = data.get("content_type", "Meme")
    
    risk_map = {
        "High": ("CRITICAL", "badge-critical", "This notice is a formal request for immediate removal based on a high-confidence copyright violation."),
        "Medium": ("MEDIUM", "badge-medium", "A potential violation has been detected. We request a manual review of this content."),
        "Low": ("LOW", "badge-low", "This content is being monitored. No immediate action is required but rights are reserved.")
    }
    label, cls, tone = risk_map.get(risk, ("UNKNOWN", "badge-low", "Review suggested."))

    draft_text = f"To: Copyright Agent, {platform}\nRE: Infringement Notice - {ts}\n\nNotice of Copyright Infringement:\nThe detected content ({ct}) matching at {match_pct}% has been flagged as {risk} risk.\n\n{tone}\n\nReference ID: SG-{ts.replace(':', '')}\nAuthorized by SportsGuard AI Enforcement Hub"

    st.markdown(f"""
    <div class="sg-feature-card">
        <div class="sg-feature-title">🛡️ Smart DMCA Generator</div>
        <div class="sg-feature-subtitle">Context-aware enforcement automation</div>
        
        <div class="sg-dmca-detail-row">
            <span class="sg-dmca-detail-label">Risk Threshold</span>
            <span class="badge {cls}">{label}</span>
        </div>
        <div class="sg-dmca-detail-row">
            <span class="sg-dmca-detail-label">Platform Origin</span>
            <span class="sg-dmca-detail-value">{platform}</span>
        </div>
        <div class="sg-dmca-detail-row">
            <span class="sg-dmca-detail-label">Asset Timestamp</span>
            <span class="sg-dmca-detail-value">{ts}</span>
        </div>
        <div class="sg-dmca-detail-row">
            <span class="sg-dmca-detail-label">Peak Match</span>
            <span class="sg-dmca-detail-value">{match_pct}%</span>
        </div>
        
        <div class="sg-dmca-preview">{html_lib.escape(draft_text)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Generate DMCA Notice", key=f"btn_dmca_{ts.replace(':', '_')}", use_container_width=True):
        st.toast("Drafting legal notice...", icon="⚖️")
        st.success(f"DMCA successfully staged for {platform}")


def copy_to_clipboard_button(text: str) -> None:
    payload = json.dumps(text)
    components.html(
        f"""
        <button type="button" id="sg-copy-btn"
          style="width:100%;padding:12px 16px;border-radius:8px;border:1px solid #6b584e;
          background:#352820;color:#f2e8d5;font-weight:600;cursor:pointer;font-family:serif;font-size:14px;">
          Copy to Clipboard
        </button>
        <script>
        const btn = document.getElementById("sg-copy-btn");
        const payload = {payload};
        btn.addEventListener("click", () => {{
          navigator.clipboard.writeText(payload).then(() => {{
            const prev = btn.textContent;
            btn.textContent = "Copied!";
            setTimeout(() => {{ btn.textContent = prev; }}, 2000);
          }});
        }});
        </script>
        """,
        height=58,
    )
