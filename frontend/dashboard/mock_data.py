"""Static demo data for the SportsGuard AI Streamlit dashboard (no Streamlit imports)."""

from __future__ import annotations

# --- Dashboard home: compact feed (match % + pill labels) ---
DASHBOARD_FEED_ROWS: list[dict] = [
    {
        "platform": "twitter",
        "display_url": "twitter.com/ipl_leaks_hd/status/1910234891",
        "match_pct": 94,
        "classification": "Piracy",
    },
    {
        "platform": "telegram",
        "display_url": "t.me/ipl_highlights_2026/887",
        "match_pct": 87,
        "classification": "Piracy",
    },
    {
        "platform": "youtube",
        "display_url": "youtube.com/shorts/xK9mP2rLtZ",
        "match_pct": 71,
        "classification": "Transformative",
    },
    {
        "platform": "twitter",
        "display_url": "twitter.com/cricket_memes24/status/1910200112",
        "match_pct": 45,
        "classification": "Meme/Fan",
    },
]

# --- Detection feed (session_state seed) ---
DETECTION_FEED_BASE_ROWS: list[dict] = [
    {
        "platform": "twitter",
        "display_url": "twitter.com/ipl_leaks_hd/status/1910234891",
        "match_pct": 94,
        "Classification": "Piracy",
        "Risk Score": 10,
        "Detected At": "2026-04-11 09:18:32",
        "Action": "Take Down",
    },
    {
        "platform": "telegram",
        "display_url": "t.me/ipl_highlights_2026/887",
        "match_pct": 87,
        "Classification": "Piracy",
        "Risk Score": 9,
        "Detected At": "2026-04-11 09:15:10",
        "Action": "Take Down",
    },
    {
        "platform": "youtube",
        "display_url": "youtube.com/shorts/xK9mP2rLtZ",
        "match_pct": 71,
        "Classification": "Transformative",
        "Risk Score": 6,
        "Detected At": "2026-04-11 09:09:02",
        "Action": "Review",
    },
    {
        "platform": "youtube",
        "display_url": "youtube.com/watch?v=Jk9LmN34OpQ",
        "match_pct": 63,
        "Classification": "Transformative",
        "Risk Score": 5,
        "Detected At": "2026-04-11 09:04:19",
        "Action": "Review",
    },
    {
        "platform": "twitter",
        "display_url": "twitter.com/cricket_memes24/status/1910200112",
        "match_pct": 45,
        "Classification": "Meme/Fan",
        "Risk Score": 3,
        "Detected At": "2026-04-11 08:58:47",
        "Action": "Ignore",
    },
    {
        "platform": "telegram",
        "display_url": "t.me/cricketzone_unofficial/4421",
        "match_pct": 89,
        "Classification": "Piracy",
        "Risk Score": 9,
        "Detected At": "2026-04-11 08:53:05",
        "Action": "Take Down",
    },
]

SIMULATED_PIRACY_ROW: dict = {
    "platform": "twitter",
    "display_url": "twitter.com/ipl_leak_mirror/status/1910255001",
    "match_pct": 95,
    "Classification": "Piracy",
    "Risk Score": 9,
    "Detected At": "2026-04-11 09:22:01",
    "Action": "Take Down",
}

# --- Hourly violation spread (mock chart) ---
VIOLATION_SPREAD_HOURLY: list[dict] = [
    {"time": "06:00", "count": 2},
    {"time": "07:00", "count": 5},
    {"time": "08:00", "count": 8},
    {"time": "09:00", "count": 11},
    {"time": "10:00", "count": 9},
    {"time": "11:00", "count": 14},
    {"time": "12:00", "count": 12},
    {"time": "13:00", "count": 15},
    {"time": "14:00", "count": 13},
]

# Legacy name used by older chart code paths
PROPAGATION_ROWS = VIOLATION_SPREAD_HOURLY

# --- DMCA pending table ---
PENDING_VIOLATIONS: list[dict] = [
    {
        "ref_id": "SG-2026-0847",
        "display_url": "twitter.com/ipl_leaks_hd/status/1910234891",
        "platform": "Twitter (X)",
        "match_pct": 94,
        "status": "Pending",
    },
    {
        "ref_id": "SG-2026-0842",
        "display_url": "t.me/ipl_highlights_2026/887",
        "platform": "Telegram",
        "match_pct": 87,
        "status": "Pending",
    },
    {
        "ref_id": "SG-2026-0838",
        "display_url": "youtube.com/shorts/xK9mP2rLtZ",
        "platform": "YouTube",
        "match_pct": 71,
        "status": "Pending",
    },
]

DMCA_CASES: list[dict] = [
    {
        "label": "Twitter — full over replay (Piracy, risk 10)",
        "ref_id": "SG-2026-0847",
        "infringing_url": "https://twitter.com/ipl_leaks_hd/status/1910234891",
        "original_title": "IPL 2026 — Official Broadcast Feed (BCCI / rights partner)",
        "match_pct": 94.0,
        "classification": "Piracy",
        "risk_score": 10,
    },
    {
        "label": "Telegram — segment mirror (Piracy, risk 9)",
        "ref_id": "SG-2026-0842",
        "infringing_url": "https://t.me/ipl_highlights_2026/887",
        "original_title": "IPL 2026 — Official Broadcast Feed (BCCI / rights partner)",
        "match_pct": 87.0,
        "classification": "Piracy",
        "risk_score": 9,
    },
    {
        "label": "YouTube — clip (Transformative, risk 6)",
        "ref_id": "SG-2026-0838",
        "infringing_url": "https://youtube.com/shorts/xK9mP2rLtZ",
        "original_title": "IPL 2026 — Official Highlights (BCCI / rights partner)",
        "match_pct": 71.0,
        "classification": "Transformative",
        "risk_score": 6,
    },
]


def build_dmca_notice(case: dict) -> str:
    ref = case.get("ref_id", "SG-2026-DEMO")
    return "\n".join(
        [
            "DMCA TAKEDOWN NOTICE",
            "",
            f"Date: 2026-04-11",
            f"Reference ID: {ref}",
            "",
            "TO:",
            "Designated Copyright Agent / Abuse Team",
            "Hosting / Platform Provider (as applicable)",
            "",
            "FROM:",
            "Board of Control for Cricket in India (BCCI)",
            "IPL Media Rights & Anti-Piracy Desk (demo sender)",
            "Email: ipl-rights-demo@sportsguard.ai",
            "",
            "SUBJECT: Notice of copyright infringement under applicable policy",
            "",
            "DESCRIPTION OF COPYRIGHTED WORK:",
            case["original_title"],
            "",
            "LOCATION OF INFRINGING MATERIAL:",
            case["infringing_url"],
            "",
            "TECHNICAL & CONTEXT SIGNALS (DEMO):",
            f"- Perceptual match confidence: {case['match_pct']:.1f}%",
            f"- Automated classification: {case['classification']}",
            f"- Risk score: {case['risk_score']}/10",
            "",
            "STATEMENT:",
            "The use described above is not authorized by the rights holder. We request expeditious removal or disablement of access.",
            "",
            "GOOD FAITH / ACCURACY (DEMO TEXT):",
            "This notice is provided in good faith. This export is for demonstration only and is not legal advice.",
            "",
            "Signature: IPL Media Rights — Demo Export (SportsGuard AI)",
        ]
    )
