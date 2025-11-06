
"""
AI Portfolio Budgeter - New Feature Page
=========================================
This page allows a user to input a budget and risk profile, and receive
a fully-allocated investment plan based on AI analysis of Finnhub data.

- Uses Finnhub for analyst ratings and price targets.
- Generates a diversified plan based on risk.
- Allows one-click saving of the entire plan to the blockchain portfolio.
"""

import streamlit as st
import sys
import os
import pandas as pd
import random
from datetime import datetime
import time

# --- Path Setup ---
# Add parent directory to path to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    # Import existing modules from the streamlit_app directory
    from stock_advisor_finnhub import StockAdvisorFinnhub
    from portfolio_manager import BlockchainPortfolioManagerEnhanced
    from blockchain_integration import BlockchainPortfolioManager
except ImportError as e:
    st.error(f"**Import Error:** {e}")
    st.error("Could not import required modules. Ensure `stock_advisor_finnhub.py` and `portfolio_manager.py` are in the `streamlit_app` directory.")
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
    
    # Get Finnhub API key from secrets
    if 'finnhub_key' not in st.session_state:
        st.session_state.finnhub_key = st.secrets.get("FINNHUB_API_KEY", "d415bmpr01qo6qdf06d0d415bmpr01qo6qdf06dg")
    
    # Initialize StockAdvisorFinnhub (using Finnhub, as requested)
    if 'advisor' not in st.session_state:
        st.session_state.advisor = StockAdvisorFinnhub(st.session_state.finnhub_key)
    
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

@st.cache_data(ttl=3600) # Cache for 1 hour to avoid re-fetching Finnhub data
def get_stock_candidates(_advisor: StockAdvisorFinnhub) -> list:
    """
    Fetches recommendation trends and price targets for a predefined
    list of popular, high-quality stocks to build our "analysis universe".
    
    Args:
        _advisor: The initialized StockAdvisorFinnhub instance.
        
    Returns:
        A list of candidate stock dictionaries.
    """
    
    # This is our "analysis universe" - a set of well-known, liquid stocks.
    # The AI will pick from this list.
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
    
    for i, (symbol, sector) in enumerate(stock_universe.items()):
        try:
            progress_bar.progress((i + 1) / len(stock_universe), text=f"Analyzing {symbol}...")
            
            # Use Finnhub methods (as requested)
            recs = _advisor.client.recommendation_trends(symbol)
            target = _advisor.client.price_target(symbol)
            
            if not recs or not target:
                continue
            
            # Get the most recent recommendation and target
            latest_rec = recs[0]
            
            # Ensure target data is valid
            if not latest_target.get('targetMean') or latest_target['targetMean'] == 0:
                continue
                
            candidates.append({
                'symbol': symbol,
                'sector': sector,
                'strongBuy': latest_rec['strongBuy'],
                'buy': latest_rec['buy'],
                'hold': latest_rec['hold'],
                'sell': latest_rec['sell'],
                'strongSell': latest_rec['strongSell'],
                'targetHigh': latest_target['targetHigh'],
                'targetLow': latest_target['targetLow'],
                'targetMean': latest_target['targetMean'],
                'targetMedian': latest_target['targetMedian']
            })
            time.sleep(0.5) # Avoid hitting API rate limits if any

        except Exception as e:
            # Finnhub API can be strict. We'll just skip this stock if it fails.
            print(f"Error fetching candidate data for {symbol}: {e}")
            
    progress_bar.empty()
    return candidates

