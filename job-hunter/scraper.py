import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from slack_sdk.webhook import WebhookClient
from tqdm import tqdm

from fetchers import fetch_greenhouse, fetch_lever, fetch_ashby
from similarity import embed_text, cosine_similarity

load_dotenv()

DB_PATH = "jobs.db"
KEYWORDS = [k.strip().lower() for k in os.getenv("KEYWORDS", "").split(",") if k.strip()]
MIN_SALARY = int(os.getenv("MIN_SALARY", 150000))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.75))
GREENHOUSE_SLUGS = [c.strip() for c in os.getenv("GREENHOUSE_SLUGS", "").split(",") if c.strip()]
LEVER_SLUGS = [c.strip() for c in os.getenv("LEVER_SLUGS", "").split(",") if c.strip()]
ASHBY_SLUGS = [c.strip() for c in os.getenv("ASHBY_SLUGS", "").split(",") if c.strip()]
RESUME_FILE = os.getenv("RESUME_FILE", "resume.txt")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

RESUME_EMB = embed_text(open(RESUME_FILE).read()) if os.path.exists(RESUME_FILE) else None


def keyword_match(job: dict) -> bool:
    if not KEYWORDS:
        return True
    haystack = f"{job['title']} {job.get('content', '')}".lower()
    return any(k in haystack for k in KEYWORDS)


def salary_from_ranges(ranges) -> tuple:
    if not ranges:
        return None, None
    try:
        floor = min(int(r.get('min_cents', 0)) for r in ranges) // 100
        ceil = max(int(r.get('max_cents', 0)) for r in ranges) // 100
        return floor, ceil
    except Exception:
        return None, None


def notify(job: dict) -> None:
    if not SLACK_WEBHOOK:
        return
    text = (
        f"*{job['title']}* @ {job['company']}\n"
        f"{job.get('location','')} | ${job['salary_floor']:,}-{job['salary_ceil']:,}\n"
        f"<{job['url']}|Apply ➜> (score {job['similarity']:.2f})"
    )
    WebhookClient(SLACK_WEBHOOK).send(text=text)


def persist(conn, job: dict) -> None:
    with conn:
        cur = conn.execute("SELECT 1 FROM jobs WHERE id=?", (job['id'],))
        if cur.fetchone():
            return
        conn.execute(
            """
            INSERT INTO jobs (id, board, company, title, location, url,
                              salary_floor, salary_ceil, description,
                              similarity, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job['id'], job['board'], job['company'], job['title'],
                job.get('location'), job.get('url'),
                job.get('salary_floor'), job.get('salary_ceil'),
                job.get('content'), job.get('similarity'),
                job.get('updated_at'),
            ),
        )


def process_jobs(conn, jobs):
    for j in jobs:
        if not keyword_match(j):
            continue
        floor, ceil = salary_from_ranges(j.get('pay_ranges'))
        j['salary_floor'] = floor
        j['salary_ceil'] = ceil
        if floor and floor < MIN_SALARY:
            continue
        if RESUME_EMB is not None:
            emb = embed_text(j.get('content', ''))
            j['similarity'] = cosine_similarity(emb, RESUME_EMB)
        else:
            j['similarity'] = 0.0
        if j['similarity'] < RELEVANCE_THRESHOLD:
            continue
        persist(conn, j)
        notify(j)


def crawl_once():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(open(os.path.join(os.path.dirname(__file__), 'schema.sql')).read())

    for slug in tqdm(GREENHOUSE_SLUGS, desc="Greenhouse"):
        try:
            jobs = fetch_greenhouse(slug)
        except Exception as e:
            print(f"[WARN] {slug}: {e}")
            continue
        process_jobs(conn, jobs)

    for slug in tqdm(LEVER_SLUGS, desc="Lever"):
        try:
            jobs = fetch_lever(slug)
        except Exception as e:
            print(f"[WARN] {slug}: {e}")
            continue
        process_jobs(conn, jobs)

    for slug in tqdm(ASHBY_SLUGS, desc="Ashby"):
        try:
            jobs = fetch_ashby(slug)
        except Exception as e:
            print(f"[WARN] {slug}: {e}")
            continue
        process_jobs(conn, jobs)

    conn.close()


if __name__ == "__main__":
    crawl_once()
