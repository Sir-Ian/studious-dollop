import os
import sqlite3
from docx import Document
try:
    import openai  # optional
except Exception:  # pragma: no cover - optional
    openai = None

DB_PATH = 'jobs.db'
RESUME_FILE = os.getenv('RESUME_FILE', 'resume.txt')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def generate(job_id: str, out_path: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT title, company, description FROM jobs WHERE id=?', (job_id,)).fetchone()
    conn.close()
    if not row:
        raise SystemExit('job not found')

    master = open(RESUME_FILE).read()
    if openai and OPENAI_API_KEY:
        prompt = (
            "Tailor this resume to the following job:\n"
            f"Job: {row[0]} at {row[1]}\n"
            f"Description:\n{row[2]}\nResume:\n{master}"
        )
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp["choices"][0]["message"]["content"]
    else:
        print("OPENAI_API_KEY not set; returning original resume")
        text = master

    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    doc.save(out_path)


if __name__ == '__main__':
    import sys
    generate(sys.argv[1], sys.argv[2])
