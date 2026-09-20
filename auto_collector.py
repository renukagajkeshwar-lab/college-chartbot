import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin

# =====================================================
# PRPCEM OFFICIAL DATA COLLECTOR
# =====================================================

BASE_URL = "https://prpotepatilengg.ac.in"

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "official_data.json"
)


def get_page(url):
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()
        return response.text

    except Exception as e:
        print("Error:", e)
        return None


def clean_text(text):
    return " ".join(text.split())


def collect_page(url):
    html = get_page(url)

    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Remove unnecessary elements
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.string if soup.title else ""

    paragraphs = []

    for element in soup.find_all(
        ["h1", "h2", "h3", "h4", "p", "li"]
    ):
        text = clean_text(element.get_text(" ", strip=True))

        if text and len(text) > 2:
            paragraphs.append(text)

    links = []

    for link in soup.find_all("a", href=True):

        href = link.get("href")

        full_url = urljoin(url, href)

        if full_url.startswith(BASE_URL):
            links.append(full_url)

    return {
        "url": url,
        "title": clean_text(title),
        "content": paragraphs,
        "links": list(set(links))
    }


def save_data(data):

    os.makedirs(
        os.path.dirname(DATA_FILE),
        exist_ok=True
    )

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n================================")
    print(" DATA SAVED SUCCESSFULLY")
    print("================================")
    print(DATA_FILE)


def main():

    print("\n========================================")
    print("🤖 PRPCEM AI DATA COLLECTOR")
    print("========================================")

    print("\n🌐 Connecting to official website...")

    home = collect_page(BASE_URL)

    if not home:
        print("❌ Could not connect to website.")
        return

    print("✅ Website connected!")

    collected_data = {
        "source": BASE_URL,
        "website": "P. R. Pote Patil College of Engineering & Management",
        "pages": []
    }

    collected_data["pages"].append(home)

    # URLs discovered from homepage
    urls = home["links"]

    # Limit first run so it doesn't crawl hundreds of pages
    urls = urls[:30]

    print("\n🔎 Collecting official pages...\n")

    for index, url in enumerate(urls, start=1):

        print(
            f"[{index}/{len(urls)}] {url}"
        )

        page = collect_page(url)

        if page:
            collected_data["pages"].append(page)

    save_data(collected_data)

    print("\n========================================")
    print("🎉 COLLECTION COMPLETE")
    print("========================================")

    print(
        f"Pages collected: "
        f"{len(collected_data['pages'])}"
    )


if __name__ == "__main__":
    main()