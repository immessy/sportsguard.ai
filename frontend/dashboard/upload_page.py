# dashboard/upload_page.py
# ─────────────────────────────────────────────────────────────────────────────
# Content registration page.
#
# Data source:
#   - do_upload(file_bytes, filename, title) → POST /api/upload (or mock)
# Loader passed via session_state from app.py
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import time
from branding import COLORS, page_header


def render_json_block(data, indent=0):
    lines = []
    pad = "&nbsp;" * (indent * 4)
    for k, v in data.items():
        key_html = f'<span class="json-key">"{k}"</span>'
        if isinstance(v, dict):
            inner = render_json_block(v, indent + 1)
            lines.append(f'{pad}  {key_html}: {{<br>{inner}{pad}  }},')
        elif isinstance(v, bool):
            lines.append(f'{pad}  {key_html}: <span class="json-bool">{"true" if v else "false"}</span>,')
        elif isinstance(v, int):
            lines.append(f'{pad}  {key_html}: <span class="json-num">{v}</span>,')
        elif isinstance(v, list):
            items = ", ".join(f'<span class="json-str">"{i}"</span>' for i in v)
            lines.append(f'{pad}  {key_html}: [{items}],')
        else:
            lines.append(f'{pad}  {key_html}: <span class="json-str">"{v}"</span>,')
    return "<br>".join(lines) + "<br>"