def generate_investment_plan(budget: float, risk_profile: str, candidates: list, advisor: StockAdvisorFinnhub) -> (list, str):
    """
    The core AI budgeting logic.
    Generates a diversified portfolio plan based on risk profile and predicted data.
    
    Args:
        budget (float): Total user budget.
        risk_profile (str): 'Conservative', 'Moderate', or 'Aggressive'.
        candidates (list): List of stocks from get_stock_candidates.
        advisor (StockAdvisorFinnhub): Instance to get live prices.
        
    Returns:
        A tuple of (final_plan, error_message).
    """
    if not candidates:
        return None, "Error: Could not fetch any stock candidates. Finnhub API might be down or key is invalid."

    # 1. Filter candidates based on strong analyst ratings
    buy_list = []
    for c in candidates:
        # Define "Buy" as > 50% combined buy/strongBuy ratings
        buy_score = c['buy'] + c['strongBuy']
        sell_score = c['sell'] + c['strongSell']
        
        # We want stocks where analysts are clearly bullish
        if buy_score > (c['hold'] + sell_score) and buy_score > 10:
            buy_list.append(c)

    if not buy_list:
        return None, "Error: No stocks met the 'Strong Buy' criteria from analyst ratings. Market might be bearish or data is unavailable."
    
    # 2. Get live quotes for all our "Buy" candidates
    # This is critical for calculating share amounts
    quotes = {}
    st.info("Fetching live prices for 'Buy' list stocks...")
    for stock in buy_list:
        symbol = stock['symbol']
        quote = advisor.get_stock_quote(symbol) # Uses existing finnhub method
        if quote and quote['price'] > 0:
            quotes[symbol] = quote['price']
        else:
            print(f"Could not get quote for {symbol}")
    
    if not quotes:
        return None, "Error: Could not fetch live prices for 'Buy' list stocks. Cannot calculate allocation."
    
    # 3. Define allocation strategy based on risk
    plan_config = {
        'Conservative': {
            'num_stocks': 7, # Broad diversification
            'sectors': ['Technology', 'Healthcare', 'Financial', 'Energy', 'Consumer Defensive'], # Stable sectors
            'min_buy_score': 10, # Good 'Buy' rating
            'max_weight': 0.20 # Max 20% in one stock
        },
        'Moderate': {
            'num_stocks': 5, # Balanced diversification
            'sectors': ['Technology', 'Consumer Cyclical', 'Healthcare', 'Financial'],
            'min_buy_score': 15, # Strong 'Buy' rating
            'max_weight': 0.30 # Max 30% in one stock
        },
        'Aggressive': {
            'num_stocks': 3, # Concentrated bets
            'sectors': ['Technology', 'Consumer Cyclical'], # High-growth sectors
            'min_buy_score': 20, # Very Strong 'Buy' rating
            'max_weight': 0.50 # Max 50% in one stock
        }
    }
    
    config = plan_config[risk_profile]
    
    # 4. Filter stocks by our risk-profile config
    final_candidates = []
    for stock in buy_list:
        if stock['symbol'] not in quotes: # Skip if we failed to get a price
            continue
        
        # Check sector
        if stock['sector'] not in config['sectors']:
            continue
        
        # Check rating score
        if (stock['buy'] + stock['strongBuy']) < config['min_buy_score']:
            continue
            
        # Calculate potential upside *based on predicted data* (as requested)
        current_price = quotes[stock['symbol']]
        target_price = stock['targetMean']
        
        if current_price > 0 and target_price > current_price:
            stock['upside_pct'] = ((target_price - current_price) / current_price) * 100
            stock['current_price'] = current_price
            final_candidates.append(stock)
    
    if not final_candidates:
        return None, f"Error: No stocks matched the specific criteria for a '{risk_profile}' profile. Try a different risk profile."

    # 5. Select top N stocks based on highest potential upside
    final_candidates.sort(key=lambda x: x['upside_pct'], reverse=True)
    selected_stocks = final_candidates[:config['num_stocks']]
    
    # 6. Allocate budget
    # We'll do a simple equal-weight allocation
    num_stocks = len(selected_stocks)
    if num_stocks == 0:
         return None, f"Error: No stocks matched the criteria for a '{risk_profile}' profile after final filtering."

    allocation_per_stock = budget / num_stocks
    
    final_plan = []
    total_cost = 0
    
    for stock in selected_stocks:
        # Ensure allocation doesn't exceed max weight (though equal weight should be fine)
        stock_budget = min(allocation_per_stock, budget * config['max_weight'])
        
        shares_to_buy = stock_budget / stock['current_price']
        cost = shares_to_buy * stock['current_price']
        
        plan_item = {
            'symbol': stock['symbol'],
            'shares': shares_to_buy,
            'current_price': stock['current_price'],
            'cost': cost,
            'allocation_pct': (cost / budget) * 100,
            'target_mean': stock['targetMean'],
            'upside_pct': stock['upside_pct']
        }
        final_plan.append(plan_item)
        total_cost += cost
        
    # If allocation left money, put it in the top pick
    remainder = budget - total_cost
    if remainder > 1.00: # More than $1
        top_pick = final_plan[0]
        extra_shares = remainder / top_pick['current_price']
        top_pick['shares'] += extra_shares
        top_pick['cost'] += remainder
        
    return final_plan, None # Return plan and no error

# --- END OF AI LOGIC ---


