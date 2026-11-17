"""Compare the ranking methods against eight labeled example profiles."""

from fastapi.testclient import TestClient

from app import app

CASES = [
    ("I built a Python API and stored application records in database tables.", 1),
    ("I worked on meaning-based search and used a language model to explain results.", 2),
    ("I created a user interface using reusable components and CSS.", 3),
    ("I developed product pages with Next.js and a document database.", 4),
    ("I made spreadsheet summaries of business trends.", 5),
    ("I used Express and JWT to build a login service.", 6),
    ("I handled packaging services and maintained build pipelines.", 7),
    ("I compared predictive models on held-out data.", 8),
]


def main():
    with TestClient(app) as client:
        for method in ("keyword", "default"):
            hits_at_1 = hits_at_3 = 0
            for profile, expected in CASES:
                response = client.post("/api/search", json={"profile": profile, "method": method})
                response.raise_for_status()
                data = response.json()
                ranked = [job["id"] for job in data["matches"]]
                hits_at_1 += ranked[0] == expected
                hits_at_3 += expected in ranked
                print(f"{data['method']:7} | expected {expected} | got {ranked} | {profile}")
            print(f"Hit@1: {hits_at_1}/{len(CASES)} | Hit@3: {hits_at_3}/{len(CASES)}\n")


if __name__ == "__main__":
    main()
