"""
Report Generator - Generate evaluation and calibration reports

Implements:
- Weekly backtest reports (markdown format)
- Calibration analysis reports
- CSV export functionality
- Performance visualizations
"""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate evaluation reports for backtesting and calibration

    Supports:
    - Weekly performance reports in markdown
    - Detailed calibration analysis
    - CSV export for further analysis
    - Summary statistics formatting
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize report generator

        Args:
            output_dir: Directory for saving reports (default: current directory)
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized ReportGenerator - Output dir: {self.output_dir}")

    def generate_weekly_report(
        self,
        week: int,
        league: str,
        metrics: Dict[str, any],
        include_details: bool = True
    ) -> str:
        """
        Generate weekly backtest report in markdown format

        Args:
            week: Week number
            league: League name
            metrics: Dictionary of metrics from backtest
            include_details: Include detailed breakdowns

        Returns:
            Markdown-formatted report string
        """
        report_lines = [
            f"# Backtest Report - {league} Week {week}",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
        ]

        # Executive Summary
        report_lines.extend(self._format_executive_summary(metrics))

        # Performance Metrics
        if "roi_metrics" in metrics:
            report_lines.extend(self._format_roi_section(metrics["roi_metrics"]))

        # Risk Metrics
        if "sharpe_ratio" in metrics or "drawdown" in metrics:
            report_lines.extend(self._format_risk_section(metrics))

        # Calibration Metrics
        if "calibration" in metrics:
            report_lines.extend(self._format_calibration_section(metrics["calibration"]))

        # Win Rate Analysis
        if "win_rate_by_confidence" in metrics:
            report_lines.extend(
                self._format_win_rate_section(metrics["win_rate_by_confidence"])
            )

        # Detailed Breakdown (optional)
        if include_details:
            report_lines.extend(self._format_detailed_breakdown(metrics))

        # Recommendations
        report_lines.extend(self._format_recommendations(metrics))

        return "\n".join(report_lines)

    def _format_executive_summary(self, metrics: Dict) -> List[str]:
        """Format executive summary section"""
        roi = metrics.get("roi_metrics", {}).get("roi", 0.0)
        win_rate = metrics.get("win_rate", 0.0)
        sharpe = metrics.get("sharpe_ratio", 0.0)

        # Determine overall performance rating
        if roi > 10 and sharpe > 1.5:
            rating = "Excellent"
        elif roi > 5 and sharpe > 1.0:
            rating = "Good"
        elif roi > 0:
            rating = "Fair"
        else:
            rating = "Poor"

        return [
            "## Executive Summary",
            "",
            f"**Overall Performance:** {rating}",
            "",
            f"- **ROI:** {roi:.2f}%",
            f"- **Win Rate:** {win_rate * 100:.1f}%",
            f"- **Sharpe Ratio:** {sharpe:.2f}",
            "",
        ]

    def _format_roi_section(self, roi_metrics: Dict) -> List[str]:
        """Format ROI section"""
        return [
            "## Return on Investment",
            "",
            f"- **Total Profit:** ${roi_metrics.get('total_profit', 0.0):.2f}",
            f"- **Total Wagered:** ${roi_metrics.get('total_wagered', 0.0):.2f}",
            f"- **Final Bankroll:** ${roi_metrics.get('final_bankroll', 0.0):.2f}",
            f"- **Number of Bets:** {roi_metrics.get('num_bets', 0)}",
            f"- **ROI:** {roi_metrics.get('roi', 0.0):.2f}%",
            "",
        ]

    def _format_risk_section(self, metrics: Dict) -> List[str]:
        """Format risk metrics section"""
        lines = [
            "## Risk Analysis",
            "",
        ]

        # Sharpe ratio
        sharpe = metrics.get("sharpe_ratio", 0.0)
        sharpe_rating = (
            "Excellent" if sharpe > 2.0
            else "Good" if sharpe > 1.0
            else "Fair" if sharpe > 0.5
            else "Poor"
        )
        lines.append(f"**Sharpe Ratio:** {sharpe:.3f} ({sharpe_rating})")
        lines.append("")

        # Drawdown
        if "drawdown" in metrics:
            dd = metrics["drawdown"]
            lines.extend([
                "**Drawdown Analysis:**",
                f"- Max Drawdown: {dd.get('max_drawdown', 0.0):.2f}%",
                f"- Drawdown Amount: ${dd.get('max_drawdown_amount', 0.0):.2f}",
                f"- Peak Value: ${dd.get('peak_value', 0.0):.2f}",
                f"- Valley Value: ${dd.get('valley_value', 0.0):.2f}",
                f"- Recovery Rate: {dd.get('recovery_rate', 0.0):.1f}%",
                "",
            ])

        return lines

    def _format_calibration_section(self, calibration: Dict) -> List[str]:
        """Format calibration metrics section"""
        ece = calibration.get("ece", 0.0)
        brier = calibration.get("brier_score", 0.0)
        mce = calibration.get("mce", 0.0)

        # Determine calibration quality
        if ece < 0.05:
            cal_quality = "Excellent"
        elif ece < 0.08:
            cal_quality = "Good"
        elif ece < 0.10:
            cal_quality = "Fair"
        else:
            cal_quality = "Poor"

        return [
            "## Calibration Quality",
            "",
            f"**Overall Quality:** {cal_quality}",
            "",
            f"- **Expected Calibration Error (ECE):** {ece:.4f}",
            f"- **Brier Score:** {brier:.4f}",
            f"- **Maximum Calibration Error (MCE):** {mce:.4f}",
            "",
            "*Lower values indicate better calibration*",
            "",
        ]

    def _format_win_rate_section(self, win_rate_by_conf: Dict) -> List[str]:
        """Format win rate by confidence section"""
        lines = [
            "## Win Rate by Confidence Level",
            "",
            "| Confidence | Win Rate | Num Bets |",
            "|------------|----------|----------|",
        ]

        # Sort by confidence threshold
        sorted_items = sorted(
            win_rate_by_conf.items(),
            key=lambda x: x[1].get("threshold", 0.0)
        )

        for conf_key, stats in sorted_items:
            threshold = stats.get("threshold", 0.0)
            win_rate = stats.get("win_rate", 0.0)
            num_bets = stats.get("num_bets", 0)

            lines.append(
                f"| ≥{threshold:.1f} | {win_rate * 100:.1f}% | {num_bets} |"
            )

        lines.append("")
        return lines

    def _format_detailed_breakdown(self, metrics: Dict) -> List[str]:
        """Format detailed breakdown section"""
        lines = [
            "## Detailed Breakdown",
            "",
        ]

        # By risk mode (if available)
        if "by_risk_mode" in metrics:
            lines.extend([
                "### Performance by Risk Mode",
                "",
            ])
            for risk_mode, stats in metrics["by_risk_mode"].items():
                lines.extend([
                    f"**{risk_mode.capitalize()}:**",
                    f"- ROI: {stats.get('roi', 0.0):.2f}%",
                    f"- Win Rate: {stats.get('win_rate', 0.0) * 100:.1f}%",
                    f"- Num Bets: {stats.get('num_bets', 0)}",
                    "",
                ])

        # By market type (if available)
        if "by_market_type" in metrics:
            lines.extend([
                "### Performance by Market Type",
                "",
                "| Market | ROI | Win Rate | Num Bets |",
                "|--------|-----|----------|----------|",
            ])
            for market, stats in metrics["by_market_type"].items():
                roi = stats.get("roi", 0.0)
                win_rate = stats.get("win_rate", 0.0)
                num_bets = stats.get("num_bets", 0)
                lines.append(
                    f"| {market} | {roi:.1f}% | {win_rate * 100:.1f}% | {num_bets} |"
                )
            lines.append("")

        return lines

    def _format_recommendations(self, metrics: Dict) -> List[str]:
        """Format recommendations section"""
        lines = [
            "## Recommendations",
            "",
        ]

        recommendations = []

        # ROI-based recommendations
        roi = metrics.get("roi_metrics", {}).get("roi", 0.0)
        if roi < 0:
            recommendations.append(
                "- Review betting strategy - negative ROI indicates unprofitable performance"
            )
        elif roi > 20:
            recommendations.append(
                "- Strong performance - consider scaling up bet sizes gradually"
            )

        # Calibration-based recommendations
        if "calibration" in metrics:
            ece = metrics["calibration"].get("ece", 0.0)
            if ece > 0.10:
                recommendations.append(
                    "- Recalibrate model - high ECE indicates poor probability calibration"
                )
            elif ece < 0.05:
                recommendations.append(
                    "- Calibration is excellent - maintain current calibration approach"
                )

        # Sharpe-based recommendations
        sharpe = metrics.get("sharpe_ratio", 0.0)
        if sharpe < 0.5:
            recommendations.append(
                "- Risk-adjusted returns are low - review risk management strategy"
            )

        # Drawdown-based recommendations
        if "drawdown" in metrics:
            max_dd = metrics["drawdown"].get("max_drawdown", 0.0)
            if max_dd > 30:
                recommendations.append(
                    "- Large drawdown detected - implement stricter risk controls"
                )

        # Default recommendation if none generated
        if not recommendations:
            recommendations.append(
                "- Performance is satisfactory - continue monitoring and backtesting"
            )

        lines.extend(recommendations)
        lines.append("")

        return lines

    def generate_calibration_report(
        self,
        calibration_data: Dict[str, any]
    ) -> str:
        """
        Generate detailed calibration analysis report

        Args:
            calibration_data: Dictionary with calibration analysis data

        Returns:
            Markdown-formatted calibration report
        """
        report_lines = [
            "# Calibration Analysis Report",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
        ]

        # Current Status
        status = calibration_data.get("status", "unknown")
        ece = calibration_data.get("ece", 0.0)
        brier = calibration_data.get("brier", 0.0)

        report_lines.extend([
            "## Current Calibration Status",
            "",
            f"**Status:** {status.upper()}",
            f"**ECE:** {ece:.4f}",
            f"**Brier Score:** {brier:.4f}",
            "",
        ])

        # Trend Analysis
        if "trend" in calibration_data:
            trend = calibration_data["trend"]
            trend_emoji = {
                "improving": "📈",
                "stable": "➡️",
                "degrading": "📉",
                "unknown": "❓",
            }.get(trend, "")

            report_lines.extend([
                "## Trend Analysis",
                "",
                f"**Calibration Trend:** {trend.capitalize()} {trend_emoji}",
                "",
            ])

        # Issues and Recommendations
        if calibration_data.get("is_degraded"):
            issues = calibration_data.get("issues", [])
            recommendations = calibration_data.get("recommendations", [])

            report_lines.extend([
                "## Issues Detected",
                "",
            ])
            for issue in issues:
                report_lines.append(f"- {issue}")
            report_lines.append("")

            if recommendations:
                report_lines.extend([
                    "## Recommended Actions",
                    "",
                ])
                for rec in recommendations:
                    report_lines.append(f"- {rec}")
                report_lines.append("")

        # Historical Context
        if "history_length" in calibration_data:
            report_lines.extend([
                "## Historical Context",
                "",
                f"**Number of Calibration Checks:** {calibration_data['history_length']}",
                "",
            ])

        return "\n".join(report_lines)

    def export_to_csv(
        self,
        data: List[Dict],
        filepath: str
    ) -> str:
        """
        Export data to CSV file

        Args:
            data: List of dictionaries to export
            filepath: Path to save CSV file

        Returns:
            Absolute path to saved file
        """
        if not data:
            logger.warning("No data to export")
            return ""

        # Determine output path
        output_path = self.output_dir / filepath if not Path(filepath).is_absolute() else Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert to DataFrame for easier CSV export
            df = pd.DataFrame(data)

            # Save to CSV
            df.to_csv(output_path, index=False)

            logger.info(f"Exported {len(data)} rows to {output_path}")
            return str(output_path.absolute())

        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return ""

    def save_report(
        self,
        report: str,
        filename: str
    ) -> str:
        """
        Save report to file

        Args:
            report: Report content (markdown or text)
            filename: Filename to save as

        Returns:
            Absolute path to saved file
        """
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w") as f:
                f.write(report)

            logger.info(f"Saved report to {output_path}")
            return str(output_path.absolute())

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return ""

    def generate_summary_table(
        self,
        weekly_results: List[Dict[str, any]]
    ) -> str:
        """
        Generate summary table for multiple weeks

        Args:
            weekly_results: List of weekly backtest results

        Returns:
            Markdown table string
        """
        if not weekly_results:
            return "No results available"

        lines = [
            "# Multi-Week Summary",
            "",
            "| Week | ROI | Win Rate | Sharpe | ECE | Brier | Num Bets |",
            "|------|-----|----------|--------|-----|-------|----------|",
        ]

        for result in weekly_results:
            week = result.get("week", "?")
            roi = result.get("roi_metrics", {}).get("roi", 0.0)
            win_rate = result.get("win_rate", 0.0)
            sharpe = result.get("sharpe_ratio", 0.0)
            ece = result.get("calibration", {}).get("ece", 0.0)
            brier = result.get("calibration", {}).get("brier_score", 0.0)
            num_bets = result.get("roi_metrics", {}).get("num_bets", 0)

            lines.append(
                f"| {week} | {roi:.1f}% | {win_rate * 100:.1f}% | "
                f"{sharpe:.2f} | {ece:.3f} | {brier:.3f} | {num_bets} |"
            )

        return "\n".join(lines)
