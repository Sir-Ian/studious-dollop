import requests
from urllib.parse import quote_plus


def fetch_greenhouse(slug: str) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{quote_plus(slug)}/jobs?content=true"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    jobs = []
    for j in resp.json().get("jobs", []):
        jobs.append({
            "id": str(j["id"]),
            "board": "greenhouse",
            "company": slug,
            "title": j["title"],
            "location": j.get("location", {}).get("name"),
            "url": j.get("absolute_url"),
            "content": j.get("content", ""),
            "pay_ranges": j.get("pay_input_ranges", []),
            "updated_at": j.get("updated_at"),
        })
    return jobs


def fetch_lever(slug: str) -> list:
    url = f"https://jobs.lever.co/{quote_plus(slug)}?format=json"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    jobs = []
    for j in resp.json():
        jobs.append({
            "id": j.get("id"),
            "board": "lever",
            "company": slug,
            "title": j.get("text"),
            "location": j.get("categories", {}).get("location"),
            "url": j.get("hostedUrl"),
            "content": j.get("description", ""),
            "pay_ranges": j.get("workplaceType"),
            "updated_at": j.get("updatedAt"),
        })
    return jobs


def fetch_ashby(slug: str) -> list:
    url = f"https://jobs.ashbyhq.com/{quote_plus(slug)}?format=json"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    postings = data.get("jobs", data)
    jobs = []
    for j in postings:
        jobs.append({
            "id": j.get("id"),
            "board": "ashby",
            "company": slug,
            "title": j.get("title"),
            "location": j.get("location"),
            "url": j.get("url"),
            "content": j.get("description", ""),
            "pay_ranges": j.get("pay_range"),
            "updated_at": j.get("updated_at"),
        })
    return jobs
