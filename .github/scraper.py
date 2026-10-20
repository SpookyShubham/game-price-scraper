import httpx, json, time, os
from bs4 import BeautifulSoup
from datetime import datetime, timezone

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE44_API = "https://api.base44.com/v1/apps/{app_id}/tables/prices/records"

def push_to_base44(records: list[dict]):
    app_id = os.environ["BASE44_APP_ID"]
    api_key = os.environ["BASE44_API_KEY"]
    url = BASE44_API.format(app_id=app_id)
    for r in records:
        resp = httpx.post(url, json=r, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        if resp.status_code != 200:
            print(f"  WARN: {resp.status_code} - {resp.text[:100]}")

def scrape_site(url, parse_fn):
    resp = httpx.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    return parse_fn(soup)

def parse_gameloot(soup):
    results = []
    for card in soup.select(".product_item"):
        name_el = card.select_one(".product_details h5")
        price_el = card.select_one(".product_price")
        link = card.select_one("a")
        if not (name_el and price_el):
            continue
        name_text = name_el.get_text(strip=True)
        results.append({
            "product_name": name_text,
            "site": "gameloot",
            "listing_type": "buy" if "buy" in name_text.lower() else "sell",
            "price": price_el.get_text(strip=True),
            "url": link["href"] if link and "href" in link.attrs else "",
            "scraped_at": datetime.now(timezone.utc).isoformat()
        })
    return results

def main():
    products = json.load(open("products.json"))
    all_records = []
    for p in products:
        print(f"Scraping: {p['name']} ({p['platform']})")
        try:
            results = scrape_site(p["search_url"], parse_gameloot)
            all_records.extend(results)
            print(f"  Found {len(results)} listings")
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(2)

    push_to_base44(all_records)
    print(f"Done. Pushed {len(all_records)} records to Base44")

if __name__ == "__main__":
    main()   
