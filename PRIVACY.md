# Privacy Policy - FindMate AI

**Last updated:** 8 November 2026
**Applies to:** the FindMate AI application and its source code in this repository
(live demo: <https://findmate-ai-dhxvmhdgri3ju4fgkedida.streamlit.app/>).

> **Status: working draft.** This document describes only what the application *actually does today*.
> Anything that is not implemented yet is marked **⚠ Not implemented** and collected in the
> [checklist at the end](#7-what-still-needs-to-be-implemented). It is not legal advice; the project
> owner must review it against the laws that apply to them (for example GDPR, CCPA or local data-protection law)
> before using the app with real people.

---

## 1. Information we collect

FindMate AI has **no user accounts**. It stores only what people type or upload into the report forms.

| Category | What is stored | Required? |
|----------|----------------|-----------|
| Item details | Item name, description, category, location, date lost/found | Yes |
| Contact details | Reporter's **name**, **e-mail address** and **11-digit contact number** | Yes |
| Photo | One optional image (PNG, JPG or WEBP, up to 5 MB) | No |
| Generated data | A numeric "embedding" of the item name + description, report status (open/resolved), creation time, and match scores between reports | Created automatically |

We do **not** collect: precise device location/GPS, payment data, government IDs, passwords from users,
advertising identifiers, or analytics. Streamlit's own usage-statistics collection is switched off in this
project (`gatherUsageStats = false` in `.streamlit/config.toml`).

## 2. How the information is used

- To compare lost and found reports and suggest possible matches (AI matching, see section 5).
- To let people search reports and to let a reporter edit or delete their own reports.
- To let an administrator review matches, contact the people involved and mark cases as resolved.

The information is not sold and is not used for advertising or profiling.

## 3. Who can see what

| Information | Visible to |
|-------------|-----------|
| Item name, description, category, location, date, photo | **Anyone using the app** (dashboard, match lists, search results) |
| Reporter's **name** | **Anyone using the app** - it is shown on report cards |
| Reporter's **e-mail and phone number** | The **administrator** only (match view, "All reports" table and CSV export in the Admin Dashboard) |
| Everything above | The person operating the server / database |

⚠ **Known limitations (not yet fixed):**
- The reporter's name is public. There is no option to hide it.
- "Manage Reports" finds reports by e-mail address **without verifying** that the visitor owns that address.
  Anyone who knows an address could view, edit or delete the reports linked to it.
- The administrator area is protected by one shared password (configured through Streamlit secrets or an
  environment variable). There are no individual admin accounts or audit logs.

## 4. Uploaded images

- Images are validated (file type, size, and that they are real images) and saved to the `uploads/` folder on the
  server under a random file name. The database stores only the file path.
- Images are **not encrypted** and are displayed to all users of the app together with the report.
- Images are **not** analysed by the AI; matching uses text only.
- An image is deleted from disk when its report is deleted or when the photo is replaced.
- ⚠ **Not implemented:** the original file is saved unchanged, so hidden metadata such as **EXIF GPS location or
  camera details is not removed**. Users should not upload photos that reveal sensitive locations.

## 5. AI processing

- Matching and search run **inside the application** with the open-source `all-MiniLM-L6-v2`
  sentence-embedding model. Report text is **not sent to any external AI service or paid API.**
- On first start the model files are downloaded once from Hugging Face. That download request does not contain
  any report data.
- The resulting embeddings are stored in the database next to the report. They are derived from the item name and
  description only (not from the contact details or the photo). The category and location of a report are used as
  small additional signals when scores are calculated.
- Similarity scores are suggestions, not proof of identity, and no decision about a person is made automatically.
  A human administrator closes each case.

## 6. Storage, retention and deletion

**Storage.** Data is kept in a local SQLite file (`data/findmate.db`) and the `uploads/` folder on the machine that
runs the app. Neither is encrypted by the application, and the app creates no backups. The files are excluded from
Git (`.gitignore`) so they are not published with the source code. On hosts with temporary storage (this includes
Streamlit Community Cloud) the data may be lost when the app restarts or is redeployed.

**Retention.**
- There is **no automatic deletion**. A report stays until it is deleted.
- Resolved cases (including the contact details) also stay in the database.
- ⚠ **Not implemented:** a retention period, automatic clean-up, or anonymisation of resolved cases.

**Deletion.**
- *Implemented:* in **Manage Reports** a person can permanently delete a report. This removes the report row (including
  the contact details and embedding), the matches linked to it, and its image file. A confirmation dialog is shown first.
- ⚠ **Not implemented:** an administrator "delete" function, verified identity checks for deletion/access requests,
  and a data-export tool for a person's data (an admin can only download a CSV of all reports).
- Until those exist, a deletion request sent to the privacy contact below can only be handled **manually** by the
  operator, who must edit the database directly.

## 7. What still needs to be implemented

Before real personal data is collected, the project owner should complete the following.

- [ ] **Add a real privacy contact** (see section 9) and decide who answers requests, and within what time.
- [ ] Define and enforce a **retention period** (for example, auto-delete open reports after N days and resolved
      cases after N days).
- [ ] Add an **admin delete / anonymise** tool so deletion requests can be handled inside the app.
- [ ] Add **verification** (for example, an e-mailed code) before showing or changing reports in "Manage Reports".
- [ ] Add a **privacy notice and consent checkbox** on the report forms and a link to this document inside the app.
- [ ] Make the reporter's **name optional or private**.
- [ ] **Strip EXIF/metadata** from uploaded images.
- [ ] **Self-host the fonts** (see section 8) so no request goes to Google.
- [ ] Add **encryption at rest and backups**, individual admin accounts and **access logging**.
- [ ] Document a **data-breach response process**.
- [ ] Have the policy **reviewed against applicable law** (lawful basis, international transfers, children's data).

## 8. Third-party services

| Service | Why | What it receives |
|---------|-----|------------------|
| **Hugging Face** (`huggingface.co`) | One-time download of the AI model when the app starts | The server's request for the model files; no report data |
| **Google Fonts** (`fonts.googleapis.com`) | The interface loads the *Inter* and *Playfair Display* fonts from Google when a page opens | The visitor's browser sends Google its **IP address** and standard request headers. ⚠ Not self-hosted yet |
| **Streamlit Community Cloud** (if the app is hosted there) | Hosting the live demo | Everything users submit passes through the host; its own terms and privacy policy apply |
| **GitHub** | Hosts the source code only | No user data |

The application code itself sets no tracking cookies and includes no advertising or analytics tools. The Streamlit
framework and the hosting platform may use technical cookies or session identifiers that are outside this
project's control.

## 9. Privacy contact and requests

To ask about, correct or delete your data, contact:

> **[PRIVACY CONTACT E-MAIL - TO BE ADDED BY THE PROJECT OWNER]**

⚠ No contact address has been configured yet, and no response process or deadline has been defined. Until the owner
adds one, people can delete their own reports in **Manage Reports**.

## 10. Changes to this policy

When the application's data practices change, this file will be updated and the "Last updated" date changed.
The Git history of this file shows earlier versions.
