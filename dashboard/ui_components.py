"""HTML snippets + clipboard helper for mock-aligned Streamlit UI."""

from __future__ import annotations

import html as html_lib
import json

import streamlit.components.v1 as components


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
            f'<td style="color:#8b949e">{html_lib.escape(r["platform"])}</td>'
            f'<td style="color:#ef4444;font-weight:700">{int(r["match_pct"])}%</td>'
            '<td><span class="sg-pend-pill">⏳ Pending</span></td>'
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def copy_to_clipboard_button(text: str) -> None:
    payload = json.dumps(text)
    components.html(
        f"""
        <button type="button" id="sg-copy-btn"
          style="width:100%;padding:12px 16px;border-radius:8px;border:1px solid #30363d;
          background:#161b22;color:#f0f6fc;font-weight:600;cursor:pointer;font-family:Inter,system-ui,sans-serif;font-size:14px;">
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
