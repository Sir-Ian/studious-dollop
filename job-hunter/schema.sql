CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    board TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    url TEXT,
    salary_floor INTEGER,
    salary_ceil INTEGER,
    description TEXT,
    similarity REAL,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_similarity ON jobs(similarity);
CREATE INDEX IF NOT EXISTS idx_jobs_updated ON jobs(updated_at);
