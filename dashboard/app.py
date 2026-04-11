import streamlit as st

# ── Must be first Streamlit call ─────────────────────────────────────────────
st.set_page_config(
    page_title="SportsGuard AI — Tactical Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports after page config ─────────────────────────────────────────────────
from branding import (
    inject_global_css,
    render_sidebar_logo,
    render_sidebar_status,
    COLORS,
)
import dashboard_page
import upload_page
import detection_page
import dmca_page

# ── Session state defaults ────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "active_page":        "Dashboard",
        "demo_mode":          True,
        "backend_live":       False,
        "upload_success":     False,
        "upload_reg_id":      None,
        "upload_response":    None,
        "upload_title":       None,
        "detections_list":    None,
        "selected_violation": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ── Inject global CSS ─────────────────────────────────────────────────────────
inject_global_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_logo()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Nav items with icons
    NAV_ITEMS = {
        "Dashboard":      "⊞  Dashboard",
        "Upload":         "⬆  Upload",
        "Detection Feed": "◎  Detection Feed",
        "DMCA Reports":   "☰  DMCA Reports",
    }

    # Render nav using radio (hidden label, styled via CSS)
    selected = st.radio(
        "Navigation",
        list(NAV_ITEMS.keys()),
        format_func=lambda x: NAV_ITEMS[x],
        key="nav_radio",
        label_visibility="hidden",
    )
    st.session_state["active_page"] = selected

    # Spacer
    st.markdown(
        f"<div style='flex:1;min-height:40px;'></div>",
        unsafe_allow_html=True,
    )

    # Demo mode toggle
    st.markdown(f"""
    <div style="padding:8px 16px 0 16px;">
        <div style="font-size:9px;font-weight:700;letter-spacing:.1em;
                    text-transform:uppercase;color:{COLORS['text_muted']};
                    margin-bottom:6px;">Mode</div>
    </div>
    """, unsafe_allow_html=True)

    demo_mode = st.toggle(
        "Demo Mode",
        value=st.session_state["demo_mode"],
        key="demo_toggle",
        help="When ON: uses mock data. Safe for live presentations.",
    )
    st.session_state["demo_mode"] = demo_mode

    # Backend status
    render_sidebar_status(
        backend_live=st.session_state["backend_live"],
        demo_mode=demo_mode,
    )

    # Sentinel mode panel
    sentinel_color = COLORS["accent"] if demo_mode else COLORS["success"]
    st.markdown(f"""
    <div style="
        margin: 8px 12px 12px 12px;
        background: rgba(245,158,11,0.06);
        border: 1px solid rgba(245,158,11,0.2);
        border-radius: 6px;
        padding: 10px 12px;
    ">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
            <div style="width:6px;height:6px;background:{sentinel_color};
                        border-radius:50%;animation:pulse-dot 1.5s infinite;"></div>
            <span style="font-size:10px;font-weight:700;letter-spacing:.1em;
                         text-transform:uppercase;color:{COLORS['accent']};">
                Sentinel Mode</span>
        </div>
        <div style="font-size:10px;color:{COLORS['text_muted']};line-height:1.5;">
            {'Demo data active' if demo_mode else 'Live threat monitoring active'}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Route to pages ────────────────────────────────────────────────────────────
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
    # Demo-safe fallback — never show raw traceback
    st.markdown(f"""
    <div style="
        background:rgba(239,68,68,0.08);
        border:1px solid rgba(239,68,68,0.25);
        border-left:3px solid #EF4444;
        border-radius:6px;padding:20px;
        font-family:'JetBrains Mono',monospace;font-size:12px;
    ">
        <div style="color:#FCA5A5;font-weight:700;margin-bottom:6px;">
            ⚠ Runtime Error — Demo Mode Active
        </div>
        <div style="color:{COLORS['text_muted']}">{str(e)}</div>
        <div style="color:{COLORS['text_muted']};margin-top:8px;font-size:11px;">
            Switch to Demo Mode (sidebar toggle) to continue safely.
        </div>
    </div>
    """, unsafe_allow_html=True)