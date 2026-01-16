import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generate charts for backtest results"""
    
    # Color scheme matching SageForge theme
    COLORS = {
        'primary': '#FF6B6B',
        'success': '#51CF66',
        'warning': '#FFD43B',
        'danger': '#FF6B6B',
        'info': '#74B9FF',
        'purple': '#667EEA',
        'dark': '#1A1A2E'
    }
    
    @staticmethod
    def set_style():
        """Set consistent style for all charts"""
        sns.set_style("whitegrid")
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 13
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 9
    
    @staticmethod
    def create_outcome_pie_chart(results: Dict) -> BytesIO:
        """
        Chart 1: Outcome Distribution Pie Chart
        Shows percentage of Target Hit, Stop Loss, EOD Exit
        """
        ChartGenerator.set_style()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        labels = ['Target Hit', 'Stop Loss', 'EOD Exit']
        sizes = [
            results['target_hit_count'],
            results['stop_loss_count'],
            results['eod_exit_count']
        ]
        colors = [
            ChartGenerator.COLORS['success'],
            ChartGenerator.COLORS['danger'],
            ChartGenerator.COLORS['warning']
        ]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11, 'weight': 'bold'}
        )
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
        
        ax.set_title('Trade Outcome Distribution', fontsize=14, weight='bold', pad=20)
        
        # Add legend with counts
        legend_labels = [
            f'{labels[i]}: {sizes[i]} ({sizes[i]/sum(sizes)*100:.1f}%)'
            for i in range(len(labels))
        ]
        ax.legend(legend_labels, loc='lower left', bbox_to_anchor=(0, -0.1))
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    @staticmethod
    def create_max_vs_final_profit_chart(trades: List[Dict]) -> BytesIO:
        """
        Chart 4: Max Profit vs Final Profit Scatter Plot
        Shows missed opportunities (trades that went into profit then reversed)
        """
        ChartGenerator.set_style()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Extract data
        max_profits = [trade['max_profit_points'] for trade in trades]
        final_profits = [trade['points_gained'] for trade in trades]
        
        # Color by outcome
        colors = []
        for trade in trades:
            if trade['outcome'] == 'target_hit':
                colors.append(ChartGenerator.COLORS['success'])
            elif trade['outcome'] == 'stop_loss':
                colors.append(ChartGenerator.COLORS['danger'])
            else:
                colors.append(ChartGenerator.COLORS['warning'])
        
        # Scatter plot
        scatter = ax.scatter(
            max_profits,
            final_profits,
            c=colors,
            alpha=0.6,
            s=50,
            edgecolors='black',
            linewidth=0.5
        )
        
        # Add diagonal line (max = final, perfect scenario)
        max_val = max(max(max_profits), max(final_profits))
        min_val = min(min(max_profits), min(final_profits))
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.3, linewidth=1, label='Max = Final')
        
        # Add zero lines
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        ax.axvline(x=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        
        ax.set_xlabel('Max Profit Reached (₹)', fontsize=11, weight='bold')
        ax.set_ylabel('Final Profit/Loss (₹)', fontsize=11, weight='bold')
        ax.set_title('Max Profit vs Final Profit (Missed Opportunities)', fontsize=14, weight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=ChartGenerator.COLORS['success'], label='Target Hit'),
            Patch(facecolor=ChartGenerator.COLORS['danger'], label='Stop Loss'),
            Patch(facecolor=ChartGenerator.COLORS['warning'], label='EOD Exit')
        ]
        ax.legend(handles=legend_elements, loc='lower right')
        
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    @staticmethod
    def create_win_loss_distribution_chart(trades: List[Dict]) -> BytesIO:
        """
        Chart 5: Win/Loss Distribution Histogram
        Shows distribution of profit/loss amounts
        """
        ChartGenerator.set_style()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Extract percentage returns
        returns = [trade['percentage_return'] for trade in trades]
        
        # Create histogram
        n, bins, patches = ax.hist(
            returns,
            bins=20,
            edgecolor='black',
            linewidth=0.5,
            alpha=0.8
        )
        
        # Color bars based on positive/negative
        for i, patch in enumerate(patches):
            if bins[i] >= 0:
                patch.set_facecolor(ChartGenerator.COLORS['success'])
            else:
                patch.set_facecolor(ChartGenerator.COLORS['danger'])
        
        # Add vertical line at zero
        ax.axvline(x=0, color='black', linestyle='--', linewidth=2, label='Break-even')
        
        ax.set_xlabel('Return (%)', fontsize=11, weight='bold')
        ax.set_ylabel('Number of Trades', fontsize=11, weight='bold')
        ax.set_title('Profit/Loss Distribution', fontsize=14, weight='bold', pad=20)
        ax.grid(True, axis='y', alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    @staticmethod
    def create_time_analysis_chart(trades: List[Dict]) -> BytesIO:
        """
        Chart 6: Patterns by Hour of Day
        Shows when hammer patterns occur most frequently
        """
        ChartGenerator.set_style()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Extract hour from pattern_time
        hours = []
        for trade in trades:
            time_str = trade['pattern_time']  # Format: "HH:MM"
            hour = int(time_str.split(':')[0])
            hours.append(hour)
        
        # Count patterns per hour
        from collections import Counter
        hour_counts = Counter(hours)
        
        # Create data for bar chart
        all_hours = range(9, 16)  # Market hours 9 AM to 3 PM
        counts = [hour_counts.get(h, 0) for h in all_hours]
        
        # Create bar chart
        bars = ax.bar(
            all_hours,
            counts,
            color=ChartGenerator.COLORS['info'],
            alpha=0.8,
            edgecolor='black',
            linewidth=0.5
        )
        
        # Add value labels
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    str(count),
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    weight='bold'
                )
        
        ax.set_xlabel('Hour of Day', fontsize=11, weight='bold')
        ax.set_ylabel('Number of Patterns', fontsize=11, weight='bold')
        ax.set_title('Hammer Patterns by Time of Day', fontsize=14, weight='bold', pad=20)
        ax.set_xticks(all_hours)
        ax.set_xticklabels([f'{h}:00' for h in all_hours])
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    @staticmethod
    def generate_all_charts(results: Dict) -> Dict[str, BytesIO]:
        """
        Generate all charts and return as dictionary
        
        Returns:
            Dict with chart names as keys and BytesIO objects as values
        """
        try:
            logger.info("Generating charts...")
            
            charts = {}
            
            # Chart 1: Outcome Pie Chart
            charts['outcome_pie'] = ChartGenerator.create_outcome_pie_chart(results)
            logger.info("✓ Outcome pie chart generated")
            
            # Chart 4: Max vs Final Profit
            charts['max_vs_final'] = ChartGenerator.create_max_vs_final_profit_chart(results['trades'])
            logger.info("✓ Max vs final profit chart generated")
            
            # Chart 5: Win/Loss Distribution
            charts['win_loss_dist'] = ChartGenerator.create_win_loss_distribution_chart(results['trades'])
            logger.info("✓ Win/loss distribution chart generated")
            
            # Chart 6: Time Analysis
            charts['time_analysis'] = ChartGenerator.create_time_analysis_chart(results['trades'])
            logger.info("✓ Time analysis chart generated")
            
            logger.info("✅ All charts generated successfully")
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
            raise
