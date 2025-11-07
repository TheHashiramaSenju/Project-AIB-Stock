"""
AI Portfolio Budgeter - Alpha Vantage Edition
=============================================
This page allows a user to input a budget and risk profile, and receive
a fully-allocated investment plan based on AI analysis using Alpha Vantage.

Features:
- Uses Alpha Vantage for technical analysis (RSI, MACD, trend analysis)
- Generates a diversified plan based on risk profile
- Allows one-click saving of the entire plan to the blockchain portfolio
- Full integration with existing portfolio management system

Author: Bhoomika M
Date: 2025-11-07
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import time
from typing import Tuple, List, Dict, Optional

# --- Path Setup ---
# Add parent directory to path to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    # Import Alpha Vantage modules (UPDATED FROM FINNHUB)
    from stock_advisor_alphavantage import StockAdvisorAlphaVantage
    from ai_budgeter import AIBudgeter
    from portfolio_manager import BlockchainPortfolioManagerEnhanced
    from blockchain_integration import BlockchainPortfolioManager
except ImportError as e:
    st.error(f"**Import Error:** {e}")
    st.error("Could not import required modules. Ensure all files are in the `streamlit_app` directory.")
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Budgeting - AI Stock Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS (from other pages for consistency) ---
st.markdown("""
<style>
    /* Main header gradient */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* Subheader - blue color */
    .sub-header {
        text-align: center;
        color: #1f77b4 !important;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    
    /* Info boxes for results */
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .info-box h3 {
        color: white !important;
        margin-top: 0;
        font-size: 1.3rem;
        font-weight: 700;
    }
    .info-box p {
        color: white !important;
        opacity: 0.95;
        font-size: 1rem;
        line-height: 1.6;
    }

    /* Expander headers */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
def init_session_state():
    """Initialize all session state variables"""
    
    # Get Alpha Vantage API key from secrets (CHANGED FROM FINNHUB)
    if 'alpha_vantage_key' not in st.session_state:
        st.session_state.alpha_vantage_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", "ZRBAZ10IY283K3T7")
    
    # Initialize StockAdvisorAlphaVantage (CHANGED FROM FINNHUB)
    if 'advisor' not in st.session_state:
        st.session_state.advisor = StockAdvisorAlphaVantage(st.session_state.alpha_vantage_key)
    
    # Initialize portfolio manager
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = BlockchainPortfolioManagerEnhanced(
            blockchain_enabled=True
        )
        st.session_state.portfolio_manager.set_stock_advisor(st.session_state.advisor)
    
    # Wallet connection status
    if 'wallet_connected' not in st.session_state:
        st.session_state.wallet_connected = False
    
    # Blockchain configuration (loaded from secrets)
    if 'contract_address' not in st.session_state:
        st.session_state.contract_address = st.secrets.get("CONTRACT_ADDRESS", "")
    
    if 'rpc_url' not in st.session_state:
        st.session_state.rpc_url = st.secrets.get("RPC_URL", "")
    
    # User ID for portfolio
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "streamlit_user"
        
    # State variable to hold the generated plan
    if 'generated_plan' not in st.session_state:
        st.session_state.generated_plan = None

# Call initialization
init_session_state()

# --- AI BUDGETING LOGIC ---
# This section contains the "brain" of the AI Budgeter

@st.cache_data(ttl=3600)  # Cache for 1 hour to avoid re-fetching data
def get_stock_candidates(_advisor: StockAdvisorAlphaVantage) -> list:
    """
    Fetches technical analysis for a predefined list of popular, 
    high-quality stocks to build our "analysis universe".
    
    Uses Alpha Vantage API for:
    - Real-time stock quotes
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Trend analysis (SMA 50 vs SMA 200)
    
    Args:
        _advisor: The initialized StockAdvisorAlphaVantage instance.
        
    Returns:
        A list of candidate stock dictionaries with technical data.
    """
    
    # This is our "analysis universe" - a set of well-known, liquid stocks.
    # The AI will pick from this list based on technical indicators.
    stock_universe = {
        'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
        'TSLA': 'Consumer Cyclical', 'NVDA': 'Technology', 'AMZN': 'Consumer Cyclical',
        'JPM': 'Financial', 'BAC': 'Financial', 'META': 'Technology',
        'NFLX': 'Communication Services', 'AMD': 'Technology', 'INTC': 'Technology',
        'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare',
        'XOM': 'Energy', 'CVX': 'Energy', 'COST': 'Consumer Defensive',
        'WMT': 'Consumer Defensive', 'MCD': 'Consumer Cyclical'
    }
    
    candidates = []
    progress_bar = st.progress(0, text="Analyzing market candidates...")
    
    total_stocks = len(stock_universe)
    analyzed_count = 0
    failed_count = 0
    
    for i, (symbol, sector) in enumerate(stock_universe.items()):
        try:
            progress_bar.progress(
                (i + 1) / total_stocks, 
                text=f"Analyzing {symbol} ({i+1}/{total_stocks})..."
            )
            
            # Use Alpha Vantage technical analysis
            analysis = _advisor.analyze_stock_technical(symbol)
            
            if not analysis:
                failed_count += 1
                print(f"Warning: Could not analyze {symbol}")
                continue
            
            # Build candidate dictionary with all necessary data
            candidates.append({
                'symbol': symbol,
                'name': symbol,  # Can enhance with company names later
                'sector': sector,
                'price': analysis['price'],
                'change_percent': analysis['change_percent'],
                'rsi': analysis['rsi'],
                'macd_signal': analysis['macd_signal'],
                'trend': analysis['trend'],
                'recommendation': analysis['recommendation'],
                'volume': analysis['volume'],
                'high': analysis.get('high', 0),
                'low': analysis.get('low', 0),
                'change': analysis.get('change', 0)
            })
            
            analyzed_count += 1
            
        except Exception as e:
            # Alpha Vantage API can hit rate limits or have errors
            # We'll just skip this stock if it fails
            failed_count += 1
            print(f"Error fetching candidate data for {symbol}: {e}")
    
    progress_bar.empty()
    
    # Show summary of analysis
    if analyzed_count > 0:
        st.success(f"✅ Successfully analyzed {analyzed_count} stocks")
    if failed_count > 0:
        st.warning(f"⚠️ Failed to analyze {failed_count} stocks (API limits or errors)")
    
    return candidates


def generate_investment_plan(budget: float, risk_profile: str, 
                            candidates: list, advisor: StockAdvisorAlphaVantage) -> Tuple[Optional[list], Optional[str]]:
    """
    The core AI budgeting logic.
    Generates a diversified portfolio plan based on risk profile and technical analysis.
    
    This function now uses the AIBudgeter class which implements:
    - Technical scoring (0-100) based on RSI, MACD, trend, momentum
    - Risk-based filtering and selection
    - Smart budget allocation
    
    Args:
        budget (float): Total user budget.
        risk_profile (str): 'Conservative', 'Moderate', or 'Aggressive'.
        candidates (list): List of stocks from get_stock_candidates.
        advisor (StockAdvisorAlphaVantage): Instance for any additional data needs.
        
    Returns:
        A tuple of (final_plan, error_message).
    """
    if not candidates:
        return None, "Error: Could not fetch any stock candidates. Alpha Vantage API might be down or rate-limited."
    
    # Initialize the AI Budgeter
    budgeter = AIBudgeter()
    budgeter.set_verbose(True)  # Enable detailed logging
    
    # Generate the investment plan using technical analysis
    plan, error = budgeter.generate_investment_plan(budget, risk_profile, candidates)
    
    if error:
        return None, error
    
    if not plan:
        return None, "Error: Plan generation returned empty result."
    
    # Add sector information to plan items for display
    for item in plan:
        item['sector'] = item.get('sector', 'Unknown')
    
    return plan, None

# --- END OF AI LOGIC ---

# --- PAGE UI ---
st.markdown("""
<div class="info-box">
    <h3>🤖 AI Portfolio Budgeter</h3>
    <p>This is a proactive portfolio generation tool powered by <strong>Alpha Vantage</strong>. 
    Based on your budget and risk tolerance, the AI will analyze the market using technical indicators 
    (RSI, MACD, trend analysis) to find optimal investment opportunities. It will then generate a 
    diversified, ready-to-execute investment plan tailored to your risk profile.</p>
</div>
""", unsafe_allow_html=True)

st.subheader("1. Configure Your Investment Plan")

# Input Controls
col1, col2 = st.columns(2)
with col1:
    budget = st.number_input(
        "Enter Your Total Investment Budget ($)",
        min_value=100.0,
        max_value=1000000.0,
        value=1000.0,
        step=100.0,
        help="Enter the total amount (e.g., $1000) you want to invest. Minimum: $100"
    )

with col2:
    risk_profile = st.selectbox(
        "Select Your Risk Profile",
        ['Conservative', 'Moderate', 'Aggressive'],
        index=1,
        help="**Conservative**: Broad diversification (5-7 stocks) in stable sectors.\n"
             "**Moderate**: Balanced (3-5 stocks) with a mix of growth and stability.\n"
             "**Aggressive**: Concentrated (2-3 stocks) in high-growth sectors."
    )

# Generate Plan Button
generate_btn = st.button(
    "🚀 Generate AI Investment Plan",
    type="primary",
    use_container_width=True
)

st.divider()

# --- Plan Generation and Display ---
if generate_btn:
    st.session_state.generated_plan = None  # Clear old plan
    
    with st.spinner(f"🤖 **Analyzing market...** Generating a '{risk_profile}' plan for **${budget:,.2f}**..."):
        try:
            # 1. Get all stock candidates (uses cache)
            candidates = get_stock_candidates(st.session_state.advisor)
            
            if not candidates:
                st.error("❌ Could not analyze any stocks. Please check your Alpha Vantage API key and try again.")
                st.info("💡 **Tip:** Free tier has 5 calls/minute limit. Wait 60 seconds and retry.")
                st.stop()
            
            # 2. Generate the plan using AI Budgeter
            plan, error = generate_investment_plan(
                budget, 
                risk_profile, 
                candidates, 
                st.session_state.advisor
            )
            
            if error:
                st.error(f"**AI Plan Generation Failed:** {error}")
                st.info("💡 Try selecting a different risk profile or check if market conditions are suitable.")
            elif plan:
                st.session_state.generated_plan = plan  # Save the plan
                st.success(f"✅ AI Investment Plan Generated Successfully for {len(plan)} stocks!")
            else:
                st.error("❌ An unknown error occurred during plan generation.")
                
        except Exception as e:
            st.error(f"An unexpected application error occurred: {e}")
            st.exception(e)
            st.info("Please try again or contact support if the issue persists.")

# --- Display the generated plan if it exists in session state ---
if st.session_state.generated_plan:
    plan = st.session_state.generated_plan
    
    st.subheader(f"📈 Your {risk_profile} AI Investment Plan")
    
    # Display Plan Metrics
    plan_df_data = []
    total_allocated = 0
    total_potential_value = 0
    
    for item in plan:
        total_allocated += item['cost']
        potential_value = item['shares'] * item['target_mean']
        total_potential_value += potential_value
        
        plan_df_data.append({
            "Stock": item['symbol'],
            "Sector": item.get('sector', 'N/A'),
            "Allocation": f"${item['cost']:.2f}",
            "% of Portfolio": f"{item['allocation_pct']:.1f}%",
            "Shares to Buy": f"{item['shares']:.4f}",
            "Current Price": f"${item['current_price']:.2f}",
            "Target Price": f"${item['target_mean']:.2f}",
            "Potential Upside": f"{item['upside_pct']:.2f}%",
            "Tech Score": f"{item.get('buy_score', 0):.0f}/100"
        })
    
    # Display the plan in a clean DataFrame
    plan_df = pd.DataFrame(plan_df_data)
    st.dataframe(
        plan_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Stock": st.column_config.TextColumn("Stock", width="small"),
            "Sector": st.column_config.TextColumn("Sector", width="medium"),
            "Allocation": st.column_config.TextColumn("Allocation", width="small"),
            "% of Portfolio": st.column_config.TextColumn("%", width="small"),
            "Shares to Buy": st.column_config.TextColumn("Shares", width="medium"),
            "Current Price": st.column_config.TextColumn("Current Price", width="small"),
            "Target Price": st.column_config.TextColumn("12-Mo Target", width="small"),
            "Potential Upside": st.column_config.TextColumn("Upside", width="small"),
            "Tech Score": st.column_config.TextColumn("Score", width="small"),
        }
    )

    # Display Summary Metrics
    total_upside_pct = ((total_potential_value - total_allocated) / total_allocated) * 100 if total_allocated > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Budget", f"${budget:,.2f}")
    col2.metric("Total Allocated", f"${total_allocated:,.2f}")
    col3.metric("Stocks Selected", f"{len(plan)}")
    col4.metric("Est. 12-Mo. Upside", f"{total_upside_pct:,.2f}%", 
               help=f"Based on technical analysis projections, potential value of ${total_potential_value:,.2f}")

    st.markdown("---")
    
    # --- Technical Analysis Summary ---
    with st.expander("📊 Technical Analysis Details", expanded=False):
        tech_df_data = []
        for item in plan:
            tech_df_data.append({
                "Stock": item['symbol'],
                "RSI": f"{item.get('rsi', 'N/A')}",
                "MACD Signal": item.get('macd_signal', 'N/A'),
                "Trend": item.get('trend', 'N/A'),
                "Technical Score": f"{item.get('buy_score', 0):.0f}/100"
            })
        tech_df = pd.DataFrame(tech_df_data)
        st.dataframe(tech_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # --- Save Plan to Blockchain Section ---
    st.subheader("2. Save Plan to Blockchain")
    st.markdown("Click the button below to execute this plan and save all transactions to your blockchain portfolio.")
    
    if not st.session_state.wallet_connected:
        st.warning("⚠️ **Wallet not connected!** Please connect your wallet via the 'Home' page sidebar to save this plan.")
    
    save_plan_btn = st.button(
        f"🔗 Save {len(plan)} Investments to Blockchain Portfolio",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.wallet_connected,
        key="save_plan_button"
    )
    
    if save_plan_btn:
        st.info(f"**Executing Plan...** Saving {len(plan)} investments to the blockchain. This will take a moment. Please wait.")
        progress_bar = st.progress(0, text="Initializing...")
        
        success_count = 0
        fail_count = 0
        
        for i, item in enumerate(plan):
            symbol = item['symbol']
            progress_text = f"Saving {symbol} ({i+1}/{len(plan)})..."
            progress_bar.progress((i + 1) / len(plan), text=progress_text)
            
            try:
                # Call the existing function from portfolio_manager
                result_str = st.session_state.portfolio_manager.add_investment_blockchain(
                    user_id=st.session_state.user_id,
                    company=symbol,  # For this model, company name is the symbol
                    shares=item['shares'],
                    purchase_price=item['current_price'],
                    purchase_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # Check the string response from your existing function
                if "Transaction Hash" in result_str:
                    st.success(f"✅ **{symbol}**: Successfully saved to blockchain.")
                    success_count += 1
                else:
                    st.warning(f"⚠️ **{symbol}**: Saved locally but blockchain write failed. {result_str}")
                    fail_count += 1
                    
            except Exception as e:
                st.error(f"❌ **{symbol}**: Critical error during save. {str(e)}")
                fail_count += 1
        
        # Final summary of execution
        progress_bar.empty()
        st.success(f"**Plan Execution Complete!**")
        st.markdown(f"### Summary:")
        st.markdown(f"- **{success_count}** investments successfully saved to blockchain.")
        st.markdown(f"- **{fail_count}** investments failed or saved locally only.")
        st.info("Navigate to the **'💼 Portfolio'** page to see your new holdings!")
        
        # Clear the plan to prevent accidental re-saving
        st.session_state.generated_plan = None
        
st.divider()

# --- Educational Expanders ---
with st.expander("📚 Understanding Risk Profiles", expanded=False):
    st.markdown("""
    Your risk profile determines how the AI builds your portfolio.
    
    ### 🛡️ Conservative
    - **Goal:** Capital preservation with modest growth.
    - **Strategy:**
        - **Broad Diversification:** Spreads your budget across 5-7 different stocks.
        - **Stable Sectors:** Focuses on mature sectors like Healthcare, Consumer Defensive, Energy, and Utilities.
        - **Quality Stocks:** Selects stocks with good technical scores (60/100 minimum).
    - **Best for:** Investors new to the market or those with a low tolerance for volatility.

    ### ⚖️ Moderate
    - **Goal:** A balance of growth and stability.
    - **Strategy:**
        - **Balanced Portfolio:** Selects 3-5 stocks.
        - **Mixed Sectors:** Includes stable sectors *and* growth sectors like Technology and Consumer Cyclical.
        - **Strong Technical Signals:** Focuses on stocks with strong technical scores (70/100 minimum).
    - **Best for:** Most investors looking for long-term growth without extreme risk.

    ### 🚀 Aggressive
    - **Goal:** Maximum capital growth.
    - **Strategy:**
        - **Concentrated Bets:** Focuses your budget on only 2-3 high-conviction stocks.
        - **Growth Sectors:** Heavily favors Technology and Consumer Cyclical sectors (e.g., TSLA, NVDA).
        - **Highest Conviction:** Selects only stocks with very strong technical scores (80/100 minimum).
    - **Best for:** Experienced investors with a high risk tolerance and a long time horizon.
    """)

with st.expander("❓ How does the AI generate this plan?"):
    st.markdown("""
    This AI Budgeter follows a **6-step professional-grade process** using Alpha Vantage technical analysis:
    
    1.  **Define Universe:** Analyzes a pre-defined list of ~20 high-quality, popular stocks.
    
    2.  **Technical Analysis:** For each stock, fetches:
        - **Real-time price** and volume data
        - **RSI (Relative Strength Index)**: Measures if stock is oversold (<30) or overbought (>70)
        - **MACD**: Identifies buy/sell momentum signals
        - **Trend Analysis**: Compares 50-day vs 200-day moving averages
    
    3.  **Calculate Technical Score:** Each stock gets a 0-100 score based on:
        - RSI (30 points)
        - MACD (30 points)
        - Trend (20 points)
        - Price Momentum (20 points)
    
    4.  **Filter by Risk Profile:** Applies your risk profile criteria:
        - Sector restrictions
        - Minimum technical score requirements
    
    5.  **Rank & Select:** Ranks stocks by weighted score (60% technical + 40% upside potential) 
        and selects the top picks for your profile.
    
    6.  **Allocate Budget:** Distributes your budget optimally:
        - Conservative/Moderate: Equal weight allocation
        - Aggressive: Weighted allocation (50/30/20 split)
    
    **All powered by real-time Alpha Vantage technical analysis!**
    """)

with st.expander("🔧 Technical Indicators Explained"):
    st.markdown("""
    ### What the AI looks for:
    
    **RSI (Relative Strength Index)**
    - Measures momentum on a 0-100 scale
    - <30 = Oversold (potential buy signal)
    - 30-70 = Neutral
    - >70 = Overbought (potential sell signal)
    
    **MACD (Moving Average Convergence Divergence)**
    - Shows momentum and trend changes
    - BUY signal: MACD line crosses above signal line
    - SELL signal: MACD line crosses below signal line
    
    **Trend Analysis (SMA 50 vs SMA 200)**
    - BULLISH: 50-day average > 200-day average (uptrend)
    - BEARISH: 50-day average < 200-day average (downtrend)
    
    **Price Momentum**
    - Current day's price change
    - Positive momentum adds to technical score
    """)

with st.expander("🔑 API Information & Limits"):
    st.markdown(f"""
    ### Alpha Vantage Configuration
    - **API Status:** {"✅ Connected" if st.session_state.alpha_vantage_key else "❌ Not configured"}
    - **Free Tier Limit:** 5 API calls per minute
    - **Cache Duration:** 1 hour (data refreshes hourly)
    - **Stocks Analyzed:** 20 symbols from major sectors
    
    **Note:** If you encounter rate limit errors:
    1. Wait 60 seconds before retrying
    2. Data is cached for 1 hour to minimize API calls
    3. Consider upgrading to Alpha Vantage premium for higher limits
    
    **Your API Key:** `{st.session_state.alpha_vantage_key[:10]}...` (hidden for security)
    """)
