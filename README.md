# Job Search Assistant

A web app built with **Python, FastAPI, and SQLite** that helps users find relevant internships from a sample catalog.

[Live demo](https://job-search-assistant-pi.vercel.app/)

## Features

- Paste a short profile and filter roles by work mode.
- See which skills match, which were not detected, and a suggested next step.
- Compare **Recommended** results with a **Keyword baseline**.

## How it ranks jobs

The score combines profile similarity (70%) and skill overlap (30%). Recommended mode combines TF-IDF with a phrase dictionary, so “build pipelines” and “deployment workflows” can count toward the same concept. Run `python evaluate.py` to compare both modes on eight sample profiles.

## Run locally

On Windows, double-click `start-windows.cmd`. Or run these commands from the project folder with Python 3.11 or 3.12:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app:app
```

Open [localhost:8000](http://127.0.0.1:8000) and click **Use example → Find matches**.
