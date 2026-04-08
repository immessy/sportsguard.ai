import time

import pandas as pd
import streamlit as st


st.set_page_config(
    title="SportsGuard AI",
    layout="wide",
    page_icon="🛡️",
)

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    label="",
    options=["Dashboard", "Upload", "Detection Feed", "DMCA Reports"],
)

st.title("🛡️ SportsGuard AI — Rights Protection Dashboard")

if page == "Dashboard":
    c1, c2, c3 = st.columns(3)
    c1.metric("Videos Protected", 12, "+2 today")
    c2.metric("Violations Caught", 47, "+8 today")
    c3.metric("Avg Detection Time", "6.3s", "-0.4s")

    st.subheader("Live Detection Feed")

    df = pd.DataFrame(
        [
            {
                "Source URL": "https://twitter.com/cricketbuzz/status/1782049912001234567",
                "Match Confidence": "96.2%",
                "Gemini Classification": "🔴 Piracy",
                "Risk Score": 9,
                "Detected At": "2026-04-08 11:42:08",
            },
            {
                "Source URL": "https://t.me/ipl_highlights/8421",
                "Match Confidence": "92.8%",
                "Gemini Classification": "🔴 Piracy",
                "Risk Score": 8,
                "Detected At": "2026-04-08 11:39:51",
            },
            {
                "Source URL": "https://youtube.com/watch?v=Qx9wz2pL7kA",
                "Match Confidence": "88.4%",
                "Gemini Classification": "🟡 Transformative",
                "Risk Score": 4,
                "Detected At": "2026-04-08 11:33:10",
            },
            {
                "Source URL": "https://twitter.com/MI_FanClub/status/1782049909009876543",
                "Match Confidence": "85.7%",
                "Gemini Classification": "🟢 Meme/Fan",
                "Risk Score": 2,
                "Detected At": "2026-04-08 11:27:44",
            },
        ],
        columns=[
            "Source URL",
            "Match Confidence",
            "Gemini Classification",
            "Risk Score",
            "Detected At",
        ],
    )

    st.dataframe(df, use_container_width=True, hide_index=True)
elif page == "Upload":
    st.header("📤 Register Official Content")
    st.info(
        "Upload an official sports clip to fingerprint and protect it. The system will extract frames and generate perceptual hashes."
    )

    uploaded_file = st.file_uploader(
        "Upload Official Video",
        type=["mp4", "mov"],
        accept_multiple_files=False,
    )

    if uploaded_file is not None:
        st.video(uploaded_file)

    title = st.text_input(
        "Content Title",
        placeholder="e.g. IPL Match 42 Highlights",
    )

    # TODO Phase 3: replace with api_client.upload_video()
    if st.button("🔒 Fingerprint & Protect This Video", use_container_width=True):
        with st.spinner("Extracting frames and generating fingerprints..."):
            time.sleep(2)

        final_title = title.strip() if title and title.strip() else "IPL Match 42 Highlights"
        st.success("✅ Video registered! 143 frames fingerprinted and stored.")
        st.json(
            {
                "video_id": 7,
                "title": final_title,
                "frames_processed": 143,
                "status": "protected",
            }
        )
elif page == "Detection Feed":
    st.header("🔍 Live Detection Feed")

    m1, m2, m3 = st.columns(3)
    m1.metric("Scanned Today", 1247)
    m2.metric("Flagged", 23)
    m3.metric("High Risk", 8)

    risk_filter = st.selectbox(
        "Filter by Risk Level",
        ["All", "🔴 High Risk", "🟡 Medium Risk", "🟢 Low Risk"],
        index=0,
    )

    # TODO Phase 3: replace mock_data with api_client.run_scan()
    data = [
        {
            "Source URL": "https://twitter.com/CricketIndia/status/1782050012345678901",
            "Match %": 96.8,
            "Classification": "Piracy",
            "Risk Score": 10,
            "Detected At": "2026-04-08 11:48:32",
            "Action": "Take Down",
        },
        {
            "Source URL": "https://t.me/ipl_fullmatch/1290",
            "Match %": 94.1,
            "Classification": "Piracy",
            "Risk Score": 9,
            "Detected At": "2026-04-08 11:45:10",
            "Action": "Take Down",
        },
        {
            "Source URL": "https://youtube.com/watch?v=Jk9LmN34OpQ",
            "Match %": 89.5,
            "Classification": "Transformative",
            "Risk Score": 6,
            "Detected At": "2026-04-08 11:39:02",
            "Action": "Review",
        },
        {
            "Source URL": "https://twitter.com/RCB_Analysis/status/1782049987654321098",
            "Match %": 86.3,
            "Classification": "Transformative",
            "Risk Score": 5,
            "Detected At": "2026-04-08 11:34:19",
            "Action": "Review",
        },
        {
            "Source URL": "https://youtube.com/shorts/Zx8pqR1TuVc",
            "Match %": 83.9,
            "Classification": "Meme",
            "Risk Score": 3,
            "Detected At": "2026-04-08 11:28:47",
            "Action": "Ignore",
        },
        {
            "Source URL": "https://twitter.com/MI_FanClub/status/1782049909009876543",
            "Match %": 81.2,
            "Classification": "Meme",
            "Risk Score": 2,
            "Detected At": "2026-04-08 11:23:05",
            "Action": "Ignore",
        },
    ]

    df_feed = pd.DataFrame(data)

    if risk_filter == "🔴 High Risk":
        df_feed = df_feed[df_feed["Risk Score"] >= 8]
    elif risk_filter == "🟡 Medium Risk":
        df_feed = df_feed[(df_feed["Risk Score"] >= 4) & (df_feed["Risk Score"] <= 7)]
    elif risk_filter == "🟢 Low Risk":
        df_feed = df_feed[df_feed["Risk Score"] < 4]

    def highlight_risk(row):
        if row["Risk Score"] >= 8:
            return ["background-color: #fff0f0"] * len(row)
        if 4 <= row["Risk Score"] <= 7:
            return ["background-color: #fffbf0"] * len(row)
        return ["background-color: #f0fff4"] * len(row)

    styled = df_feed.style.apply(highlight_risk, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    if st.button("🔄 Refresh Scan", use_container_width=True):
        st.toast("Scan triggered — checking 3 platforms...")
else:
    st.subheader(page)
    st.info("Demo UI stub. This page will be implemented in the next steps.")

st.caption("SportsGuard AI — Google Solution Challenge 2026")

