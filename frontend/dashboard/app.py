# dashboard/app.py
# ─────────────────────────────────────────────────────────────────────────────
# Main entry point for SportsGuard AI dashboard.
# Handles sidebar nav, session state, and routing to page modules.
#
# Integration status (Prompt 8):
#   - api_client.py is imported and used throughout
#   - Demo Mode toggle controls whether real API or mock data is used
#   - All API calls fall back silently to mock — UI never crashes
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st

# ── Must be the very first Streamlit call ─────────────────────────────────────
st.set_page_config(
    page_title="SportsGuard AI — Tactical Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports after page config ─────────────────────────────────────────────────
import api_client
from branding import (
    inject_global_css,
    render_sidebar_logo,
    render_sidebar_status,
    render_header_decoration,
    COLORS,
)
import dashboard_page
import upload_page
import detection_page
import dmca_page


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "active_page":         "Dashboard",
        "demo_mode":           True,
        "backend_live":        False,
        "upload_success":      False,
        "upload_reg_id":       None,
        "upload_response":     None,
        "upload_title":        None,
        "detections_list":     None,
        "selected_violation":  None,
        "cached_stats":        None,
        "cached_detections":   None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ── Inject global CSS & Patterns ──────────────────────────────────────────────
inject_global_css()
render_header_decoration()


# ─────────────────────────────────────────────────────────────────────────────
# BACKEND HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────
def refresh_backend_status(demo_mode: bool):
    if demo_mode:
        st.session_state["backend_live"] = False
        api_client.MOCK_MODE = True
    else:
        api_client.MOCK_MODE = False
        is_live = api_client.check_backend_health()
        st.session_state["backend_live"] = is_live
        if not is_live:
            api_client.MOCK_MODE = True


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADERS — passed to pages via session state
# ─────────────────────────────────────────────────────────────────────────────
def load_stats() -> dict:
    return api_client.get_stats()

def load_detections() -> dict:
    return api_client.run_scan()

def do_upload(file_bytes: bytes, filename: str, title: str) -> dict:
    return api_client.upload_video(file_bytes, filename, title)

st.session_state["load_stats"]        = load_stats
st.session_state["load_detections"]   = load_detections
st.session_state["do_upload"]         = do_upload
st.session_state["get_sim_detection"] = api_client.get_simulated_detection


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_logo()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    NAV_ITEMS = {
        "Dashboard":      "⊞  Dashboard",
        "Upload":         "⬆  Upload",
        "Detection Feed": "◎  Detection Feed",
        "DMCA Reports":   "☰  DMCA Reports",
    }

    selected = st.radio(
        "Navigation",
        list(NAV_ITEMS.keys()),
        format_func=lambda x: NAV_ITEMS[x],
        key="nav_radio",
        label_visibility="hidden",
    )
    st.session_state["active_page"] = selected

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Demo Mode toggle ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding: 0 16px 4px 16px;">
        <div style="font-size:9px;font-weight:700;letter-spacing:.1em;
                    text-transform:uppercase;color:{COLORS['sidebar_text']};
                    margin-bottom:6px; font-family: 'Syne', sans-serif;">Mode</div>
    </div>
    """, unsafe_allow_html=True)

    prev_demo = st.session_state["demo_mode"]
    demo_mode = st.toggle(
        "Demo Mode",
        value=st.session_state["demo_mode"],
        key="demo_toggle",
        help="ON = mock data (safe for presentations). OFF = tries real Flask API.",
    )

    if demo_mode != prev_demo:
        st.session_state["demo_mode"]          = demo_mode
        st.session_state["cached_stats"]       = None
        st.session_state["cached_detections"]  = None
        refresh_backend_status(demo_mode)
        st.rerun()

    if st.session_state["cached_stats"] is None:
        refresh_backend_status(demo_mode)

    # ── Backend status ────────────────────────────────────────────────────────
    render_sidebar_status(
        backend_live=st.session_state["backend_live"],
        demo_mode=demo_mode,
    )

    # ── Sentinel mode panel ───────────────────────────────────────────────────
    is_live    = st.session_state["backend_live"]
    dot_color  = COLORS["success"] if is_live else COLORS["accent"]
    mode_text  = "Live threat monitoring active" if is_live else "Demo data active"
    mode_label = "LIVE MODE"  if is_live else "DEMO MODE"
    border_clr = "rgba(34,197,94,0.25)" if is_live else "rgba(245,158,11,0.2)"
    bg_clr     = "rgba(34,197,94,0.05)" if is_live else "rgba(245,158,11,0.06)"

    st.markdown(f"""
    <div style="
        margin: 8px 12px 12px 12px;
        background: {bg_clr};
        border: 1px solid {border_clr};
        border-radius: 6px;
        padding: 10px 12px;
    ">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
            <div style="width:6px;height:6px;background:{dot_color};
                        border-radius:50%;animation:pulse-dot 1.5s infinite;"></div>
            <span style="font-size:10px;font-weight:700;letter-spacing:.1em;
                         text-transform:uppercase;color:{dot_color}; font-family: 'Syne', sans-serif;">
                {mode_label}
            </span>
        </div>
        <div style="font-size:10px;color:{COLORS['sidebar_text']};line-height:1.5; opacity: 1;">
            {mode_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not demo_mode:
        st.markdown(f"""
        <div style="padding: 0 16px 8px 16px;">
            <div style="font-size:10px;color:{COLORS['sidebar_text']}; opacity: 1;">
                Flask:
                <span style="color:{'#22C55E' if is_live else '#EF4444'};">
                    {'✅ Connected' if is_live else '❌ Offline'}
                </span>
            </div>
            <div style="font-size:10px;color:{COLORS['sidebar_text']};margin-top:2px; opacity: 1;">
                MOCK_MODE:
                <span style="font-family:'JetBrains Mono',monospace;color:{COLORS['accent']};">
                    {api_client.MOCK_MODE}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────────────────────────────────────
page = st.session_state["active_page"]

try:
    if page == "Dashboard":
        dashboard_page.render()
    elif page == "Upload":
        upload_page.render()
    elif page == "Detection Feed":
        detection_page.render()
    elif page == "DMCA Reports":
        dmca_page.render()

except Exception as e:
    st.markdown(f"""
    <div style="
        background: rgba(239,68,68,0.08);
        border: 1px solid rgba(239,68,68,0.25);
        border-left: 3px solid #EF4444;
        border-radius: 6px;
        padding: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        margin-top: 20px;
    ">
        <div style="color:#FCA5A5;font-weight:700;margin-bottom:8px;">
            ⚠ Runtime Error — Switching to Demo Mode
        </div>
        <div style="color:{COLORS['text_muted']};margin-bottom:8px;">{str(e)}</div>
        <div style="color:{COLORS['text_muted']};font-size:11px;">
            Enable Demo Mode in the sidebar to continue safely.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state["demo_mode"] = True
    api_client.MOCK_MODE = True