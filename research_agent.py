import asyncio
import os
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from tavily import TavilyClient

# --- Models ---

class ResearchInput(BaseModel):
    query: str = Field(description="The user's search query or ticker symbol.")

class TopicResolution(BaseModel):
    is_ticker: bool = Field(description="True if the input is a stock ticker symbol.")
    company_name: Optional[str] = Field(description="The full company name if a ticker was provided.")
    context: str = Field(description="A brief sentence describing what the topic is.")

class ResearchAngle(BaseModel):
    title: str = Field(description="Title of the research angle (e.g., 'SWOT Analysis', 'Financial Performance').")
    keywords: List[str] = Field(description="Specific keywords to use for searching this angle.")
    description: str = Field(description="Brief description of what to look for.")

class AnglePlan(BaseModel):
    angles: List[ResearchAngle] = Field(description="List of 3-4 distinct research angles.")

class SearchResult(BaseModel):
    source_url: str
    title: str
    content: str

class SectionReport(BaseModel):
    title: str = Field(description="Title of this section.")
    key_findings: List[str] = Field(description="Bulleted list of key facts found.")
    evidence: List[str] = Field(description="Quotes or data points supporting the findings.")
    risks: Optional[List[str]] = Field(description="Risks or uncertainties identified in this area.")

class FinalReport(BaseModel):
    executive_summary: str = Field(description="High-level summary of the entire report.")
    sections: List[SectionReport] = Field(description="Detailed sections for each research angle.")
    future_outlook: str = Field(description="Forward-looking statement on what to watch next.")

# --- Dependencies ---

class ResearchDeps:
    def __init__(self, tavily_api_key: str):
        self.tavily_client = TavilyClient(api_key=tavily_api_key)

# --- Agents ---

# 1. Resolution Agent
resolution_agent = Agent(
    'openai:gpt-4o-mini',
    output_type=TopicResolution,
    system_prompt="You are an expert at identifying search topics. Determine if the input is a stock ticker or a general query. If it's a ticker, resolve it to the full company name."
)

# 2. Planning Agent
planning_agent = Agent(
    'openai:gpt-4o-mini',
    output_type=AnglePlan,
    system_prompt="You are a research strategist. Given a topic and some initial context, generate 3-4 distinct research angles (e.g., SWOT, Competitors, Financials) to investigate deep aspects of the topic. Ensure keywords are specific."
)

# 3. Deep Dive Agent (uses tools)
search_agent = Agent(
    'openai:gpt-4o-mini',
    deps_type=ResearchDeps,
    system_prompt="You are a deep researcher. Use the compiled research results to extract key findings for a specific angle."
)

# 4. Synthesis Agent
synthesis_agent = Agent(
    'openai:gpt-4o', # Stronger model for writing
    output_type=FinalReport,
    system_prompt="You are a senior analyst. Synthesize all the provided research notes into a cohesive, professional report. Cite sources where possible in the evidence."
)

# 5. Validator Agent
validator_agent = Agent(
    'openai:gpt-4o',
    output_type=FinalReport,
    system_prompt="You are a Fact-Checking Auditor. Review the provided report for logical inconsistencies, potential hallucinations, or outdated info relative to the current date. deeply check the report for any misinformation or fake news. If you find any, correct it. Ensure the final output is in the requested language."
)

# --- Tools ---

async def tavily_search(tavily_client: TavilyClient, query: str) -> List[SearchResult]:
    """Helper to perform a Tavily search."""
    try:
        # qna_search often gives good concise answers, but 'search' with 'include_raw_content' is better for deep dive.
        # We will use the 'search' method and extract results.
        response = tavily_client.search(query=query, search_depth="advanced", max_results=3)
        results = []
        for res in response.get("results", []):
            results.append(SearchResult(
                source_url=res.get("url", ""),
                title=res.get("title", ""),
                content=res.get("content", "")
            ))
        return results
    except Exception as e:
        print(f"Search error for {query}: {e}")
        return []

# --- Workflow Logic ---

async def run_deep_research(user_query: str, language: str = "English") -> FinalReport:
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        raise ValueError("TAVILY_API_KEY not found in environment")
    
    deps = ResearchDeps(tavily_api_key=tavily_key)
    current_date = datetime.now().strftime("%Y-%m-%d")
    print(f"Starting research. Date: {current_date}, Language: {language}")

    # Step 1: Resolve Topic
    print(f"Resolving topic for: {user_query}")
    print(f"Resolving topic for: {user_query}")
    res_result = await resolution_agent.run(f"Current Date: {current_date}\nQuery: {user_query}")
    topic_res = res_result.output
    
    search_subject = topic_res.company_name if topic_res.is_ticker and topic_res.company_name else user_query
    print(f"Resolved subject: {search_subject}")

    # Step 2: Initial Discovery Search
    print("Running discovery search...")
    discovery_results = await tavily_search(deps.tavily_client, f"{search_subject} overview news")
    discovery_context = "\n".join([f"{r.title}: {r.content}" for r in discovery_results])

    # Step 3: Plan Research Angles
    print("Planning research angles...")
    plan_result = await planning_agent.run(
        f"Current Date: {current_date}\nSubject: {search_subject}\nContext: {topic_res.context}\nInitial Findings: {discovery_context}"
    )
    angle_plan = plan_result.output
    print(f"Angles generated: {[a.title for a in angle_plan.angles]}")

    # Step 4: Deep Dive (Parallel Execution)
    print("Executing deep dives...")
    
    # We will gather raw data for each angle
    angle_data_map = {}

    async def process_angle(angle: ResearchAngle):
        # Construct a targeted query
        query = f"{search_subject} {angle.keywords[0]} {' '.join(angle.keywords[1:])}"
        results = await tavily_search(deps.tavily_client, query)
        content = "\n\n".join([f"Source: {r.title} ({r.source_url})\nContent: {r.content}" for r in results])
        return angle.title, content

    # Run searches in parallel
    tasks = [process_angle(angle) for angle in angle_plan.angles]
    angle_results = await asyncio.gather(*tasks)
    
    for title, content in angle_results:
        angle_data_map[title] = content

    # Step 5: Synthesize Report
    print("Synthesizing final report...")
    
    # Construct a big prompt context with all the data
    # Construct a big prompt context with all the data
    synthesis_input = f"Report Subject: {search_subject}\nTarget Language: {language}\nCurrent Date: {current_date}\n\n"
    for title, content in angle_data_map.items():
        synthesis_input += f"## Research Angle: {title}\n{content}\n\n{'-'*20}\n"

    final_result = await synthesis_agent.run(synthesis_input)
    final_result = await synthesis_agent.run(synthesis_input)
    
    # Step 6: Validation
    print("Validating report...")
    validation_input = f"Original Query: {user_query}\nTarget Language: {language}\nCurrent Date: {current_date}\n\nDraft Report:\n{final_result.output}"
    validated_result = await validator_agent.run(validation_input)
    
    return validated_result.output
