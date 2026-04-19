# Portfolio Advisor

An intelligent Streamlit-based portfolio advisory application that analyzes an investor’s financial profile and generates personalized asset allocation, risk assessment, scenario analysis, warnings, and next steps.

## Overview

Portfolio Advisor helps users input financial details manually, via pasted profile text, or through a profile URL.  
It then validates the profile, estimates risk, generates a suitable portfolio allocation, analyzes financial scenarios, and optionally uses a multi-agent AI layer to provide human-readable advisory insights.

This project is designed as a decision-support tool for basic investment planning and financial education.

## Features

- Multiple input modes:
  - Manual form
  - Paste profile text
  - Profile URL parsing
- Risk assessment based on investor profile
- Portfolio allocation generation
- Scenario analysis:
  - Market crash
  - Stable growth
  - Inflation shock
  - Emergency withdrawal
- Warning generation for financial safety checks
- Next-step recommendations
- Confidence score estimation
- Multi-agent AI explanation layer
- Interactive Streamlit UI with custom executive theme
- Charts and tab-based dashboard layout

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- Pydantic
- Custom logic modules
- Multi-agent orchestration layer

```

## How It Works

1. User enters financial profile data.
2. Profile is validated using the `UserProfile` schema.
3. Risk is calculated using the profile details.
4. Portfolio allocation is generated.
5. Scenario outcomes are computed.
6. Warnings and next steps are created.
7. Optional AI agents generate summaries and explanations.
8. Results are displayed in a dashboard with tabs and analytics.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/portfolio-advisor.git
cd portfolio-advisor
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

## Input Modes

### Manual Form
Enter investor details such as age, income, expenses, savings, liabilities, investment amount, horizon, goal, risk appetite, and liquidity need.

### Paste Profile Text
Paste a natural-language financial profile and let the parser extract the values.

### Profile URL
Provide a public profile URL for automatic parsing.

## Output Sections

- Executive Summary
- Pipeline Visualizer
- Portfolio Allocation
- AI Advisory Layer
- Schema Validation
- Decision Trace
- Flashcards

## Example Use Case

A 22-year-old investor with moderate income, emergency savings, and a medium-risk appetite can get a diversified allocation recommendation with scenario-based insights and confidence scoring.

## Notes

- This project is for educational and advisory purposes only.
- It should not be treated as professional financial advice.
- Output quality depends on the accuracy of the input profile.

## Future Improvements

- Add user authentication
- Save analysis history
- Improve profile extraction from URLs
- Add stronger portfolio optimization logic
- Export reports as PDF

