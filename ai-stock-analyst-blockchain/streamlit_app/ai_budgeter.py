"""
AI Budgeting Engine - Alpha Vantage Version (FIXED)
===================================================
Uses technical analysis instead of analyst ratings.
Robust with better scoring thresholds.

Author: Bhoomika M
Date: 2025-11-08
Version: 2.1 (Fixed Scoring)
"""

from typing import List, Dict, Tuple, Optional, Any
import math


class AIBudgeter:
    """
    AI-driven investment plan generator using technical indicators.
    
    Features:
    - Multiple risk profiles (Conservative, Moderate, Aggressive)
    - Technical scoring system (0-100 scale)
    - Sector-based diversification
    - Dynamic budget allocation with leftover handling
    - Comprehensive error handling and validation
    - Flexible scoring thresholds to ensure plan generation
    """

    def __init__(self):
        """
        Initialize the AI Budgeter with risk profile configurations.
        """
        
        # Risk profile configurations based on portfolio optimization principles
        self.RISK_PROFILES: Dict[str, Dict[str, Any]] = {
            'Conservative': {
                'num_stocks': (5, 7),  # Target range for diversification
                'allowed_sectors': [
                    'Technology', 
                    'Healthcare', 
                    'Financial', 
                    'Consumer Defensive', 
                    'Energy', 
                    'Utilities',
                    'Real Estate'
                ],
                'min_technical_score': 50,  # LOWERED from 60 - more lenient
                'allocation_strategy': 'equal',  # Equal weighting for safety
                'max_single_allocation': 0.25,  # Max 25% in any single stock
                'description': 'Broad diversification with stable sectors'
            },
            'Moderate': {
                'num_stocks': (3, 5),
                'allowed_sectors': [
                    'Technology', 
                    'Consumer Cyclical', 
                    'Healthcare', 
                    'Financial',
                    'Communication Services',
                    'Industrials',
                    'Consumer Defensive'  # ADDED
                ],
                'min_technical_score': 50,  # LOWERED from 70 - more lenient
                'allocation_strategy': 'equal',
                'max_single_allocation': 0.35,  # Max 35% in any single stock
                'description': 'Balanced growth and stability'
            },
            'Aggressive': {
                'num_stocks': (2, 3),
                'allowed_sectors': [
                    'Technology', 
                    'Consumer Cyclical',
                    'Communication Services'
                ],
                'min_technical_score': 60,  # LOWERED from 80 - more lenient
                'allocation_strategy': 'weighted',  # Weighted towards top picks
                'max_single_allocation': 0.50,  # Max 50% in any single stock
                'description': 'Concentrated bets on high-conviction stocks'
            }
        }
        
        # Technical indicator weights for scoring
        self.INDICATOR_WEIGHTS = {
            'rsi': 0.30,      # 30% weight
            'macd': 0.30,     # 30% weight
            'trend': 0.20,    # 20% weight
            'momentum': 0.20  # 20% weight (price change)
        }
        
        # Logging
        self.verbose = True
    
    def set_verbose(self, verbose: bool):
        """Enable or disable verbose logging."""
        self.verbose = verbose
    
    def _log(self, message: str):
        """Internal logging function."""
        if self.verbose:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] AI Budgeter: {message}")
    
    def _calculate_technical_score(self, stock: Dict) -> float:
        """
        Calculate a 0-100 technical score based on multiple indicators.
        
        IMPROVED: More balanced scoring to ensure plans can be generated.
        
        Scoring breakdown:
        - RSI (35 points max) - Measures momentum
        - MACD (35 points max) - Shows momentum signals
        - Trend (20 points max) - Direction analysis
        - Momentum (10 points max) - Price change
        
        Args:
            stock: Dict containing technical indicator data
            
        Returns:
            Technical score between 0 and 100
        """
        score = 0.0
        
        # RSI scoring (35 points max - increased from 30)
        rsi = stock.get('rsi')
        if rsi is not None:
            try:
                rsi_value = float(rsi)
                # More lenient RSI scoring
                if rsi_value < 20:  # Very oversold
                    score += 35
                elif rsi_value < 30:  # Oversold
                    score += 33
                elif rsi_value < 40:  # Slightly oversold
                    score += 28
                elif rsi_value < 60:  # Neutral zone (favorable)
                    score += 25
                elif rsi_value < 70:  # Slightly overbought
                    score += 20
                elif rsi_value < 80:  # Overbought
                    score += 10
                # >80 extremely overbought gets minimal points
            except (ValueError, TypeError):
                self._log(f"Warning: Invalid RSI value: {rsi}")
                score += 15  # Default mid-range score
        else:
            score += 15  # Default if no RSI data
        
        # MACD scoring (35 points max - increased from 30)
        macd = stock.get('macd_signal')
        if macd:
            macd_str = str(macd).upper()
            if macd_str == 'BUY':
                score += 35  # Strong buy signal
            elif macd_str == 'HOLD':
                score += 20  # Neutral hold
            elif macd_str == 'SELL':
                score += 5   # Weak sell signal (still some value)
            else:
                score += 17  # Default mid-range
        else:
            score += 17  # Default if no MACD data
        
        # Trend scoring (20 points max)
        trend = stock.get('trend')
        if trend:
            trend_str = str(trend).upper()
            if trend_str == 'BULLISH':
                score += 20
            elif trend_str == 'NEUTRAL':
                score += 10
            elif trend_str == 'BEARISH':
                score += 2   # Even bearish trends have some value
            else:
                score += 10  # Default
        else:
            score += 10  # Default if no trend data
        
        # Price momentum scoring (10 points max - changed from 20)
        change_pct = stock.get('change_percent', 0)
        try:
            change_value = float(str(change_pct).replace('%', ''))
            if change_value > 3:
                score += 10
            elif change_value > 0:
                score += 6
            elif change_value > -3:
                score += 3
            # Negative changes get minimal points
        except (ValueError, TypeError):
            self._log(f"Warning: Invalid change_percent: {change_pct}")
            score += 5  # Default mid-range
        
        # Cap score at 100
        score = min(score, 100.0)
        return round(score, 2)
    
    def _filter_candidates(self, stock_candidates: List[Dict], 
                          config: Dict[str, Any]) -> List[Dict]:
        """
        Filter stocks by sector, technical score, and data validity.
        
        IMPROVED: More lenient filtering to ensure candidates pass through.
        
        Args:
            stock_candidates: List of stock dictionaries with technical data
            config: Risk profile configuration
            
        Returns:
            Filtered list of stocks that meet criteria
        """
        filtered_stocks = []
        
        for stock in stock_candidates:
            symbol = stock.get('symbol', 'UNKNOWN')
            
            # 1. Check for required fields
            if not stock.get('sector'):
                self._log(f"Skipping {symbol}: Missing sector information")
                continue
            
            # 2. Check sector eligibility
            if stock['sector'] not in config['allowed_sectors']:
                self._log(f"Skipping {symbol}: Sector '{stock['sector']}' not in allowed list for this profile")
                continue
            
            # 3. Calculate technical score
            technical_score = self._calculate_technical_score(stock)
            stock['technical_score'] = technical_score
            
            # 4. Check minimum technical score threshold (LENIENT)
            if technical_score < config['min_technical_score']:
                self._log(f"Skipping {symbol}: Technical score {technical_score} below minimum {config['min_technical_score']}")
                continue
            
            # 5. Validate price data
            price = stock.get('price', 0)
            try:
                price = float(price)
                if price <= 0:
                    self._log(f"Skipping {symbol}: Invalid price {price}")
                    continue
                stock['price'] = price  # Ensure it's a float
            except (ValueError, TypeError):
                self._log(f"Skipping {symbol}: Cannot parse price {price}")
                continue
            
            # 6. Calculate estimated 12-month target price
            # More generous upside calculation for scoring
            score_factor = technical_score / 100.0  # Normalize to 0-1
            estimated_target = price * (1 + (score_factor * 0.50))  # Up to 50% upside (increased from 30%)
            
            stock['target_mean'] = round(estimated_target, 2)
            stock['upside_pct'] = round(((estimated_target - price) / price) * 100, 2)
            stock['buy_score'] = technical_score
            
            filtered_stocks.append(stock)
            self._log(f"✓ {symbol}: Score={technical_score:.1f}, Price=${price:.2f}, Upside={stock['upside_pct']:.1f}%")
        
        return filtered_stocks
    
    def _rank_candidates(self, filtered_stocks: List[Dict]) -> List[Dict]:
        """
        Rank stocks by weighted combination of technical score and upside potential.
        
        Ranking formula: (Technical Score × 0.7) + (Upside % × 0.3)
        
        Args:
            filtered_stocks: List of filtered stocks
            
        Returns:
            Sorted list of stocks (best to worst)
        """
        def calculate_weighted_score(stock):
            technical = stock.get('technical_score', 0)
            upside = stock.get('upside_pct', 0)
            # Weight technical score more heavily
            return (technical * 0.7) + (upside * 0.3)
        
        filtered_stocks.sort(key=calculate_weighted_score, reverse=True)
        
        # Log top rankings
        self._log("Top ranked stocks:")
        for i, stock in enumerate(filtered_stocks[:5], 1):
            score = calculate_weighted_score(stock)
            self._log(f"  {i}. {stock['symbol']}: Weighted Score={score:.2f}")
        
        return filtered_stocks
    
    def _allocate_budget(self, budget: float, risk_profile: str, 
                         selected_stocks: List[Dict]) -> List[Dict]:
        """
        Allocate budget across selected stocks based on strategy.
        
        Strategies:
        - Equal: Divide budget equally (Conservative, Moderate)
        - Weighted: Concentrate in top picks (Aggressive)
        
        Args:
            budget: Total investment amount
            risk_profile: Selected risk profile
            selected_stocks: Stocks to invest in
            
        Returns:
            List of investment plan items with shares and costs
        """
        num_stocks = len(selected_stocks)
        if num_stocks == 0:
            return []
        
        config = self.RISK_PROFILES[risk_profile]
        allocation_strategy = config['allocation_strategy']
        max_single = config['max_single_allocation']
        
        weights = []
        
        # Determine allocation weights based on strategy
        if allocation_strategy == 'weighted' and risk_profile == 'Aggressive':
            # Weighted allocation for aggressive profile
            if num_stocks == 1:
                weights = [1.0]
            elif num_stocks == 2:
                weights = [0.60, 0.40]  # 60/40 split
            elif num_stocks == 3:
                weights = [0.50, 0.30, 0.20]  # 50/30/20 split
            else:
                # Fallback to equal if more stocks than expected
                weights = [1.0 / num_stocks] * num_stocks
        else:
            # Equal weight allocation (default for Conservative and Moderate)
            weights = [1.0 / num_stocks] * num_stocks
        
        # Enforce max single allocation constraint
        for i in range(len(weights)):
            if weights[i] > max_single:
                self._log(f"Warning: Weight {weights[i]:.1%} exceeds max {max_single:.1%}, capping")
                weights[i] = max_single
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Calculate allocations
        final_plan = []
        total_cost_calculated = 0.0
        
        for i, stock in enumerate(selected_stocks):
            allocated_amount = budget * weights[i]
            current_price = stock['price']
            
            if current_price <= 0:
                shares_to_buy = 0.0
                cost = 0.0
            else:
                shares_to_buy = allocated_amount / current_price
                cost = shares_to_buy * current_price
            
            total_cost_calculated += cost
            
            plan_item = {
                'symbol': stock['symbol'],
                'company_name': stock.get('name', stock['symbol']),
                'sector': stock['sector'],
                'shares': round(shares_to_buy, 6),  # 6 decimal places for fractional shares
                'current_price': current_price,
                'cost': round(cost, 2),
                'allocation_pct': round(weights[i] * 100, 2),
                'target_mean': stock['target_mean'],
                'upside_pct': stock['upside_pct'],
                'buy_score': stock['technical_score'],
                'rsi': stock.get('rsi'),
                'macd_signal': stock.get('macd_signal'),
                'trend': stock.get('trend')
            }
            final_plan.append(plan_item)
            
            self._log(f"Allocated ${cost:.2f} ({weights[i]*100:.1f}%) to {stock['symbol']} = {shares_to_buy:.4f} shares")
        
        # Handle leftover budget (dust)
        leftover_budget = budget - total_cost_calculated
        
        if leftover_budget > 0.01 and final_plan:
            self._log(f"Leftover budget: ${leftover_budget:.2f}, adding to top pick")
            top_pick = final_plan[0]
            
            if top_pick['current_price'] > 0:
                extra_shares = leftover_budget / top_pick['current_price']
                top_pick['shares'] = round(top_pick['shares'] + extra_shares, 6)
                top_pick['cost'] = round(top_pick['cost'] + leftover_budget, 2)
                
                # Recalculate allocation percentages
                total_cost_final = sum(item['cost'] for item in final_plan)
                for item in final_plan:
                    item['allocation_pct'] = round((item['cost'] / total_cost_final) * 100, 2)
        
        return final_plan
    
    def generate_investment_plan(self, budget: float, risk_profile: str, 
                                stock_candidates: List[Dict]
                                ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Main entry point: Generate a complete AI-driven investment plan.
        
        Process:
        1. Validate inputs
        2. Filter stocks by sector and technical criteria
        3. Rank stocks by weighted score
        4. Select top N stocks based on risk profile
        5. Allocate budget with proper weighting
        
        Args:
            budget: Total investment amount (minimum $50)
            risk_profile: 'Conservative', 'Moderate', or 'Aggressive'
            stock_candidates: List of stocks with technical analysis data
            
        Returns:
            Tuple of:
            - List of investment plan items (or None if failed)
            - Error message (or None if successful)
        """
        self._log(f"Starting plan generation for ${budget:.2f} ({risk_profile})")
        
        # ===== INPUT VALIDATION =====
        
        # Check stock candidates
        if not stock_candidates:
            error_msg = "No stock candidates provided for analysis. The market analysis returned empty."
            self._log(f"ERROR: {error_msg}")
            return None, error_msg
        
        # Check risk profile
        if risk_profile not in self.RISK_PROFILES:
            valid_profiles = ', '.join(self.RISK_PROFILES.keys())
            error_msg = f"Invalid risk profile '{risk_profile}'. Must be one of: {valid_profiles}"
            self._log(f"ERROR: {error_msg}")
            return None, error_msg
        
        # Check budget
        min_budget = 50.0
        if budget < min_budget:
            error_msg = f"Budget ${budget:.2f} is below minimum ${min_budget:.2f}. Please increase your budget."
            self._log(f"ERROR: {error_msg}")
            return None, error_msg
        
        if budget > 10_000_000:  # Sanity check
            self._log("WARNING: Budget exceeds $10M, this is unusual")
        
        config = self.RISK_PROFILES[risk_profile]
        
        # ===== FILTERING =====
        
        self._log(f"Filtering {len(stock_candidates)} candidates...")
        self._log(f"Criteria: Sectors={config['allowed_sectors']}, Min Score={config['min_technical_score']}")
        
        filtered_stocks = self._filter_candidates(stock_candidates, config)
        
        if not filtered_stocks:
            sectors_str = ', '.join(config['allowed_sectors'])
            error_msg = (
                f"No stocks passed the filtering criteria for '{risk_profile}' profile.\n"
                f"Criteria: Sectors [{sectors_str}], Min Technical Score {config['min_technical_score']}/100.\n"
                f"Suggestion: Try 'Conservative' profile or check if market conditions are suitable."
            )
            self._log(f"ERROR: {error_msg}")
            return None, error_msg
        
        self._log(f"✓ {len(filtered_stocks)} stocks passed filtering")
        
        # ===== RANKING =====
        
        self._log(f"Ranking stocks by weighted score...")
        ranked_stocks = self._rank_candidates(filtered_stocks)
        
        # ===== SELECTION =====
        
        num_to_select = config['num_stocks'][0]  # Target number (lower bound)
        max_to_select = config['num_stocks'][1]   # Maximum number (upper bound)
        
        # Select top N, but don't exceed what's available
        num_available = len(ranked_stocks)
        actual_select = min(num_to_select, num_available)
        
        if actual_select < num_to_select:
            self._log(f"WARNING: Only {actual_select} stocks available, target was {num_to_select}")
        
        selected_stocks = ranked_stocks[:actual_select]
        
        if len(selected_stocks) == 0:
            error_msg = "Internal error: No stocks were selected after ranking."
            self._log(f"ERROR: {error_msg}")
            return None, error_msg
        
        symbols = [s['symbol'] for s in selected_stocks]
        self._log(f"✓ Selected {len(selected_stocks)} stocks: {', '.join(symbols)}")
        
        # ===== ALLOCATION =====
        
        self._log(f"Allocating ${budget:.2f} using '{config['allocation_strategy']}' strategy...")
        final_plan = self._allocate_budget(budget, risk_profile, selected_stocks)
        
        if not final_plan:
            error_msg = "Internal error: Budget allocation failed."
            self._log(f"ERROR: {error_msg}")
            return None, error_msg
        
        # ===== SUCCESS =====
        
        total_allocated = sum(item['cost'] for item in final_plan)
        self._log(f"✅ Plan complete: {len(final_plan)} stocks, ${total_allocated:.2f} allocated")
        
        return final_plan, None
    
    def get_risk_profile_info(self, risk_profile: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a risk profile.
        
        Args:
            risk_profile: Profile name
            
        Returns:
            Configuration dict or None if invalid
        """
        return self.RISK_PROFILES.get(risk_profile)
    
    def list_risk_profiles(self) -> List[str]:
        """Get list of available risk profile names."""
        return list(self.RISK_PROFILES.keys())
