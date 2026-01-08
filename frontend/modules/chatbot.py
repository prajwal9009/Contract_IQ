"""
Contract Chatbot Page
Q&A interface using GraphRAG technology, CSV analysis, and OpenAI API
"""

import streamlit as st
import pandas as pd
import json
import os
from typing import Dict, List
import sys
import openai

# Add parent directory to path for imports
sys.path.append('..')

# Try to import modules, create fallbacks if not available
try:
    import config
except ImportError:
    class Config:
        CFO_DIMENSIONS_AND_QUESTIONS = [
            ("Financial", "What is the total value of all contracts?"),
            ("Financial", "What are the payment terms across all contracts?"),
            ("Vendor", "Which vendors have the highest contract values?"),
            ("Risk", "What are the compliance requirements across all contracts?"),
            ("Performance", "What are the SLA requirements for all contracts?")
        ]
    config = Config()

try:
    import graph
except ImportError:
    class Graph:
        @staticmethod
        def detect_communities(G):
            return G, {}
    graph = Graph()

try:
    import clustering
except ImportError:
    class Clustering:
        @staticmethod
        def summarize_clusters(G, partition, data):
            return {}
        
        @staticmethod
        def build_graph_context_memory(G, partition, summaries):
            return ""
    clustering = Clustering()

try:
    import cfo_analytics
except ImportError:
    class CFOAnalytics:
        @staticmethod
        def generate_cfo_insights_from_context(context):
            return []
    cfo_analytics = CFOAnalytics()

# Set OpenAI API key
openai.api_key = "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"

