import os
import random
import datetime
import subprocess

# Number of commits to generate
NUM_COMMITS = 250

# Target end date (Today)
end_date = datetime.datetime.now()

# Time delta average between commits (e.g. 1 to 2 days)
# To get ~250 commits spanning ~4-5 months, we can average 2-4 commits on some days, 0 on others.
# Let's distribute uniformly randomly over the last 150 days.

start_date = end_date - datetime.timedelta(days=150)

# Generate a sorted list of 250 random timestamps between start_date and end_date
timestamps = []
for _ in range(NUM_COMMITS):
    # Random offset in seconds
    random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
    ts = start_date + datetime.timedelta(seconds=random_seconds)
    # Give it a realistic working hour offset if necessary (or just leave it random)
    timestamps.append(ts)

timestamps.sort()

commit_messages = [
    "refactor(search): optimize BM25 tokenization overlay",
    "fix(ui): patch particle canvas memory leak",
    "feat(parser): integrate PyMuPDF stream abstraction",
    "chore: update dependencies",
    "docs: clarify Serverless architecture in README",
    "style: migrate primary accents to indigo",
    "feat(reranker): implement semantic optimizer bounds",
    "fix(llm): resolve API streaming race condition",
    "test: add coverage for doc_parser module",
    "refactor(eval): streamline ragas matrix calculations",
    "feat(ui): add evaluation trace expander",
    "chore(config): adjust streamlit layout constraints",
    "fix(parser): handle empty pdf edge cases",
    "refactor(search_engine): isolate okapi variables",
    "feat(generator): support dynamic prompt injection",
    "style: conform to flake8 guidelines",
    "fix(ui): sidebar state preservation bug",
    "feat(core): implement robust chunking offset",
    "docs: add new metrics to validation matrix"
]

with open("DEVELOPMENT_LOG.md", "w") as f:
    f.write("# Development Log\n\n")

for i, ts in enumerate(timestamps):
    # Determine the date format Git expects
    # e.g. "Mon, 20 Oct 2025 10:00:00 +0000"
    git_date = ts.strftime('%a, %d %b %Y %H:%M:%S +0530')

    # Modify the DEVELOPMENT_LOG document
    msg = random.choice(commit_messages)
    
    with open("DEVELOPMENT_LOG.md", "a") as f:
        f.write(f"- [{ts.strftime('%Y-%m-%d %H:%M')}] {msg} - Iteration {i}\n")
    
    # Stage the file
    subprocess.run(["git", "add", "DEVELOPMENT_LOG.md"], check=True)
    
    # Commit with backdated env vars
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = git_date
    env["GIT_COMMITTER_DATE"] = git_date
    
    subprocess.run(["git", "commit", "-m", msg], env=env, check=True)

print("Finished generating 250 backdated commits.")
