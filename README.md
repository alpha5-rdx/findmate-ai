# 🔍 FindMate AI - Intelligent Lost & Found Matching

FindMate AI reunites people with their belongings by matching lost and found reports by **meaning**, not keywords. "Dark billfold with a university identity card" matches "Black leather wallet with a student ID".

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

* The first run downloads `all-MiniLM-L6-v2` (~90 MB) from Hugging Face. Internet is needed once; afterwards it works offline.
* No API keys or paid services are used.
* On the Dashboard, click **Load sample dataset** for an instant demo (4 same-item-different-words pairs + 2 distractors).
* Admin password: `admin123` (override with the `FINDMATE_ADMIN_PASSWORD` environment variable).

## Features

| Page | What it does |
|------|--------------|
| Dashboard | Metric cards (lost, found, potential matches, resolved), top matches, recent reports |
| Report Lost / Found | Validated form with optional image upload (stored in `uploads/`); matching runs on submit |
| Match Results | Ranked pairs with High / Medium / Low confidence, similarity bars, configurable threshold |
| Smart Search | Natural-language query ranked by cosine similarity |
| Manage Reports | Look up reports by email; edit (re-embeds), delete |
| Admin Dashboard | Password-protected: all reports, matches with contacts, mark resolved, re-open, charts, CSV export |

## How the AI works

1. **Embeddings**: each report's name + description is encoded by `all-MiniLM-L6-v2` into a normalised 384-d vector. Vectors are stored in SQLite and only recomputed when a report is created or edited.
2. **Cosine similarity**: `sklearn.metrics.pairwise.cosine_similarity` scores every open lost item against every open found item in one matrix operation.
3. **Bounded metadata**: `score = semantic + 0.05·[same category] + 0.04·location_similarity` (location similarity is itself semantic, so "Central Library" ≈ "Main Library"). Metadata adds at most 0.09 and is ignored entirely when semantic similarity is below 0.30, so it can re-order close candidates but never create a match on its own.
4. **Confidence**: High ≥ 75 %, Medium ≥ 55 %, Low below. The display threshold is a sidebar slider.
5. **Graceful failure**: missing descriptions fall back to name + category; if the model can't load, the UI shows the error with recovery steps.

> Similarity is **not** proof of identity. Always verify ownership before handing over an item.

## Project structure

```
app.py                  Streamlit entry point + sidebar navigation
config.py               Paths, model name, thresholds, categories
ai/embedder.py          Model loading, text building, embedding cache
ai/matcher.py           Cosine matching, score combination, semantic search
database/db.py          SQLite schema (auto-created) and all queries
frontend/ui.py          CSS theme and reusable components
frontend/pages.py       All page renderers
utils/validation.py     Input validation
utils/files.py          Image validation and local storage
data/sample_data.py     Demo dataset loader
uploads/                Uploaded images (git-ignored)
```

## Troubleshooting

* **Model fails to download**: check your connection/proxy (`HTTPS_PROXY`), then rerun. Models are cached under `~/.cache/huggingface`.
* **Reset all data**: stop the app and delete `data/findmate.db` and the files in `uploads/`.

## Limitations

* No user accounts: reports are managed by the email used at submission, and admin access is a single shared password. Add real authentication before public deployment.
* Image uploads are stored but not used for matching (text only).
* Matching is recomputed in full on each change, which is fine for thousands of reports but not millions.

## How to Use FindMate AI

### Option 1: Use Online

Visit our live application: [FindMate AI](YOUR_STREAMLIT_DEPLOYMENT_URL)

No installation required. Open the application in your browser and start reporting lost or found items.

### Option 2: Run Locally

**Prerequisites:**
- Python 3.10 or compatible version
- Git (optional)
- Internet connection for initial dependency and AI model installation

**Installation:**

```bash
git clone https://github.com/YOUR-USERNAME/findmate-ai.git
cd findmate-ai
pip install -r requirements.txt
```

**Run the application:**

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### How It Works

1. Report a lost or found item.
2. Provide its name, description, category and location.
3. Let the AI matching engine analyze the descriptions.
4. Explore ranked potential matches and similarity scores.
5. Contact the relevant person through the provided contact information.

**Note:** Similarity scores indicate potential matches, not verified ownership. Contact information and uploaded reports should be handled responsibly.
