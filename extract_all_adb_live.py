import asyncio
import re
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import pytz
from playwright.async_api import async_playwright

MANILA_TZ = pytz.timezone("Asia/Manila")
IST_TZ = pytz.timezone("Asia/Kolkata")

COUNTRY_ISO_MAP = {
    "IND": "India",
    "PAK": "Pakistan",
    "CAM": "Cambodia",
    "PRC": "China",
    "TAJ": "Tajikistan",
    "BHU": "Bhutan",
    "AZE": "Azerbaijan",
    "FIJ": "Fiji",
    "GEO": "Georgia",
    "KGZ": "Kyrgyz Republic",
    "PHI": "Philippines",
    "REG": "Regional",
    "UZB": "Uzbekistan",
    "BAN": "Bangladesh",
    "NEP": "Nepal",
    "VIE": "Vietnam",
    "SRI": "Sri Lanka",
    "MON": "Mongolia",
    "LAO": "Lao PDR",
    "MYA": "Myanmar",
    "ARM": "Armenia",
    "KAZ": "Kazakhstan",
    "MAL": "Maldives",
    "TIM": "Timor-Leste",
    "PNG": "Papua New Guinea",
    "SOL": "Solomon Islands",
    "VAN": "Vanuatu",
    "SAM": "Samoa",
    "TON": "Tonga",
    "FSM": "Micronesia",
    "RMI": "Marshall Islands",
    "PAL": "Palau",
    "KIR": "Kiribati",
    "TKM": "Turkmenistan",
    "AFG": "Afghanistan",
    "INA": "Indonesia",
    "THA": "Thailand",
    "MAL": "Malaysia"
}

def parse_deadline(deadline_str):
    if not deadline_str:
        return None
    try:
        clean = deadline_str.replace("Manila local time", "").replace("Manila", "").strip()
        for fmt in ("%d-%b-%Y %I:%M %p", "%d-%b-%Y %H:%M", "%d-%b-%Y"):
            try:
                dt_naive = datetime.strptime(clean, fmt)
                dt_manila = MANILA_TZ.localize(dt_naive)
                return dt_manila.astimezone(IST_TZ).replace(tzinfo=None)
            except ValueError:
                continue
    except Exception:
        pass
    return None

def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def resolve_country_and_pkg(title):
    # Match patterns like "TA-10850 AZE:", "LOAN-4553 CAM:", "GRANT E-060009-001 PAK:", etc.
    country = "Regional"
    package = ""
    project = ""
    
    # Try finding 3-letter uppercase country code followed by colon or space
    iso_match = re.search(r'\b([A-Z]{3}):', title)
    if iso_match:
        code = iso_match.group(1)
        if code in COUNTRY_ISO_MAP:
            country = COUNTRY_ISO_MAP[code]
    else:
        # Check title text for country names directly
        for code, name in COUNTRY_ISO_MAP.items():
            if name.lower() in title.lower():
                country = name
                break

    # Extract loan/grant/TA number
    proj_match = re.search(r'((?:LOAN|GRANT|TA|RETA)[\s\-]*(?:\d+|E\-\d+\-\d+))', title, re.IGNORECASE)
    if proj_match:
        project = proj_match.group(1).strip()

    # Extract package code if present like CS-01, LA-CS01, PR/ML-1/Cons-1, etc.
    pkg_match = re.search(r'[\-\s]([A-Z0-9\/\-]{2,20}\-(?:CS\d+|Cons\d+|[A-Z0-9]+))', title)
    if pkg_match:
        package = pkg_match.group(1).strip()
    elif project:
        package = f"PKG-{project}"
    else:
        package = "PKG-ADB-" + str(abs(hash(title)) % 100000)

    return country, package, project

async def scrape_all_csrn_opportunities():
    opportunities = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Navigating to ADB CSRN portal: https://selfservice.adb.org/OA_HTML/adb/xxcrs/jsp/Csrn.jsp")
        await page.goto("https://selfservice.adb.org/OA_HTML/adb/xxcrs/jsp/Csrn.jsp", wait_until="networkidle", timeout=60000)
        
        page_num = 1
        while True:
            await page.wait_for_selector('a[id*="imgCsrn:0"]', timeout=30000)
            
            # Extract rows from table
            rows_data = await page.evaluate('''() => {
                const trs = document.querySelectorAll('table[id*="Results"] tr, table[id*="results"] tr, table[class*="OraTable"] tr');
                const results = [];
                for (const tr of trs) {
                    const viewLink = tr.querySelector('a[id*="imgCsrn:"]');
                    if (!viewLink) continue;
                    const tds = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                    results.push({
                        viewId: viewLink.id,
                        cells: tds
                    });
                }
                return results;
            }''')
            
            print(f"Page {page_num}: Extracted {len(rows_data)} opportunity rows")
            
            for item in rows_data:
                cells = item['cells']
                # Finding the title cell (usually the longest or cell index 1)
                title = ""
                sector = ""
                c_type = "Firm"
                months = "12"
                pub_date_str = ""
                deadline_str = ""
                
                # Cells typically: [View, Title, Sector, Type, Months, PubDate, Deadline]
                for c in cells:
                    if len(c) > 25 and not title:
                        title = c
                    elif any(s in c for s in ["Firm", "Individual"]):
                        c_type = "Individual" if "Individual" in c else "Firm"
                    elif re.search(r'\d{1,2}\-[A-Za-z]{3}\-\d{4}\s+\d{1,2}:\d{2}', c):
                        deadline_str = c
                    elif re.search(r'^\d{1,2}\-[A-Za-z]{3}\-\d{4}$', c):
                        pub_date_str = c
                    elif c.isdigit() and int(c) < 120 and not months:
                        months = c
                    elif len(c) > 3 and not sector and c != title and not any(s in c for s in ["Firm", "Individual"]):
                        sector = c

                if not title and len(cells) > 1:
                    title = cells[1]
                if not sector and len(cells) > 2:
                    sector = cells[2]
                if not deadline_str:
                    for c in reversed(cells):
                        if any(m in c for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                            deadline_str = c
                            break

                country, package, project = resolve_country_and_pkg(title)
                
                opp = {
                    "view_id": item['viewId'],
                    "title": title,
                    "sector": sector or "Engineering & Technical Consulting",
                    "consultant_type": c_type,
                    "duration_months": months,
                    "published_date_str": pub_date_str,
                    "deadline_str": deadline_str,
                    "country": country,
                    "package_number": package,
                    "project_number": project,
                    "page": page_num
                }
                opportunities.append(opp)
            
            # Check for Next 25 link
            next_links = page.locator('a:has-text("Next 25")')
            if await next_links.count() > 0:
                first_next = next_links.first
                await first_next.click()
                await page.wait_for_load_state("networkidle", timeout=45000)
                page_num += 1
            else:
                print(f"Reached final page. Total pages traversed: {page_num}")
                break
                
        await browser.close()
        
    print(f"Total opportunities extracted across all pages: {len(opportunities)}")
    with open("all_adb_scraped.json", "w") as f:
        json.dump(opportunities, f, indent=2)
    return opportunities

if __name__ == "__main__":
    asyncio.run(scrape_all_csrn_opportunities())
