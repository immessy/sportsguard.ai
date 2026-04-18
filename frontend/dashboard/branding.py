import streamlit as st

# ─── Design Tokens ────────────────────────────────────────────────────────────
COLORS = {
    "bg_primary":          "#F0F2FF",
    "bg_secondary":        "#FFFFFF",
    "bg_tertiary":         "#E8EAFF",
    "accent":              "#7C3AED",
    "accent_hover":        "#6D28D9",
    "accent_dim":          "#EDE9FE",
    "danger":              "#EF4444",
    "danger_dim":          "#FEE2E2",
    "success":             "#10B981",
    "success_dim":         "#D1FAE5",
    "warning":             "#F59E0B",
    "warning_dim":         "#FEF3C7",
    "medium":              "#8B5CF6",
    "medium_dim":          "#EDE9FE",
    "text_primary":        "#1E1B4B",
    "text_secondary":      "#6B7280",
    "text_muted":          "#9CA3AF",
    "border":              "#E5E7EB",
    "border_accent":       "#7C3AED33",
    "green_neon":          "#8B5CF6",
    # Sidebar
    "sidebar_bg":          "#2D1B69",
    "sidebar_border":      "#3D2A7D",
    "sidebar_text":        "#FFFFFF",
    "sidebar_active":      "#FFFFFF",
    "sidebar_hover_bg":    "rgba(167,139,250,0.15)",
    "sidebar_active_border":"#A78BFA",
}


