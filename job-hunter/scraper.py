import os
import sqlite3
from datetime import datetime, timedelta
import time
import argparse

from dotenv import load_dotenv
from slack_sdk.webhook import WebhookClient
from tqdm import tqdm

from fetchers import fetch_greenhouse, fetch_lever, fetch_ashby
from similarity import embed_text, cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    _model = (
        SentenceTransformer('all-MiniLM-L6-v2')
        if not OPENAI_API_KEY or openai is None
        else None
    )
except Exception:  # pragma: no cover - optional
    _model = None
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


def crawl_loop(hours: float, interval: int) -> None:
    """Continuously crawl for ``hours`` hours, sleeping ``interval`` seconds
    between iterations. A value of 0 for ``hours`` runs indefinitely.
    """
    deadline = None if hours <= 0 else datetime.now() + timedelta(hours=hours)
    iteration = 1
    while True:
        print(f"\n[INFO] Crawl iteration {iteration}")
        crawl_once()
        iteration += 1
        if deadline and datetime.now() >= deadline:
            break
        time.sleep(max(1, interval))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--duration",
        type=float,
        default=CRAWL_HOURS,
        help="run for the given number of hours (0 = run once)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=CRAWL_INTERVAL,
        help="seconds between iterations when running in a loop",
    )
    args = parser.parse_args()

    if args.duration and args.duration > 0:
        crawl_loop(args.duration, args.interval)
    else:
        crawl_once()
