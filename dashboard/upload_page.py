import streamlit as st
import time
from branding import COLORS, page_header

# ─── Mock API response ────────────────────────────────────────────────────────
def mock_upload_response(title):
    return {
        "status":        "success",
        "registry_id":   "SG-7729-AX",
        "fingerprint": {
            "frames_processed":  143,
            "hash_algorithm":    "pHash-512/Sentinel",
            "root_merkle":       "0xBf2a...f921",
        },
        "protection": {
            "takedown_enabled":  True,
            "whitelist":         ["youtube.com/official"],
        },
    }


def render_json_block(data, indent=0):
    """Render a dict as syntax-highlighted HTML."""
    lines = []
    pad = "&nbsp;" * (indent * 4)
    for k, v in data.items():
        key_html = f'<span class="json-key">"{k}"</span>'
        if isinstance(v, dict):
            inner = render_json_block(v, indent + 1)
            lines.append(f'{pad}  {key_html}: {{<br>{inner}{pad}  }},')
        elif isinstance(v, bool):
            val_html = f'<span class="json-bool">{"true" if v else "false"}</span>'
            lines.append(f'{pad}  {key_html}: {val_html},')
        elif isinstance(v, int):
            val_html = f'<span class="json-num">{v}</span>'
            lines.append(f'{pad}  {key_html}: {val_html},')
        elif isinstance(v, list):
            items = ", ".join(f'<span class="json-str">"{i}"</span>' for i in v)
            lines.append(f'{pad}  {key_html}: [{items}],')
        else:
            val_html = f'<span class="json-str">"{v}"</span>'
            lines.append(f'{pad}  {key_html}: {val_html},')
    return "<br>".join(lines) + "<br>"


