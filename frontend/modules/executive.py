"""
Executive Insights Page
Comprehensive CFO insights and analytics
"""

import streamlit as st
import pandas as pd
from typing import Dict, List

def create_page(analytics_data: Dict):
    """Create Executive Insights page"""
    cfo_insights = analytics_data["cfo_insights"]
    
    st.markdown("## 📊 Executive Insights")
    
    # Display insights by dimension
    if cfo_insights:
        dimensions = {}
        for insight in cfo_insights:
            dim = insight['dimension']
            if dim not in dimensions:
                dimensions[dim] = []
            dimensions[dim].append(insight)
        
        for dimension, insights in dimensions.items():
            with st.expander(f"📁 {dimension} ({len(insights)} insights)", expanded=True):
                for insight in insights:
                    formatted_text = format_insights_clean_text(insight)
                    st.markdown(formatted_text)
                    st.markdown("---")
    else:
        st.info("No CFO insights available. Please run GraphRAG processing to generate insights.")

def format_insights_clean_text(insight_data):
    """Format insight data into clean, readable text"""
    
    formatted_text = f"""
    **Question:** {insight_data.get('question', 'N/A')}
    
    **Insight:** {insight_data.get('insight', 'N/A')}
    """
    
    # Add KPIs if available
    if insight_data.get('kpis'):
        kpi_text = "**Key Metrics:** "
        kpi_items = []
        for key, value in insight_data['kpis'].items():
            if isinstance(value, (int, float)):
                kpi_items.append(f"{key}: {value:,.0f}")
            else:
                kpi_items.append(f"{key}: {value}")
        formatted_text += f"\n{kpi_text}{', '.join(kpi_items)}\n"
    
    # Add risks if available
    if insight_data.get('risks'):
        risk_text = "**Risks:** "
        formatted_text += f"\n{risk_text}{', '.join(insight_data['risks'])}\n"
    
    # Add opportunities if available
    if insight_data.get('opportunities'):
        opp_text = "**Opportunities:** "
        formatted_text += f"\n{opp_text}{', '.join(insight_data['opportunities'])}\n"
    
    # Add evidence if available
    if insight_data.get('evidence'):
        formatted_text += "\n**Supporting Evidence:**\n"
        for evidence in insight_data['evidence']:
            formatted_text += f"- {evidence.get('snippet', 'N/A')} (Source: {evidence.get('source', 'N/A')})\n"
    
    # Add data gaps if available
    if insight_data.get('data_gaps'):
        gap_text = "**Data Gaps:** "
        formatted_text += f"\n{gap_text}{', '.join(insight_data['data_gaps'])}\n"
    
    # Add confidence score
    if insight_data.get('confidence'):
        formatted_text += f"\n**Confidence:** {insight_data['confidence']:.1%}\n"
    
    return formatted_text



