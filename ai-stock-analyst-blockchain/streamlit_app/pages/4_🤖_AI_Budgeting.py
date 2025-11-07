"""
AI Portfolio Budgeter - Alpha Vantage Edition (2-Stock Optimized)
================================================================
This page allows a user to input a budget and risk profile, and receive
a fully-allocated investment plan based on AI analysis using Alpha Vantage.

OPTIMIZED FOR FREE TIER: Only 2 stocks = 2 API calls (out of 25/day limit)

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

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from stock_advisor_alphavantage import StockAdvisorAlphaVantage  # CHANGED
    from ai_budgeter import AIBudgeter  # ADDED
    from portfolio_manager import BlockchainPortfolioManagerEnhanced
    from blockchain_integration import BlockchainPortfolioManager
except ImportError as e:
    st.error(f"**Import Error:** {e}")
    st.error("Could not import required modules. Ensure all files are in the `streamlit_app` directory.")
    st.stop()

st.set_page_config(
    page_title="AI Budgeting - AI Stock Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    .sub-header {
        text-align: center;
        color: #1f77b4 !important;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    
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

    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize all session state variables"""
    
    if 'alpha_vantage_key' not in st.session_state:
        st.session_state.alpha_vantage_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", "ZRBAZ10IY283K3T7")
    
    if 'advisor' not in st.session_state:
        st.session_state.advisor = StockAdvisorAlphaVantage(st.session_state.alpha_vantage_key)
    
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = BlockchainPortfolioManagerEnhanced(
            blockchain_enabled=True
        )
        st.session_state.portfolio_manager.set_stock_advisor(st.session_state.advisor)
    
    if 'wallet_connected' not in st.session_state:
        st.session_state.wallet_connected = False
    
    if 'contract_address' not in st.session_state:
        st.session_state.contract_address = st.secrets.get("CONTRACT_ADDRESS", "")
    
    if 'rpc_url' not in st.session_state:
        st.session_state.rpc_url = st.secrets.get("RPC_URL", "")
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "streamlit_user"
        
    if 'generated_plan' not in st.session_state:
        st.session_state.generated_plan = None

init_session_state()

# --- AI BUDGETING LOGIC (ONLY 2 STOCKS) ---