def inject_global_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Reset & Base ── */
    html, body, [class*="css"] {{
        font-family: 'Outfit', sans-serif !important;
        background-color: {COLORS['bg_primary']} !important;
        color: {COLORS['text_primary']} !important;
    }}
    /* ── Full-Page Uiverse Background (Native Injection) ── */
    .stApp {{
        background-color: {COLORS['bg_primary']} !important;
        background-image: 
            linear-gradient(to bottom, rgba(30, 27, 75, 0.2) 0%, transparent 50%, rgba(124, 58, 237, 0.08) 100%),
            linear-gradient(to right, rgba(14, 210, 218, 0.18), rgba(95, 41, 199, 0.18)) !important;
        background-attachment: fixed !important;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 240px;
        right: 0;
        bottom: 0;
        background-image: linear-gradient(90deg, rgba(124, 58, 237, 0.1) 1px, transparent 1px);
        background-size: 50px 100%;
        pointer-events: none;
        z-index: 0;
        opacity: 0.9;
    }}

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}
    div[data-testid="stToolbar"] {{ display: none; }}
    .viewerBadge_container__1QSob {{ display: none; }}

    /* 1. Force sidebar to stay fixed, visible, and full-height */
    [data-testid="stSidebar"] {{
        position: fixed !important;
        top: 0 !important;
        bottom: 0 !important;
        height: 100vh !important;
        background-color: {COLORS['sidebar_bg']} !important;
        border-right: 1px solid {COLORS['sidebar_border']} !important;
        width: 240px !important;
        min-width: 240px !important;
        max-width: 240px !important;
        display: block !important;
        visibility: visible !important;
        z-index: 1000 !important;
        transform: none !important;
        transition: none !important;
        overflow-y: auto !important;
    }}

    /* 2. Fix the overlap by shifting the main dashboard and header */
    [data-testid="stMain"], [data-testid="stHeader"] {{
        margin-left: 240px !important;
        width: calc(100% - 240px) !important;
    }}

    /* 3. Hide BOTH arrows (the '<<' inside and the '>' outside) */
    [data-testid="stSidebarCollapseButton"], 
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    /* 4. Force expansion state regardless of internal Streamlit toggle */
    [data-testid="stSidebar"][aria-expanded="false"] {{
        margin-left: 0 !important;
        width: 240px !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
    }}

    /* Hide the radio group label text above the buttons */
    [data-testid="stSidebar"] .stRadio > label {{
        display: none !important;
    }}

    /* Stack radio items vertically */
    [data-testid="stSidebar"] .stRadio > div,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{
        display: flex !important;
        flex-direction: column !important;
        gap: 2px !important;
    }}

    /* ── Every nav label — always visible with text ── */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {{
        display: flex !important;
        align-items: center !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: {COLORS['sidebar_text']} !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }}

    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
        padding: 10px 16px !important;
        margin: 1px 8px !important;
        border-radius: 6px !important;
        border-left: 2px solid transparent !important;
        cursor: pointer !important;
    }}

    /* Force all text elements inside the label to inherit the white color */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div p {{
        color: {COLORS['sidebar_text']} !important;
        visibility: visible !important;
        opacity: 1 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }}

    /* Hover state */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
        background: {COLORS['sidebar_hover_bg']} !important;
        color: {COLORS['sidebar_active']} !important;
        border-left-color: {COLORS['sidebar_active_border']} !important;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover p,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover div p {{
        color: {COLORS['sidebar_active']} !important;
    }}

    /* Active / selected state — multiple selectors for Streamlit version compatibility */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"],
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input:checked ~ div,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input:checked + div {{
        background: {COLORS['sidebar_hover_bg']} !important;
        color: {COLORS['sidebar_active']} !important;
        border-left-color: {COLORS['sidebar_active_border']} !important;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] p,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] p {{
        color: {COLORS['sidebar_active']} !important;
    }}

    /* Hide the radio circle dot completely */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input[type="radio"] {{
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Hide any residual SVG circle/indicator Streamlit renders */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div:first-child {{
        display: none !important;
    }}

    /* ── Main content padding ── */
    .main .block-container {{
        padding: 1.5rem 2rem 2rem 2rem !important;
        max-width: 100% !important;
    }}

    h1, h2, h3 {{ 
        font-family: 'Syne', sans-serif; 
        font-weight: 800; 
        letter-spacing: -0.02em;
        margin-bottom: 1rem;
    }}

    /* ── Metric cards ── */
    .sg-metric-card {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-top: 2px solid {COLORS['accent']};
        border-radius: 12px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s;
        box-shadow: 0 2px 12px rgba(124,58,237,0.07);
    }}
    .sg-metric-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 60px;
        background: linear-gradient(180deg, rgba(124,58,237,0.05) 0%, transparent 100%);
        pointer-events: none;
    }}
    .sg-metric-card:hover {{
        border-top-color: {COLORS['accent_hover']};
        box-shadow: 0 4px 20px rgba(124,58,237,0.14);
        transform: translateY(-1px);
    }}
    .sg-metric-label {{
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: {COLORS['text_muted']};
        margin-bottom: 8px;
    }}
    .sg-metric-value {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 42px;
        font-weight: 700;
        color: {COLORS['text_primary']};
        line-height: 1;
        letter-spacing: -1px;
    }}
    .sg-metric-delta {{
        font-size: 11px;
        font-weight: 600;
        margin-top: 6px;
        display: inline-flex;
        align-items: center;
        gap: 3px;
    }}
    .sg-metric-delta.up   {{ color: {COLORS['success']}; }}
    .sg-metric-delta.down {{ color: {COLORS['danger']};  }}
    .sg-metric-delta.good {{ color: {COLORS['success']}; }}
    .sg-metric-icon {{
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 22px;
        opacity: 0.5;
    }}

    /* ── Section headers ── */
    .sg-section-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
    }}
    .sg-section-title {{
        font-family: 'Syne', sans-serif;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: {COLORS['text_primary']};
    }}
    .sg-live-dot {{
        width: 8px;
        height: 8px;
        background: {COLORS['accent']};
        border-radius: 50%;
        animation: pulse-dot 1.5s infinite;
        flex-shrink: 0;
    }}
    @keyframes pulse-dot {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(124,58,237,0.6); }}
        50%       {{ box-shadow: 0 0 0 5px rgba(124,58,237,0); }}
    }}

    /* ── Panel / card container ── */
    .sg-panel {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(124,58,237,0.05);
    }}

    /* ── Risk badges ── */
    .badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        white-space: nowrap;
    }}
    .badge-critical  {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #FECACA; }}
    .badge-medium    {{ background: #EDE9FE; color: #5B21B6; border: 1px solid #DDD6FE; }}
    .badge-low       {{ background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }}
    .badge-piracy    {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #FECACA; }}
    .badge-transform {{ background: #EDE9FE; color: #5B21B6; border: 1px solid #DDD6FE; }}
    .badge-meme      {{ background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }}

    /* ── Detection table ── */
    .sg-table {{ width: 100%; border-collapse: collapse; }}
    .sg-table th {{
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {COLORS['text_muted']};
        padding: 10px 12px;
        border-bottom: 1px solid {COLORS['border']};
        text-align: left;
        background: {COLORS['bg_tertiary']};
    }}
    .sg-table td {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        padding: 11px 12px;
        border-bottom: 1px solid {COLORS['border']};
        vertical-align: middle;
    }}
    .sg-table tr:hover td {{
        background: {COLORS['accent_dim']};
        color: {COLORS['text_primary']};
    }}
    .sg-table .url-cell {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: {COLORS['text_primary']};
        max-width: 200px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .sg-table .conf-high {{ color: {COLORS['danger']};  font-weight: 700; font-family: 'Space Grotesk', sans-serif; font-size: 14px; }}
    .sg-table .conf-med  {{ color: {COLORS['medium']}; font-weight: 700; font-family: 'Inter', sans-serif; font-size: 14px; }}
    .sg-table .conf-low  {{ color: {COLORS['success']}; font-weight: 700; font-family: 'Space Grotesk', sans-serif; font-size: 14px; }}

    /* ── Table action buttons ── */
    .btn-takedown {{
        background: #FEE2E2; color: #B91C1C; border: 1px solid #FECACA;
        padding: 3px 9px; border-radius: 4px; font-size: 10px;
        font-weight: 700; letter-spacing: 0.05em; cursor: pointer; text-transform: uppercase;
    }}
    .btn-review {{
        background: #EDE9FE; color: #5B21B6; border: 1px solid #DDD6FE;
        padding: 3px 9px; border-radius: 4px; font-size: 10px;
        font-weight: 700; letter-spacing: 0.05em; cursor: pointer; text-transform: uppercase;
    }}
    .btn-ignore {{
        background: #F3F4F6; color: {COLORS['text_muted']}; border: 1px solid {COLORS['border']};
        padding: 3px 9px; border-radius: 4px; font-size: 10px;
        font-weight: 700; letter-spacing: 0.05em; cursor: pointer; text-transform: uppercase;
    }}

    /* ── Primary CTA button ── */
    .stButton > button {{
        background: linear-gradient(135deg, #7C3AED, #8B5CF6) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        letter-spacing: 0.06em !important;
        padding: 10px 24px !important;
        transition: all 0.15s ease !important;
        text-transform: uppercase !important;
        width: 100% !important;
        box-shadow: 0 2px 8px rgba(124,58,237,0.25) !important;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, #6D28D9, #7C3AED) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(124,58,237,0.4) !important;
    }}

    /* ── Inputs ── */
    .stTextInput > div > div > input {{
        background: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        color: {COLORS['text_primary']} !important;
        font-size: 13px !important;
    }}
    .stTextInput label, .stSelectbox label {{
        font-size: 10px !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: {COLORS['text_muted']} !important;
    }}

    /* ── Sidebar Text Overrides ── */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] span,
    [data-testid="stSidebar"] .st-emotion-cache-121p6b1,
    [data-testid="stSidebar"] .st-emotion-cache-6q9sum,
    [data-testid="stSidebar"] .st-emotion-cache-162961b,
    [data-testid="stSidebar"] .st-emotion-cache-ocq96v,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {{
        color: #FFFFFF !important;
        opacity: 1 !important;
        font-family: 'Outfit', sans-serif !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    /* ── Page title ── */
    .sg-page-title {{
        font-family: 'Syne', sans-serif;
        font-size: 32px;
        font-weight: 700;
        color: {COLORS['text_primary']};
        letter-spacing: -0.5px;
        line-height: 1.1;
        margin-bottom: 2px;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar       {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: {COLORS['bg_primary']}; }}
    ::-webkit-scrollbar-thumb {{ background: {COLORS['accent']}; border-radius: 3px; }}

    /* ── Breadcrumb ── */
    .sg-breadcrumb {{ font-size: 11px; color: {COLORS['text_muted']}; margin-bottom: 4px; }}

    /* ── Content Type & DMCA Components ── */
    .sg-feature-card {{
        background: #FFFFFF;
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }}
    .sg-feature-title {{
        font-family: 'Syne', sans-serif;
        font-size: 16px;
        font-weight: 700;
        color: {COLORS['text_primary']};
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .sg-feature-subtitle {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        margin-bottom: 20px;
    }}
    .sg-ct-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .ct-raw      {{ background: #FEE2E2; color: #EF4444; border: 1px solid #FECACA; }}
    .ct-meme     {{ background: #D1FAE5; color: #10B981; border: 1px solid #A7F3D0; }}
    .ct-analysis {{ background: #DBEAFE; color: #3B82F6; border: 1px solid #BFDBFE; }}
    .ct-reaction {{ background: #FEF3C7; color: #F59E0B; border: 1px solid #FDE68A; }}

    .sg-dmca-preview {{
        background: #F8FAFC;
        color: #475569;
        padding: 16px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        line-height: 1.6;
        height: 160px;
        overflow-y: auto;
        border: 1px solid #E2E8F0;
        margin: 16px 0;
        white-space: pre-wrap;
    }}
    .sg-dmca-detail-row {{
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #F1F5F9;
        font-size: 12px;
    }}
    .sg-dmca-detail-label {{ color: {COLORS['text_muted']}; font-weight: 500; }}
    .sg-dmca-detail-value {{ color: {COLORS['text_primary']}; font-weight: 600; font-family: 'Space Grotesk', sans-serif; }}

    /* (Note: Pattern logic moved to .stApp for reliability) */
    </style>
    """, unsafe_allow_html=True)


def render_sidebar_logo():
    st.markdown(f"""
    <div style="padding: 20px 16px 16px 16px; border-bottom: 1px solid {COLORS['sidebar_border']}; margin-bottom: 8px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:32px; height:32px; background: linear-gradient(135deg, #7C3AED, #A78BFA); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; color:#FFFFFF; font-weight:900;">🛡</div>
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:16px; font-weight:700; color:#FFFFFF; letter-spacing:0.05em;">SportsGuard AI</div>
                <div style="font-size:9px; color:{COLORS['sidebar_text']}; letter-spacing:0.12em; text-transform:uppercase;">Tactical Hub</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_status(backend_live=False, demo_mode=True):
    status_color = COLORS['success'] if backend_live else COLORS['danger']
    status_text  = "Backend Live"    if backend_live else "Backend Offline"
    st.markdown(f"""
    <div style="padding: 12px 16px; border-top: 1px solid {COLORS['sidebar_border']}; margin-top: 8px;">
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:7px; height:7px; background:{status_color}; border-radius:50%; animation:pulse-dot 2s infinite;"></div>
            <span style="font-size:11px; color:{COLORS['sidebar_text']}; font-weight:500;">{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label, value, delta, delta_type="up", icon="📊"):
    arrow = "↑" if delta_type in ("up", "good") else "↓"
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-icon">{icon}</div>
        <div class="sg-metric-label">{label}</div>
        <div class="sg-metric-value">{value}</div>
        <div class="sg-metric-delta {delta_type}">{arrow} {delta}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title, live=False, view_all=False):
    live_dot  = '<div class="sg-live-dot"></div>' if live else ""
    view_link = '<span class="sg-view-all">VIEW ALL →</span>' if view_all else ""
    st.markdown(f"""
    <div class="sg-section-header" style="display:flex;align-items:center;">
        {live_dot}
        <span class="sg-section-title">{title}</span>
        {view_link}
    </div>
    """, unsafe_allow_html=True)


def risk_badge(classification):
    mapping = {
        "Piracy":         ("PIRACY",        "badge badge-piracy"),
        "Transformative": ("TRANSFORMATIVE", "badge badge-transform"),
        "Meme":           ("MEME / FAN",     "badge badge-meme"),
        "CRITICAL":       ("● CRITICAL",     "badge badge-critical"),
        "MEDIUM":         ("● MEDIUM",       "badge badge-medium"),
        "LOW":            ("● LOW",          "badge badge-low"),
    }
    label, cls = mapping.get(classification, (classification, "badge badge-meme"))
    return f'<span class="{cls}">{label}</span>'


def page_header(title, subtitle=None, breadcrumb=None, show_active=True):
    bc = f'<div class="sg-breadcrumb">{breadcrumb}</div>' if breadcrumb else ""
    st.markdown(f"""
    {bc}
    <div class="sg-page-title">{title}</div>
    <div class="sg-page-subtitle">
        {subtitle or ""}
        {"<span class='sg-status-live'>● ACTIVE MONITORING</span>" if show_active else ""}
    </div>
    """, unsafe_allow_html=True)


def render_header_decoration():
    """Renders the fixed background pattern decorative div."""
    st.markdown('<div class="sg-header-pattern"></div>', unsafe_allow_html=True)