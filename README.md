# Job Hunter

This project scrapes job boards (Greenhouse, Lever and Ashby) and stores roles in a local SQLite database.  Jobs are filtered by keyword, salary and similarity to your resume.  Matching results can be pushed to Slack and viewed in a Streamlit dashboard.

## Setup

1. Install Python 3.10+ and create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r job-hunter/requirements.txt
   ```
3. Copy `job-hunter/.env` and edit values for your use:
   - `KEYWORDS` – comma separated keywords used for simple matching
   - `MIN_SALARY` – discard jobs below this salary floor
   - `RELEVANCE_THRESHOLD` – cosine similarity threshold
   - `GREENHOUSE_SLUGS`, `LEVER_SLUGS`, `ASHBY_SLUGS` – board identifiers
   - `RESUME_FILE` – path to your resume text
   - `SLACK_WEBHOOK` – optional Slack incoming webhook URL
   - `OPENAI_API_KEY` – required for OpenAI embeddings

## Usage

Run the crawler:
```bash
python job-hunter/scraper.py
```

View results in a browser:
```bash
python -m streamlit run dashboard.py
```
If `pip` installed the packages in user mode and `streamlit` is not on your
`PATH`, using `python -m` ensures the module is found.

Generate a tailored résumé for a job id:
```bash
python resume_tailer.py <job_id> out.docx
```

## GitHub Actions

The workflow in `.github/workflows/crawl.yml` runs the scraper on a schedule.  Add the above variables as repository secrets so the action can authenticate.
