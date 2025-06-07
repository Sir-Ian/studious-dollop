import sqlite3
import streamlit as st

DB_PATH = 'jobs.db'

st.title('Job Tracker')

conn = sqlite3.connect(DB_PATH)
rows = conn.execute(
    'SELECT company, title, location, salary_floor, salary_ceil, similarity, url, updated_at '
    'FROM jobs ORDER BY updated_at DESC'
).fetchall()
conn.close()

min_salary = st.sidebar.number_input('Minimum salary', value=150000)
min_score = st.sidebar.slider('Min relevance', 0.0, 1.0, 0.75, 0.01)

for r in rows:
    if r[3] and r[3] < min_salary:
        continue
    if r[5] < min_score:
        continue
    st.write(f"### {r[1]} @ {r[0]}")
    st.write(r[2])
    st.write(f"${r[3]:,}-{r[4]:,} | score {r[5]:.2f}")
    st.write(f"[Apply]({r[6]})")
    st.write('---')