def render():
    page_header(
        "Content Registration",
        subtitle="Secure your intellectual property against illegal restreaming.",
        show_active=False,
    )

    # ── Success banner ────────────────────────────────────────────────────────
    if st.session_state.get("upload_success"):
        reg_id = st.session_state.get("upload_reg_id", "SG-7729-AX")
        st.markdown(f"""
        <div class="sg-banner-success">
            <span style="font-size:16px">✅</span>
            <div>
                Video registered! 143 frames fingerprinted.
                <span style="font-family:'JetBrains Mono',monospace;
                             color:{COLORS['accent']};font-size:11px;
                             margin-left:12px;">{reg_id}</span>
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

    left_col, right_col = st.columns([1, 1], gap="large")

    # ── LEFT: Form ────────────────────────────────────────────────────────────
    with left_col:
        st.markdown(f"""
        <div style="background:{COLORS['bg_secondary']};border:1px solid {COLORS['border']};
                    border-radius:10px;padding:24px;">
            <div style="font-family:'Rajdhani',sans-serif;font-size:20px;font-weight:700;
                        color:{COLORS['text_primary']};margin-bottom:6px;">
                Register Official Content</div>
            <div style="font-size:12px;color:{COLORS['text_muted']};margin-bottom:20px;">
                Secure your intellectual property against illegal restreaming.</div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "DROP MP4 OR MOV FILE HERE",
            type=["mp4", "mov"],
            key="video_upload",
            label_visibility="collapsed",
        )

        st.markdown(f"""
        <div style="text-align:center;padding:20px 0 12px;">
            <div style="border:1.5px dashed rgba(245,158,11,0.3);border-radius:10px;
                        padding:28px 20px;background:rgba(245,158,11,0.02);">
                <div style="font-size:32px;margin-bottom:8px;">⬆️</div>
                <div style="font-size:14px;color:{COLORS['text_secondary']};margin-bottom:4px;">
                    Drag and drop MP4 or MOV file here</div>
                <div style="font-size:11px;color:{COLORS['text_muted']};margin-bottom:10px;">
                    Maximum file size: 2.0 GB</div>
                <div style="font-size:11px;font-weight:700;color:{COLORS['accent']};
                            letter-spacing:.1em;text-transform:uppercase;cursor:pointer;">
                    Browse Local Files</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        content_title = st.text_input(
            "CONTENT TITLE",
            placeholder="e.g. IPL Match 42 Highlights",
            key="content_title",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.text_input("RIGHTS HOLDER", value="Sports Media Group Ltd.", key="rights_holder")
        with col_b:
            st.selectbox("REGION", ["Global Rights","IN-WEST","IN-EAST","Asia Pacific","Europe"], key="region")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("🔒  FINGERPRINT & PROTECT", key="fingerprint_btn"):
            if not content_title:
                st.warning("Please enter a content title before protecting.")
            else:
                # ── INTEGRATION POINT ────────────────────────────────────────
                # do_upload is injected by app.py and calls either:
                #   - api_client.upload_video() → POST /api/upload (real)
                #   - MOCK_UPLOAD_RESPONSE      → instant fallback
                do_upload = st.session_state.get("do_upload")

                with st.spinner("Fingerprinting..."):
                    st.markdown(f"""
                    <div style="background:{COLORS['bg_tertiary']};border:1px solid {COLORS['border']};
                                border-radius:6px;padding:12px 16px;
                                font-family:'JetBrains Mono',monospace;font-size:11px;
                                color:{COLORS['accent']};margin:8px 0;">
                        ⚙️ Extracting keyframes at 1 FPS...<br>
                        🔐 Generating perceptual hashes (pHash-512)...<br>
                        💾 Writing fingerprints to sentinel database...
                    </div>
                    """, unsafe_allow_html=True)

                    if do_upload and uploaded_file:
                        resp = do_upload(
                            uploaded_file.read(),
                            uploaded_file.name,
                            content_title,
                        )
                    elif do_upload:
                        # No file selected — pass empty bytes, still returns mock
                        resp = do_upload(b"", "demo_clip.mp4", content_title)
                    else:
                        # Fallback if session_state not set yet
                        time.sleep(1)
                        resp = {
                            "video_id": 7,
                            "title": content_title,
                            "frames_processed": 143,
                            "status": "protected",
                            "registry_id": "SG-7729-AX",
                            "fingerprint": {"frames_processed": 143,
                                            "hash_algorithm": "pHash-512/Sentinel",
                                            "root_merkle": "0xBf2a...f921"},
                            "protection": {"takedown_enabled": True,
                                           "whitelist": ["youtube.com/official"]},
                        }

                if resp.get("status") == "error":
                    st.error(f"Upload failed: {resp.get('message', 'Unknown error')}")
                else:
                    st.session_state["upload_success"]  = True
                    st.session_state["upload_reg_id"]   = resp.get("registry_id", "SG-0001")
                    st.session_state["upload_response"] = resp
                    st.session_state["upload_title"]    = content_title
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── RIGHT: Preview + JSON ─────────────────────────────────────────────────
    with right_col:
        filename = (
            uploaded_file.name
            if uploaded_file
            else st.session_state.get("upload_title", "IPL_Match42_HL_Final.mp4")
        )

        st.markdown(f"""
        <div style="background:{COLORS['bg_secondary']};border:1px solid {COLORS['border']};
                    border-radius:10px;overflow:hidden;margin-bottom:16px;">
            <div style="background:{COLORS['bg_tertiary']};height:140px;
                        display:flex;align-items:center;justify-content:center;
                        border-bottom:1px solid {COLORS['border']};position:relative;">
                <div style="text-align:center;">
                    <div style="font-size:36px;margin-bottom:6px;opacity:0.4">▶</div>
                    <div style="font-size:11px;color:{COLORS['text_muted']};">Video preview area</div>
                </div>
                <div style="position:absolute;bottom:10px;right:10px;font-size:9px;font-weight:700;
                            letter-spacing:.1em;color:{COLORS['accent']};
                            background:rgba(245,158,11,0.12);
                            border:1px solid rgba(245,158,11,0.25);
                            padding:2px 8px;border-radius:3px;text-transform:uppercase;">
                    ● Fingerprinting Engine Active</div>
            </div>
        """, unsafe_allow_html=True)

        if uploaded_file:
            st.video(uploaded_file)

        st.markdown(f"""
            <div style="padding:16px;">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:12px;">
                    <div>
                        <div style="font-size:14px;font-weight:600;
                                    color:{COLORS['text_primary']};margin-bottom:2px;">
                            {filename}</div>
                        <div style="font-size:11px;color:{COLORS['text_muted']};">
                            Uploaded 12 mins ago</div>
                    </div>
                    <span style="background:rgba(34,197,94,0.15);color:#86EFAC;
                                 border:1px solid rgba(34,197,94,0.3);padding:3px 10px;
                                 border-radius:4px;font-size:10px;font-weight:700;
                                 letter-spacing:.08em;text-transform:uppercase;">
                        PROTECTED</span>
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
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:8px;">
            <div style="font-size:10px;font-weight:700;letter-spacing:.12em;
                        text-transform:uppercase;color:{COLORS['text_muted']};">
                Registry Response</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get("upload_success") and st.session_state.get("upload_response"):
            resp = st.session_state["upload_response"]
            json_html = render_json_block(resp)
            st.markdown(f"""
            <div class="sg-code-block">{{<br>{json_html}}}</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="sg-code-block" style="color:{COLORS['text_muted']}">
                // Response will appear here after fingerprinting...
            </div>
            """, unsafe_allow_html=True)