# --- PAGE UI ---
st.markdown("""
<div class="info-box">
    <h3>🤖 AI Portfolio Budgeter</h3>
    <p>This is a proactive portfolio generation tool. Based on your budget and risk tolerance, the AI will scan the market for stocks with strong analyst 'Buy' ratings and high price targets. It will then generate a diversified, ready-to-execute investment plan.</p>
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
        help="Enter the total amount (e.g., $1000) you want to invest."
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
    st.session_state.generated_plan = None # Clear old plan
    
    with st.spinner(f"🤖 **Analyzing market...** Generating a '{risk_profile}' plan for **${budget:,.2f}**..."):
        try:
            # 1. Get all stock candidates (uses cache)
            candidates = get_stock_candidates(st.session_state.advisor)
            
            # 2. Generate the plan
            plan, error = generate_investment_plan(
                budget, 
                risk_profile, 
                candidates, 
                st.session_state.advisor
            )
            
            if error:
                st.error(f"**AI Plan Generation Failed:** {error}")
            elif plan:
                st.session_state.generated_plan = plan # Save the plan
                st.success(f"✅ AI Investment Plan Generated Successfully for {len(plan)} stocks!")
            else:
                st.error("❌ An unknown error occurred during plan generation.")
                
        except Exception as e:
            st.error(f"An unexpected application error occurred: {e}")
            st.exception(e)

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
            "Allocation": f"${item['cost']:.2f}",
            "% of Portfolio": f"{item['allocation_pct']:.1f}%",
            "Shares to Buy": f"{item['shares']:.4f}",
            "Current Price": f"${item['current_price']:.2f}",
            "Analyst Target": f"${item['target_mean']:.2f}",
            "Potential Upside": f"{item['upside_pct']:.2f}%"
        })
    
    # Display the plan in a clean DataFrame
    plan_df = pd.DataFrame(plan_df_data)
    st.dataframe(
        plan_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Stock": st.column_config.TextColumn("Stock", width="small"),
            "Allocation": st.column_config.TextColumn("Allocation", width="small"),
            "% of Portfolio": st.column_config.TextColumn("%", width="small"),
            "Shares to Buy": st.column_config.TextColumn("Shares", width="medium"),
            "Current Price": st.column_config.TextColumn("Current Price", width="small"),
            "Analyst Target": st.column_config.TextColumn("12-Mo Target", width="small"),
            "Potential Upside": st.column_config.TextColumn("Upside", width="small"),
        }
    )

    # Display Summary Metrics
    total_upside_pct = ((total_potential_value - total_allocated) / total_allocated) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Budget", f"${budget:,.2f}")
    col2.metric("Total Allocated", f"${total_allocated:,.2f}")
    col3.metric("Stocks Selected", f"{len(plan)}")
    col4.metric("Potential 12-Mo. Upside", f"{total_upside_pct:,.2f}%", 
               help=f"Based on mean analyst price targets, potential value of ${total_potential_value:,.2f}")

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
                # Call the *existing* function from portfolio_manager
                # This re-uses your code perfectly.
                result_str = st.session_state.portfolio_manager.add_investment_blockchain(
                    user_id=st.session_state.user_id,
                    company=symbol, # For this model, company name is the symbol
                    shares=item['shares'],
                    purchase_price=item['current_price'],
                    purchase_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # Check the string response from your existing function
                if "Transaction Hash" in result_str:
                    st.markdown(f"✅ **{symbol}**: Successfully saved to blockchain.")
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
        - **Stable Sectors:** Focuses on mature sectors like Healthcare, Consumer Defensive, and Energy.
        - **Quality Stocks:** Selects stocks with good 'Buy' ratings, but doesn't chase the highest growth.
    - **Best for:** Investors new to the market or those with a low tolerance for volatility.

    ### ⚖️ Moderate
    - **Goal:** A balance of growth and stability.
    - **Strategy:**
        - **Balanced Portfolio:** Selects 3-5 stocks.
        - **Mixed Sectors:** Includes stable sectors *and* growth sectors like Technology and Consumer Cyclical.
        - **Strong Ratings:** Focuses on stocks with strong analyst 'Buy' ratings.
    - **Best for:** Most investors looking for long-term growth without extreme risk.

    ### 🚀 Aggressive
    - **Goal:** Maximum capital growth.
    - **Strategy:**
        - **Concentrated Bets:** Focuses your budget on only 2-3 high-conviction stocks.
        - **Growth Sectors:** Heavily favors Technology and Consumer Cyclical sectors (e.g., TSLA, NVDA).
        - **Highest Conviction:** Selects only stocks with very strong 'Buy' ratings and high analyst price targets.
    - **Best for:** Experienced investors with a high risk tolerance and a long time horizon.
    """)

with st.expander("❓ How does the AI generate this plan?"):
    st.markdown("""
    This AI Budgeter follows a 6-step professional-grade process:
    
    1.  **Define Universe:** It starts by analyzing a pre-defined list of ~20 high-quality, popular stocks.
    2.  **Analyst Ratings:** It fetches **Finnhub** analyst recommendations (`recommendation_trends`) for all stocks in this universe.
    3.  **Filter for 'Buys':** It creates a "Buy List" of stocks where the majority of analysts have a 'Buy' or 'Strong Buy' rating.
    4.  **Fetch Predicted Data:** It fetches **Finnhub** price targets (`price_target`) for every stock on the "Buy List" and calculates the potential percentage upside.
    5.  **Apply Risk Profile:** It filters the "Buy List" again based on your chosen risk profile (e.g., an 'Aggressive' profile looks for high-growth sectors, a 'Conservative' one looks for stable sectors).
    6.  **Allocate Budget:** It selects the top stocks from this final list (based on upside potential) and allocates your budget among them to generate the final plan.
    """)
    