

"""
AI Budgeting Engine
===================
This file contains the core "brain" for the AI Budgeting feature.
It takes a list of pre-analyzed stock candidates (from Finnhub),
a user's budget, and a risk profile, then generates a
complete, weighted, and costed investment plan.

This logic is intentionally kept separate from the Streamlit UI
for clarity and testability.

Author: Bhoomika M
Date: 2025-10-29
"""

from typing import List, Dict, Tuple, Optional, Any
import math

class AIBudgeter:
    """
    Encapsulates all logic for generating an AI-driven investment plan.
    This class implements the rule-based logic for different risk profiles.
    """

    def __init__(self):
        """
        Initializes the AI Budgeter with predefined risk profile configurations.
        These configurations are the "AI" rules that drive the portfolio selection.
        """
        
        # This dictionary defines the core rules for each risk profile.
        # It is exhaustive and directly implements the user's request.
        self.RISK_PROFILES: Dict[str, Dict[str, Any]] = {
            'Conservative': {
                'num_stocks': (5, 7),  # Target 5, max 7 stocks for broad diversification
                'allowed_sectors': [
                    'Technology', 
                    'Healthcare', 
                    'Financial', 
                    'Consumer Defensive', 
                    'Energy', 
                    'Utilities'
                ],
                'min_buy_score': 10,   # Minimum analyst "Buy" + "Strong Buy" count
                'allocation_strategy': 'equal' # Diversified
            },
            'Moderate': {
                'num_stocks': (3, 5),  # Target 3, max 5 stocks for a balanced mix
                'allowed_sectors': [
                    'Technology', 
                    'Consumer Cyclical', 
                    'Healthcare', 
                    'Financial',
                    'Communication Services'
                ],
                'min_buy_score': 15,   # Requires a stronger analyst conviction
                'allocation_strategy': 'equal' # Balanced
            },
            'Aggressive': {
                'num_stocks': (2, 3),  # Target 2, max 3 stocks for concentrated bets
                'allowed_sectors': [
                    'Technology', 
                    'Consumer Cyclical' # Focus on high-growth sectors
                ],
                'min_buy_score': 20,   # Must have very high analyst conviction
                'allocation_strategy': 'weighted' # Concentrated in top picks
            }
        }

    def _filter_candidates(self, 
                           stock_candidates: List[Dict], 
                           config: Dict[str, Any]) -> List[Dict]:
        """
        Private helper to filter the master list of candidates based on
        the selected risk profile's configuration.
        
        Args:
            stock_candidates: The full list of stocks from StockAdvisorFinnhub.
            config: The specific risk profile dictionary (e.g., self.RISK_PROFILES['Conservative']).

        Returns:
            A filtered list of stock candidates.
        """
        filtered_stocks = []
        for stock in stock_candidates:
            # 1. Check Sector
            if stock.get('sector') not in config['allowed_sectors']:
                continue
                
            # 2. Check Analyst Buy Score
            if stock.get('buy_score', 0) < config['min_buy_score']:
                continue
                
            # 3. Check for valid upside and price
            if stock.get('upside_pct', 0) <= 0 or stock.get('current_price', 0) <= 0:
                continue
                
            # If it passes all filters, add it to the list
            filtered_stocks.append(stock)
            
        return filtered_stocks

    def _rank_candidates(self, filtered_stocks: List[Dict]) -> List[Dict]:
        """
        Ranks the filtered list of stocks.
        The ranking is a weighted score of analyst conviction (buy_score)
        and predicted upside (upside_pct) to find the best opportunities.
        
        Args:
            filtered_stocks: The list of stocks that passed the filter.

        Returns:
            A sorted list of stocks, best-to-worst.
        """
        
        # This score is the "secret sauce" of the AI, balancing conviction
        # with raw upside potential.
        def calculate_weighted_score(stock):
            # 40% weight to analyst conviction, 60% weight to predicted upside
            conviction_score = stock.get('buy_score', 0)
            upside_score = stock.get('upside_pct', 0)
            return (conviction_score * 0.4) + (upside_score * 0.6)

        # Sort the list in descending order by our new weighted score
        filtered_stocks.sort(key=calculate_weighted_score, reverse=True)
        return filtered_stocks

    def _allocate_budget(self, 
                         budget: float, 
                         risk_profile: str, 
                         selected_stocks: List[Dict]) -> List[Dict]:
        """
        Performs the final budget allocation and share calculation.
        This function implements the "Aggressive" weighted logic
        and the "Conservative/Moderate" equal-weight logic.
        
        Args:
            budget: The total budget.
            risk_profile: The user's chosen profile string.
            selected_stocks: The final, sorted list of stocks to invest in.

        Returns:
            A list of plan items with exact cost and share counts.
        """
        num_stocks = len(selected_stocks)
        if num_stocks == 0:
            return [] # Should not happen, but a robust check

        allocation_strategy = self.RISK_PROFILES[risk_profile]['allocation_strategy']
        weights = []

        # 1. Determine allocation weights based on strategy
        if allocation_strategy == 'weighted' and risk_profile == 'Aggressive':
            # As requested: "concentrate" the budget
            if num_stocks == 2:
                weights = [0.60, 0.40]  # 60% to the #1 pick
            elif num_stocks == 3:
                weights = [0.50, 0.30, 0.20] # 50% to the #1 pick
            else:
                # Fallback for aggressive if only 1 stock is found
                weights = [1.0]
        else:
            # 'equal' strategy for Conservative and Moderate
            weights = [1.0 / num_stocks] * num_stocks

        # 2. Calculate allocation, shares, and cost for each stock
        final_plan = []
        total_cost_calculated = 0.0
        
        for i, stock in enumerate(selected_stocks):
            allocated_amount = budget * weights[i]
            current_price = stock['current_price']
            
            # Robust check for zero price
            if current_price <= 0:
                shares_to_buy = 0.0
                cost = 0.0
            else:
                # Calculate exact shares
                shares_to_buy = allocated_amount / current_price
                cost = shares_to_buy * current_price # This will equal allocated_amount
            
            total_cost_calculated += cost

            plan_item = {
                'symbol': stock['symbol'],
                'company_name': stock.get('name', stock['symbol']), # Get name if available
                'sector': stock['sector'],
                'shares': shares_to_buy,
                'current_price': current_price,
                'cost': cost,
                'allocation_pct': weights[i] * 100,
                'target_mean': stock['targetMean'],
                'upside_pct': stock['upside_pct'],
                'buy_score': stock['buy_score']
            }
            final_plan.append(plan_item)
            
        # 3. Handle any leftover "dust" (small change)
        # This ensures 100% of the budget is used
        leftover_budget = budget - total_cost_calculated
        
        if leftover_budget > 0.01 and final_plan: # If more than 1 cent left
            # Add the leftover dust to the #1 pick (highest conviction)
            top_pick = final_plan[0]
            if top_pick['current_price'] > 0:
                extra_shares = leftover_budget / top_pick['current_price']
                top_pick['shares'] += extra_shares
                top_pick['cost'] += leftover_budget
                
                # Recalculate allocation percentage for the top pick
                total_cost_final = sum(item['cost'] for item in final_plan)
                for item in final_plan:
                    item['allocation_pct'] = (item['cost'] / total_cost_final) * 100
        
        return final_plan

    # --- PUBLIC FUNCTION ---

    def generate_investment_plan(self, 
                                 budget: float, 
                                 risk_profile: str, 
                                 stock_candidates: List[Dict]
                                 ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Generates a complete, AI-driven investment plan.
        This is the main public entry point for this class.

        Args:
            budget: Total amount (e.g., 1000.0) to invest.
            risk_profile: 'Conservative', 'Moderate', or 'Aggressive'.
            stock_candidates: The list of analyzed stocks from StockAdvisorFinnhub.

        Returns:
            A tuple containing:
            1. The final plan (List[Dict]) or None if it fails.
            2. An error message (str) or None if it succeeds.
        """
        
        # 1. --- Validation (Robustness) ---
        print(f"AI Budgeter: Generating plan for ${budget} ({risk_profile})")
        if not stock_candidates:
            print("AI Budgeter Error: Stock candidate list is empty.")
            return None, "The AI stock analysis pool is empty. No stocks could be analyzed from Finnhub."
            
        if risk_profile not in self.RISK_PROFILES:
            print(f"AI Budgeter Error: Invalid risk profile '{risk_profile}'")
            return None, f"Invalid risk profile '{risk_profile}' selected."
            
        if budget < 50.0:
            print(f"AI Budgeter Error: Budget ${budget} is too small.")
            return None, "Budget must be at least $50.00 to generate a diversified plan."

        config = self.RISK_PROFILES[risk_profile]

        # 2. --- Filtering (The "AI" part 1) ---
        print(f"AI Budgeter: Filtering {len(stock_candidates)} candidates for '{risk_profile}' profile...")
        filtered_stocks = self._filter_candidates(stock_candidates, config)
        
        if not filtered_stocks:
            print("AI Budgeter Error: No stocks passed the filtering criteria.")
            return None, (f"No stocks matched the strict criteria for a '{risk_profile}' profile "
                          f"(Sectors: {', '.join(config['allowed_sectors'])}, "
                          f"Min Buy Score: {config['min_buy_score']}). "
                          f"Try a different risk profile (e.g., 'Moderate').")

        # 3. --- Ranking ---
        print(f"AI Budgeter: Ranking {len(filtered_stocks)} filtered stocks...")
        ranked_stocks = self._rank_candidates(filtered_stocks)

        # 4. --- Selection ---
        num_to_select = config['num_stocks'][0] # Target the lower bound of the tuple (e.g., 5 for Conservative)
        selected_stocks = ranked_stocks[:num_to_select]
        
        if len(selected_stocks) == 0:
             print("AI Budgeter Error: No stocks were selected after ranking.")
             return None, "An internal error occurred, and no stocks were selected for the plan."
             
        print(f"AI Budgeter: Selected top {len(selected_stocks)} stocks: {[s['symbol'] for s in selected_stocks]}")

        # 5. --- Allocation (The "AI" part 2) ---
        print(f"AI Budgeter: Allocating ${budget} across selected stocks...")
        final_plan = self._allocate_budget(budget, risk_profile, selected_stocks)
        
        if not final_plan:
             print("AI Budgeter Error: Budget allocation failed.")
             return None, "An internal error occurred during budget allocation."
        
        print(f"AI Budgeter: Plan generation complete. Returning {len(final_plan)} items.")
        
        # 6. --- Success ---
        return final_plan, None