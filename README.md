# Job Hunter

This project scrapes job boards (Greenhouse, Lever and Ashby) and stores roles in a local SQLite database.  Jobs are filtered by keyword, salary and similarity to your resume.  Matching results can be pushed to Slack and viewed in a Streamlit dashboard.

## Setup

1. Install Python 3.10+ and create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r job-hunter/requirements.txt
   ```
3. Copy `job-hunter/.env.example` to `job-hunter/.env` and edit values:
   - `KEYWORDS` – comma separated keywords used for simple matching
   - `MIN_SALARY` – discard jobs below this salary floor
   - `RELEVANCE_THRESHOLD` – cosine similarity threshold
   - `GREENHOUSE_SLUGS`, `LEVER_SLUGS`, `ASHBY_SLUGS` – board identifiers
   - `RESUME_FILE` – path to your resume text
   - `SLACK_WEBHOOK` – optional Slack incoming webhook URL
   - `OPENAI_API_KEY` – optional OpenAI key for remote embeddings
   - `CRAWL_HOURS` – number of hours to loop the crawler (0 to run once)
   - `CRAWL_INTERVAL` – seconds to wait between crawl iterations
   - `OPENAI_API_KEY` – required for OpenAI embeddings
   - `CRAWL_HOURS` – number of hours to loop the crawler (0 to run once)
   - `CRAWL_INTERVAL` – seconds to wait between crawl iterations
  - `OPENAI_API_KEY` – optional key for OpenAI embeddings

## Usage

Run the crawler once:
```bash
python job-hunter/scraper.py
```

Loop the crawler for a given duration:
```bash
python job-hunter/scraper.py --duration 8 --interval 600
```

View results in a browser:
```bash
streamlit run dashboard.py
```

Generate a tailored résumé for a job id (falls back to your unmodified résumé if OpenAI isn't configured):
```bash
python resume_tailer.py <job_id> out.docx
```

## GitHub Actions

The workflow in `.github/workflows/crawl.yml` runs the scraper on a schedule.  Add the above variables as repository secrets so the action can authenticate.
