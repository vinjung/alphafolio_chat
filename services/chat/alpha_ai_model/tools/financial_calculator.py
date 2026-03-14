# services/chat/alpha_ai_model/tools/financial_calculator.py
"""
Financial Calculator for Alpha AI

Provides accurate financial calculations that LLM cannot reliably perform:
- Returns and growth rates (CAGR, total return)
- Risk metrics (volatility, Sharpe ratio, max drawdown)
- Statistical analysis (moving averages, momentum)
- Formatting utilities for currency and percentages
"""
from typing import List, Optional, Tuple, Union
import numpy as np
from config import logger


class FinancialCalculator:
    """
    Financial calculation utilities for stock analysis.

    All methods are static for easy use without instantiation.
    Handles edge cases and returns None for invalid inputs.
    """

    # =========================================================================
    # Return Calculations
    # =========================================================================

    @staticmethod
    def calculate_return(start_price: float, end_price: float) -> Optional[float]:
        """
        Calculate simple return percentage.

        Args:
            start_price: Starting price
            end_price: Ending price

        Returns:
            Return percentage (e.g., 10.5 for 10.5%), or None if invalid
        """
        if start_price is None or end_price is None:
            return None
        if start_price <= 0:
            logger.warning("[FinancialCalculator] Invalid start_price for return calculation")
            return None

        return ((end_price - start_price) / start_price) * 100

    @staticmethod
    def calculate_total_return(prices: List[float]) -> Optional[float]:
        """
        Calculate total return from a series of prices.

        Args:
            prices: List of prices (chronological order, oldest first)

        Returns:
            Total return percentage, or None if invalid
        """
        if not prices or len(prices) < 2:
            return None

        start_price = prices[0]
        end_price = prices[-1]

        return FinancialCalculator.calculate_return(start_price, end_price)

    @staticmethod
    def calculate_cagr(
        start_value: float,
        end_value: float,
        years: float
    ) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate (CAGR).

        Args:
            start_value: Starting value
            end_value: Ending value
            years: Number of years (can be fractional)

        Returns:
            CAGR percentage (e.g., 12.5 for 12.5%), or None if invalid
        """
        if start_value is None or end_value is None or years is None:
            return None
        if start_value <= 0 or years <= 0:
            logger.warning("[FinancialCalculator] Invalid input for CAGR calculation")
            return None
        if end_value < 0:
            return None

        try:
            cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
            return cagr
        except Exception as e:
            logger.error(f"[FinancialCalculator] CAGR calculation error: {e}")
            return None

    @staticmethod
    def calculate_daily_returns(prices: List[float]) -> Optional[List[float]]:
        """
        Calculate daily returns from price series.

        Args:
            prices: List of prices (chronological order)

        Returns:
            List of daily returns (percentage), or None if invalid
        """
        if not prices or len(prices) < 2:
            return None

        try:
            prices_arr = np.array(prices, dtype=float)
            returns = np.diff(prices_arr) / prices_arr[:-1] * 100
            return returns.tolist()
        except Exception as e:
            logger.error(f"[FinancialCalculator] Daily returns calculation error: {e}")
            return None

    # =========================================================================
    # Risk Metrics
    # =========================================================================

    @staticmethod
    def calculate_volatility(
        prices: List[float],
        annualize: bool = True,
        trading_days: int = 252
    ) -> Optional[float]:
        """
        Calculate volatility (standard deviation of returns).

        Args:
            prices: List of prices (chronological order)
            annualize: Whether to annualize the volatility
            trading_days: Number of trading days per year

        Returns:
            Volatility percentage, or None if invalid
        """
        if not prices or len(prices) < 3:
            return None

        try:
            prices_arr = np.array(prices, dtype=float)
            returns = np.diff(prices_arr) / prices_arr[:-1]

            daily_vol = np.std(returns, ddof=1) * 100

            if annualize:
                return daily_vol * np.sqrt(trading_days)
            return daily_vol
        except Exception as e:
            logger.error(f"[FinancialCalculator] Volatility calculation error: {e}")
            return None

    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 3.0,
        annualize: bool = True,
        trading_days: int = 252
    ) -> Optional[float]:
        """
        Calculate Sharpe Ratio.

        Args:
            returns: List of returns (percentage, e.g., [1.5, -0.8, 2.1])
            risk_free_rate: Annual risk-free rate percentage (default 3%)
            annualize: Whether to annualize the ratio
            trading_days: Number of trading days per year

        Returns:
            Sharpe ratio, or None if invalid
        """
        if not returns or len(returns) < 2:
            return None

        try:
            returns_arr = np.array(returns, dtype=float)

            # Convert annual risk-free rate to daily
            daily_rf = risk_free_rate / trading_days

            excess_returns = returns_arr - daily_rf

            mean_excess = np.mean(excess_returns)
            std_excess = np.std(excess_returns, ddof=1)

            if std_excess == 0:
                return None

            daily_sharpe = mean_excess / std_excess

            if annualize:
                return daily_sharpe * np.sqrt(trading_days)
            return daily_sharpe
        except Exception as e:
            logger.error(f"[FinancialCalculator] Sharpe ratio calculation error: {e}")
            return None

    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> Optional[float]:
        """
        Calculate Maximum Drawdown (MDD).

        Args:
            prices: List of prices (chronological order)

        Returns:
            Maximum drawdown percentage (negative value), or None if invalid
        """
        if not prices or len(prices) < 2:
            return None

        try:
            prices_arr = np.array(prices, dtype=float)

            # Calculate running maximum
            running_max = np.maximum.accumulate(prices_arr)

            # Calculate drawdown at each point
            drawdowns = (prices_arr - running_max) / running_max * 100

            # Return the maximum drawdown (most negative)
            return float(np.min(drawdowns))
        except Exception as e:
            logger.error(f"[FinancialCalculator] Max drawdown calculation error: {e}")
            return None

    @staticmethod
    def calculate_drawdown_duration(prices: List[float]) -> Optional[Tuple[int, int]]:
        """
        Calculate drawdown duration statistics.

        Args:
            prices: List of prices (chronological order)

        Returns:
            Tuple of (max_duration_days, current_duration_days), or None if invalid
        """
        if not prices or len(prices) < 2:
            return None

        try:
            prices_arr = np.array(prices, dtype=float)
            running_max = np.maximum.accumulate(prices_arr)

            in_drawdown = prices_arr < running_max

            max_duration = 0
            current_duration = 0
            current_streak = 0

            for is_dd in in_drawdown:
                if is_dd:
                    current_streak += 1
                    max_duration = max(max_duration, current_streak)
                else:
                    current_streak = 0

            current_duration = current_streak

            return (max_duration, current_duration)
        except Exception as e:
            logger.error(f"[FinancialCalculator] Drawdown duration calculation error: {e}")
            return None

    # =========================================================================
    # Statistical Analysis
    # =========================================================================

    @staticmethod
    def calculate_moving_average(
        prices: List[float],
        period: int
    ) -> Optional[List[Optional[float]]]:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            prices: List of prices
            period: Moving average period

        Returns:
            List of moving averages (None for initial periods), or None if invalid
        """
        if not prices or period <= 0 or len(prices) < period:
            return None

        try:
            result = [None] * (period - 1)

            for i in range(period - 1, len(prices)):
                window = prices[i - period + 1:i + 1]
                result.append(sum(window) / period)

            return result
        except Exception as e:
            logger.error(f"[FinancialCalculator] Moving average calculation error: {e}")
            return None

    @staticmethod
    def calculate_price_momentum(
        prices: List[float],
        period: int = 20
    ) -> Optional[float]:
        """
        Calculate price momentum (rate of change over period).

        Args:
            prices: List of prices (chronological order)
            period: Lookback period

        Returns:
            Momentum percentage, or None if invalid
        """
        if not prices or len(prices) <= period:
            return None

        try:
            current_price = prices[-1]
            past_price = prices[-period - 1]

            if past_price <= 0:
                return None

            return ((current_price - past_price) / past_price) * 100
        except Exception as e:
            logger.error(f"[FinancialCalculator] Momentum calculation error: {e}")
            return None

    @staticmethod
    def calculate_average_volume(volumes: List[int]) -> Optional[float]:
        """
        Calculate average trading volume.

        Args:
            volumes: List of trading volumes

        Returns:
            Average volume, or None if invalid
        """
        if not volumes:
            return None

        try:
            return sum(volumes) / len(volumes)
        except Exception as e:
            logger.error(f"[FinancialCalculator] Average volume calculation error: {e}")
            return None

    @staticmethod
    def calculate_volume_ratio(
        current_volume: int,
        average_volume: float
    ) -> Optional[float]:
        """
        Calculate volume ratio vs average.

        Args:
            current_volume: Current trading volume
            average_volume: Average trading volume

        Returns:
            Volume ratio (e.g., 1.5 means 150% of average), or None if invalid
        """
        if average_volume is None or average_volume <= 0:
            return None
        if current_volume is None:
            return None

        return current_volume / average_volume

    # =========================================================================
    # Formatting Utilities
    # =========================================================================

    @staticmethod
    def format_currency(
        value: Union[int, float],
        unit: str = "KRW",
        decimals: int = 0
    ) -> str:
        """
        Format currency value with appropriate suffixes.

        Args:
            value: Numeric value
            unit: Currency unit (KRW, USD)
            decimals: Decimal places for display

        Returns:
            Formatted string (e.g., "1.5T", "320B", "45M")
        """
        if value is None:
            return "-"

        try:
            abs_value = abs(value)
            sign = "-" if value < 0 else ""

            if unit == "KRW":
                # Korean style: 조(T), 억(B), 만(M)
                if abs_value >= 1_000_000_000_000:  # 1조
                    formatted = f"{sign}{abs_value / 1_000_000_000_000:,.{decimals}f}조"
                elif abs_value >= 100_000_000:  # 1억
                    formatted = f"{sign}{abs_value / 100_000_000:,.{decimals}f}억"
                elif abs_value >= 10_000:  # 1만
                    formatted = f"{sign}{abs_value / 10_000:,.{decimals}f}만"
                else:
                    formatted = f"{sign}{abs_value:,.{decimals}f}"
                return formatted + "원" if abs_value < 10_000 else formatted
            else:
                # International style: T, B, M, K
                if abs_value >= 1_000_000_000_000:
                    return f"{sign}${abs_value / 1_000_000_000_000:,.{decimals}f}T"
                elif abs_value >= 1_000_000_000:
                    return f"{sign}${abs_value / 1_000_000_000:,.{decimals}f}B"
                elif abs_value >= 1_000_000:
                    return f"{sign}${abs_value / 1_000_000:,.{decimals}f}M"
                elif abs_value >= 1_000:
                    return f"{sign}${abs_value / 1_000:,.{decimals}f}K"
                else:
                    return f"{sign}${abs_value:,.{decimals}f}"
        except Exception:
            return str(value)

    @staticmethod
    def format_percentage(
        value: float,
        decimals: int = 2,
        show_sign: bool = True
    ) -> str:
        """
        Format percentage value.

        Args:
            value: Percentage value (e.g., 10.5 for 10.5%)
            decimals: Decimal places
            show_sign: Whether to show + for positive values

        Returns:
            Formatted percentage string (e.g., "+10.50%")
        """
        if value is None:
            return "-"

        try:
            if show_sign and value > 0:
                return f"+{value:,.{decimals}f}%"
            return f"{value:,.{decimals}f}%"
        except Exception:
            return str(value)

    @staticmethod
    def format_number(
        value: Union[int, float],
        decimals: int = 0
    ) -> str:
        """
        Format number with thousand separators.

        Args:
            value: Numeric value
            decimals: Decimal places

        Returns:
            Formatted number string (e.g., "1,234,567")
        """
        if value is None:
            return "-"

        try:
            return f"{value:,.{decimals}f}"
        except Exception:
            return str(value)

    # =========================================================================
    # Composite Analysis
    # =========================================================================

    @staticmethod
    def calculate_risk_metrics(
        prices: List[float],
        risk_free_rate: float = 3.0
    ) -> Optional[dict]:
        """
        Calculate comprehensive risk metrics from price series.

        Args:
            prices: List of prices (chronological order)
            risk_free_rate: Annual risk-free rate percentage

        Returns:
            Dictionary with volatility, sharpe_ratio, max_drawdown, or None if invalid
        """
        if not prices or len(prices) < 5:
            return None

        try:
            daily_returns = FinancialCalculator.calculate_daily_returns(prices)

            return {
                "total_return": FinancialCalculator.calculate_total_return(prices),
                "volatility": FinancialCalculator.calculate_volatility(prices),
                "sharpe_ratio": FinancialCalculator.calculate_sharpe_ratio(
                    daily_returns, risk_free_rate
                ) if daily_returns else None,
                "max_drawdown": FinancialCalculator.calculate_max_drawdown(prices),
                "period_days": len(prices)
            }
        except Exception as e:
            logger.error(f"[FinancialCalculator] Risk metrics calculation error: {e}")
            return None

    @staticmethod
    def calculate_performance_summary(
        prices: List[float],
        volumes: List[int] = None,
        period_label: str = "Period"
    ) -> Optional[dict]:
        """
        Calculate comprehensive performance summary.

        Args:
            prices: List of prices (chronological order)
            volumes: Optional list of volumes
            period_label: Label for the period

        Returns:
            Dictionary with performance metrics, or None if invalid
        """
        if not prices or len(prices) < 2:
            return None

        try:
            summary = {
                "period": period_label,
                "start_price": prices[0],
                "end_price": prices[-1],
                "high": max(prices),
                "low": min(prices),
                "return_pct": FinancialCalculator.calculate_total_return(prices),
                "volatility": FinancialCalculator.calculate_volatility(prices),
                "max_drawdown": FinancialCalculator.calculate_max_drawdown(prices),
            }

            if volumes:
                summary["avg_volume"] = FinancialCalculator.calculate_average_volume(volumes)
                summary["total_volume"] = sum(volumes)

            return summary
        except Exception as e:
            logger.error(f"[FinancialCalculator] Performance summary error: {e}")
            return None
