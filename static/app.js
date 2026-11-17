const form = document.querySelector("#search");
const profileInput = document.querySelector("#profile");
const modeInput = document.querySelector("#mode");
const methodInput = document.querySelector("#method");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const submit = form.querySelector('button[type="submit"]');

document.querySelector("#example").onclick = () => {
  profileInput.value = "I built web service endpoints with Python, FastAPI and SQL. I used vector search to find related job descriptions and Gemini to summarize the results.";
  profileInput.focus();
};

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error("Request failed.");
  return response.json();
}

function addText(parent, tag, text, className = "") {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  parent.append(element);
  return element;
}

function showJob(job, profile, useGemini) {
  const card = document.createElement("article");
  addText(card, "h2", job.title);
  addText(card, "p", job.team + " · " + job.mode, "muted");
  addText(card, "p", job.description);
  addText(card, "p", "Ranking score: " + job.score.toFixed(2), "muted");
  addText(card, "p", "Skills found: " + (job.matched.join(", ") || "None"));
  addText(card, "p", "Skills not detected: " + (job.missing.join(", ") || "None"));
  const button = addText(card, "button", useGemini ? "Explain with Gemini" : "Show next step", "secondary");
  const note = addText(card, "div", "", "note");
  note.setAttribute("role", "status");
  note.hidden = true;
  button.onclick = async () => {
    button.disabled = true;
    note.hidden = false;
    note.textContent = "Preparing explanation…";
    try {
      const data = await post("/api/explain", { profile, job_id: job.id });
      note.replaceChildren();
      addText(note, "p", data.source === "gemini" ? "Gemini explanation" : "Skills summary", "muted");
      addText(note, "p", data.note.summary);
      addText(note, "p", data.note.next_step);
    } catch {
      note.textContent = "Could not load the explanation. Try again.";
    } finally {
      button.disabled = false;
    }
  };
  results.append(card);
}

form.onsubmit = async (event) => {
  event.preventDefault();
  const profile = profileInput.value.trim();
  if (profile.length < 5) {
    status.textContent = "Enter at least five characters about your skills or experience.";
    return;
  }
  submit.disabled = true;
  results.replaceChildren();
  status.textContent = "Finding matches…";
  try {
    const data = await post("/api/search", { profile, mode: modeInput.value, method: methodInput.value });
    if (data.matches.length === 0) {
      status.textContent = "No sample jobs match that work mode.";
      return;
    }
    const method = {
      concept: "Local concept search",
      minilm: "MiniLM embedding search",
      keyword: "Keyword search",
    }[data.method];
    status.textContent = method + " · " + data.matches.length + " sample matches";
    data.matches.forEach((job) => showJob(job, profile, data.gemini_available));
  } catch {
    status.textContent = "Search failed. Check that the app is running and try again.";
  } finally {
    submit.disabled = false;
  }
};
