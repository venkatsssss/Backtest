from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
from typing import Dict, List
import logging

from backend.utils.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """Generate comprehensive PDF reports with charts and tables"""
    
    @staticmethod
    def create_pdf_report(results: Dict, summary_data: Dict) -> BytesIO:
        """
        Create a complete PDF report with:
        1. Executive Summary
        2. Performance Charts (6 charts)
        3. Detailed Trade Table
        
        Args:
            results: Backtest results with trades data
            summary_data: Summary statistics
            
        Returns:
            BytesIO object containing PDF
        """
        try:
            logger.info("Creating PDF report...")
            
            # Create PDF buffer
            pdf_buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Container for PDF elements
            story = []
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#FF6B6B'),
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#667EEA'),
                spaceAfter=12
            )
            
            subheading_style = ParagraphStyle(
                'CustomSubHeading',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#1A1A2E'),
                spaceAfter=10
            )
            
            # 1. TITLE PAGE
            story.append(Spacer(1, 1*inch))
            story.append(Paragraph("🔨 SAGEFORGE", title_style))
            story.append(Paragraph("Hammer Pattern Backtest Report", styles['Heading2']))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
            story.append(PageBreak())
            
            # 2. EXECUTIVE SUMMARY
            story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Summary table
            summary_items = [
                ['Strategy', summary_data.get('strategy', 'N/A')],
                ['Period', summary_data.get('period', 'N/A')],
                ['Stocks Analyzed', str(summary_data.get('stocks_analyzed', 0))],
                ['Timeframe', '15-minute candles'],
                ['', ''],
                ['Total Patterns Found', str(summary_data.get('total_patterns', 0))],
                ['Target Hit', f"{summary_data.get('target_hit_count', 0)} ({summary_data.get('target_hit_rate', 0):.1f}%)"],
                ['Stop Loss Hit', f"{summary_data.get('stop_loss_count', 0)} ({summary_data.get('stop_loss_rate', 0):.1f}%)"],
                ['End of Day Exits', str(summary_data.get('eod_exit_count', 0))],
                ['', ''],
                ['Average Return', f"{summary_data.get('avg_return', 0):.2f}%"],
                ['Total Points Gained', f"₹{summary_data.get('total_points_gained', 0):.2f}"],
            ]
            
            summary_table = Table(summary_items, colWidths=[3*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F0F0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(summary_table)
            story.append(PageBreak())
            
            # 3. PERFORMANCE CHARTS
            story.append(Paragraph("PERFORMANCE ANALYSIS", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Generate all charts
            logger.info("Generating charts for PDF...")
            charts = ChartGenerator.generate_all_charts(results)
            
            # Add each chart to PDF
            chart_titles = {
                'outcome_pie': 'Trade Outcome Distribution',
                'cumulative_profit': 'Cumulative Profit Over Time',
                'stock_performance': 'Stock-wise Performance',
                'max_vs_final': 'Maximum vs Final Profit Analysis',
                'win_loss_dist': 'Profit/Loss Distribution',
                'time_analysis': 'Pattern Frequency by Time of Day'
            }
            
            for chart_key, chart_buffer in charts.items():
                # Add chart title
                story.append(Paragraph(chart_titles[chart_key], subheading_style))
                
                # Add chart image
                chart_buffer.seek(0)
                img = Image(chart_buffer, width=6.5*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
                
                # Page break after every 2 charts for better layout
                if chart_key in ['cumulative_profit', 'max_vs_final']:
                    story.append(PageBreak())
            
            story.append(PageBreak())
            
            # 4. DETAILED TRADE TABLE
            story.append(Paragraph("DETAILED TRADE RECORDS", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Table headers
            table_data = [[
                'Stock', 'Date', 'Time', 'Entry', 'Target', 'Stop Loss',
                'Exit', 'Outcome', 'Points', '% Return', 'Max Profit'
            ]]
            
            # Add trade data
            for trade in results['trades']:
                table_data.append([
                    trade['stock'],
                    trade['pattern_date'],
                    trade['pattern_time'],
                    f"₹{trade['entry_price']:.1f}",
                    f"₹{trade['target_price']:.1f}",
                    f"₹{trade['stop_loss_price']:.1f}",
                    f"₹{trade['exit_price']:.1f}",
                    PDFReportGenerator._format_outcome(trade['outcome']),
                    f"{trade['points_gained']:+.1f}",
                    f"{trade['percentage_return']:+.1f}%",
                    f"₹{trade['max_profit_points']:.1f}"
                ])
            
            # Create table
            trade_table = Table(table_data, colWidths=[
                0.6*inch, 0.7*inch, 0.5*inch, 0.6*inch, 0.6*inch,
                0.7*inch, 0.6*inch, 0.7*inch, 0.6*inch, 0.7*inch, 0.7*inch
            ])
            
            # Style table
            trade_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667EEA')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
            ]))
            
            # Color code outcomes in table
            for idx, trade in enumerate(results['trades'], start=1):
                outcome = trade['outcome']
                if outcome == 'target_hit':
                    color = colors.HexColor('#51CF66')
                elif outcome == 'stop_loss':
                    color = colors.HexColor('#FF6B6B')
                else:
                    color = colors.HexColor('#FFD43B')
                
                trade_table.setStyle(TableStyle([
                    ('BACKGROUND', (7, idx), (7, idx), color),
                    ('TEXTCOLOR', (7, idx), (7, idx), colors.white if outcome != 'eod_exit' else colors.black),
                ]))
            
            story.append(trade_table)
            
            # Build PDF
            doc.build(story)
            
            pdf_buffer.seek(0)
            logger.info("✅ PDF report generated successfully")
            
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error creating PDF report: {e}")
            raise
    
    @staticmethod
    def _format_outcome(outcome: str) -> str:
        """Format outcome text for display"""
        format_map = {
            'target_hit': 'Target',
            'stop_loss': 'Stop Loss',
            'eod_exit': 'EOD'
        }
        return format_map.get(outcome, outcome)