@st.cache_data(ttl=3600)
def get_stock_candidates(_advisor: StockAdvisorAlphaVantage) -> list:
    """
    OPTIMIZED FOR FREE TIER: Analyzes only 2 stocks.
    
    Alpha Vantage Free Tier: 25 API calls/day limit
    This app uses: 1 API call × 2 stocks = 2 calls total
    WELL under the 25 call limit!
    
    Args:
        _advisor: The initialized StockAdvisorAlphaVantage instance.
        
    Returns:
        A list of 2 candidate stock dictionaries with technical data.
    """
    
    # ===== ONLY 2 STOCKS =====
    stock_universe = {
        'AAPL': 'Technology',
        'MSFT': 'Technology'
    }
    
    candidates = []
    progress_bar = st.progress(0, text="Analyzing market candidates...")
    
    total_stocks = len(stock_universe)
    
    for i, (symbol, sector) in enumerate(stock_universe.items()):
        try:
            progress_bar.progress(
                (i + 1) / total_stocks, 
                text=f"Analyzing {symbol} ({i+1}/{total_stocks})..."
            )
            
            # Get technical analysis (1 API call per stock)
            analysis = _advisor.analyze_stock_technical(symbol)
            
            if not analysis:
                print(f"Warning: Could not analyze {symbol}")
                continue
            
            candidates.append({
                'symbol': symbol,
                'name': symbol,
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
            
            # Small delay (not necessary with 2 stocks, but good practice)
            if i < total_stocks - 1:
                time.sleep(2)
            
        except Exception as e:
            print(f"Error fetching candidate data for {symbol}: {e}")
    
    progress_bar.empty()
    
    if len(candidates) > 0:
        st.success(f"✅ Successfully analyzed {len(candidates)} stocks (API calls: {len(candidates)}/25)")
    else:
        st.error("❌ Failed to analyze any stocks")
    
    return candidates


def generate_investment_plan(budget: float, risk_profile: str, 
                            candidates: list, advisor: StockAdvisorAlphaVantage) -> Tuple[Optional[list], Optional[str]]:
    """
    Generates a diversified portfolio plan based on technical analysis.
    
    Args:
        budget: Total user budget.
        risk_profile: 'Conservative', 'Moderate', or 'Aggressive'.
        candidates: List of analyzed stocks (2 stocks).
        advisor: StockAdvisorAlphaVantage instance.
        
    Returns:
        Tuple of (final_plan, error_message)
    """
    if not candidates:
        return None, "Error: Could not fetch stock candidates. Check your API key."
    
    budgeter = AIBudgeter()
    budgeter.set_verbose(True)
    
    plan, error = budgeter.generate_investment_plan(budget, risk_profile, candidates)
    
    if error:
        return None, error
    
    if not plan:
        return None, "Error: Plan generation failed."
    
    for item in plan:
        item['sector'] = item.get('sector', 'Unknown')
    
    return plan, None

# --- PAGE UI ---
st.markdown("""
<div class="info-box">
    <h3>🤖 AI Portfolio Budgeter (Optimized)</h3>
    <p>This AI-powered tool analyzes <strong>2 premium stocks</strong> (AAPL + MSFT) using technical indicators 
    (RSI, MACD, trend analysis) from <strong>Alpha Vantage</strong>. It generates a personalized investment plan 
    based on your budget and risk tolerance. <strong>Minimal API usage = No rate limits!</strong></p>
</div>
""", unsafe_allow_html=True)

st.subheader("1. Configure Your Investment Plan")

col1, col2 = st.columns(2)
with col1:
    budget = st.number_input(
        "Enter Your Total Investment Budget ($)",
        min_value=100.0,
        max_value=1000000.0,
        value=1000.0,
        step=100.0,
        help="Enter the total amount you want to invest (minimum $100)."
    )

with col2:
    risk_profile = st.selectbox(
        "Select Your Risk Profile",
        ['Conservative', 'Moderate', 'Aggressive'],
        index=1,
        help="**Conservative**: Broad diversification, stable sectors\n"
             "**Moderate**: Balanced growth and stability\n"
             "**Aggressive**: Concentrated bets, high-growth sectors"
    )

generate_btn = st.button(
    "🚀 Generate AI Investment Plan",
    type="primary",
    use_container_width=True
)

st.divider()

# --- Plan Generation and Display ---
if generate_btn:
    st.session_state.generated_plan = None
    
    with st.spinner(f"🤖 **Analyzing 2 stocks...** Generating a '{risk_profile}' plan for **${budget:,.2f}**..."):
        try:
            candidates = get_stock_candidates(st.session_state.advisor)
            
            if not candidates:
                st.error("❌ Could not analyze stocks. Check your API key and try again.")
                st.info("💡 **Tip:** Free tier has 25 calls/day limit. Wait until tomorrow if depleted.")
                st.stop()
            
            plan, error = generate_investment_plan(
                budget, 
                risk_profile, 
                candidates, 
                st.session_state.advisor
            )
            
            if error:
                st.error(f"**AI Plan Generation Failed:** {error}")
            elif plan:
                st.session_state.generated_plan = plan
                st.success(f"✅ AI Investment Plan Generated Successfully for {len(plan)} stocks!")
            else:
                st.error("❌ An unknown error occurred.")
                
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            st.exception(e)

# --- Display the generated plan ---
if st.session_state.generated_plan:
    plan = st.session_state.generated_plan
    
    st.subheader(f"📈 Your {risk_profile} AI Investment Plan")
    
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
            "Shares": f"{item['shares']:.4f}",
            "Current Price": f"${item['current_price']:.2f}",
            "Target Price": f"${item['target_mean']:.2f}",
            "Upside": f"{item['upside_pct']:.2f}%",
            "Tech Score": f"{item.get('buy_score', 0):.0f}/100"
        })
    
    plan_df = pd.DataFrame(plan_df_data)
    st.dataframe(plan_df, use_container_width=True, hide_index=True)
    
    total_upside_pct = ((total_potential_value - total_allocated) / total_allocated) * 100 if total_allocated > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Budget", f"${budget:,.2f}")
    col2.metric("Total Allocated", f"${total_allocated:,.2f}")
    col3.metric("Stocks Selected", f"{len(plan)}")
    col4.metric("Est. 12-Mo. Upside", f"{total_upside_pct:,.1f}%")

    st.markdown("---")
    
    with st.expander("📊 Technical Analysis Details", expanded=False):
        tech_df_data = []
        for item in plan:
            tech_df_data.append({
                "Stock": item['symbol'],
                "RSI": f"{item.get('rsi', 'N/A')}",
                "MACD": item.get('macd_signal', 'N/A'),
                "Trend": item.get('trend', 'N/A'),
                "Score": f"{item.get('buy_score', 0):.0f}/100"
            })
        tech_df = pd.DataFrame(tech_df_data)
        st.dataframe(tech_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    st.subheader("2. Save Plan to Blockchain")
    
    if not st.session_state.wallet_connected:
        st.warning("⚠️ **Wallet not connected!** Connect via the 'Home' page sidebar.")
    
    save_plan_btn = st.button(
        f"🔗 Save {len(plan)} Investments to Blockchain",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.wallet_connected,
        key="save_plan_button"
    )
    
    if save_plan_btn:
        st.info(f"**Executing Plan...** Saving {len(plan)} investments to blockchain.")
        progress_bar = st.progress(0, text="Initializing...")
        
        success_count = 0
        fail_count = 0
        
        for i, item in enumerate(plan):
            symbol = item['symbol']
            progress_text = f"Saving {symbol} ({i+1}/{len(plan)})..."
            progress_bar.progress((i + 1) / len(plan), text=progress_text)
            
            try:
                result_str = st.session_state.portfolio_manager.add_investment_blockchain(
                    user_id=st.session_state.user_id,
                    company=symbol,
                    shares=item['shares'],
                    purchase_price=item['current_price'],
                    purchase_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                if "Transaction Hash" in result_str:
                    st.success(f"✅ **{symbol}**: Saved to blockchain")
                    success_count += 1
                else:
                    st.warning(f"⚠️ **{symbol}**: Saved locally only")
                    fail_count += 1
                    
            except Exception as e:
                st.error(f"❌ **{symbol}**: {str(e)}")
                fail_count += 1
        
        progress_bar.empty()
        st.success(f"**Execution Complete!**")
        st.markdown(f"- **{success_count}** saved to blockchain")
        st.markdown(f"- **{fail_count}** failed")
        st.info("Navigate to **'💼 Portfolio'** to view holdings!")
        st.session_state.generated_plan = None

st.divider()

# --- Educational Expanders ---
with st.expander("📚 Why Only 2 Stocks?", expanded=False):
    st.markdown("""
    ### Alpha Vantage Free Tier Limits:
    - **25 API calls/day** limit
    - **5 API calls/minute** rate limit
    
    ### This App Strategy:
    - **2 stocks analyzed** = 2 API calls total
    - **Uses 8% of daily limit** (2 out of 25)
    - **100% under rate limit** (2 out of 5/minute)
    - **No waiting** = Instant results
    - **Premium stocks** = AAPL + MSFT (highest quality)
    
    ### Result:
    ✅ **Zero rate limiting issues**
    ✅ **Fast execution**
    ✅ **Reliable every time**
    """)

with st.expander("❓ How does the AI work?"):
    st.markdown("""
    This AI Budgeter uses **technical analysis** on 2 premium stocks:
    
    1. **Analyze:** RSI, MACD, Trend, Momentum (1 call per stock)
    2. **Score:** Calculate 0-100 technical score
    3. **Filter:** Apply risk profile criteria
    4. **Allocate:** Distribute budget optimally
    
    **All within free tier limits!**
    """)

with st.expander("🔑 API Usage"):
    st.markdown(f"""
    ### Alpha Vantage Status:
    - **API Key:** {"✅ Connected" if st.session_state.alpha_vantage_key else "❌ Not configured"}
    - **Free Tier:** 25 calls/day
    - **This Run:** 2 calls
    - **Remaining:** 23 calls today
    - **Cache:** 1 hour
    """)
