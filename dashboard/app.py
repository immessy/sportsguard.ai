import streamlit as st
from streamlit.errors import StreamlitAPIException

# Correct Streamlit API: use page_title (not title). Icon shortcode avoids Windows emoji issues.
try:
    st.set_page_config(
        page_title="SportsGuard AI",
        layout="wide",
        page_icon=":shield:",
        initial_sidebar_state="expanded",
    )
except StreamlitAPIException:
    pass

import time

import pandas as pd
import plotly.express as px

from mock_data import (
    DASHBOARD_FEED_ROWS,
    DETECTION_FEED_BASE_ROWS,
    DMCA_CASES,
    PROPAGATION_ROWS,
    SIMULATED_PIRACY_ROW,
    build_dmca_notice,
)

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Section",
    options=["Dashboard", "Upload", "Detection Feed", "DMCA Reports"],
    label_visibility="collapsed",
)

st.title("🛡️ SportsGuard AI — Rights Protection Dashboard")

if page == "Dashboard":
    c1, c2, c3 = st.columns(3)
    c1.metric("Videos Protected", 12, "+2 today")
    c2.metric("Violations Caught", 47, "+8 today")
    c3.metric("Avg Detection Time", "6.3s", "-0.4s")

    st.subheader("Live Detection Feed")

    df = pd.DataFrame(DASHBOARD_FEED_ROWS)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Mock propagation — reshares over time (demo)")
    prop_df = pd.DataFrame(PROPAGATION_ROWS)
    fig = px.line(
        prop_df,
        x="Minutes since post",
        y="Estimated reshares",
        markers=True,
        title="Estimated viral spread (mock)",
    )
    fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

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
    if "detection_rows" not in st.session_state:
        st.session_state.detection_rows = [dict(r) for r in DETECTION_FEED_BASE_ROWS]

    df_feed = pd.DataFrame(st.session_state.detection_rows)

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

    b1, b2 = st.columns(2)
    with b1:
        if st.button("🔄 Refresh Scan", use_container_width=True):
            st.toast("Scan triggered — checking 3 platforms...")
    with b2:
        if st.button("Simulate Detection", use_container_width=True):
            st.session_state.detection_rows.insert(0, dict(SIMULATED_PIRACY_ROW))
            st.toast("New detection added — Gemini: Piracy (demo).")

elif page == "DMCA Reports":
    st.header("📄 DMCA Reports")
    st.caption("Select a mock violation — notice text fills in for download (demo only).")

    # TODO Phase 3: wire selected row to real detection IDs from the API
    case_idx = st.selectbox(
        "Violation",
        range(len(DMCA_CASES)),
        format_func=lambda i: DMCA_CASES[i]["label"],
        index=0,
    )
    case = DMCA_CASES[case_idx]

    body = build_dmca_notice(case)
    st.text_area("Notice draft", value=body, height=320)
    st.download_button(
        label="⬇️ Download notice (.txt)",
        data=body.encode("utf-8"),
        file_name="sportsguard_dmca_notice_demo.txt",
        mime="text/plain",
        use_container_width=True,
    )

st.caption("SportsGuard AI — Google Solution Challenge 2026")
