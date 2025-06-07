import os, json, sqlite3, time
from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from slack_sdk.webhook import WebhookClient
from apscheduler.schedulers.blocking import BlockingScheduler
from tqdm import tqdm

load_dotenv()

DB_PATH        = "jobs.db"
KEYWORDS       = [k.strip().lower() for k in os.getenv("KEYWORDS").split(",")]
MIN_SALARY     = int(os.getenv("MIN_SALARY", 150000))
COMPANIES      = [c.strip() for c in os.getenv("COMPANIES").split(",")]
SLACK_WEBHOOK  = os.getenv("SLACK_WEBHOOK")

# -------- helpers ----------------------------------------------------------

def gh_endpoint(slug: str) -> str:
    # Greenhouse Job Board API: public JSON – no auth needed ◆ docs :contentReference[oaicite:0]{index=0}
    return f"https://boards-api.greenhouse.io/v1/boards/{quote_plus(slug)}/jobs?content=true"

def matches(job: dict) -> bool:
    haystack = f"{job['title']} {job.get('content','')}".lower()
    return any(k in haystack for k in KEYWORDS)

def parse_salary(job: dict):
    ranges = job.get("pay_input_ranges") or []
    if not ranges:
        return None, None
    floor = min(r["min_cents"] for r in ranges) // 100
    ceil  = max(r["max_cents"] for r in ranges) // 100
    return floor, ceil

def notify(job):
    if not SLACK_WEBHOOK:
        return
    text = (f"*{job['title']}* @ {job['company']}  \n"
            f"{job['location']} | ${job['salary_floor']:,}–${job['salary_ceil']:,}  \n"
            f"<{job['abs_url']}|Apply ➜>")
    WebhookClient(SLACK_WEBHOOK).send(text=text)

# -------- core -------------------------------------------------------------

def crawl_once():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(open("schema.sql").read())

    for company in tqdm(COMPANIES, desc="Companies"):
        try:
            resp = requests.get(gh_endpoint(company), timeout=20)
            resp.raise_for_status()
            jobs = resp.json().get("jobs", [])
        except Exception as e:
            print(f"[WARN] {company}: {e}")
            continue

        for j in jobs:
            if not matches(j):
                continue
            floor, ceil = parse_salary(j)
            if floor and floor < MIN_SALARY:
                continue        # under your target

            # insert if new
            with conn:
                cur = conn.execute(
                    "SELECT 1 FROM jobs WHERE id=?",
                    (j["id"],)
                )
                if cur.fetchone():
                    continue

                conn.execute("""
                    INSERT INTO jobs (id, company, title, location, abs_url,
                                      salary_floor, salary_ceil, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    j["id"], company, j["title"],
                    j["location"]["name"],
                    j["absolute_url"],
                    floor, ceil,
                    j["updated_at"]
                ))
            j.update(company=company, salary_floor=floor, salary_ceil=ceil)
            notify(j)

    conn.close()

# -------- schedule nightly at 9 PM central --------------------------------
if __name__ == "__main__":
    crawl_once()  # fire immediately

    sched = BlockingScheduler(timezone="America/Chicago")
    sched.add_job(crawl_once, "cron", hour=21, minute=0)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass
