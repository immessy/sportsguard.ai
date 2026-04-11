"""Static demo data for the SportsGuard AI Streamlit dashboard (no Streamlit imports)."""

from __future__ import annotations

# --- Dashboard home: live feed preview ---
DASHBOARD_FEED_ROWS: list[dict] = [
    {
        "Source URL": "https://twitter.com/cricketbuzz/status/1782049912001234567",
        "Match Confidence": "96.2%",
        "Gemini Classification": "🔴 Piracy",
        "Risk Score": 9,
        "Detected At": "2026-04-11 09:12:08",
    },
    {
        "Source URL": "https://t.me/ipl_highlights/8421",
        "Match Confidence": "92.8%",
        "Gemini Classification": "🔴 Piracy",
        "Risk Score": 8,
        "Detected At": "2026-04-11 09:09:51",
    },
    {
        "Source URL": "https://youtube.com/watch?v=Qx9wz2pL7kA",
        "Match Confidence": "88.4%",
        "Gemini Classification": "🟡 Transformative",
        "Risk Score": 4,
        "Detected At": "2026-04-11 09:03:10",
    },
    {
        "Source URL": "https://twitter.com/MI_FanClub/status/1782049909009876543",
        "Match Confidence": "85.7%",
        "Gemini Classification": "🟢 Meme/Fan",
        "Risk Score": 2,
        "Detected At": "2026-04-11 08:57:44",
    },
]

# --- Detection feed: baseline table (copied into session_state so we can append demos) ---
DETECTION_FEED_BASE_ROWS: list[dict] = [
    {
        "Source URL": "https://twitter.com/CricketIndia/status/1782050012345678901",
        "Match %": 96.8,
        "Classification": "Piracy",
        "Risk Score": 10,
        "Detected At": "2026-04-11 09:18:32",
        "Action": "Take Down",
    },
    {
        "Source URL": "https://t.me/ipl_fullmatch/1290",
        "Match %": 94.1,
        "Classification": "Piracy",
        "Risk Score": 9,
        "Detected At": "2026-04-11 09:15:10",
        "Action": "Take Down",
    },
    {
        "Source URL": "https://youtube.com/watch?v=Jk9LmN34OpQ",
        "Match %": 89.5,
        "Classification": "Transformative",
        "Risk Score": 6,
        "Detected At": "2026-04-11 09:09:02",
        "Action": "Review",
    },
    {
        "Source URL": "https://twitter.com/RCB_Analysis/status/1782049987654321098",
        "Match %": 86.3,
        "Classification": "Transformative",
        "Risk Score": 5,
        "Detected At": "2026-04-11 09:04:19",
        "Action": "Review",
    },
    {
        "Source URL": "https://youtube.com/shorts/Zx8pqR1TuVc",
        "Match %": 83.9,
        "Classification": "Meme",
        "Risk Score": 3,
        "Detected At": "2026-04-11 08:58:47",
        "Action": "Ignore",
    },
    {
        "Source URL": "https://twitter.com/MI_FanClub/status/1782049909009876543",
        "Match %": 81.2,
        "Classification": "Meme",
        "Risk Score": 2,
        "Detected At": "2026-04-11 08:53:05",
        "Action": "Ignore",
    },
]

SIMULATED_PIRACY_ROW: dict = {
    "Source URL": "https://twitter.com/ipl_leak_mirror/status/1782051122334455667",
    "Match %": 95.4,
    "Classification": "Piracy",
    "Risk Score": 9,
    "Detected At": "2026-04-11 09:22:01",
    "Action": "Take Down",
}

# --- Propagation chart (mock viral spread) ---
PROPAGATION_ROWS: list[dict] = [
    {"Minutes since post": m, "Estimated reshares": int(12 + m * 18 + (m % 5) * 7)}
    for m in range(0, 31, 2)
]

# --- DMCA report presets ---
DMCA_CASES: list[dict] = [
    {
        "label": "Twitter — full over replay (Piracy, risk 10)",
        "infringing_url": "https://twitter.com/CricketIndia/status/1782050012345678901",
        "original_title": "IPL 2026 — Match 42 Official Highlights (Rights: BCCI / Broadcaster)",
        "match_pct": 96.8,
        "classification": "Piracy",
        "risk_score": 10,
    },
    {
        "label": "Telegram — match segment mirror (Piracy, risk 9)",
        "infringing_url": "https://t.me/ipl_fullmatch/1290",
        "original_title": "IPL 2026 — Match 42 Broadcast Feed (Rights: BCCI / Broadcaster)",
        "match_pct": 94.1,
        "classification": "Piracy",
        "risk_score": 9,
    },
    {
        "label": "YouTube — tactical breakdown (Transformative, risk 6)",
        "infringing_url": "https://youtube.com/watch?v=Jk9LmN34OpQ",
        "original_title": "IPL 2026 — Match 42 Official Highlights (Rights: BCCI / Broadcaster)",
        "match_pct": 89.5,
        "classification": "Transformative",
        "risk_score": 6,
    },
]


def build_dmca_notice(case: dict) -> str:
    return "\n".join(
        [
            "DMCA TAKEDOWN NOTICE (DEMO / NOT LEGAL ADVICE)",
            "",
            "Rights holder: SportsGuard AI Demo Rights Desk",
            "Contact: rights-demo@sportsguard.ai",
            "",
            "INFRINGING URL:",
            case["infringing_url"],
            "",
            "ORIGINAL WORK:",
            case["original_title"],
            "",
            "MATCH SIGNALS (DEMO):",
            f"- Perceptual match: {case['match_pct']:.1f}%",
            f"- Classification: {case['classification']}",
            f"- Risk score: {case['risk_score']}/10",
            "",
            "REQUESTED ACTION:",
            "Remove or disable access to the listed content expeditiously.",
            "",
            "Good faith statement: This notice is submitted in good faith under applicable copyright policy.",
            "",
            "Signature: SportsGuard AI — Demo Export",
        ]
    )
