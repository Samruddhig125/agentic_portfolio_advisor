import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

from models import UserProfile
from parser import parse_profile_text, parse_profile_url
from agents.multiagent_runner import run_multi_agent
from logic import (
    calculate_risk_assessment,
    generate_portfolio,
    generate_scenarios,
    generate_warnings,
    generate_next_steps,
    calculate_confidence_score,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio Advisor AI", layout="wide", page_icon="💼")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --gold: #D4AF37; --gold-dark: #B8962E;
    --navy: #1A252F; --navy-dark: #2C3E50; --charcoal: #34495E;
    --cream: #F8F9FA; --gold-glow: #FEF9E7;
}
* { font-family: 'Inter', sans-serif; }
.main { background: linear-gradient(135deg, var(--navy) 0%, var(--navy-dark) 50%, var(--charcoal) 100%); background-attachment: fixed; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }

.hero-container {
    background: linear-gradient(145deg, rgba(212,175,55,0.12), rgba(184,150,46,0.08), rgba(26,37,47,0.95));
    backdrop-filter: blur(25px); border: 1px solid rgba(212,175,55,0.35);
    border-radius: 24px; padding: 3rem 2.5rem; margin-bottom: 2.5rem;
    box-shadow: 0 35px 70px -20px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,55,0.2);
    position: relative; overflow: hidden;
}
.hero-container::before {
    content:''; position:absolute; top:0; left:0; right:0; height:1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent); opacity:0.7;
}
.hero-title {
    font-family: 'Playfair Display', serif; font-size: 2.8rem !important; font-weight: 700;
    background: linear-gradient(135deg, var(--gold-glow) 0%, var(--gold) 50%, #FAD5A5 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    letter-spacing: -0.03em; margin-bottom: 0.5rem;
}
.hero-subtitle { font-family: 'Playfair Display', serif; font-size: 1.2rem !important; color: #E8EDED; font-weight: 500; margin-bottom: 1rem; }
.hero-description { color: #B8C4CC; font-size: 1.1rem; line-height: 1.8; }
.pill-container { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 1.5rem; }
.pill {
    background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(184,150,46,0.15));
    border: 1px solid rgba(212,175,55,0.4); backdrop-filter: blur(12px);
    padding: 10px 20px; border-radius: 40px; font-size: 0.9rem; font-weight: 500; color: var(--gold-glow);
}

.metric-card {
    background: linear-gradient(145deg, rgba(248,249,250,0.08), rgba(26,37,47,0.9));
    backdrop-filter: blur(25px); border: 1px solid rgba(212,175,55,0.25);
    border-radius: 20px; padding: 1.8rem 1.5rem !important; text-align: center;
    position: relative; overflow: hidden; transition: all 0.4s ease;
}
.metric-card:hover { transform: translateY(-8px); box-shadow: 0 30px 60px -15px rgba(0,0,0,0.4); }
.metric-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
}
.metric-value {
    font-family: 'Playfair Display', serif; font-size: 2.2rem !important; font-weight: 700;
    background: linear-gradient(135deg, var(--gold) 0%, #FAD5A5 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.metric-label { color: #B8C4CC; font-size: 1rem; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 0.75rem; }
.metric-type { font-size: 1.1rem; font-weight: 600; color: #E8EDED; font-family: 'Playfair Display', serif; }

.section-container {
    background: linear-gradient(145deg, rgba(248,249,250,0.06), rgba(26,37,47,0.92));
    backdrop-filter: blur(25px); border: 1px solid rgba(212,175,55,0.2);
    border-radius: 20px; padding: 2rem !important; margin-top: 2rem;
    box-shadow: 0 25px 50px -15px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,175,55,0.1);
}
.section-title {
    font-family: 'Playfair Display', serif; font-size: 1.6rem !important; font-weight: 600;
    background: linear-gradient(135deg, var(--gold-glow) 0%, var(--gold) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin-bottom: 1.5rem !important; letter-spacing: -0.02em;
    display: flex; align-items: center; gap: 12px; word-break: break-word; line-height: 1.3;
}

/* AI explanation cards */
.ai-card {
    background: rgba(212,175,55,0.07); border: 1px solid rgba(212,175,55,0.25);
    border-radius: 16px; padding: 1.4rem 1.6rem; margin-bottom: 1rem;
}
.ai-card-title { color: var(--gold); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.6rem; }
.ai-card-body { color: #E8EDED; font-size: 1rem; line-height: 1.7; }

/* Decision trace timeline */
.trace-step {
    display: flex; gap: 1rem; margin-bottom: 1.2rem; align-items: flex-start;
}
.trace-dot {
    width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700;
}
.trace-content { flex: 1; }
.trace-label { color: #B8C4CC; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.8px; }
.trace-value { color: #E8EDED; font-size: 0.95rem; margin-top: 0.2rem; line-height: 1.5; }

/* Scenario cards */
.scenario-card {
    background: rgba(248,249,250,0.06); border: 1px solid rgba(212,175,55,0.2);
    border-radius: 16px; padding: 1rem 1.2rem; margin-bottom: 0.8rem; min-height: 110px;
}
.scenario-title { color: #E8EDED; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.35rem; }
.scenario-body { color: var(--gold); font-size: 0.92rem; line-height: 1.4; word-break: break-word; }

/* SIP calculator */
.sip-result {
    background: linear-gradient(135deg, rgba(212,175,55,0.15), rgba(184,150,46,0.1));
    border: 1px solid rgba(212,175,55,0.4); border-radius: 16px; padding: 1.5rem;
    text-align: center; margin-top: 1rem;
}
.sip-amount { font-family: 'Playfair Display', serif; font-size: 2.5rem; font-weight: 700; color: var(--gold); }
.sip-label { color: #B8C4CC; font-size: 0.9rem; margin-top: 0.3rem; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%);
    border: 1px solid rgba(212,175,55,0.4); border-radius: 16px;
    padding: 1rem 2.5rem; font-weight: 600; font-size: 1.1rem;
    color: var(--navy); text-transform: uppercase; letter-spacing: 0.5px;
    box-shadow: 0 10px 30px rgba(212,175,55,0.4), inset 0 1px 0 rgba(255,255,255,0.3);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 20px 40px rgba(212,175,55,0.5);
}
.stRadio > div > div > label { color: #E8EDED !important; font-weight: 500; }
.stSlider > div > div > div > div { background: linear-gradient(90deg, var(--gold), var(--gold-dark)); }
.stTabs [data-baseweb="tab-list"] { gap: 8px; padding: 0 1rem; }
.stTabs [data-baseweb="tab"] {
    background: rgba(248,249,250,0.08) !important; border: 1px solid rgba(212,175,55,0.3) !important;
    border-radius: 16px !important; padding: 12px 24px !important;
    font-weight: 500 !important; color: #E8EDED !important; transition: all 0.3s ease !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, var(--gold), var(--gold-dark)) !important;
    border-color: var(--gold) !important; color: var(--navy) !important;
}
.stSuccess { background: rgba(16,185,129,0.2); border: 1px solid rgba(16,185,129,0.4); border-radius: 12px; }
.stWarning { background: rgba(245,158,11,0.2); border: 1px solid rgba(245,158,11,0.4); border-radius: 12px; }
h1,h2,h3,h4,h5,h6,.section-title { word-break: break-word !important; overflow-wrap: break-word !important; line-height: 1.3 !important; }
</style>
""", unsafe_allow_html=True)


# ── PDF Export ────────────────────────────────────────────────────────────────
def generate_pdf(profile, risk, portfolio, warnings, next_steps, confidence_score, multi_output):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    gold = colors.HexColor("#D4AF37")
    navy = colors.HexColor("#1A252F")
    dark = colors.HexColor("#2C3E50")

    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=22, textColor=gold, spaceAfter=6)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=gold, spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#333333"), spaceAfter=4, leading=16)
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#666666"), spaceAfter=2)

    story = []

    # Title
    story.append(Paragraph("Portfolio Intelligence Report", title_style))
    story.append(Paragraph(f"Prepared for {profile.name} · {profile.age} years · {profile.financial_goal.title()}", label_style))
    story.append(HRFlowable(width="100%", thickness=1, color=gold, spaceAfter=12))

    # KPI table
    story.append(Paragraph("Executive Summary", h2_style))
    kpi_data = [
        ["Risk Score", "Investor Type", "Confidence", "Goal"],
        [str(risk.risk_score), risk.investor_type.title(), f"{confidence_score}%", profile.financial_goal.title()],
    ]
    kpi_table = Table(kpi_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), navy),
        ("TEXTCOLOR", (0,0), (-1,0), gold),
        ("BACKGROUND", (0,1), (-1,1), dark),
        ("TEXTCOLOR", (0,1), (-1,1), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("FONTSIZE", (0,1), (-1,1), 13),
        ("FONTNAME", (0,1), (-1,1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [navy, dark]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D4AF37")),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # AI Summary
    if multi_output:
        finance = multi_output["finance"]
        story.append(Paragraph("AI Advisor Summary", h2_style))
        story.append(Paragraph(finance.summary, body_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("Advisor Note", h2_style))
        story.append(Paragraph(finance.advisor_note, body_style))
        story.append(Spacer(1, 6))

    # Portfolio Allocation
    story.append(Paragraph("Portfolio Allocation", h2_style))
    alloc_data = [
        ["Asset Class", "Allocation"],
        ["Equity", f"{portfolio.equity}%"],
        ["Mutual Funds / ETFs", f"{portfolio.mutual_funds_etfs}%"],
        ["Bonds / Debt", f"{portfolio.bonds_debt}%"],
        ["Gold", f"{portfolio.gold}%"],
        ["Cash", f"{portfolio.cash}%"],
    ]
    alloc_table = Table(alloc_data, colWidths=[8*cm, 8*cm])
    alloc_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), navy),
        ("TEXTCOLOR", (0,0), (-1,0), gold),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F8F8F8"), colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
        ("ALIGN", (1,0), (1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(alloc_table)
    story.append(Spacer(1, 14))

    # Warnings
    story.append(Paragraph("Risk Warnings", h2_style))
    for w in warnings:
        story.append(Paragraph(f"• {w}", body_style))
    story.append(Spacer(1, 8))

    # Next Steps
    story.append(Paragraph("Recommended Next Steps", h2_style))
    steps = multi_output["finance"].next_steps if multi_output else next_steps
    for i, s in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {s}", body_style))

    # Risk Rationale
    story.append(Spacer(1, 8))
    story.append(Paragraph("Risk Rationale", h2_style))
    for r in risk.rationale:
        story.append(Paragraph(f"• {r}", body_style))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=gold))
    story.append(Spacer(1, 6))
    story.append(Paragraph("This report is generated for educational purposes only. Not financial advice.", label_style))

    doc.build(story)
    buf.seek(0)
    return buf


# ── SIP Calculator ────────────────────────────────────────────────────────────
def calculate_sip(target_amount, years, annual_return_pct):
    r = (annual_return_pct / 100) / 12
    n = years * 12
    if r == 0:
        return target_amount / n
    sip = target_amount * r / ((1 + r) ** n - 1)
    return sip


def projected_growth(monthly_sip, years, annual_return_pct):
    r = (annual_return_pct / 100) / 12
    values, invested = [], []
    total = 0
    deposited = 0
    for month in range(1, years * 12 + 1):
        total = total * (1 + r) + monthly_sip
        deposited += monthly_sip
        if month % 12 == 0:
            values.append(round(total))
            invested.append(round(deposited))
    return values, invested


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Investor Profile")
    input_mode = st.radio("Choose Input Mode", ["Manual Form", "Paste Profile Text", "Profile URL"], index=0)

    if input_mode == "Manual Form":
        name = st.text_input("Name", value="Tamanna")
        age = st.slider("Age", 18, 80, 22)
        monthly_income = st.number_input("Monthly Income (₹)", min_value=1000.0, value=50000.0, step=1000.0)
        monthly_expenses = st.number_input("Monthly Expenses (₹)", min_value=0.0, value=20000.0, step=1000.0)
        current_savings = st.number_input("Current Savings (₹)", min_value=0.0, value=100000.0, step=5000.0)
        liabilities = st.number_input("Liabilities (₹)", min_value=0.0, value=20000.0, step=5000.0)
        investment_amount = st.number_input("Investment Amount (₹)", min_value=1000.0, value=50000.0, step=1000.0)
        investment_horizon_years = st.slider("Investment Horizon (Years)", 1, 40, 5)
        financial_goal = st.selectbox("Financial Goal", ["wealth creation","retirement","education","home purchase","emergency backup"])
        risk_appetite = st.selectbox("Risk Appetite", ["low", "medium", "high"])
        liquidity_need = st.selectbox("Liquidity Need", ["low", "medium", "high"])
        has_emergency_fund = st.checkbox("Already have emergency fund", value=True)

    elif input_mode == "Paste Profile Text":
        raw_profile_text = st.text_area("Paste Investor Profile", height=220,
            placeholder="Tamanna, age 22, monthly income 50000, expenses 20000, savings 100000...")

    elif input_mode == "Profile URL":
        profile_url = st.text_input("Paste Public Profile URL", placeholder="https://example.com/investor-profile")

    generate = st.button("✨ Generate Portfolio Intelligence", use_container_width=True)


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">💼 Portfolio Advisor AI</div>
    <div class="hero-subtitle">Institutional-Grade Investment Intelligence</div>
    <div class="hero-description">Multi-agent AI system combining deterministic financial models with LLM-powered advisory insights.</div>
    <div class="pill-container">
        <div class="pill">⚡ Real-time Analysis</div>
        <div class="pill">🤖 AI-Powered Insights</div>
        <div class="pill">📊 5 Asset Classes</div>
        <div class="pill">📄 PDF Export</div>
        <div class="pill">🧮 SIP Calculator</div>
    </div>
</div>
""", unsafe_allow_html=True)

if generate:
    try:
        # Profile parsing
        if input_mode == "Manual Form":
            profile = UserProfile(
                name=name, age=age, monthly_income=monthly_income,
                monthly_expenses=monthly_expenses, current_savings=current_savings,
                liabilities=liabilities, investment_amount=investment_amount,
                investment_horizon_years=investment_horizon_years, financial_goal=financial_goal,
                risk_appetite=risk_appetite, liquidity_need=liquidity_need,
                has_emergency_fund=has_emergency_fund,
            )
        elif input_mode == "Paste Profile Text":
            if not raw_profile_text.strip():
                st.warning("Please paste an investor profile first.")
                st.stop()
            profile = parse_profile_text(raw_profile_text)
        elif input_mode == "Profile URL":
            if not profile_url.strip():
                st.warning("Please paste a public profile URL first.")
                st.stop()
            try:
                profile = parse_profile_url(profile_url)
            except Exception as e:
                st.error(f"Could not fetch or parse the URL: {e}")
                st.stop()

        # Deterministic computation
        risk = calculate_risk_assessment(profile)
        portfolio = generate_portfolio(profile, risk)
        scenarios = generate_scenarios(profile, portfolio)
        warnings = generate_warnings(profile, risk)
        next_steps = generate_next_steps(profile)
        confidence_score = calculate_confidence_score(profile, warnings)

        # AI layer
        multi_output = None
        ai_error = None
        with st.spinner("🤖 AI advisory engine thinking..."):
            try:
                user_input = f"""
                Name: {profile.name}
                Age: {profile.age}
                Income: {profile.monthly_income}
                Expenses: {profile.monthly_expenses}
                Savings: {profile.current_savings}
                Liabilities: {profile.liabilities}
                Investment: {profile.investment_amount}
                Horizon: {profile.investment_horizon_years}
                Goal: {profile.financial_goal}
                Risk: {profile.risk_appetite}
                Liquidity: {profile.liquidity_need}
                Emergency Fund: {profile.has_emergency_fund}
                """
                multi_output = run_multi_agent(user_input)
            except Exception as e:
                ai_error = str(e)

        st.success("✅ Portfolio intelligence generated successfully!")

        # ── KPI Cards ──────────────────────────────────────────────────────
        risk_colors = {"conservative": "#10b981", "balanced": "#f59e0b", "growth": "#f97316", "aggressive": "#ef4444"}
        risk_color = risk_colors.get(risk.investor_type, "#D4AF37")

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Risk Score</div><div class="metric-value">{risk.risk_score}</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Investor Type</div><div class="metric-type" style="color:{risk_color};">{risk.investor_type.title()}</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Confidence</div><div class="metric-value">{confidence_score}</div></div>', unsafe_allow_html=True)
        with k4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Primary Goal</div><div class="metric-type">{profile.financial_goal.title()}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not multi_output:
            st.warning("🤖 AI explanation layer temporarily unavailable. Showing deterministic portfolio intelligence.")
            st.caption(f"Debug: {ai_error}")

        # ── PDF Download ────────────────────────────────────────────────────
        pdf_buf = generate_pdf(profile, risk, portfolio, warnings, next_steps, confidence_score, multi_output)
        st.download_button(
            label="📄 Download Portfolio Report (PDF)",
            data=pdf_buf,
            file_name=f"{profile.name.replace(' ','_')}_portfolio_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Tabs ────────────────────────────────────────────────────────────
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Executive Report",
            "💰 Allocation Analytics",
            "🤖 AI Explanation",
            "🧮 SIP Calculator",
            "🔍 Decision Trace",
            "✅ Validation & Schema",
        ])

        # ── Tab 1: Executive Report ─────────────────────────────────────────
        with tab1:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">📈 Executive Summary</h3>', unsafe_allow_html=True)

            if multi_output:
                finance = multi_output["finance"]
                st.markdown(f"**{finance.summary}**")
                st.info(finance.advisor_note)
                st.markdown('<h4 class="section-title" style="font-size:1.4rem;">💡 Plain Explanation</h4>', unsafe_allow_html=True)
                st.markdown(multi_output["explanation"])
            else:
                st.markdown(f"""
                **{profile.name}'s portfolio** is classified as **{risk.investor_type}**
                with risk score **{risk.risk_score}**. Aligned with {profile.investment_horizon_years}-year
                horizon, **{profile.financial_goal}** objective, and **{profile.liquidity_need}** liquidity.
                """)

            st.markdown('<h4 class="section-title" style="font-size:1.4rem;">⚠️ Risk Rationale</h4>', unsafe_allow_html=True)
            for item in risk.rationale:
                st.write(f"• {item}")

            st.markdown('<h4 class="section-title" style="font-size:1.4rem;">🚨 Warnings</h4>', unsafe_allow_html=True)
            for warning in warnings:
                st.warning(warning)

            st.markdown('<h4 class="section-title" style="font-size:1.4rem;">✅ Next Steps</h4>', unsafe_allow_html=True)
            final_steps = multi_output["finance"].next_steps if multi_output else next_steps
            for i, step in enumerate(final_steps, 1):
                st.markdown(f"**{i}.** {step}")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Tab 2: Allocation Analytics (UPGRADED) ──────────────────────────
        with tab2:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">💰 Portfolio Allocation Analytics</h3>', unsafe_allow_html=True)

            alloc_df = pd.DataFrame({
                "Asset": ["Equity", "Mutual Funds / ETFs", "Bonds / Debt", "Gold", "Cash"],
                "Allocation": [portfolio.equity, portfolio.mutual_funds_etfs, portfolio.bonds_debt, portfolio.gold, portfolio.cash],
                "Amount (₹)": [
                    portfolio.equity / 100 * profile.investment_amount,
                    portfolio.mutual_funds_etfs / 100 * profile.investment_amount,
                    portfolio.bonds_debt / 100 * profile.investment_amount,
                    portfolio.gold / 100 * profile.investment_amount,
                    portfolio.cash / 100 * profile.investment_amount,
                ]
            })
            alloc_df["Amount (₹)"] = alloc_df["Amount (₹)"].apply(lambda x: f"₹{x:,.0f}")

            COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#06b6d4"]

            c1, c2 = st.columns(2)
            with c1:
                # Donut chart
                fig_donut = go.Figure(go.Pie(
                    labels=alloc_df["Asset"], values=alloc_df["Allocation"],
                    hole=0.55, marker_colors=COLORS,
                    textinfo="label+percent", textfont_size=12,
                    hovertemplate="<b>%{label}</b><br>%{value}%<extra></extra>",
                ))
                fig_donut.update_layout(
                    title="Portfolio Donut", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#E8EDED", showlegend=False, height=340,
                    annotations=[dict(text=f"<b>{risk.investor_type.title()}</b>", x=0.5, y=0.5,
                                      font_size=13, font_color="#D4AF37", showarrow=False)],
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with c2:
                # Horizontal bar
                fig_bar = go.Figure(go.Bar(
                    y=alloc_df["Asset"], x=alloc_df["Allocation"],
                    orientation="h", marker_color=COLORS,
                    text=[f"{v}%" for v in alloc_df["Allocation"]], textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x}%<extra></extra>",
                ))
                fig_bar.update_layout(
                    title="Allocation Breakdown", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#E8EDED", height=340, xaxis=dict(showgrid=False, color="#E8EDED"),
                    yaxis=dict(color="#E8EDED"), margin=dict(l=10, r=60),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # Amount breakdown table
            st.markdown('<h4 class="section-title" style="font-size:1.3rem;">💵 Investment Amount Breakdown</h4>', unsafe_allow_html=True)
            st.dataframe(alloc_df, use_container_width=True, hide_index=True)

            # Projected growth chart
            st.markdown('<h4 class="section-title" style="font-size:1.3rem;">📈 Projected Portfolio Growth</h4>', unsafe_allow_html=True)
            expected_returns = {"conservative": 7, "balanced": 9, "growth": 11, "aggressive": 13}
            exp_return = expected_returns.get(risk.investor_type, 9)

            monthly_sip_est = (profile.monthly_income - profile.monthly_expenses) * 0.3
            growth_vals, invested_vals = projected_growth(monthly_sip_est, profile.investment_horizon_years, exp_return)
            years_list = list(range(1, profile.investment_horizon_years + 1))

            fig_growth = go.Figure()
            fig_growth.add_trace(go.Scatter(
                x=years_list, y=growth_vals, name="Portfolio Value",
                fill="tozeroy", line=dict(color="#D4AF37", width=2.5),
                fillcolor="rgba(212,175,55,0.15)",
                hovertemplate="Year %{x}<br>Value: ₹%{y:,.0f}<extra></extra>",
            ))
            fig_growth.add_trace(go.Scatter(
                x=years_list, y=invested_vals, name="Amount Invested",
                line=dict(color="#6366f1", width=2, dash="dash"),
                hovertemplate="Year %{x}<br>Invested: ₹%{y:,.0f}<extra></extra>",
            ))
            fig_growth.update_layout(
                title=f"Estimated Growth at {exp_return}% p.a. ({risk.investor_type.title()} portfolio)",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E8EDED", height=340, legend=dict(bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(title="Year", color="#E8EDED", showgrid=False),
                yaxis=dict(title="Value (₹)", color="#E8EDED", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            )
            st.plotly_chart(fig_growth, use_container_width=True)

            # Scenario Analysis
            st.markdown('<h4 class="section-title" style="font-size:1.3rem;">🎭 Scenario Analysis</h4>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            def scenario_box(title, text):
                st.markdown(f'<div class="scenario-card"><div class="scenario-title">{title}</div><div class="scenario-body">{text}</div></div>', unsafe_allow_html=True)
            with col1:
                scenario_box("📉 Market Crash", scenarios.market_crash)
                scenario_box("📈 Stable Growth", scenarios.stable_growth)
            with col2:
                scenario_box("💸 Inflation Shock", scenarios.inflation_shock)
                scenario_box("🚨 Emergency Withdrawal", scenarios.emergency_withdrawal)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Tab 3: AI Explanation (UPGRADED) ───────────────────────────────
        with tab3:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">🤖 AI Advisory Layer</h3>', unsafe_allow_html=True)

            if multi_output:
                finance = multi_output["finance"]
                ai = finance.ai_explanation

                st.markdown(f'<div class="ai-card"><div class="ai-card-title">📋 Advisor Summary</div><div class="ai-card-body">{ai.advisor_summary}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-card"><div class="ai-card-title">⚖️ Risk Justification</div><div class="ai-card-body">{ai.risk_justification}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-card"><div class="ai-card-title">🎵 Advisor Note</div><div class="ai-card-body"><em>{ai.advisor_note}</em></div></div>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="ai-card-title" style="color:#D4AF37;font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.6rem;">📊 Allocation Explanation</div>', unsafe_allow_html=True)
                    for item in ai.allocation_explanation:
                        st.markdown(f"✦ {item}")
                with col2:
                    st.markdown('<div class="ai-card-title" style="color:#D4AF37;font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.6rem;">🚀 Improvement Suggestions</div>', unsafe_allow_html=True)
                    for item in ai.improvement_suggestions:
                        st.markdown(f"→ {item}")

                # Confidence gauge
                st.markdown("<br>", unsafe_allow_html=True)
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number", value=confidence_score,
                    title={"text": "Confidence Score", "font": {"color": "#E8EDED"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#E8EDED"},
                        "bar": {"color": "#D4AF37"},
                        "bgcolor": "rgba(0,0,0,0)",
                        "steps": [
                            {"range": [0, 50], "color": "rgba(239,68,68,0.3)"},
                            {"range": [50, 75], "color": "rgba(245,158,11,0.3)"},
                            {"range": [75, 100], "color": "rgba(16,185,129,0.3)"},
                        ],
                    },
                    number={"suffix": "%", "font": {"color": "#D4AF37", "size": 32}},
                ))
                fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E8EDED", height=260)
                st.plotly_chart(fig_gauge, use_container_width=True)

            else:
                st.info("🤖 AI explanation unavailable this run. Deterministic intelligence is still active above.")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Tab 4: SIP Calculator (NEW) ─────────────────────────────────────
        with tab4:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">🧮 SIP Calculator</h3>', unsafe_allow_html=True)
            st.markdown("Calculate how much you need to invest monthly to reach your financial goal.")

            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                target = st.number_input("Target Amount (₹)", min_value=10000.0, value=float(profile.investment_amount * 3), step=10000.0)
            with sc2:
                sip_years = st.slider("Duration (Years)", 1, 40, profile.investment_horizon_years)
            with sc3:
                exp_returns = {"conservative": 7.0, "balanced": 9.0, "growth": 11.0, "aggressive": 13.0}
                sip_return = st.number_input("Expected Return (% p.a.)", min_value=1.0, max_value=30.0,
                                              value=exp_returns.get(risk.investor_type, 9.0), step=0.5)

            monthly_sip = calculate_sip(target, sip_years, sip_return)
            total_invested = monthly_sip * sip_years * 12
            total_returns = target - total_invested

            r1, r2, r3 = st.columns(3)
            with r1:
                st.markdown(f'<div class="sip-result"><div class="sip-amount">₹{monthly_sip:,.0f}</div><div class="sip-label">Monthly SIP Required</div></div>', unsafe_allow_html=True)
            with r2:
                st.markdown(f'<div class="sip-result"><div class="sip-amount">₹{total_invested:,.0f}</div><div class="sip-label">Total Amount Invested</div></div>', unsafe_allow_html=True)
            with r3:
                st.markdown(f'<div class="sip-result"><div class="sip-amount">₹{total_returns:,.0f}</div><div class="sip-label">Estimated Returns Earned</div></div>', unsafe_allow_html=True)

            # Growth projection for SIP
            g_vals, i_vals = projected_growth(monthly_sip, sip_years, sip_return)
            fig_sip = go.Figure()
            fig_sip.add_trace(go.Scatter(
                x=list(range(1, sip_years + 1)), y=g_vals, name="Portfolio Value",
                fill="tozeroy", line=dict(color="#D4AF37", width=2.5),
                fillcolor="rgba(212,175,55,0.15)",
            ))
            fig_sip.add_trace(go.Scatter(
                x=list(range(1, sip_years + 1)), y=i_vals, name="Amount Invested",
                line=dict(color="#6366f1", width=2, dash="dash"),
            ))
            fig_sip.update_layout(
                title=f"SIP Growth Projection at {sip_return}% p.a.",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E8EDED", height=340,
                xaxis=dict(title="Year", showgrid=False, color="#E8EDED"),
                yaxis=dict(title="Value (₹)", showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#E8EDED"),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_sip, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Tab 5: Decision Trace (UPGRADED) ───────────────────────────────
        with tab5:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">🔍 Decision Trace</h3>', unsafe_allow_html=True)

            # Visual timeline of decision steps
            trace_steps = [
                ("#3b82f6", "01", "Input Parsing", f"Mode: {input_mode} → Profile parsed for {profile.name}"),
                ("#10b981", "02", "Pydantic Validation", f"All {len(profile.model_fields)} fields validated — age, income, liabilities, goal, risk, liquidity"),
                ("#f59e0b", "03", "Risk Engine", f"Base score 50 → adjusted by {len(risk.rationale)} factors → Final score: {risk.risk_score} ({risk.investor_type})"),
                ("#8b5cf6", "04", "Portfolio Engine", f"Investor type '{risk.investor_type}' → Equity {portfolio.equity}% | MF {portfolio.mutual_funds_etfs}% | Bonds {portfolio.bonds_debt}% | Gold {portfolio.gold}% | Cash {portfolio.cash}%"),
                ("#ef4444", "05", "Warning Engine", f"{len(warnings)} warning(s) generated based on profile constraints"),
                ("#D4AF37", "06", "Confidence Scorer", f"Base 92 → deductions applied → Final: {confidence_score}/100"),
            ]
            if multi_output:
                trace_steps.append(("#06b6d4", "07", "Ollama AI Layer", "Single LLM call → advisor_summary, risk_justification, allocation_explanation, advisor_note generated"))

            for color, num, label, value in trace_steps:
                st.markdown(f"""
                <div class="trace-step">
                    <div class="trace-dot" style="background:{color}22;border:2px solid {color};color:{color};">{num}</div>
                    <div class="trace-content">
                        <div class="trace-label">{label}</div>
                        <div class="trace-value">{value}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Risk factor breakdown chart
            st.markdown('<h4 class="section-title" style="font-size:1.3rem;">⚙️ Risk Factor Breakdown</h4>', unsafe_allow_html=True)
            factor_labels = [r[:45] + "..." if len(r) > 45 else r for r in risk.rationale]
            fig_factors = go.Figure(go.Bar(
                y=factor_labels, x=[5] * len(factor_labels),
                orientation="h", marker_color="#D4AF37",
                text=factor_labels, textposition="inside",
                hovertext=risk.rationale, hoverinfo="text",
            ))
            fig_factors.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E8EDED", height=max(200, len(risk.rationale) * 45),
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(showticklabels=False),
                margin=dict(l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig_factors, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Tab 6: Validation & Schema ──────────────────────────────────────
        with tab6:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">✅ Schema Validation</h3>', unsafe_allow_html=True)
            st.markdown("### 👤 Input Model")
            st.code(profile.model_dump_json(indent=2), language="json")
            st.markdown("### ⚠️ Risk Model")
            st.code(risk.model_dump_json(indent=2), language="json")
            st.markdown("### 💰 Portfolio Model")
            st.code(portfolio.model_dump_json(indent=2), language="json")
            if multi_output:
                st.markdown("### 🎯 Final Advice Model")
                st.code(multi_output["finance"].model_dump_json(indent=2), language="json")
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Processing error: {e}")

else:
    st.markdown("""
    <div class="section-container" style="text-align:center;padding:4rem 2rem;">
        <h2 style="color:#94a3b8;font-size:1.5rem;margin-bottom:1rem;">👤 Complete investor profile in sidebar</h2>
        <p style="color:#64748b;font-size:1.1rem;">Click "✨ Generate Portfolio Intelligence" to begin</p>
    </div>
    """, unsafe_allow_html=True)