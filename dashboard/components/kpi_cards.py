import streamlit as st

def render_kpi_card(title: str, value: str, subtext: str, color_hex: str = "#2563EB", icon: str = "📊"):
    """Renders a styled metric card for the executive dashboard."""
    card_html = f"""
    <div style="
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 5px solid {color_hex};
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    ">
        <div style="font-size: 0.9rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px;">
            {icon} {title}
        </div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #F3F4F6; margin: 4px 0;">
            {value}
        </div>
        <div style="font-size: 0.82rem; color: #6B7280;">
            {subtext}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_risk_badge(risk_level: str) -> str:
    """Returns HTML color-coded risk badge."""
    level = str(risk_level).capitalize()
    if level == "High":
        bg, color = "#7F1D1D", "#FCA5A5"
    elif level == "Medium":
        bg, color = "#78350F", "#FDE68A"
    else:
        bg, color = "#064E3B", "#A7F3D0"
        
    return f"""<span style="
        background-color: {bg};
        color: {color};
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    ">{level} Risk</span>"""
