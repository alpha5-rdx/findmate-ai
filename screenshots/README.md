# Screenshots

This folder holds the **real** screenshots used by the project README.
No screenshots are committed yet - they must be captured from the running app.
Please do not use mock-ups, illustrations or edited images.

## Required screenshots

| File | Page to capture | What it must show |
|------|-----------------|-------------------|
| `dashboard.png` | **Dashboard** | The four metric cards, *Top potential matches* and *Recent reports* (load the sample dataset first) |
| `report-submission.png` | **Report Lost Item** (or Found) | The completed form: item details, contact details and photo section, ideally with the success message below it |
| `ai-matches.png` | **Match Results** | Several ranked matches with confidence badges, similarity rings and the lost / found cards side by side |
| `admin-dashboard.png` | **Admin Dashboard** (signed in) | Metric cards, the *Signed in as Administrator* bar and the Matches / All reports / Statistics tabs |

## How to capture them

1. Start from a fresh database so no real data is visible: stop the app, move `data/findmate.db`
   somewhere safe (do not delete it if it contains real reports), then run `streamlit run app.py`.
2. On the Dashboard click **Load sample dataset** - it only contains fictional people and items.
3. Use a browser window about 1400 px wide and capture the page as PNG.
4. Before saving, check the image for personal data, real e-mail addresses / phone numbers,
   and anything secret (the admin password is a password field and is masked, but do not capture it being typed).
5. Save the files in this folder using exactly the names above, then uncomment the matching
   image lines in the main `README.md` (see its *Screenshots* section).

Keep each file under ~1 MB if possible.
