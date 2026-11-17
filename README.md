# Job Search Assistant

Paste a short profile to rank nine fictional internships. The app shows which listed skills appear in your profile and which it could not find. Filter by work mode or request an explanation for a result.

## Run locally

Install Python 3.11 or 3.12 and extract the ZIP. On Windows, double-click
`start-windows.cmd` in the extracted folder. It creates a virtual environment,
installs dependencies, and starts the server. The first run needs internet access
to install packages. Keep the terminal open and visit [the app](http://127.0.0.1:8000).
Click **Use example**, then **Find matches**.

For manual setup, open a terminal in the project folder.

```sh
python -m venv .venv
```

Activate the environment with `.\.venv\Scripts\Activate.ps1` in Windows PowerShell or `source .venv/bin/activate` on macOS/Linux. Then run:

```sh
python -m pip install -r requirements.txt
python -m uvicorn app:app
```

Open [the app](http://127.0.0.1:8000) and choose **Use example**. You can also try the API at [the interactive docs](http://127.0.0.1:8000/docs).

## Enable semantic search and Gemini

The default local concept search combines a small phrase dictionary with TF-IDF.
It needs no model download or API key. Choose **Keyword baseline** to compare
the results. To enable embeddings, install `requirements-semantic.txt` and set `ENABLE_SEMANTIC=1` before starting Uvicorn. The first start needs internet access to download the MiniLM model. The app shows which search method is active. If the model cannot load, the server logs the cause and uses local concept search.

To enable Gemini, set `GEMINI_API_KEY` in your terminal session before starting Uvicorn. You can set `GEMINI_MODEL` to override the default model if your account gives you access to a different one. The app sends the sample job title and detected skill labels to Gemini only when you click **Explain with Gemini**. The profile text stays on the FastAPI server. If Gemini is unavailable or returns invalid JSON, the app shows a template summary.

For example, once the optional requirements are installed, set the values for the features you want and restart the server from that same terminal:

| Shell | MiniLM | Gemini |
|---|---|---|
| PowerShell | `$env:ENABLE_SEMANTIC = "1"` | `$env:GEMINI_API_KEY = "your-key"` |
| macOS/Linux | `export ENABLE_SEMANTIC=1` | `export GEMINI_API_KEY="your-key"` |

## How ranking works

SQLite loads the sample catalog from `jobs.json` and filters by work mode. The server computes document vectors once at startup. For each profile, it compares the profile vector with the job vectors and combines similarity (70%) with the fraction of skills found (30%). The default similarity blends concept vector similarity (70%) with TF-IDF
similarity (30%). The concept vectors are defined by the phrases in `concepts.py`.
For example, “build pipelines” and “deployment workflows” contribute to the same dimension.
When enabled, MiniLM replaces the blended similarity with the cosine similarity of its embeddings. The score orders results and is not a probability of getting hired.

For a catalog this small, comparing every vector with NumPy keeps the implementation easy to inspect. Gemini writes the optional explanation after ranking. It has no control over the scores.

## Reproduce the ranking comparison

Run `python evaluate.py` in the project's virtual environment. For the eight
handwritten cases, the expected job ranked first in 6/8 with the keyword
baseline and 8/8 with local concept search. Both found the expected job in the
top three for all eight cases. These are sample cases tied to the included
catalog and vocabulary. They do not measure performance on unseen listings.

## Demo the Backend API Intern listing

Search for “I built REST APIs with Node.js and Express and stored data in
MongoDB.” Backend API Intern ranks first in both local ranking modes, and the
result shows all three required skills as found. The listing is fictional.

## Make a change you can explain

1. Add three anonymized job descriptions to `jobs.json` and restart the app. Give each job its own ID. The UI shows the top three results.
2. Write five short profiles. Before searching, record which jobs you expect for each. Include one profile that uses a phrase like “built service endpoints” instead of “built REST APIs.”
3. Run the same profiles with the keyword baseline and your chosen default method. Count how often an expected job appears in the first three results. Try changing the similarity and skill weights in `app.py` and record one case where ranking improved or got worse.
4. Commit the data and your results. In an interview, show one example and explain what you changed and why.

References: [Sentence Transformers](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html) · [Gemini structured output](https://ai.google.dev/gemini-api/docs/migrate-to-interactions)
