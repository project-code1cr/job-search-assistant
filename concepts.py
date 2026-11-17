"""A small, editable vocabulary for search without a model download."""

import re

import numpy as np

# Each group is one dimension of the vector. Phrases in the same group
# contribute to the same dimension, even when they share no words.
CONCEPTS = {
    "backend": ["backend", "web service", "api endpoints", "server side", "service routes"],
    "python_web": ["fastapi", "flask", "django", "python api"],
    "relational_data": ["sql", "postgres", "relational data", "database tables"],
    "semantic_search": ["semantic retrieval", "semantic search", "vector search", "embeddings", "meaning-based search", "catalog ranking"],
    "llm": ["gemini", "language model", "llm", "generated explanations"],
    "frontend": ["frontend", "web interfaces", "reusable components", "react", "user interface"],
    "full_stack": ["full stack", "product pages", "next.js", "across the interface and database"],
    "javascript_backend": ["node.js", "nodejs", "express", "application endpoints"],
    "document_database": ["mongodb", "document database", "nosql"],
    "auth": ["authentication", "login", "jwt", "access control"],
    "analytics": ["data analyst", "business trends", "reports", "spreadsheet summaries", "excel"],
    "containers": ["docker", "containers", "containerize", "package services", "packaging services"],
    "infrastructure": ["platform engineering", "deployment workflows", "application infrastructure", "ci/cd", "build pipelines", "linux"],
    "model_training": ["machine learning", "training datasets", "classifiers", "predictive models", "held-out data", "scikit-learn"],
    "data_preparation": ["pandas", "clean datasets", "prepare datasets", "data cleaning"],
}
PATTERNS = [
    re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, phrases)) + r")(?!\w)", re.I)
    for phrases in CONCEPTS.values()
]


def concept_vectors(texts):
    vectors = np.array(
        [[float(bool(pattern.search(text))) for pattern in PATTERNS] for text in texts]
    )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(norms, 1)
