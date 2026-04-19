import streamlit as st
import pandas as pd
import plotly.express as px

from models import UserProfile
from parser import parse_profile_text, parse_profile_url
#from agent import build_advice
from agents.multiagent_runner import run_multi_agent

from logic import (
    calculate_risk_assessment,
    generate_portfolio,
    generate_scenarios,
    generate_warnings,
    generate_next_steps,
    calculate_confidence_score,
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

/* === PORTFOLIO ADVISOR EXECUTIVE THEME + TEXT FIXES === */
:root {
    --gold: #D4AF37;
    --gold-dark: #B8962E;
    --navy: #1A252F;
    --navy-dark: #2C3E50;
    --charcoal: #34495E;
    --cream: #F8F9FA;
    --gold-glow: #FEF9E7;
}

* { font-family: 'Inter', sans-serif; }

.main {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-dark) 50%, var(--charcoal) 100%);
    background-attachment: fixed;
}

.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }

/* Hero - FIXED SIZING */
.hero-container {
    background: linear-gradient(145deg, rgba(212,175,55,0.12), rgba(184,150,46,0.08), rgba(26,37,47,0.95));
    backdrop-filter: blur(25px);
    border: 1px solid rgba(212,175,55,0.35);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 35px 70px -20px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,55,0.2);
    position: relative;
    overflow: hidden;
}

.hero-container::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    opacity: 0.7;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem !important;
    font-weight: 700;
    background: linear-gradient(135deg, var(--gold-glow) 0%, var(--gold) 50%, #FAD5A5 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 0.5rem;
    word-break: break-word;
}

.hero-subtitle {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem !important;
    color: #E8EDED; font-weight: 500;
    margin-bottom: 1rem; letter-spacing: 0.5px;
}

.hero-description {
    color: #B8C4CC; font-size: 1.1rem; line-height: 1.8;
}

/* Gold Executive Pills */
.pill-container { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 1.5rem; }

.pill {
    background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(184,150,46,0.15));
    border: 1px solid rgba(212,175,55,0.4); backdrop-filter: blur(12px);
    padding: 10px 20px;
    border-radius: 40px; font-size: 0.9rem;
    font-weight: 500; color: var(--gold-glow); position: relative; overflow: hidden;
}

.pill::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: var(--gold); opacity: 0.6;
}

.pill:hover {
    background: linear-gradient(135deg, rgba(212,175,55,0.3), rgba(184,150,46,0.25));
    border-color: var(--gold); transform: translateY(-3px);
    box-shadow: 0 12px 30px rgba(212,175,55,0.3);
}

/* KPI Cards - FIXED SIZING */
.metric-card {
    background: linear-gradient(145deg, rgba(248,249,250,0.08), rgba(26,37,47,0.9));
    backdrop-filter: blur(25px); border: 1px solid rgba(212,175,55,0.25);
    border-radius: 20px;
    padding: 1.8rem 1.5rem !important;
    text-align: center;
    position: relative; overflow: hidden; transition: all 0.4s ease;
}

.metric-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 30px 60px -15px rgba(0,0,0,0.4), 0 0 0 1px rgba(212,175,55,0.2);
}

.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
}

.metric-value {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem !important;
    font-weight: 700;
    background: linear-gradient(135deg, var(--gold) 0%, #FAD5A5 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    color: #B8C4CC; font-size: 1rem; font-weight: 500;
    letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 0.75rem;
}

.metric-type {
    font-size: 1.1rem; font-weight: 600; color: #E8EDED;
    font-family: 'Playfair Display', serif;
}

/* Sections - FIXED PADDING */
.section-container {
    background: linear-gradient(145deg, rgba(248,249,250,0.06), rgba(26,37,47,0.92));
    backdrop-filter: blur(25px); border: 1px solid rgba(212,175,55,0.2);
    border-radius: 20px;
    padding: 2rem !important;
    margin-top: 2rem;
    box-shadow: 0 25px 50px -15px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,175,55,0.1);
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem !important;
    font-weight: 600;
    background: linear-gradient(135deg, var(--gold-glow) 0%, var(--gold) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 1.5rem !important;
    letter-spacing: -0.02em;
    display: flex; align-items: center; gap: 12px;
    word-break: break-word;
    line-height: 1.3;
}

/* Step Cards - FIXED */
.step-card {
    background: linear-gradient(145deg, rgba(248,249,250,0.08), rgba(26,37,47,0.9));
    backdrop-filter: blur(20px); border: 1px solid rgba(212,175,55,0.2);
    border-radius: 20px;
    padding: 1.8rem 1.5rem !important;
    text-align: center;
    min-height: 180px !important;
    transition: all 0.3s ease;
}

.step-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,0,0,0.25); }

