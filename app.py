import json
import logging
import os
import re
import sqlite3
from contextlib import asynccontextmanager, closing
from pathlib import Path
from tempfile import gettempdir
from typing import Literal

import httpx

from concepts import concept_vectors
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints
from sklearn.feature_extraction.text import TfidfVectorizer
from typing_extensions import Annotated

ROOT = Path(__file__).resolve().parent
# Vercel mounts deployed source as read-only. The sample catalog is rebuilt at startup.
DATABASE = (Path(gettempdir()) if os.getenv("VERCEL") == "1" else ROOT) / "jobs.sqlite"
SEMANTIC_WEIGHT = 0.7
logger = logging.getLogger(__name__)

Profile = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=1500)]


class SearchInput(BaseModel):
    profile: Profile
    mode: Literal["Any", "Remote", "Hybrid", "On-site"] = "Any"
    limit: int = Field(default=3, ge=1, le=20)
    method: Literal["default", "keyword"] = "default"


class ExplainInput(BaseModel):
    profile: Profile
    job_id: int


class MatchNote(BaseModel):
    summary: str = Field(min_length=1, max_length=500)
    next_step: str = Field(min_length=1, max_length=300)


def get_jobs(mode="Any"):
    with closing(sqlite3.connect(DATABASE)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM jobs WHERE ? = 'Any' OR mode = ? ORDER BY id", (mode, mode)
        ).fetchall()
    return [{**dict(row), "skills": json.loads(row["skills"])} for row in rows]


@asynccontextmanager
async def lifespan(app):
    seed = json.loads((ROOT / "jobs.json").read_text(encoding="utf-8"))
    with closing(sqlite3.connect(DATABASE)) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, title TEXT, "
            "team TEXT, mode TEXT, description TEXT, skills TEXT)"
        )
        connection.execute("DELETE FROM jobs")
        connection.executemany(
            "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?)",
            [(j["id"], j["title"], j["team"], j["mode"], j["description"],
              json.dumps(j["skills"])) for j in seed],
        )

    jobs = get_jobs()
    documents = [f"{j['title']}. {j['description']} Skills: {', '.join(j['skills'])}" for j in jobs]
    app.state.index = {job["id"]: i for i, job in enumerate(jobs)}
    app.state.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    app.state.keywords = app.state.vectorizer.fit_transform(documents)
    app.state.model = None
    app.state.concepts = concept_vectors(documents)

    if os.getenv("ENABLE_SEMANTIC") == "1":
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
            app.state.vectors = model.encode(documents, normalize_embeddings=True)
            app.state.model = model
        except (ImportError, OSError, RuntimeError) as error:
            logger.warning("MiniLM unavailable. Using local concept search. %s", error)

    yield


app = FastAPI(title="Job Search Assistant", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "static" / "index.html")


SKILL_ALIASES = {
    "REST": ["REST API", "RESTful", "REST"],
    "Node.js": ["Node.js", "NodeJS", "Node JS"],
    "Next.js": ["Next.js", "NextJS", "Next JS"],
    "React": ["React", "React.js", "ReactJS"],
    "Embeddings": ["embeddings", "embedding", "semantic search", "vector search"],
    "scikit-learn": ["scikit-learn", "sklearn"],
}


def skill_evidence(profile, skills):
    matched, missing = [], []
    for skill in skills:
        aliases = SKILL_ALIASES.get(skill, [skill])
        found = any(
            re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", profile, re.IGNORECASE)
            for alias in aliases
        )
        (matched if found else missing).append(skill)
    return matched, missing


@app.post("/api/search")
def search(data: SearchInput):
    model = app.state.model
    query = app.state.vectorizer.transform([data.profile])
    keyword_scores = (app.state.keywords @ query.T).toarray().ravel()
    if data.method == "keyword":
        similarities, method = keyword_scores, "keyword"
    elif model is not None:
        query = model.encode([data.profile], normalize_embeddings=True)[0]
        similarities, method = app.state.vectors @ query, "minilm"
    else:
        query = concept_vectors([data.profile])[0]
        concept_scores = app.state.concepts @ query
        similarities = 0.7 * concept_scores + 0.3 * keyword_scores
        method = "concept"

    results = []
    for job in get_jobs(data.mode):
        matched, missing = skill_evidence(data.profile, job["skills"])
        similarity = max(0.0, min(1.0, float(similarities[app.state.index[job["id"]]])))
        coverage = len(matched) / len(job["skills"])
        score = SEMANTIC_WEIGHT * similarity + (1 - SEMANTIC_WEIGHT) * coverage
        results.append({
            **job, "score": score, "similarity": round(similarity, 3),
            "matched": matched, "missing": missing,
        })
    results.sort(key=lambda job: (-job["score"], job["id"]))
    return {
        "method": method,
        "matches": [{**job, "score": round(job["score"], 3)} for job in results[:data.limit]],
        "gemini_available": bool(os.getenv("GEMINI_API_KEY")),
    }


@app.post("/api/explain")
def explain(data: ExplainInput):
    job = next((j for j in get_jobs() if j["id"] == data.job_id), None)
    if job is None:
        raise HTTPException(404, "Sample job was not found.")

    matched, missing = skill_evidence(data.profile, job["skills"])
    evidence = f"Skills found in your profile: {', '.join(matched)}." if matched else (
        "No listed skills were detected in your profile."
    )
    next_step = f"Check whether you can show experience with {missing[0]}." if missing else (
        "Prepare an example of using these skills in a project."
    )
    fallback = MatchNote(summary=evidence, next_step=next_step)
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return {"source": "skills", "note": fallback}

    # Only send the sample job and skill labels to Gemini, never the profile itself.
    prompt_data = {"role": job["title"], "matched": matched, "not_detected": missing}
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    try:
        result = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": key},
            json={
                "contents": [{"parts": [{"text": (
                    "Write a short job match summary and one practical next step. "
                    "Use only the evidence in this JSON. Describe undetected skills as "
                    "not found in the profile and do not invent experience.\n"
                    + json.dumps(prompt_data)
                )}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseJsonSchema": MatchNote.model_json_schema(),
                },
            },
            timeout=12,
        )
        result.raise_for_status()
        parts = result.json()["candidates"][0]["content"]["parts"]
        output = "".join(part.get("text", "") for part in parts if not part.get("thought"))
        return {"source": "gemini", "note": MatchNote.model_validate_json(output)}
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
        logger.warning("Gemini explanation unavailable (%s)", type(error).__name__)
        return {"source": "skills", "note": fallback}
