import streamlit as st

# ─── Design Tokens ────────────────────────────────────────────────────────────
# Rustic ledger: weathered wood & leather, oxidized red, cream ink (no stark black)
COLORS = {
    "bg_primary":    "#4D3F36",   # weathered oak — main field
    "bg_secondary":  "#5C4D42",   # lifted card / folio
    "bg_tertiary":   "#352820",   # cellar leather — sidebar
    "accent":        "#8F2E2E",   # oxidized barn red
    "accent_hover":  "#A84848",
    "accent_dim":    "#5C2424",
    "danger":        "#B04A40",
    "danger_dim":    "#4A2820",
    "success":       "#6E8562",   # dried sage
    "success_dim":   "#3A4534",
    "warning":       "#A67C2E",   # brass / aged gold
    "warning_dim":   "#5C4A22",
    "medium":        "#A0703A",   # rusted iron
    "medium_dim":    "#5C3D22",
    "text_primary":  "#F2E8D5",   # cream parchment
    "text_secondary": "#C9B99E",
    "text_muted":    "#8A7B6A",
    "border":        "#6E5E52",
    "border_accent": "rgba(143, 46, 46, 0.4)",
    "accent_rgba":   "143, 46, 46",
}

def inject_global_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Alegreya:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Cormorant+Garamond:wght@500;600;700&family=Courier+Prime:wght@400;700&display=swap');

    :root {{
        --sg-font-display: 'Cormorant Garamond', Georgia, 'Times New Roman', serif;
        --sg-font-body: 'Alegreya', Georgia, 'Times New Roman', serif;
        --sg-font-mono: 'Courier Prime', 'Courier New', monospace;
    }}

    /* ── Reset & Base ── */
    html, body, [class*="css"] {{
        font-family: var(--sg-font-body) !important;
        background-color: {COLORS['bg_primary']} !important;
        color: {COLORS['text_primary']} !important;
    }}
    .stApp {{
        background-color: {COLORS['bg_primary']} !important;
        background-image:
            radial-gradient(ellipse at 12% 5%, rgba(143, 46, 46, 0.07) 0%, transparent 50%),
            radial-gradient(ellipse at 88% 95%, rgba(45, 32, 24, 0.35) 0%, transparent 45%),
            linear-gradient(175deg, rgba(78, 62, 52, 0.5) 0%, {COLORS['bg_primary']} 42%);
    }}
    /* Subtle paper / linen grain — feels hand-made, not glass UI */
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 5;
        opacity: 0.04;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='a'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23a)'/%3E%3C/svg%3E");
    }}

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    div[data-testid="stToolbar"] {{display: none;}}
    .viewerBadge_container__1QSob {{display: none;}}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background-color: {COLORS['bg_tertiary']} !important;
        border-right: 1px solid {COLORS['border']} !important;
        min-width: 220px !important;
        max-width: 220px !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
    }}

    /* ── Radio nav buttons ── */
    [data-testid="stSidebar"] .stRadio > label {{display: none;}}
    [data-testid="stSidebar"] .stRadio > div {{
        display: flex;
        flex-direction: column;
        gap: 2px;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
        display: flex !important;
        align-items: center !important;
        padding: 10px 16px !important;
        border-radius: 3px !important;
        cursor: pointer !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: {COLORS['text_secondary']} !important;
        transition: all 0.15s ease !important;
        border-left: 2px solid transparent !important;
        margin: 1px 8px !important;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
        background: rgba(143, 46, 46, 0.1) !important;
        color: {COLORS['accent_hover']} !important;
        border-left-color: {COLORS['accent']} !important;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input:checked + div {{
        background: rgba(143, 46, 46, 0.16) !important;
        color: {COLORS['accent']} !important;
        border-left-color: {COLORS['accent']} !important;
    }}
    [data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] p {{
        font-size: 13px !important;
        margin: 0 !important;
    }}
    /* hide radio circle */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input[type="radio"] {{
        display: none !important;
    }}

    /* ── Main content padding ── */
    .main .block-container {{
        padding: 1.5rem 2rem 2rem 2rem !important;
        max-width: 100% !important;
    }}

    /* ── Metric cards ── */
    .sg-metric-card {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-top: 2px solid {COLORS['accent']};
        border-radius: 4px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s;
        box-shadow: inset 0 1px 0 rgba(242, 232, 213, 0.07),
                    2px 3px 0 rgba(26, 18, 14, 0.28);
    }}
    .sg-metric-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 60px;
        background: linear-gradient(180deg, rgba(143, 46, 46, 0.08) 0%, transparent 100%);
        pointer-events: none;
    }}
    .sg-metric-card:hover {{
        border-color: {COLORS['accent']};
        border-top-color: {COLORS['accent_hover']};
    }}
    .sg-metric-label {{
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: {COLORS['text_secondary']};
        margin-bottom: 8px;
    }}
    .sg-metric-value {{
        font-family: var(--sg-font-display);
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
    .sg-metric-delta.up {{color: {COLORS['success']};}}
    .sg-metric-delta.down {{color: {COLORS['danger']};}}
    .sg-metric-delta.good {{color: {COLORS['success']};}}
    .sg-metric-icon {{
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 22px;
        opacity: 0.6;
    }}

    /* ── Section headers ── */
    .sg-section-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
    }}
    .sg-section-title {{
        font-family: var(--sg-font-display);
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: none;
        font-variant: small-caps;
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
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(143, 46, 46, 0.45); }}
        50% {{ box-shadow: 0 0 0 5px rgba(143, 46, 46, 0); }}
    }}

    /* ── Panel / card container ── */
    .sg-panel {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 20px;
        box-shadow: inset 0 1px 0 rgba(242, 232, 213, 0.05);
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
    .badge-critical {{
        background: rgba(143, 46, 46, 0.2);
        color: #e8c4c0;
        border: 1px solid rgba(143, 46, 46, 0.4);
    }}
    .badge-medium {{
        background: rgba(193, 127, 58, 0.18);
        color: #e8c9a8;
        border: 1px solid rgba(193, 127, 58, 0.35);
    }}
    .badge-low {{
        background: rgba(125, 154, 110, 0.18);
        color: #d4e4cc;
        border: 1px solid rgba(125, 154, 110, 0.35);
    }}
    .badge-piracy    {{ background: rgba(143, 46, 46, 0.2);  color: #e8c4c0; border: 1px solid rgba(143, 46, 46, 0.4); }}
    .badge-transform {{ background: rgba(193, 127, 58, 0.18); color: #e8c9a8; border: 1px solid rgba(193, 127, 58, 0.35); }}
    .badge-meme      {{ background: rgba(125, 154, 110, 0.18);  color: #d4e4cc; border: 1px solid rgba(125, 154, 110, 0.35); }}

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
    }}
    .sg-table td {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        padding: 11px 12px;
        border-bottom: 1px solid rgba(107, 88, 78, 0.45);
        vertical-align: middle;
    }}
    .sg-table tr:hover td {{ background: rgba(143, 46, 46, 0.07); color: {COLORS['text_primary']}; }}
    .sg-table .url-cell {{
        font-family: var(--sg-font-mono);
        font-size: 11px;
        color: {COLORS['text_primary']};
        max-width: 200px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .sg-table .conf-high {{ color: {COLORS['danger']}; font-weight: 700; font-family: var(--sg-font-display); font-size: 14px; }}
    .sg-table .conf-med  {{ color: {COLORS['medium']}; font-weight: 700; font-family: var(--sg-font-display); font-size: 14px; }}
    .sg-table .conf-low  {{ color: {COLORS['success']}; font-weight: 700; font-family: var(--sg-font-display); font-size: 14px; }}

    /* ── Action buttons in table ── */
    .btn-takedown {{
        background: rgba(143, 46, 46, 0.18);
        color: #e8c4c0;
        border: 1px solid rgba(143, 46, 46, 0.4);
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        cursor: pointer;
        text-transform: uppercase;
    }}
    .btn-review {{
        background: rgba(193, 127, 58, 0.14);
        color: #e8c9a8;
        border: 1px solid rgba(193, 127, 58, 0.35);
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        cursor: pointer;
        text-transform: uppercase;
    }}
    .btn-ignore {{
        background: rgba(107, 88, 78, 0.35);
        color: {COLORS['text_secondary']};
        border: 1px solid rgba(107, 88, 78, 0.5);
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        cursor: pointer;
        text-transform: uppercase;
    }}

    /* ── Primary CTA button ── */
    .stButton > button {{
        background: {COLORS['accent']} !important;
        color: {COLORS['text_primary']} !important;
        border: none !important;
        border-radius: 3px !important;
        font-family: var(--sg-font-body) !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        letter-spacing: 0.04em !important;
        padding: 10px 24px !important;
        transition: background 0.2s ease, box-shadow 0.2s ease !important;
        text-transform: none !important;
        font-variant: small-caps !important;
        width: 100% !important;
        box-shadow: 1px 2px 0 rgba(26, 18, 14, 0.35) !important;
    }}
    .stButton > button:hover {{
        background: {COLORS['accent_hover']} !important;
        box-shadow: 2px 3px 0 rgba(26, 18, 14, 0.3) !important;
    }}
    .stButton > button:active {{
        box-shadow: 1px 1px 0 rgba(26, 18, 14, 0.4) !important;
    }}

    /* ── Outlined button variant ── */
    .btn-outlined {{
        background: transparent !important;
        color: {COLORS['accent']} !important;
        border: 1px solid {COLORS['accent']} !important;
    }}
    .btn-outlined:hover {{
        background: rgba(143, 46, 46, 0.12) !important;
    }}

    /* ── Log panel ── */
    .sg-log-panel {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 16px;
        font-family: var(--sg-font-mono);
        font-size: 11px;
        line-height: 1.7;
        max-height: 160px;
        overflow-y: auto;
    }}
    .log-alert   {{ color: {COLORS['danger']}; }}
    .log-info    {{ color: {COLORS['text_secondary']}; }}
    .log-success {{ color: {COLORS['success']}; }}
    .log-ts      {{ color: {COLORS['accent']}; margin-right: 6px; }}

    /* ── Upload zone ── */
    .sg-upload-zone {{
        border: 1.5px dashed rgba(143, 46, 46, 0.4);
        border-radius: 10px;
        padding: 40px 24px;
        text-align: center;
        background: rgba(52, 38, 31, 0.35);
        transition: all 0.2s;
        cursor: pointer;
    }}
    .sg-upload-zone:hover {{
        border-color: {COLORS['accent']};
        background: rgba(143, 46, 46, 0.08);
    }}
    .sg-upload-icon {{
        font-size: 36px;
        margin-bottom: 12px;
        opacity: 0.7;
    }}
    .sg-upload-text {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
        margin-bottom: 6px;
    }}
    .sg-upload-subtext {{
        font-size: 11px;
        color: {COLORS['text_muted']};
    }}

    /* ── Code / JSON block ── */
    .sg-code-block {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border']};
        border-left: 3px solid {COLORS['accent']};
        border-radius: 6px;
        padding: 16px;
        font-family: var(--sg-font-mono);
        font-size: 11px;
        line-height: 1.7;
        color: {COLORS['text_secondary']};
        white-space: pre;
        overflow-x: auto;
    }}
    .json-key   {{ color: {COLORS['accent']}; }}
    .json-str   {{ color: #c4d4b8; }}
    .json-num   {{ color: #d4c4b6; }}
    .json-bool  {{ color: #F9A8D4; }}

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {{
        background: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 6px !important;
        color: {COLORS['text_primary']} !important;
        font-size: 13px !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {COLORS['accent']} !important;
        box-shadow: 0 0 0 2px rgba(143, 46, 46, 0.2) !important;
    }}
    .stTextInput label, .stSelectbox label {{
        font-size: 10px !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: {COLORS['text_secondary']} !important;
    }}

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {{
        background: {COLORS['bg_tertiary']};
        border: 1.5px dashed rgba(143, 46, 46, 0.35);
        border-radius: 10px;
        padding: 8px;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: {COLORS['accent']};
    }}
    [data-testid="stFileUploader"] label {{
        color: {COLORS['text_secondary']} !important;
        font-size: 13px !important;
    }}
    [data-testid="stFileUploader"] section {{
        border: none !important;
        background: transparent !important;
    }}

    /* ── Toggle / checkbox ── */
    .stToggle > label span {{
        font-size: 12px !important;
        color: {COLORS['text_secondary']} !important;
        font-weight: 500 !important;
    }}

    /* ── Selectbox ── */
    .stSelectbox > div > div > div {{
        background: {COLORS['bg_tertiary']} !important;
        border-color: {COLORS['border']} !important;
        color: {COLORS['text_primary']} !important;
    }}

    /* ── Divider ── */
    hr {{
        border-color: {COLORS['border']} !important;
        margin: 16px 0 !important;
    }}

    /* ── Page title ── */
    .sg-page-title {{
        font-family: var(--sg-font-display);
        font-size: 32px;
        font-weight: 700;
        color: {COLORS['text_primary']};
        letter-spacing: -0.5px;
        line-height: 1.1;
        margin-bottom: 2px;
    }}
    .sg-page-subtitle {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        letter-spacing: 0.04em;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .sg-status-live {{
        color: {COLORS['text_secondary']};
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 0.04em;
        text-transform: none;
        font-style: italic;
        padding: 3px 10px;
        background: rgba(53, 40, 32, 0.45);
        border-radius: 2px;
        border: 1px solid {COLORS['border']};
    }}

    /* ── Warning / info banners ── */
    .sg-banner-warning {{
        background: rgba(184, 134, 11, 0.1);
        border: 1px solid rgba(184, 134, 11, 0.35);
        border-left: 3px solid {COLORS['warning']};
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 12px;
        color: {COLORS['text_secondary']};
        margin-bottom: 16px;
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }}
    .sg-banner-success {{
        background: rgba(125, 154, 110, 0.12);
        border: 1px solid rgba(125, 154, 110, 0.35);
        border-left: 3px solid {COLORS['success']};
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 12px;
        color: #dce8d4;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 500;
    }}
    .sg-banner-info {{
        background: rgba(107, 88, 78, 0.35);
        border: 1px solid rgba(209, 196, 182, 0.25);
        border-left: 3px solid {COLORS['text_secondary']};
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 12px;
        color: {COLORS['text_secondary']};
        margin-bottom: 16px;
    }}

    /* ── DMCA notice block ── */
    .sg-dmca-notice {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 20px;
        font-size: 12px;
        color: {COLORS['text_secondary']};
        line-height: 1.8;
        font-family: var(--sg-font-mono);
        white-space: pre-wrap;
    }}
    .dmca-heading {{
        color: {COLORS['text_primary']};
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }}
    .dmca-label  {{ color: {COLORS['accent']}; font-weight: 600; }}
    .dmca-value  {{ color: {COLORS['text_primary']}; }}

    /* ── Violation card ── */
    .sg-violation-card {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: border-color 0.15s;
    }}
    .sg-violation-card:hover {{
        border-color: {COLORS['accent']};
    }}
    .sg-violation-card.active {{
        border-color: {COLORS['accent']};
        background: rgba(143, 46, 46, 0.08);
    }}
    .sg-violation-id {{
        font-family: var(--sg-font-mono);
        font-size: 10px;
        color: {COLORS['accent']};
        margin-bottom: 4px;
        font-weight: 600;
    }}
    .sg-violation-title {{
        font-size: 13px;
        font-weight: 600;
        color: {COLORS['text_primary']};
        margin-bottom: 4px;
    }}
    .sg-violation-url {{
        font-size: 10px;
        color: {COLORS['text_muted']};
        font-family: var(--sg-font-mono);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .sg-violation-status {{
        float: right;
        font-size: 10px;
        color: {COLORS['accent']};
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: -30px;
    }}

    /* ── System integrity panel ── */
    .sg-integrity-panel {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 20px;
        text-align: center;
        box-shadow: inset 0 1px 0 rgba(242, 232, 213, 0.05);
    }}
    .sg-integrity-icon {{
        font-size: 40px;
        margin-bottom: 10px;
    }}
    .sg-integrity-title {{
        font-family: var(--sg-font-display);
        font-size: 17px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: none;
        font-variant: small-caps;
        color: {COLORS['text_primary']};
        margin-bottom: 8px;
    }}
    .sg-integrity-text {{
        font-size: 11px;
        color: {COLORS['text_muted']};
        line-height: 1.6;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-track {{ background: {COLORS['bg_primary']}; }}
    ::-webkit-scrollbar-thumb {{ background: {COLORS['border']}; border-radius: 2px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {COLORS['accent']}; }}

    /* ── Plotly chart bg ── */
    .js-plotly-plot .plotly .bg {{ fill: transparent !important; }}

    /* ── Streamlit column gaps ── */
    [data-testid="column"] {{ padding: 0 6px !important; }}
    [data-testid="column"]:first-child {{ padding-left: 0 !important; }}
    [data-testid="column"]:last-child  {{ padding-right: 0 !important; }}

    /* ── Tooltip override ── */
    .stTooltipIcon {{ color: {COLORS['text_muted']} !important; }}

    /* ── View all link ── */
    .sg-view-all {{
        font-size: 11px;
        color: {COLORS['accent']};
        text-decoration: none;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        cursor: pointer;
        margin-left: auto;
    }}
    .sg-view-all:hover {{ color: {COLORS['accent_hover']}; }}

    /* ── Breadcrumb ── */
    .sg-breadcrumb {{
        font-size: 11px;
        color: {COLORS['text_muted']};
        margin-bottom: 4px;
    }}
    .sg-breadcrumb span {{ color: {COLORS['text_secondary']}; }}
    </style>
    """, unsafe_allow_html=True)


def render_sidebar_logo():
    st.markdown(f"""
    <div style="
        padding: 20px 16px 16px 16px;
        border-bottom: 1px solid {COLORS['border']};
        margin-bottom: 8px;
    ">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="
                width: 32px; height: 32px;
                background: {COLORS['accent']};
                border-radius: 2px;
                display: flex; align-items: center; justify-content: center;
                font-size: 16px;
                color: {COLORS['text_primary']};
                font-weight: 900;
                flex-shrink: 0;
            ">🛡</div>
            <div>
                <div style="
                    font-family: var(--sg-font-display);
                    font-size: 16px;
                    font-weight: 700;
                    color: {COLORS['text_primary']};
                    letter-spacing: 0.05em;
                    line-height: 1.1;
                ">SportsGuard AI</div>
                <div style="
                    font-size: 9px;
                    color: {COLORS['text_muted']};
                    letter-spacing: 0.12em;
                    text-transform: uppercase;
                ">Rights ledger</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_status(backend_live=True, demo_mode=True):
    status_color  = COLORS['success'] if backend_live else COLORS['danger']
    status_text   = "Backend Live"   if backend_live else "Backend Offline"
    demo_bg       = "rgba(143, 46, 46, 0.18)" if demo_mode else "transparent"
    demo_color    = COLORS['accent']        if demo_mode else COLORS['text_muted']
    st.markdown(f"""
    <div style="
        padding: 12px 16px;
        border-top: 1px solid {COLORS['border']};
        margin-top: 8px;
    ">
        <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
            <div style="width:7px;height:7px;background:{status_color};border-radius:50%;
                        animation:pulse-dot 2s infinite;"></div>
            <span style="font-size:11px;color:{COLORS['text_secondary']};font-weight:500;">
                {status_text}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label, value, delta, delta_type="up", icon="📊"):
    delta_class = delta_type
    arrow = "↑" if delta_type in ("up","good") else "↓"
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-icon">{icon}</div>
        <div class="sg-metric-label">{label}</div>
        <div class="sg-metric-value">{value}</div>
        <div class="sg-metric-delta {delta_class}">{arrow} {delta}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title, live=False, view_all=False):
    live_dot  = '<div class="sg-live-dot"></div>' if live else ""
    view_link = '<span class="sg-view-all">Full register →</span>' if view_all else ""
    st.markdown(f"""
    <div class="sg-section-header" style="display:flex;align-items:center;width:100%;">
        {live_dot}
        <span class="sg-section-title">{title}</span>
        {view_link}
    </div>
    """, unsafe_allow_html=True)


def risk_badge(classification):
    mapping = {
        "Piracy":        ("PIRACY",        "badge badge-piracy"),
        "Transformative":("TRANSFORMATIVE", "badge badge-transform"),
        "Meme":          ("MEME / FAN",     "badge badge-meme"),
        "CRITICAL":      ("● CRITICAL",     "badge badge-critical"),
        "MEDIUM":        ("● MEDIUM",       "badge badge-medium"),
        "LOW":           ("● LOW",          "badge badge-low"),
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
        {"<span class='sg-status-live'>On duty · match week</span>" if show_active else ""}
    </div>
    """, unsafe_allow_html=True)