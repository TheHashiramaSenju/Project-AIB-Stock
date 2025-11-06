# modified file: ai-stock-analyst-blockchain/streamlit_app/pages/2_💼_Portfolio.py

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# --- Path Setup ---
# Add parent directory (streamlit_app) to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    # Import the FINNHUB advisor (as requested)
    from stock_advisor_finnhub import StockAdvisorFinnhub
    # Import the portfolio manager (which uses the Finnhub advisor)
    from portfolio_manager import BlockchainPortfolioManagerEnhanced
    # Import the blockchain integration
    from blockchain_integration import BlockchainPortfolioManager
except ImportError:
    st.error(
        "**Import Error:** Could not find `stock_advisor_finnhub.py` or `portfolio_manager.py`."
        "Ensure they are in the `streamlit_app` root directory."
    )
    st.stop()

# --- Page Config ---
st.set_page_config(
    page_title="Portfolio Management",
    page_icon="💼",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Add rounded corners to metrics */
    .stMetric {
        background-color: #262730;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #444;
    }
    /* Style for remove button */
    .stButton>button {
        width: 100%;
    }
    .stButton>button[kind="secondary"] {
        border: 1px solid #ff4b4b;
        color: #ff4b4b;
    }
    .stButton>button[kind="secondary"]:hover {
        border: 1px solid #ff4b4b;
        color: #ff4b4b;
        background-color: #332222;
    }
    .stButton>button[kind="secondary"]:focus {
        border: 1px solid #ff4b4b !important;
        color: #ff4b4b !important;
        background-color: #332222 !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
def init_session_state():
    """Initialize all session state variables"""
    
    # Get Finnhub API key from secrets
    if 'finnhub_key' not in st.session_state:
        st.session_state.finnhub_key = st.secrets.get("FINNHUB_API_KEY", "d415bmpr01qo6qdf06d0d415bmpr01qo6qdf06dg")
    
    # Initialize StockAdvisorFinnhub 
    if 'advisor' not in st.session_state:
        st.session_state.advisor = StockAdvisorFinnhub(st.session_state.finnhub_key)
    
    # Initialize portfolio manager (which now uses the Finnhub advisor)
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = BlockchainPortfolioManagerEnhanced(
            blockchain_enabled=True
        )
        # CRITICAL: Set the portfolio manager to use the FINNHUB advisor
        st.session_state.portfolio_manager.set_stock_advisor(st.session_state.advisor)
    
    # Wallet connection status
    if 'wallet_connected' not in st.session_state:
        st.session_state.wallet_connected = False
    
    # Blockchain configuration
    if 'contract_address' not in st.session_state:
        st.session_state.contract_address = st.secrets.get("CONTRACT_ADDRESS", "")
    
    if 'rpc_url' not in st.session_state:
        st.session_state.rpc_url = st.secrets.get("RPC_URL", "")
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "streamlit_user"

# Call initialization
init_session_state()

# --- Helper Function for Visualization ---
#
# ✅ --- FIX 1 (Definition) ---
# Renamed `advisor` to `_advisor` to fix the `UnhashableParamError`.
# The leading underscore tells Streamlit's caching to ignore this argument.
#
@st.cache_data(ttl=300) # Cache charts for 5 minutes
def generate_portfolio_charts(portfolio_data, _advisor):
    """
    Generates Plotly charts for portfolio visualization.
    """
    if not portfolio_data:
        return None, None, None

    symbols = []
    sectors = []
    current_values = []
    invested_values = []

    # Prepare data for charts
    for inv in portfolio_data:
        # Use `_advisor` internally now
        symbol = _advisor.smart_symbol_lookup(inv['company'])
        current_price = _advisor.get_current_price(symbol)
        
        if current_price == 0:
            current_price = inv['purchase_price']  # Fallback
            
        invested = inv['shares'] * inv['purchase_price']
        current = inv['shares'] * current_price
        
        # Get sector (best-effort)
        try:
            # Use `_advisor` internally now
            profile = _advisor.get_company_profile(symbol)
            sector = profile.get('finnhubIndustry', 'Other')
            if not sector or sector == "":
                sector = "Other"
        except Exception:
            sector = 'Other'

        symbols.append(symbol)
        sectors.append(sector)
        current_values.append(current)
        invested_values.append(invested)

    # 1. Allocation by Stock (Pie Chart)
    pie_stock_fig = px.pie(
        names=symbols, 
        values=current_values, 
        title="<b>Allocation by Stock (Current Value)</b>",
        hole=0.3
    )
    pie_stock_fig.update_traces(textposition='inside', textinfo='percent+label')
    pie_stock_fig.update_layout(showlegend=False)

    # 2. Allocation by Sector (Pie Chart)
    sector_df = pd.DataFrame({'sector': sectors, 'value': current_values})
    sector_summary = sector_df.groupby('sector')['value'].sum().reset_index()
    
    pie_sector_fig = px.pie(
        sector_summary,
        names='sector', 
        values='value', 
        title="<b>Allocation by Sector (Current Value)</b>",
        hole=0.3
    )
    pie_sector_fig.update_traces(textposition='inside', textinfo='percent+label')
    pie_sector_fig.update_layout(showlegend=False)

    # 3. Invested vs Current (Bar Chart)
    bar_df_invested = pd.DataFrame({'symbol': symbols, 'value': invested_values, 'type': 'Invested'})
    bar_df_current = pd.DataFrame({'symbol': symbols, 'value': current_values, 'type': 'Current Value'})
    bar_df = pd.concat([bar_df_invested, bar_df_current])
    
    bar_fig = px.bar(
        bar_df, 
        x='symbol', 
        y='value', 
        color='type', 
        barmode='group',
        title="<b>Invested Value vs. Current Value</b>",
        labels={'value': 'Amount ($)', 'symbol': 'Stock', 'type': 'Metric'}
    )
    
    return pie_stock_fig, pie_sector_fig, bar_fig

# --- PAGE UI ---

# Header
st.title("💼 Portfolio Management")
st.markdown("Track your investments with real-time valuations and immutable blockchain storage.")

st.divider()

# Check wallet connection
if not st.session_state.wallet_connected:
    st.warning("⚠️ **Wallet not connected!** Connect your wallet in the **'🏠 Home'** page sidebar to add investments to blockchain.")
    st.info("💡 You can still add investments 'Locally' (for this session only) to test portfolio features.")

# --- 1. Add Investment Section ---
st.subheader("➕ Add New Investment")
st.markdown("Manually add a single investment to your portfolio.")

with st.expander("📝 Add Investment Form", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        company = st.text_input(
            "Company Name or Symbol",
            placeholder="e.g., AAPL, Microsoft",
            help="Enter company name or symbol (Finnhub advisor will look it up)"
        )
        shares = st.number_input(
            "Number of Shares",
            min_value=0.0001,
            value=10.0,
            step=0.01,
            format="%.4f",
            help="Number of shares purchased (supports fractions)"
        )
    
    with col2:
        price = st.number_input(
            "Purchase Price per Share ($)",
            min_value=0.01,
            value=175.50,
            step=0.01,
            help="Price per share at time of purchase"
        )
        date = st.date_input(
            "Purchase Date",
            value=datetime.now(),
            help="Date when investment was made"
        )
    
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
    
    with btn_col1:
        add_local_btn = st.button(
            "💾 Add Locally",
            type="secondary",
            use_container_width=True,
            help="Save to local session (temporary, lost on refresh)"
        )
    
    with btn_col2:
        add_blockchain_btn = st.button(
            "🔗 Add to Blockchain",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.wallet_connected,
            help="Save permanently on Ethereum blockchain (requires wallet connection)"
        )
    
    # Handle local addition
    if add_local_btn:
        if company and shares > 0 and price > 0:
            with st.spinner("Adding to local portfolio..."):
                try:
                    result = st.session_state.portfolio_manager.add_investment(
                        st.session_state.user_id,
                        company,
                        float(shares),
                        float(price),
                        date.strftime("%Y-%m-%d")
                    )
                    st.success(f"✅ {result}")
                    st.rerun() # Rerun to update portfolio
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.error("❌ Please fill all fields with valid values")
    
    #
    # ✅ --- FIX 2 ---
    # This block now correctly handles the *string* response from
    # `add_investment_blockchain`, fixing the "too many values to unpack" error.
    #
    if add_blockchain_btn:
        if company and shares > 0 and price > 0:
            with st.spinner(f"Adding {company} to blockchain... This may take 10-30 seconds"):
                try:
                    # Call the function from portfolio_manager
                    result_str = st.session_state.portfolio_manager.add_investment_blockchain(
                        st.session_state.user_id,
                        company,
                        float(shares),
                        float(price),
                        date.strftime("%Y-%m-%d")
                    )
                    
                    # Check the string response for success
                    if "Transaction Hash" in result_str:
                        st.success("✅ Investment added to blockchain!")
                        st.markdown(result_str) # Show the full success message
                        st.rerun()
                    else:
                        # Show the error message if it's not a success
                        st.error(f"❌ Blockchain transaction failed: {result_str}")
                        
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred: {str(e)}")
        else:
            st.error("❌ Please fill all fields with valid values")

st.divider()

# --- 2. Portfolio Overview Section ---
st.subheader("📊 Portfolio Overview")

# Get portfolio data using existing methods
portfolio = st.session_state.portfolio_manager.get_portfolio(st.session_state.user_id)

if not portfolio:
    st.info("📭 Your portfolio is empty. Add your first investment above or use the 'AI Budgeting' page!")
    
    # Sync from blockchain option if portfolio is empty
    if st.session_state.wallet_connected:
        st.markdown("---")
        if st.button("🔄 Sync from Blockchain", help="Try to load existing investments from the blockchain"):
            with st.spinner("Syncing from blockchain..."):
                try:
                    result = st.session_state.portfolio_manager.sync_from_blockchain(
                        st.session_state.user_id
                    )
                    st.success(result if isinstance(result, str) else "✅ Synced from blockchain")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Sync failed: {str(e)}")

else:
    # Calculate stats using existing method
    stats = st.session_state.portfolio_manager.calculate_portfolio_value(
        st.session_state.user_id,
        st.session_state.advisor
    )
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Invested",
            value=f"${stats['total_invested']:,.2f}",
            help="Total cost basis of all your active holdings"
        )
    
    with col2:
        st.metric(
            label="📈 Current Value",
            value=f"${stats['current_value']:,.2f}",
            help="Current market value of all your holdings"
        )
    
    with col3:
        st.metric(
            label="💵 Total Gain/Loss",
            value=f"${stats['gain_loss']:,.2f}",
            delta=f"{stats['gain_loss_pct']:+.2f}%",
            delta_color="normal",
            help="Total profit or loss across all holdings"
        )
    
    with col4:
        st.metric(
            label="📦 Holdings",
            value=len(portfolio),
            help="Number of unique assets in your portfolio"
        )

    # --- 3. Portfolio Visualization Section ---
    st.markdown("---")
    st.subheader("🎨 Portfolio Visualization")
    
    with st.spinner("Generating portfolio charts..."):
        #
        # ✅ --- FIX 1 (Call) ---
        # Pass the advisor object using the `_advisor=` kwarg.
        # This tells Streamlit to ignore this unhashable argument.
        #
        pie_stock_fig, pie_sector_fig, bar_fig = generate_portfolio_charts(
            portfolio, 
            _advisor=st.session_state.advisor
        )
    
    if pie_stock_fig:
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            st.plotly_chart(pie_stock_fig, use_container_width=True)
        with viz_col2:
            st.plotly_chart(pie_sector_fig, use_container_width=True)
        
        st.plotly_chart(bar_fig, use_container_width=True)
    else:
        st.info("Could not generate portfolio charts. Data might be processing.")


    # --- 4. Detailed Holdings Section (Interactive List) ---
    st.markdown("---")
    st.subheader("📋 Detailed Holdings & Management")
    
    # Add a refresh button
    if st.button("🔄 Refresh Portfolio Values", use_container_width=True):
        st.rerun()

    # Display Header Row
    header_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
    header_cols[0].markdown("**Stock**")
    header_cols[1].markdown("**Shares**")
    header_cols[2].markdown("**Buy Price**")
    header_cols[3].markdown("**Current Price**")
    header_cols[4].markdown("**Invested**")
    header_cols[5].markdown("**Current Value**")
    header_cols[6].markdown("**G/L (%)**")
    header_cols[7].markdown("**Actions**")
    st.markdown("<hr style='margin-top:0; margin-bottom:1rem;'>", unsafe_allow_html=True)

    # Loop through each holding and display interactively
    for idx, inv in enumerate(portfolio):
        try:
            # Get current price using existing method
            symbol = st.session_state.advisor.smart_symbol_lookup(inv['company'])
            current_price = st.session_state.advisor.get_current_price(symbol)
            
            if current_price == 0:
                current_price = inv['purchase_price']  # Fallback
            
            invested = inv['shares'] * inv['purchase_price']
            current_value = inv['shares'] * current_price
            gain_loss = current_value - invested
            gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0
            
            # Check if blockchain verified
            blockchain_badge = "🔗" if inv.get('blockchain_id') else "💾"
            
            # Create columns for this row
            row_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
            
            # Column 1: Stock
            row_cols[0].markdown(f"**{symbol}** {blockchain_badge}")
            row_cols[0].caption(f"{inv['company'].title()} | {inv['purchase_date']}")
            
            # Column 2: Shares
            row_cols[1].text(f"{inv['shares']:.4f}")
            
            # Column 3: Buy Price
            row_cols[2].text(f"${inv['purchase_price']:.2f}")
            
            # Column 4: Current Price
            price_color = "green" if current_price >= inv['purchase_price'] else "red"
            row_cols[3].markdown(f"<span style='color:{price_color};'>${current_price:.2f}</span>", unsafe_allow_html=True)
            
            # Column 5: Invested
            row_cols[4].text(f"${invested:,.2f}")
            
            # Column 6: Current Value
            row_cols[5].text(f"${current_value:,.2f}")
            
            # Column 7: Gain/Loss
            gl_color = "green" if gain_loss >= 0 else "red"
            row_cols[6].markdown(f"<span style='color:{gl_color};'>${gain_loss:,.2f}</span>", unsafe_allow_html=True)
            row_cols[6].markdown(f"<span style='color:{gl_color};'>({gain_loss_pct:+.2f}%)</span>", unsafe_allow_html=True)

            # Column 8: Actions (NEW REMOVE BUTTON)
            with row_cols[7]:
                if st.button("🗑️ Remove", key=f"remove_{inv['investment_id']}", type="secondary"):
                    with st.spinner(f"Removing {symbol}..."):
                        
                        removed_from_bc = False
                        if inv.get('blockchain_id') and st.session_state.wallet_connected:
                            st.info(f"Sending blockchain transaction to remove {symbol}...")
                            tx_hash = st.session_state.portfolio_manager.blockchain.remove_investment_from_blockchain(
                                inv['blockchain_id']
                            )
                            if tx_hash:
                                st.success(f"Removed from blockchain (TX: {tx_hash[:10]}...)")
                                removed_from_bc = True
                            else:
                                st.error("Blockchain removal failed. Check wallet/funds.")
                        elif inv.get('blockchain_id'):
                            st.warning("Wallet not connected. Cannot remove from blockchain. Removing locally only.")
                        
                        # Remove from local session
                        local_remove_msg = st.session_state.portfolio_manager.remove_investment(
                            st.session_state.user_id, 
                            inv['investment_id']
                        )
                        st.success(f"Removed {symbol} from local session.")
                        st.rerun()

            st.markdown("<hr style='margin-top:0.5rem; margin-bottom:0.5rem; border-color:#333;'>", unsafe_allow_html=True)

        except Exception as e:
            st.warning(f"⚠️ Error processing holding {inv.get('company', 'N/A')}: {str(e)}")
            continue

    # Sync from blockchain option
    if st.session_state.wallet_connected:
        st.divider()
        st.subheader("⛓️ Blockchain Synchronization")
        if st.button("🔄 Sync All from Blockchain", help="Overwrite local portfolio with all active investments from the blockchain"):
            with st.spinner("Syncing from blockchain... This may take a moment."):
                try:
                    result = st.session_state.portfolio_manager.sync_from_blockchain(
                        st.session_state.user_id
                    )
                    st.success(result if isinstance(result, str) else "✅ Synced from blockchain")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Sync failed: {str(e)}")

st.divider()

# --- 5. Portfolio Tips ---
with st.expander("💡 Portfolio Management Tips & Info"):
    st.markdown("""
    **Local (💾) vs. Blockchain (🔗) Storage:**
    - **Local Storage (💾)**: 
      - Stored in your browser's session.
      - **Lost when you close or refresh the browser tab.**
      - Instant and costs no gas fees.
      - Good for temporary testing or "what-if" scenarios.
    
    - **Blockchain Storage (🔗)**:
      - Permanently and immutably stored on the Ethereum Sepolia testnet.
      - Accessible from any device or browser by reconnecting your wallet.
      - Requires a small testnet gas fee for each transaction (add/remove).
      - This is your permanent, verifiable record of ownership.
    
    **Best Practices:**
    - Use **"Add to Blockchain"** for any investments you want to track permanently.
    - Use the **"AI Budgeting"** page to create a plan and save it directly to the blockchain.
    - Use **"Sync All from Blockchain"** if your local session seems out of date.
    - **Removing (🗑️)** a blockchain-linked asset sends a *new transaction* to mark it as 'inactive' in the smart contract. It also removes it from your local view.
    
    **Understanding Metrics:**
    - **Total Invested**: The sum of all your purchase costs (`Shares * Buy Price`). This is your "cost basis".
    - **Current Value**: The real-time market value of all your holdings (`Shares * Current Price`).
    - **Total Gain/Loss**: The difference between *Current Value* and *Total Invested*.
    - **G/L (%)**: Your total percentage return on investment.
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p>💼 Portfolio powered by your investments | 🔗 Secured by Ethereum blockchain | 📈 Data by Finnhub</p>
</div>
""", unsafe_allow_html=True)