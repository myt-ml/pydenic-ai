import os
import asyncio
import gradio as gr
from dotenv import load_dotenv
from research_agent import run_deep_research, FinalReport

# Load environment variables from .env file if present
load_dotenv()

# Check for API Key
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in environment variables or .env file.")
if not os.getenv("TAVILY_API_KEY"):
    print("Warning: TAVILY_API_KEY not found in environment variables or .env file.")

def format_report_markdown(report: FinalReport) -> str:
    """Converts the structured FinalReport into a Markdown string."""
    md = f"# Executive Summary\n\n{report.executive_summary}\n\n"
    
    for section in report.sections:
        md += f"## {section.title}\n\n"
        
        if section.key_findings:
            md += "### Key Findings\n"
            for item in section.key_findings:
                md += f"- {item}\n"
            md += "\n"
            
        if section.evidence:
             md += "### Evidence & Sources\n"
             for item in section.evidence:
                 md += f"> {item}\n"
             md += "\n"
             
        if section.risks:
            md += "### Risks & Uncertainties\n"
            for item in section.risks:
                md += f"- {item}\n"
            md += "\n"
            
    md += f"# Future Outlook\n\n{report.future_outlook}"
    return md

async def process_query(message, history):
    """
    Gradio callback.
    """
    if not message.strip():
        return history, ""
    
    # Initialize history if None
    if history is None:
        history = []
        
    # Append User Message
    history.append({"role": "user", "content": message})
    
    try:
        # Run research
        report = await run_deep_research(message)
        response_text = format_report_markdown(report)
        
        # Append Assistant Message
        history.append({"role": "assistant", "content": response_text})
        return history, "" # Return updated history and clear textbox
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"An error occurred: {str(e)}"
        
        # Append Error Message
        history.append({"role": "assistant", "content": error_msg})
        return history, ""

# Custom CSS for a cleaner look
custom_css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
#chatbot {
    height: 700px !important;
    overflow-y: auto;
}
"""

with gr.Blocks(title="Deep Research Agent") as demo:
    gr.Markdown("# 🕵️‍♀️ Deep Research Agent")
    gr.Markdown(
        "Enter a **stock ticker** (e.g., `NVDA`, `TSLA`) or a **topic** (e.g., `Future of AI Agents`) "
        "to generate a comprehensive deep-dive report."
    )
    
    # Gradio 6.x default format expects {"role": "...", "content": "..."}
    # We do NOT pass type="messages" as it causes a TypeError in this version
    chatbot = gr.Chatbot(label="Research Report", height=700)
    msg = gr.Textbox(label="Query", placeholder="Type a ticker or topic here...")
    
    # Pass history to function, return updated history and clear message
    msg.submit(process_query, [msg, chatbot], [chatbot, msg])

if __name__ == "__main__":
    # Theme and CSS moved to launch() as per Gradio 6.0 warning
    demo.launch(theme=gr.themes.Soft(), css=custom_css)