.step-number {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem !important;
    font-weight: 800;
    background: linear-gradient(135deg, var(--gold), #FAD5A5);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 1rem; display: block;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* Sidebar - Executive Panel */
.sidebar .sidebar-content {
    background: linear-gradient(180deg, rgba(26,37,47,0.98), rgba(44,62,80,0.98));
    backdrop-filter: blur(25px); border-right: 1px solid rgba(212,175,55,0.3);
}

.stRadio > div > div > label { color: #E8EDED !important; font-weight: 500; }

.stSlider > div > div > div > div { background: linear-gradient(90deg, var(--gold), var(--gold-dark)); }

/* GOLD EXECUTIVE BUTTON */
.stButton > button {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%);
    border: 1px solid rgba(212,175,55,0.4); border-radius: 16px;
    padding: 1rem 2.5rem;
    font-weight: 600; font-size: 1.1rem;
    color: var(--navy); text-transform: uppercase; letter-spacing: 0.5px;
    box-shadow: 0 10px 30px rgba(212,175,55,0.4), inset 0 1px 0 rgba(255,255,255,0.3);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #E8B923 0%, var(--gold) 100%);
    transform: translateY(-3px);
    box-shadow: 0 20px 40px rgba(212,175,55,0.5), inset 0 1px 0 rgba(255,255,255,0.4);
}

/* Gold Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; padding: 0 1rem; }

.stTabs [data-baseweb="tab"] {
    background: rgba(248,249,250,0.08) !important;
    border: 1px solid rgba(212,175,55,0.3) !important;
    border-radius: 16px !important; padding: 12px 24px !important;
    font-weight: 500 !important; transition: all 0.3s ease !important;
    color: #E8EDED !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(248,249,250,0.15) !important;
    border-color: rgba(212,175,55,0.5) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, var(--gold), var(--gold-dark)) !important;
    border-color: var(--gold) !important; color: var(--navy) !important;
}

/* Executive Dataframe */
.stDataFrame {
    background: rgba(248,249,250,0.08); border-radius: 16px;
    border: 1px solid rgba(212,175,55,0.3);
}

/* Messages */
.stSuccess { background: rgba(16,185,129,0.2); border: 1px solid rgba(16,185,129,0.4); border-radius: 12px; backdrop-filter: blur(10px); }
.stWarning { background: rgba(245,158,11,0.2); border: 1px solid rgba(245,158,11,0.4); border-radius: 12px; backdrop-filter: blur(10px); }

.stMetric > div > div > div > div {
    color: var(--gold) !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.8rem !important;
}

/* RESPONSIVE FIXES */
@media (max-width: 1200px) {
    .hero-title { font-size: 2.4rem !important; }
    .section-title { font-size: 1.4rem !important; }
    .metric-value { font-size: 2rem !important; }
}

@media (max-width: 768px) {
    .hero-title { font-size: 2.2rem !important; }
    .section-title { font-size: 1.3rem !important; }
    .metric-value { font-size: 1.8rem !important; }
    .pill { font-size: 0.85rem !important; padding: 8px 16px !important; }
}

/* PREVENT TEXT OVERFLOW */
h1, h2, h3, h4, h5, h6, .section-title {
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    line-height: 1.3 !important;
}

/* === SCENARIO ANALYSIS FIX ONLY === */
div[data-testid="stHorizontalBlock"] {
    gap: 0.8rem !important;
}

div[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
}

div[data-testid="stHorizontalBlock"] > div > div {
    padding: 0.25rem !important;
    min-width: 0 !important;
}

h4.section-title {
    font-size: 1.15rem !important;
    margin: 0.75rem 0 0.5rem 0 !important;
    line-height: 1.2 !important;
}

div[data-testid="stMetric"] {
    padding: 0.35rem 0.25rem !important;
    min-height: 78px !important;
    overflow: hidden !important;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    line-height: 1.05 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    max-width: 100% !important;
    margin-bottom: 0.15rem !important;
}

div[data-testid="stMetricValue"] {
    font-size: 0.95rem !important;
    line-height: 1.1 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    max-width: 100% !important;
    display: block !important;
}

div[data-testid="stMetric"] * {
    font-size: inherit !important;
}

div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] {
    margin-bottom: 0.35rem !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar remains exactly the same - just enhanced styling applied globally
with st.sidebar:
    st.header("👤 Investor Profile")
    
    input_mode = st.radio(
        "Choose Input Mode",
        ["Manual Form", "Paste Profile Text", "Profile URL"],
        index=0,
    )

    if input_mode == "Manual Form":
        name = st.text_input("Name", value="Tamanna")
        age = st.slider("Age", 18, 80, 22)
        monthly_income = st.number_input(
            "Monthly Income (₹)", min_value=1000.0, value=50000.0, step=1000.0
        )
        monthly_expenses = st.number_input(
            "Monthly Expenses (₹)", min_value=0.0, value=20000.0, step=1000.0
        )
        current_savings = st.number_input(
            "Current Savings (₹)", min_value=0.0, value=100000.0, step=5000.0
        )
        liabilities = st.number_input(
            "Liabilities (₹)", min_value=0.0, value=20000.0, step=5000.0
        )
        investment_amount = st.number_input(
            "Investment Amount (₹)", min_value=1000.0, value=50000.0, step=1000.0
        )
        investment_horizon_years = st.slider("Investment Horizon (Years)", 1, 40, 5)

        financial_goal = st.selectbox(
            "Financial Goal",
            [
                "wealth creation",
                "retirement",
                "education",
                "home purchase",
                "emergency backup",
            ],
        )
        risk_appetite = st.selectbox("Risk Appetite", ["low", "medium", "high"])
        liquidity_need = st.selectbox("Liquidity Need", ["low", "medium", "high"])
        has_emergency_fund = st.checkbox("Already have emergency fund", value=True)

    elif input_mode == "Paste Profile Text":
        raw_profile_text = st.text_area(
            "Paste Investor Profile",
            height=220,
            placeholder="Example: Tamanna, age 22, monthly income 50000, expenses 20000, savings 100000, liabilities 30000, investment amount 50000, horizon 5 years, goal retirement, medium risk, low liquidity need, has emergency fund.",
        )

    elif input_mode == "Profile URL":
        profile_url = st.text_input(
            "Paste Public Profile URL",
            placeholder="https://example.com/investor-profile",
        )

    generate = st.button("✨ Generate Portfolio Intelligence", use_container_width=True)

# Everything below remains EXACTLY the same - just inherits the new beautiful styling
if generate:
    try:
        if input_mode == "Manual Form":
            profile = UserProfile(
                name=name,
                age=age,
                monthly_income=monthly_income,
                monthly_expenses=monthly_expenses,
                current_savings=current_savings,
                liabilities=liabilities,
                investment_amount=investment_amount,
                investment_horizon_years=investment_horizon_years,
                financial_goal=financial_goal,
                risk_appetite=risk_appetite,
                liquidity_need=liquidity_need,
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

        risk = calculate_risk_assessment(profile)
        portfolio = generate_portfolio(profile, risk)
        scenarios = generate_scenarios(profile, portfolio)
        warnings = generate_warnings(profile, risk)
        next_steps = generate_next_steps(profile)
        confidence_score = calculate_confidence_score(profile, warnings)

        multi_output = None
        ai_error = None

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

        # Enhanced KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Risk Score</div>
                <div class="metric-value">{risk.risk_score}</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Investor Type</div>
                <div class="metric-type">{risk.investor_type.title()}</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Confidence</div>
                <div class="metric-value">{confidence_score}</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Primary Goal</div>
                <div class="metric-type">{profile.financial_goal.title()}</div>
            </div>
            """, unsafe_allow_html=True)

        if not multi_output:
            st.warning(
                "🤖 AI explanation layer temporarily unavailable. Showing deterministic portfolio intelligence."
            )
            st.caption(f"Debug: {ai_error}")

        # All tabs remain exactly the same - new CSS makes them beautiful automatically
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Executive Report",
            "🔄 Pipeline Visualizer", 
            "💰 Allocation Analytics",
            "🤖 AI Explanation",
            "✅ Validation & Schema",
            "🔍 Decision Trace",
            "📚 Flashcards",
        ])

        with tab1:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">📈 Executive Summary</h3>', unsafe_allow_html=True)

            if multi_output:
                finance = multi_output["finance"]
                explanation = multi_output["explanation"]

                st.markdown(f"**{finance.summary}**")
                st.info(finance.advisor_note)

                st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">💡 Explanation</h4>', unsafe_allow_html=True)
                st.markdown(explanation)

            else:
                st.markdown(f"""
                **{profile.name}'s portfolio** is classified as **{risk.investor_type}** 
                with risk score **{risk.risk_score}**. Aligned with {profile.investment_horizon_years}-year 
                horizon, **{profile.financial_goal}** objective, and **{profile.liquidity_need}** liquidity.
                """)

            st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">⚠️ Risk Rationale</h4>', unsafe_allow_html=True)
            for item in risk.rationale:
                st.write(f"• {item}")

            st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">🚨 Warnings</h4>', unsafe_allow_html=True)
            for warning in warnings:
                st.warning(warning)

            st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">✅ Next Steps</h4>', unsafe_allow_html=True)

            if multi_output:
                final_steps = multi_output["finance"].next_steps
            else:
                final_steps = next_steps

            for step in final_steps:
                st.write(f"• {step}")

            st.markdown("</div>", unsafe_allow_html=True)

        # All other tabs remain IDENTICAL - just look stunning now
        with tab2:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">🔄 Pipeline Visualizer</h3>', unsafe_allow_html=True)
            st.markdown("""
            This interactive diagram visualizes the complete data flow from raw input → validated schemas → 
            deterministic engines → multi-agent AI → final advisory output.
            """)

            flow_chart = """
            digraph G {
                rankdir=LR;
                node [shape=box, style="rounded,filled", color="#1e293b", fillcolor="#1e40af", fontcolor="white", fontname="Inter"];
                edge [color="#6366f1", arrowsize=1.2];

                Input [label="🎯 Input Layer\\nManual/Text/URL", fillcolor="#3b82f6"];
                Parse [label="🔄 Parsing Layer\\nRaw → Structured", fillcolor="#10b981"];
                Validate [label="✅ Pydantic Validation\\nUserProfile Schema", fillcolor="#f59e0b"];
                Risk [label="⚠️ Risk Engine\\nRiskAssessment", fillcolor="#ef4444"];
                Portfolio [label="💰 Portfolio Engine\\nAsset Allocation", fillcolor="#8b5cf6"];

                Planner [label="🧠 Planner Agent\\nTask Decomposition", fillcolor="#06b6d4"];
                Finance [label="💹 Finance Agent\\nCore Computation", fillcolor="#10b981"];
                Explain [label="💬 Explanation Agent\\nHuman Insights", fillcolor="#f59e0b"];

                Final [label="🎯 Final Advice\\nStructured Output", fillcolor="#8b5cf6"];

                Input -> Parse -> Validate -> Risk -> Portfolio;
                Portfolio -> Planner;
                Planner -> Finance;
                Finance -> Explain;
                Explain -> Final;
            }
            """
            st.graphviz_chart(flow_chart)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">💰 Portfolio Allocation</h3>', unsafe_allow_html=True)

            allocation_data = {
                "Asset": ["Equity", "Mutual Funds / ETFs", "Bonds / Debt", "Gold", "Cash"],
                "Allocation": [
                    portfolio.equity,
                    portfolio.mutual_funds_etfs,
                    portfolio.bonds_debt,
                    portfolio.gold,
                    portfolio.cash,
                ],
            }
            df = pd.DataFrame(allocation_data)

            c1, c2 = st.columns(2)
            with c1:
                fig1 = px.pie(df, names="Asset", values="Allocation", title="Portfolio Mix",
                            color_discrete_sequence=["#6366f1","#10b981","#f59e0b","#ef4444","#06b6d4"])
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                fig2 = px.bar(df, x="Asset", y="Allocation", title="Allocation Breakdown",
                            color_discrete_sequence=["#6366f1","#10b981","#f59e0b","#ef4444","#06b6d4"])
                st.plotly_chart(fig2, use_container_width=True)

            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">🎭 Scenario Analysis</h4>', unsafe_allow_html=True)

            def scenario_box(title, text):
                st.markdown(f"""
                <div style="
                    background: rgba(248,249,250,0.06);
                    border: 1px solid rgba(212,175,55,0.2);
                    border-radius: 16px;
                    padding: 0.9rem 1rem;
                    margin-bottom: 0.8rem;
                    overflow: hidden;
                    min-height: 110px;
                ">
                    <div style="
                        color: #E8EDED;
                        font-size: 0.9rem;
                        font-weight: 600;
                        margin-bottom: 0.35rem;
                    ">{title}</div>
                    <div style="
                        color: var(--gold);
                        font-size: 0.95rem;
                        line-height: 1.35;
                        word-break: break-word;
                        overflow-wrap: anywhere;
                    ">{text}</div>
                </div>
                """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                scenario_box("📉 Market Crash", scenarios.market_crash)
                scenario_box("📈 Stable Growth", scenarios.stable_growth)
            with col2:
                scenario_box("💸 Inflation Shock", scenarios.inflation_shock)
                scenario_box("🚨 Emergency Withdrawal", scenarios.emergency_withdrawal)

        # Rest of tabs remain exactly the same...
        with tab4:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">🤖 AI Advisory Layer</h3>', unsafe_allow_html=True)

            if multi_output:
                finance = multi_output["finance"]

                st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">📋 Advisor Summary</h4>', unsafe_allow_html=True)
                st.markdown(finance.ai_explanation.advisor_summary)

                st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">⚖️ Risk Justification</h4>', unsafe_allow_html=True)
                st.markdown(finance.ai_explanation.risk_justification)

                st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">📊 Allocation Explanation</h4>', unsafe_allow_html=True)
                for item in finance.ai_explanation.allocation_explanation:
                    st.write(f"• {item}")

                st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">🚀 Improvement Suggestions</h4>', unsafe_allow_html=True)
                for item in finance.ai_explanation.improvement_suggestions:
                    st.write(f"• {item}")

                st.markdown('<h4 class="section-title" style="font-size: 1.4rem;">🔧 Raw AI Output</h4>', unsafe_allow_html=True)
                st.json(finance.ai_explanation.model_dump())

            else:
                st.info("🤖 AI explanation unavailable this run.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab5:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">✅ Schema Validation</h3>', unsafe_allow_html=True)

            st.markdown('### 👤 Input Model')
            st.code(profile.model_dump_json(indent=2), language="json")

            st.markdown('### ⚠️ Risk Model')
            st.code(risk.model_dump_json(indent=2), language="json")

            st.markdown('### 💰 Portfolio Model')
            st.code(portfolio.model_dump_json(indent=2), language="json")

            if multi_output:
                st.markdown('### 🎯 Final Advice Model')
                st.code(multi_output["finance"].model_dump_json(indent=2), language="json")

            st.markdown("</div>", unsafe_allow_html=True)

        with tab6:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">🔍 Decision Trace</h3>', unsafe_allow_html=True)

            st.markdown("""
            ### ⚙️ Deterministic Engine
            • User input validated using `UserProfile` Pydantic schema  
            • Risk computed from age, horizon, liabilities, emergency fund status
            • Portfolio generated using investor type + profile constraints
            • Confidence score adjusted for safety concerns
            """)

            if multi_output:
                st.markdown("""
                ### 🤖 AI Pipeline
                • **Planner Agent**: Decomposes financial analysis into structured steps
                • **Finance Agent**: Executes core computations (risk, allocation, scenarios)  
                • **Explanation Agent**: Converts structured data → human insights
                • **Orchestrator**: Sequential execution ensures reliability
                """)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab7:
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">📚 Interactive Flashcards</h3>', unsafe_allow_html=True)

            with st.expander("🎯 1. Input Layer"):
                st.markdown("""
                Supports **3 input modes**: Manual forms, pasted profile text, public URL parsing.
                All paths converge to validated `UserProfile` Pydantic model.
                """)

            with st.expander("✅ 2. Pydantic Validation"):
                st.code('''
profile = UserProfile(
    name=name, age=age, monthly_income=monthly_income,
    # ... all fields validated by schema
)
                ''', language="python")
                st.markdown("**Every field** validated for type, range, and business rules.")

            with st.expander("⚠️ 3. Risk Engine"):
                st.markdown("Computes numerical **risk score** → maps to investor categories: conservative/balanced/growth/aggressive.")

            with st.expander("💰 4. Portfolio Engine"):
                st.markdown("Generates allocation across **5 asset classes**. `PortfolioAllocation` ensures weights = 100%.")

            with st.expander("🤖 5. Multi-Agent System"):
                st.markdown("""
                **Not a single LLM**. Specialized agents:
                • Planner: Task decomposition
                • Finance: Structured computation  
                • Explanation: Human-readable insights
                """)

            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Processing error: {e}")

else:
    st.markdown("""
    <div class="section-container" style="text-align: center; padding: 4rem 2rem;">
        <h2 style="color: #94a3b8; font-size: 1.5rem; margin-bottom: 1rem;">
            👤 Complete investor profile in sidebar
        </h2>
        <p style="color: #64748b; font-size: 1.1rem;">
            Click "✨ Generate Portfolio Intelligence" to see magic happen
        </p>
    </div>
    """, unsafe_allow_html=True)