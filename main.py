"""
CFO Contract Analytics Studio - Main Entry Point
Enhanced GraphRAG system with CFO-focused contract analysis
"""

import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from typing import Tuple

import config
import utils
import extraction
import graph
import cfo_analytics
import export
import clustering
import visualization
import vector
# import chat
# import ui

def initialize_system():
    """Initialize the CFO analytics system"""
    config.initialize_globals()
    print("✅ CFO Contract Analytics Studio initialized")

def main():
    """Main entry point"""
    initialize_system()
    
    print("CFO Contract Analytics Studio")
    print("=============================")
    print("Starting enhanced GraphRAG system for CFO contract analysis...")
    print(f"OpenAI API: {'✅ Configured' if config.OPENAI_API_KEY else '❌ Missing'}")
    print(f"PDF Support: {'✅ Available' if config.PDF_AVAILABLE else '❌ Missing'}")
    print(f"DOCX Support: {'✅ Available' if config.DOCX_AVAILABLE else '❌ Missing'}")
    print(f"RDF Support: {'✅ Available' if config.RDFLIB_AVAILABLE else '❌ Missing'}")
    print(f"Vector Search: {'✅ Available' if config.LLAMA_AVAILABLE else '❌ Missing'}")
    print("")
    print("Modules loaded:")
    print("- CFO Analytics Framework")
    print("- Enhanced Entity Extraction")
    print("- Risk Assessment Engine") 
    print("- Compliance Analysis")
    print("- Executive Dashboard Export")
    print("")
    print("Run 'streamlit run frontend/cfo_dashboard.py' for the CFO Dashboard")
    
    # Launch the Gradio interface (simplified)
    try:
        with gr.Blocks(title="CFO Contract Analytics Studio") as demo:
            gr.Markdown("## CFO Contract Analytics Studio")
            gr.Markdown("Enhanced contract analysis with CFO-focused insights")
            
            with gr.Row():
                file_input = gr.Files(label="Upload Contract Documents", file_types=[".pdf", ".docx", ".txt"])
                
            run_button = gr.Button("🚀 Analyze Contracts")
            
            status_output = gr.Textbox(label="Analysis Status", interactive=False)
            
            with gr.Row():
                kpi_output = gr.Textbox(label="Key Financial Metrics", interactive=False)
                risk_output = gr.Textbox(label="Risk Assessment", interactive=False)
            
            export_button = gr.Button("📊 Export CFO Reports")
            export_files = gr.Files(label="Exported Files", interactive=False)
            
            # Simple processing function
            def process_simple(upload_paths):
                if not upload_paths:
                    return "Please upload contract files", "", "", [], "error"
                
                try:
                    # Process files
                    allowed_exts = utils.normalize_types(["PDF", "Word", "Text"])
                    corpus_pairs = []
                    
                    for path in upload_paths:
                        txt = utils.read_one_file(str(path))
                        if txt.strip():
                            corpus_pairs.append((str(path), txt))
                    
                    if not corpus_pairs:
                        return "No extractable text found", "", "", [], "warning"
                    
                    # Build graph
                    config.G = nx.DiGraph()
                    total_triples = 0
                    
                    for src, txt in corpus_pairs:
                        extracted = extraction.extract_entities_relations(txt)
                        total_triples += len(extracted)
                        graph.build_graph(extracted, source=src)
                    
                    # Analyze
                    if config.G.number_of_nodes() == 0:
                        return "No relationships extracted - try with more detailed contracts", "", "", [], "warning"
                    
                    # Detect communities
                    config.G, config.PARTITION = graph.detect_communities(config.G)
                    
                    # Generate CFO insights
                    financial_metrics = cfo_analytics.extract_financial_metrics_from_graph(config.G)
                    risk_assessment = cfo_analytics.assess_contract_risks(config.G, config.PARTITION)
                    
                    # Risk insights
                    risk_text = f"""🔍 Risk Assessment:
- Contract Concentration: {risk_assessment.get('concentration_risk', {}).get('level', 'Unknown')}
- Dependency Risk: {len(risk_assessment.get('dependency_risk', {}).get('contracts_with_one_vendor', []))} single-vendor contracts
- Compliance Coverage: {len([k for k, v in risk_assessment.get('compliance_gaps', {}).get('low_coverage_standards', {}).items() if v < 0.3])} gaps"""
                    
                    # KPI insights
                    kpi_text = f"""💰 Financial Overview:
- Total Contracts: {financial_metrics.get('total_contracts', 0)}
- Relationship Network: {financial_metrics.get('total_relationships', 0)}
- Network Density: {financial_metrics.get('avg_connections_per_contract', 0):.2f}
- Vendor Relationships: {financial_metrics.get('vendor_relationships', 0)}"""
                    
                    status = f"✅ Analysis complete: {financial_metrics.get('total_contracts', 0)} contracts analyzed"
                    
                    return status, kpi_text, risk_text, [], "success"
                    
                except Exception as e:
                    return f"❌ Analysis error: {str(e)}", "", "", [], "error"
            
            def export_cfo_data():
                if not config.G or config.G.number_of_nodes() == 0:
                    return []
                
                try:
                    # Export comprehensive CFO reports
                    file_paths = export.export_all_cfo_formats()
                    
                    # Return actual file paths for Gradio
                    result_files = []
                    for ftype, path in file_paths.items():
                        if path and os.path.exists(path):
                            result_files.append(path)
                    
                    return result_files
                    
                except Exception as e:
                    print(f"Export error: {e}")
                    return []
            
            # Wire up functions
            run_button.click(
                fn=process_simple,
                inputs=[file_input],
                outputs=[status_output, kpi_output, risk_output, export_files, gr.State()]
            )
            
            export_button.click(
                fn=export_cfo_data,
                inputs=[],
                outputs=[export_files]
            )
        
        demo.launch(share=True, show_api=False)
        
    except Exception as e:
        print(f"Interface error: {e}")
        print("You can still use the Streamlit dashboard at:")
        print("streamlit run frontend/cfo_dashboard.py")

if __name__ == "__main__":
    main()





