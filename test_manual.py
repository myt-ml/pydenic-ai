import asyncio
import os
from dotenv import load_dotenv
from research_agent import run_deep_research

load_dotenv()

async def main():
    print("Testing Deep Research Agent...")
    try:
        report = await run_deep_research("NVDA")
        print("\n" + "="*50 + "\n")
        print("FINAL REPORT GENERATED")
        print("="*50 + "\n")
        print(f"Summary Start: {report.executive_summary[:100]}...")
        print(f"Sections: {len(report.sections)}")
        for sec in report.sections:
            print(f" - {sec.title}: {len(sec.key_findings)} findings")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