def create_page(analytics_data: Dict):
    """Create Contract Chatbot page with GraphRAG integration"""
    
    st.markdown("## 💬 Talk to Your Contracts")
    st.markdown("*Ask questions about your contract portfolio using AI-powered insights*")
    
    # Initialize session state for chat
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'graph_ready' not in st.session_state:
        st.session_state.graph_ready = False
    
    if 'graph_context' not in st.session_state:
        st.session_state.graph_context = ""
    
    # Auto-load graph context if it exists (check parent directory where files are)
    context_file = "../graph_context_memory.txt"
    if os.path.exists(context_file) and not st.session_state.graph_ready:
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                st.session_state.graph_context = f.read()
            st.session_state.graph_ready = True
        except Exception:
            pass
    
    # Check if graph is already processed
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🤖 Contract Intelligence Assistant")
        
        # Check if graph context memory exists
        context_file = "../graph_context_memory.txt"
        
        if os.path.exists(context_file) and st.session_state.graph_ready:
            st.success("✅ Knowledge graph ready! You can now ask questions about your contracts.")
        elif os.path.exists(context_file):
            st.info("🔄 Loading knowledge graph context...")
            st.rerun()
        else:
            st.warning("⚠️ No knowledge graph context found. Please run the contract processing pipeline first.")
            if st.button("🔄 Check for Graph Context", type="secondary"):
                st.rerun()
    
    with col2:
        st.markdown("### 📊 System Status")
        if st.session_state.graph_ready:
            st.success("🟢 Graph Ready")
            st.metric("Contracts Processed", len(analytics_data["contract_csv"]) if analytics_data["contract_csv"] is not None else 0)
        else:
            st.warning("🟡 Graph Not Ready")
            st.info("Click 'Build Knowledge Graph' to start")
        
        # Debug info
        with st.expander("🔧 Debug Info"):
            st.write(f"Graph Context Length: {len(st.session_state.get('graph_context', ''))}")
            st.write(f"Contract Data Available: {analytics_data.get('contract_csv') is not None}")
            if analytics_data.get('contract_csv') is not None:
                st.write(f"Contract Count: {len(analytics_data['contract_csv'])}")
            st.write(f"OpenAI API Key Set: {'Yes' if openai.api_key else 'No'}")
    
    # Chat interface (always available)
    st.markdown("---")
    st.markdown("### 💬 Ask Questions About Your Contracts")
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your contracts (e.g., 'What are the payment terms for IBM contracts?')"):
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your contracts..."):
                try:
                    response = generate_ai_response(prompt, analytics_data)
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"I encountered an error: {str(e)}. Please try rephrasing your question."
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = []
        st.rerun()
    
    # Sample questions
    st.markdown("---")
    st.markdown("### 💡 Sample Questions")
    
    sample_questions = [
        "What are the top vendors by contract value?",
        "Which contracts are expiring in the next 6 months?",
        "What is the timeline of IBM contracts?",
        "What contracts have unfavorable payment terms?",
        "What is our penalty exposure for SLA breaches?",
        "What contracts are expiring in the next 2 years?",
        "Which vendors have the highest concentration risk?",
        "What are the compliance requirements across all contracts?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(sample_questions):
        with cols[i % 2]:
            if st.button(f"💬 {question}", key=f"sample_{i}", use_container_width=True):
                # Add sample question to chat (always works, even without graph)
                st.session_state.chat_messages.append({"role": "user", "content": question})
                st.rerun()

def build_knowledge_graph(analytics_data: Dict) -> bool:
    """Load existing knowledge graph from processed context memory"""
    try:
        # Check if graph context memory file exists (parent directory)
        context_file = "../graph_context_memory.txt"
        
        if os.path.exists(context_file):
            with open(context_file, 'r', encoding='utf-8') as f:
                context_memory = f.read()
            
            st.session_state.graph_context = context_memory
            return True
        else:
            st.error("Graph context memory not found. Please run the contract processing pipeline first.")
            return False
        
    except Exception as e:
        st.error(f"Error loading knowledge graph: {str(e)}")
        return False

def generate_ai_response(prompt: str, analytics_data: Dict) -> str:
    """Generate AI response using Graph Context + CSV Analysis + OpenAI API"""
    try:
        # Get all available data sources
        graph_context = st.session_state.get('graph_context', '')
        df = analytics_data.get("contract_csv", pd.DataFrame())
        
        if df.empty:
            return "No contract data available. Please check your data sources."
        
        # Generate comprehensive CSV analysis
        csv_analysis = generate_comprehensive_csv_analysis(df, prompt)
        
        # Combine all context for OpenAI
        combined_context = build_combined_context(graph_context, csv_analysis, prompt)
        
        # Use OpenAI API for intelligent response
        response = generate_openai_response(prompt, combined_context)
        
        return response
    
    except Exception as e:
        # Fallback to simple CSV analysis if OpenAI fails
        try:
            df = analytics_data.get("contract_csv", pd.DataFrame())
            if not df.empty:
                return generate_simple_csv_response(prompt, df)
            else:
                return f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or contact support."
        except Exception as e2:
            return f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or contact support."

def generate_comprehensive_csv_analysis(df: pd.DataFrame, prompt: str) -> str:
    """Generate comprehensive CFO-level CSV analysis based on the question"""
    try:
        analysis = []
        prompt_lower = prompt.lower()
        
        # Remove duplicates first to get accurate data
        df_clean = df.drop_duplicates(subset=['contract_id'], keep='first')
        
        # Always include portfolio overview
        total_contracts = len(df_clean)
        total_value = df_clean['total_value_usd'].sum()
        total_annual = df_clean['annual_commitment_usd'].sum()
        active_contracts = len(df_clean[df_clean['status'].str.contains('Active', na=False)])
        
        analysis.append(f"=== PORTFOLIO OVERVIEW ===")
        analysis.append(f"• Total Contracts: {total_contracts}")
        analysis.append(f"• Total Portfolio Value: ${total_value:,.0f}")
        analysis.append(f"• Total Annual Commitments: ${total_annual:,.0f}")
        analysis.append(f"• Active Contracts: {active_contracts}")
        analysis.append(f"• Average Contract Value: ${total_value/total_contracts:,.0f}")
        
        # Top Vendors Analysis
        if any(word in prompt_lower for word in ['vendor', 'supplier', 'counterparty', 'top', 'concentration']):
            vendor_analysis = df_clean.groupby('counterparty').agg({
                'total_value_usd': 'sum',
                'annual_commitment_usd': 'sum',
                'contract_id': 'count'
            }).sort_values('total_value_usd', ascending=False)
            
            analysis.append(f"\n=== TOP VENDORS ANALYSIS ===")
            for i, (vendor, data) in enumerate(vendor_analysis.head(5).iterrows()):
                pct = (data['total_value_usd'] / total_value) * 100
                analysis.append(f"• {i+1}. {vendor}: ${data['total_value_usd']:,.0f} ({pct:.1f}% of portfolio) - {data['contract_id']} contracts")
            
            # Concentration risk
            top_vendor_pct = (vendor_analysis.iloc[0]['total_value_usd'] / total_value) * 100
            if top_vendor_pct > 50:
                analysis.append(f"⚠️ HIGH CONCENTRATION RISK: Top vendor represents {top_vendor_pct:.1f}% of portfolio")
            elif top_vendor_pct > 30:
                analysis.append(f"⚠️ MODERATE CONCENTRATION RISK: Top vendor represents {top_vendor_pct:.1f}% of portfolio")
        
        # Contract Expiry Analysis
        if any(word in prompt_lower for word in ['expiring', 'renewal', 'expiry', 'timeline', '6 months', '2 years']):
            df_temp = df_clean.copy()
            df_temp['end_date'] = pd.to_datetime(df_temp['end_date'])
            df_temp['months_to_expiry'] = (df_temp['end_date'] - pd.Timestamp.now()).dt.days / 30
            
            # 6 months
            expiring_6m = df_temp[df_temp['months_to_expiry'] <= 6]
            # 2 years
            expiring_2y = df_temp[df_temp['months_to_expiry'] <= 24]
            
            analysis.append(f"\n=== CONTRACT EXPIRY ANALYSIS ===")
            analysis.append(f"• Expiring in 6 months: {len(expiring_6m)} contracts (${expiring_6m['annual_commitment_usd'].sum():,.0f} at risk)")
            analysis.append(f"• Expiring in 2 years: {len(expiring_2y)} contracts (${expiring_2y['annual_commitment_usd'].sum():,.0f} at risk)")
            
            if not expiring_6m.empty:
                analysis.append(f"• Critical Renewals Needed: {', '.join(expiring_6m['counterparty'].unique())}")
                analysis.append(f"• Contract IDs Expiring: {', '.join(expiring_6m['contract_id'].astype(str).unique())}")
        
        # Payment Terms Analysis
        if any(word in prompt_lower for word in ['payment', 'terms', 'unfavorable']):
            payment_terms = df_clean['payment_terms'].value_counts()
            unfavorable = df_clean[df_clean['payment_terms'].isin(['Net 60', 'Net 90', 'Milestone-based'])]
            
            analysis.append(f"\n=== PAYMENT TERMS ANALYSIS ===")
            for term, count in payment_terms.items():
                analysis.append(f"• {term}: {count} contracts")
            
            if not unfavorable.empty:
                analysis.append(f"⚠️ UNFAVORABLE TERMS RISK: {len(unfavorable)} contracts (${unfavorable['annual_commitment_usd'].sum():,.0f})")
                analysis.append(f"• Vendors with Unfavorable Terms: {', '.join(unfavorable['counterparty'].unique())}")
        
        # Risk Analysis
        if any(word in prompt_lower for word in ['penalty', 'sla', 'escalation', 'risk']):
            penalty_contracts = df_clean[df_clean['sla_penalty'].notna() & (df_clean['sla_penalty'] != '')]
            escalation_contracts = df_clean[df_clean['escalation'].notna() & (df_clean['escalation'] != 'None')]
            
            analysis.append(f"\n=== RISK ANALYSIS ===")
            analysis.append(f"• SLA Penalty Risk: {len(penalty_contracts)} contracts (${penalty_contracts['total_value_usd'].sum():,.0f})")
            analysis.append(f"• Escalation Risk: {len(escalation_contracts)} contracts (${escalation_contracts['annual_commitment_usd'].sum():,.0f})")
            
            if not penalty_contracts.empty:
                analysis.append(f"• Penalty Risk Vendors: {', '.join(penalty_contracts['counterparty'].unique())}")
            if not escalation_contracts.empty:
                analysis.append(f"• Escalation Risk Vendors: {', '.join(escalation_contracts['counterparty'].unique())}")
        
        # Specific Vendor Analysis (e.g., IBM)
        for vendor in ['IBM', 'Microsoft', 'Oracle', 'SAP', 'Salesforce', 'HCL', 'Infosys', 'Alpha']:
            if vendor.lower() in prompt_lower:
                vendor_contracts = df_clean[df_clean['counterparty'].str.contains(vendor, case=False, na=False)]
                if not vendor_contracts.empty:
                    analysis.append(f"\n=== {vendor.upper()} CONTRACTS DETAILED ANALYSIS ===")
                    analysis.append(f"• Contract Count: {len(vendor_contracts)}")
                    analysis.append(f"• Total Value: ${vendor_contracts['total_value_usd'].sum():,.0f}")
                    analysis.append(f"• Annual Commitment: ${vendor_contracts['annual_commitment_usd'].sum():,.0f}")
                    analysis.append(f"• Portfolio Share: {(vendor_contracts['total_value_usd'].sum() / total_value) * 100:.1f}%")
                    
                    # Timeline for this vendor
                    vendor_timeline = vendor_contracts[['contract_id', 'start_date', 'end_date', 'annual_commitment_usd', 'status']].copy()
                    vendor_timeline['start_date'] = pd.to_datetime(vendor_timeline['start_date'])
                    vendor_timeline['end_date'] = pd.to_datetime(vendor_timeline['end_date'])
                    vendor_timeline = vendor_timeline.sort_values('start_date')
                    
                    analysis.append(f"• Contract Timeline:")
                    for _, contract in vendor_timeline.iterrows():
                        analysis.append(f"  - {contract['contract_id']}: {contract['start_date'].strftime('%Y-%m')} to {contract['end_date'].strftime('%Y-%m')} (${contract['annual_commitment_usd']:,.0f}/yr) - {contract['status']}")
        
        # Contract Types
        if 'type' in df_clean.columns:
            contract_types = df_clean['type'].value_counts()
            analysis.append(f"\n=== CONTRACT TYPES BREAKDOWN ===")
            for ctype, count in contract_types.items():
                pct = (count / total_contracts) * 100
                analysis.append(f"• {ctype}: {count} contracts ({pct:.1f}%)")
        
        # Financial Summary
        analysis.append(f"\n=== FINANCIAL SUMMARY ===")
        analysis.append(f"• Total Portfolio Value: ${total_value:,.0f}")
        analysis.append(f"• Annual Commitments: ${total_annual:,.0f}")
        analysis.append(f"• Average Annual Commitment: ${total_annual/total_contracts:,.0f}")
        analysis.append(f"• Contract Value Range: ${df_clean['total_value_usd'].min():,.0f} - ${df_clean['total_value_usd'].max():,.0f}")
        
        return "\n".join(analysis)
    
    except Exception as e:
        return f"Error in CSV analysis: {str(e)}"

def build_combined_context(graph_context: str, csv_analysis: str, prompt: str) -> str:
    """Build combined context prioritizing CSV data (primary) + Graph context (insights)"""
    context_parts = []
    
    # PRIORITY 1: CSV Analysis (Primary Data Source)
    if csv_analysis and csv_analysis.strip():
        context_parts.append(f"PRIMARY DATA SOURCE - CONTRACT CSV ANALYSIS:\n{csv_analysis}")
    
    # PRIORITY 2: Graph Context (For Deeper Insights)
    if graph_context and graph_context.strip():
        context_parts.append(f"SECONDARY INSIGHTS - KNOWLEDGE GRAPH CONTEXT:\n{graph_context}")
    
    # Add direct analysis instructions
    context_parts.append("""
ANALYSIS INSTRUCTIONS:
- PRIORITIZE CSV DATA: Use exact numbers, dates, and contract details from the CSV analysis above
- BE DIRECT: Answer the specific question asked, no extra analysis unless requested
- FORMAT: Use bullet points (•) for clarity
- BE SPECIFIC: Include exact dollar amounts, contract counts, vendor names, and dates
- NO AUTO-RISK ASSESSMENT: Only provide risk/opportunity analysis when specifically asked
- FINANCIAL ACCURACY: All financial figures must be precise and properly formatted
""")
    
    return "\n\n".join(context_parts)

def generate_openai_response(prompt: str, context: str) -> str:
    """Generate CFO-level response using CSV data (priority) + Graph context for insights"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=openai.api_key)
        
        messages = [
            {
                "role": "system",
                "content": """You are a direct, efficient CFO contract analyst assistant. Provide straightforward answers based on contract data.

CRITICAL INSTRUCTIONS:
1. PRIORITIZE CSV DATA - Use exact numbers, dates, and contract details from CSV analysis.
2. BE DIRECT - Answer the specific question asked, no extra fluff.
3. FORMAT: Use bullet points (•) for clarity and easy scanning.
4. BE SPECIFIC: Include exact dollar amounts, contract counts, vendor names, and dates.
5. ONLY PROVIDE RISK/OPPORTUNITY ANALYSIS when explicitly asked about "risk", "opportunities", or "assessment".

RESPONSE STYLE:
• Straightforward answers to the question asked
• Use bullet points (•) for key findings
• Include exact financial figures ($X,XXX,XXX)
• Mention specific vendor names and contract IDs when relevant
• NO automatic risk assessments unless specifically requested
• NO strategic recommendations unless asked for

Focus on answering the specific question with accurate data from the CSV analysis."""
            },
            {
                "role": "user",
                "content": f"""CONTRACT DATA ANALYSIS (CSV - PRIMARY SOURCE):
{context}

QUESTION: {prompt}

Provide a direct answer with:
• Specific numbers and financial figures from the CSV data
• Exact contract details, vendor names, and dates
• Clear bullet points for easy reading

Answer only what was asked - be direct and specific."""
            }
        ]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1500,
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Error generating OpenAI response: {str(e)}. Please try again."

def generate_simple_csv_response(prompt: str, df: pd.DataFrame) -> str:
    """Simple fallback response using CSV data when OpenAI fails"""
    try:
        # Remove duplicates first
        df_clean = df.drop_duplicates(subset=['contract_id'], keep='first')
        prompt_lower = prompt.lower()
        
        if "total" in prompt_lower and "value" in prompt_lower:
            total_value = df_clean['total_value_usd'].sum()
            return f"Based on contract analysis, your total contract portfolio value is ${total_value:,.0f} across {len(df_clean)} contracts."
        
        elif "vendor" in prompt_lower and "top" in prompt_lower:
            vendor_analysis = df_clean.groupby('counterparty')['total_value_usd'].sum().sort_values(ascending=False)
            response = "Top vendors by contract value:\n"
            for i, (vendor, value) in enumerate(vendor_analysis.head(5).items()):
                response += f"{i+1}. {vendor}: ${value:,.0f}\n"
            return response
        
        elif "expiring" in prompt_lower and "6 months" in prompt_lower:
            df_temp = df_clean.copy()
            df_temp['end_date'] = pd.to_datetime(df_temp['end_date'])
            df_temp['months_to_expiry'] = (df_temp['end_date'] - pd.Timestamp.now()).dt.days / 30
            expiring_contracts = df_temp[df_temp['months_to_expiry'] <= 6]
            
            if not expiring_contracts.empty:
                return f"You have {len(expiring_contracts)} contracts expiring in the next 6 months: {', '.join(expiring_contracts['counterparty'].unique())}. Total value at risk: ${expiring_contracts['annual_commitment_usd'].sum():,.0f}."
            else:
                return "No contracts are expiring in the next 6 months."
        
        elif "ibm" in prompt_lower and "timeline" in prompt_lower:
            ibm_contracts = df_clean[df_clean['counterparty'].str.contains('IBM', case=False, na=False)]
            if not ibm_contracts.empty:
                response = f"IBM Contract Timeline:\n"
                for _, contract in ibm_contracts.iterrows():
                    response += f"- {contract['contract_id']}: {contract['start_date']} to {contract['end_date']} (${contract['annual_commitment_usd']:,.0f}/yr)\n"
                return response
            else:
                return "No IBM contracts found in the portfolio."
        
        elif "payment" in prompt_lower and "terms" in prompt_lower:
            unfavorable_terms = df_clean[df_clean['payment_terms'].isin(['Net 60', 'Net 90', 'Milestone-based'])]
            if not unfavorable_terms.empty:
                return f"Found {len(unfavorable_terms)} contracts with unfavorable payment terms (Net 60, Net 90, or Milestone-based). Total annual commitment at risk: ${unfavorable_terms['annual_commitment_usd'].sum():,.0f}."
            else:
                return "Great news! All your contracts have favorable payment terms."
        
        elif "penalty" in prompt_lower:
            penalty_contracts = df_clean[df_clean['sla_penalty'].notna() & (df_clean['sla_penalty'] != '')]
            return f"You have {len(penalty_contracts)} contracts with SLA penalty clauses, representing ${penalty_contracts['total_value_usd'].sum():,.0f} in total contract value at risk."
        
        else:
            return f"Based on analysis of your {len(df_clean)} contracts, I can provide insights about payment terms, renewals, vendor relationships, SLA requirements, and financial metrics. Please ask a more specific question."
    
    except Exception as e:
        return f"Error in simple analysis: {str(e)}. Please try a different question."


def load_contract_insights():
    """Load contract extraction insights from JSONL file"""
    try:
        # Check parent directory where the file is located
        insights_file = "../cfo_contract_insights.jsonl"
        
        if os.path.exists(insights_file):
            insights = []
            with open(insights_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        insights.append(json.loads(line))
            return insights
        return []
    except Exception as e:
        return []