def render():
    page_header(
        "Content Registration",
        subtitle="Secure your intellectual property against illegal restreaming.",
        show_active=False,
    )

    # ── Success banner (shown after upload) ───────────────────────────────────
    if st.session_state.get("upload_success"):
        reg_id = st.session_state.get("upload_reg_id", "SG-7729-AX")
        st.markdown(f"""
        <div class="sg-banner-success">
            <span style="font-size:16px">✅</span>
            <div>
                Video registered! 143 frames fingerprinted.
                <span style="
                    font-family:'JetBrains Mono',monospace;
                    color:{COLORS['accent']};
                    font-size:11px;
                    margin-left:12px;
                ">{reg_id}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Info banner ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sg-banner-info">
        <span style="font-size:14px;margin-right:4px">ℹ️</span>
        Our AI engine generates a unique cryptographic "Technical Fingerprint" of every frame.
        Once registered, any unauthorised use of this footage across the web will be instantly
        flagged by the sentinel.
    </div>
    """, unsafe_allow_html=True)

    # ── Two-column layout ─────────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    # ── LEFT: Upload form ─────────────────────────────────────────────────────
    with left_col:
        st.markdown(f"""
        <div style="
            background:{COLORS['bg_secondary']};
            border:1px solid {COLORS['border']};
            border-radius:10px;
            padding:24px;
        ">
        <div style="
            font-family:'Rajdhani',sans-serif;
            font-size:20px;font-weight:700;
            color:{COLORS['text_primary']};
            margin-bottom:6px;
        ">Register Official Content</div>
        <div style="font-size:12px;color:{COLORS['text_muted']};margin-bottom:20px;">
            Secure your intellectual property against illegal restreaming.
        </div>
        """, unsafe_allow_html=True)

        # File uploader
        uploaded_file = st.file_uploader(
            "DROP MP4 OR MOV FILE HERE",
            type=["mp4", "mov"],
            key="video_upload",
            label_visibility="collapsed",
            help="Maximum file size: 2.0 GB",
        )

        st.markdown(f"""
        <div style="text-align:center;padding:20px 0 12px;">
            <div style="
                border: 1.5px dashed rgba(245,158,11,0.3);
                border-radius:10px;
                padding:28px 20px;
                background:rgba(245,158,11,0.02);
            ">
                <div style="font-size:32px;margin-bottom:8px;">⬆️</div>
                <div style="font-size:14px;color:{COLORS['text_secondary']};margin-bottom:4px;">
                    Drag and drop MP4 or MOV file here
                </div>
                <div style="font-size:11px;color:{COLORS['text_muted']};margin-bottom:10px;">
                    Maximum file size: 2.0 GB
                </div>
                <div style="
                    font-size:11px;font-weight:700;
                    color:{COLORS['accent']};
                    letter-spacing:0.1em;text-transform:uppercase;
                    cursor:pointer;
                ">Browse Local Files</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Content title
        content_title = st.text_input(
            "CONTENT TITLE",
            placeholder="e.g. IPL Match 42 Highlights",
            key="content_title",
        )

        # Two-col inputs
        col_a, col_b = st.columns(2)
        with col_a:
            rights_holder = st.text_input(
                "RIGHTS HOLDER",
                value="Sports Media Group Ltd.",
                key="rights_holder",
            )
        with col_b:
            region = st.selectbox(
                "REGION",
                ["Global Rights", "IN-WEST", "IN-EAST", "Asia Pacific", "Europe"],
                key="region",
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # CTA button
        if st.button("🔒  FINGERPRINT & PROTECT", key="fingerprint_btn"):
            if not content_title:
                st.warning("Please enter a content title before protecting.")
            else:
                with st.spinner(""):
                    st.markdown(f"""
                    <div style="
                        background:{COLORS['bg_tertiary']};
                        border:1px solid {COLORS['border']};
                        border-radius:6px;padding:12px 16px;
                        font-family:'JetBrains Mono',monospace;font-size:11px;
                        color:{COLORS['accent']};
                        animation: pulse 1s infinite;
                        margin:8px 0;
                    ">
                        ⚙️ Extracting keyframes at 1 FPS...<br>
                        🔐 Generating perceptual hashes (pHash-512)...<br>
                        💾 Writing 143 fingerprints to sentinel database...
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(2)

                resp = mock_upload_response(content_title)
                st.session_state["upload_success"]  = True
                st.session_state["upload_reg_id"]   = resp["registry_id"]
                st.session_state["upload_response"] = resp
                st.session_state["upload_title"]    = content_title
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── RIGHT: Preview + response ─────────────────────────────────────────────
    with right_col:
        # Video preview card
        st.markdown(f"""
        <div style="
            background:{COLORS['bg_secondary']};
            border:1px solid {COLORS['border']};
            border-radius:10px;
            overflow:hidden;
            margin-bottom:16px;
        ">
            <div style="
                background:{COLORS['bg_tertiary']};
                height:140px;
                display:flex;align-items:center;justify-content:center;
                border-bottom:1px solid {COLORS['border']};
                position:relative;
            ">
                <div style="text-align:center;">
                    <div style="font-size:36px;margin-bottom:6px;opacity:0.4">▶</div>
                    <div style="font-size:11px;color:{COLORS['text_muted']};">
                        Video preview area
                    </div>
                </div>
                <div style="
                    position:absolute;bottom:10px;right:10px;
                    font-size:9px;font-weight:700;letter-spacing:.1em;
                    color:{COLORS['accent']};
                    background:rgba(245,158,11,0.12);
                    border:1px solid rgba(245,158,11,0.25);
                    padding:2px 8px;border-radius:3px;text-transform:uppercase;
                ">● Fingerprinting Engine Active</div>
            </div>
        """, unsafe_allow_html=True)

        if uploaded_file:
            st.video(uploaded_file)
            filename = uploaded_file.name
        else:
            filename = st.session_state.get("upload_title", "IPL_Match42_HL_Final.mp4")

        st.markdown(f"""
            <div style="padding:16px;">
                <div style="
                    display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:12px;
                ">
                    <div>
                        <div style="font-size:14px;font-weight:600;
                                    color:{COLORS['text_primary']};margin-bottom:2px;">
                            {filename}
                        </div>
                        <div style="font-size:11px;color:{COLORS['text_muted']};">
                            Uploaded 12 mins ago
                        </div>
                    </div>
                    <span style="
                        background:rgba(34,197,94,0.15);
                        color:#86EFAC;
                        border:1px solid rgba(34,197,94,0.3);
                        padding:3px 10px;border-radius:4px;
                        font-size:10px;font-weight:700;
                        letter-spacing:.08em;text-transform:uppercase;
                    ">PROTECTED</span>
                </div>
                <div style="display:flex;gap:24px;">
                    <div>
                        <div style="font-size:9px;color:{COLORS['text_muted']};
                                    text-transform:uppercase;letter-spacing:.1em;
                                    margin-bottom:3px;">Bitrate</div>
                        <div style="font-size:14px;font-weight:600;
                                    color:{COLORS['text_primary']};">18.4 Mbps</div>
                    </div>
                    <div>
                        <div style="font-size:9px;color:{COLORS['text_muted']};
                                    text-transform:uppercase;letter-spacing:.1em;
                                    margin-bottom:3px;">Codec</div>
                        <div style="font-size:14px;font-weight:600;
                                    color:{COLORS['text_primary']};">H.264 High</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # JSON response block
        if st.session_state.get("upload_success") and st.session_state.get("upload_response"):
            resp = st.session_state["upload_response"]
            json_html = render_json_block(resp)
            st.markdown(f"""
            <div style="
                display:flex;justify-content:space-between;align-items:center;
                margin-bottom:8px;
            ">
                <div style="font-size:10px;font-weight:700;letter-spacing:.12em;
                            text-transform:uppercase;color:{COLORS['text_muted']};">
                    Registry Response</div>
                <span style="font-size:10px;color:{COLORS['text_muted']};
                             cursor:pointer;padding:2px 8px;
                             border:1px solid {COLORS['border']};border-radius:3px;">⎘</span>
            </div>
            <div class="sg-code-block">
                {{<br>{json_html}}}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                display:flex;justify-content:space-between;align-items:center;
                margin-bottom:8px;
            ">
                <div style="font-size:10px;font-weight:700;letter-spacing:.12em;
                            text-transform:uppercase;color:{COLORS['text_muted']};">
                    Registry Response</div>
            </div>
            <div class="sg-code-block" style="color:{COLORS['text_muted']}">
                // Response will appear here after fingerprinting...
            </div>
            """, unsafe_allow_html=True)