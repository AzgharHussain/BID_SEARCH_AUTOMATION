import asyncio
import os
import argparse
from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from app.db.database import SessionLocal
from app.models import models

def get_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set. Agent will fail if LLM is invoked.")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        google_api_key=SecretStr(api_key) if api_key else None
    )

async def scrape_portal(state_name, portal_url, keyword):
    print(f"\n🚀 Starting AI Agent for {state_name} - Keyword: '{keyword}'")
    
    task_prompt = f"""
    You are an intelligent procurement assistant.
    1. Navigate to the {state_name} e-procurement portal: {portal_url}
    2. Look for a 'Search' or 'Tenders by Keyword' option. 
    3. Type the keyword '{keyword}' into the search box and submit. If there is a captcha, carefully read the image and type it.
    4. Once the search results load, look for the first valid tender link and click it to open details.
    5. In the details page, find the documents section (PDFs or ZIPs) and click to download them.
    6. Stop after successfully downloading the documents for the first result, or if no results are found.
    """
    
    llm = get_llm()
    agent = Agent(
        task=task_prompt,
        llm=llm
    )
    
    try:
        result = await agent.run()
        print(f"✅ Completed task for {state_name}:")
        print(result)
    except Exception as e:
        print(f"❌ Failed to run agent for {state_name}: {e}")

async def main():
    parser = argparse.ArgumentParser(description="AI Agent for State Portals")
    parser.add_argument("--state", type=str, help="Specific state to scrape")
    parser.add_argument("--keyword", type=str, help="Specific keyword to use")
    parser.add_argument("--all", action="store_true", help="Run for all states and keywords in DB")
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    if args.all:
        states = db.query(models.State).all()
        keywords = db.query(models.Keyword).filter(models.Keyword.is_active == True).all()
        
        for state in states:
            for kw in keywords:
                # Assuming the portal URL exists
                url = getattr(state, 'portal_url', None) or "https://eprocure.gov.in/eprocure/app"
                await scrape_portal(state.name, url, kw.keyword)
                
    elif args.state and args.keyword:
        state_record = db.query(models.State).filter(models.State.name == args.state).first()
        url = state_record.portal_url if state_record and state_record.portal_url else "https://eprocure.gov.in/eprocure/app"
        await scrape_portal(args.state, url, args.keyword)
        
    else:
        print("Please provide --state and --keyword, or use --all")

if __name__ == "__main__":
    asyncio.run(main())
