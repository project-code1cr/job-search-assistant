# Job Search Assistant

A Python, FastAPI, and SQLite app that ranks sample internships by profile similarity and skill overlap. It shows matched and missing skills and lets you compare concept search with a keyword baseline.

[Live demo](https://job-search-assistant-pi.vercel.app/)

## Run locally

On Windows, double-click `start-windows.cmd`. Or run these commands from the project folder with Python 3.11 or 3.12:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app:app
```

Open [localhost:8000](http://127.0.0.1:8000) and click **Use example → Find matches**.
