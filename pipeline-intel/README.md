# KeychainOS · Pipeline Intelligence Dashboard

Interactive sales pipeline model with live variable controls. Deployed as a static site via GitHub Pages.

---

## How it works

1. `build.py` generates `index.html` — a fully self-contained single-file dashboard
2. GitHub Actions runs `build.py` on a schedule (or manually) and commits the updated `index.html`
3. GitHub Pages serves the site automatically from the `main` branch root

The dashboard has no external data dependencies. All model logic lives in `build.py` as configuration constants.

---

## One-time setup (10 minutes)

### 1. Create the repo on GitHub

Upload these files:
```
build.py
.github/workflows/weekly.yml
README.md
```
Do **not** upload `index.html` — it will be generated automatically.

### 2. Enable GitHub Pages

- Go to repo → **Settings** → **Pages**
- Source: **Deploy from a branch**
- Branch: `main` / folder: `/ (root)`
- Save

Your site will be live at:
```
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME
```

### 3. Trigger first build

- Go to **Actions** tab
- Click **Weekly Pipeline Dashboard**
- Click **Run workflow** → Run
- Wait ~30 seconds → `index.html` will appear and your site will be live

---

## Changing the access code

1. Pick a new code (must be exactly `CODE_LENGTH` characters — default 12)
2. Run this to get its hash:
   ```bash
   python3 -c "import hashlib; print(hashlib.sha256('YOURNEWCODE'.encode()).hexdigest())"
   ```
3. Open `build.py` and replace the `CODE_HASH` value with the output
4. Update the comment above it with your new code so you don't forget it
5. Commit and push — run the workflow to regenerate `index.html`

**Current default code:** `Pipeline2026`

---

## Changing model defaults

All tunable parameters are at the top of `build.py` in the `CONFIG` block:

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_CR` | `9.5` | Close rate % (slider range: 8–12) |
| `DEFAULT_ACV` | `51` | ACV in $K (slider range: 40–75) |
| `DEFAULT_LEADS` | `265` | Leads per month (slider range: 200–300) |
| `UNDER_CR_MULT` | `0.68` | Underperform scenario CR multiplier |
| `OVER_CR_MULT` | `1.32` | Outperform scenario CR multiplier |
| `CARRY_RATE` | `0.20` | % of projected closes that carry to next month |
| `CARRY_RESOLVE` | `0.80` | % of carried deals that eventually close |

After changing any value, commit and push, then run the workflow to regenerate.

---

## Changing the build schedule

Edit `.github/workflows/weekly.yml`:
```yaml
- cron: "0 13 * * 1"    # Every Monday 8am EST
- cron: "0 13 * * 1,4"  # Monday + Thursday
- cron: "0 13 * * *"    # Daily
```
Cron uses UTC. EST = UTC−5, so 8am EST = 13:00 UTC.

---

## Files

| File | Purpose |
|---|---|
| `build.py` | Model config + generates `index.html` |
| `index.html` | The live site (auto-generated — do not edit manually) |
| `.github/workflows/weekly.yml` | Runs `build.py` on schedule |
| `README.md` | This file |

---

## Dashboard slides

| Slide | Content |
|---|---|
| 01 · Flow | Horizontal pipeline architecture — Raw Leads → MQL → SQL → Projected Closes → Closed Won |
| 02 · Metrics | ACV breakdown, monthly/quarterly/annual targets, rep efficiency matrix |
| 03 · Funnel | Stage-by-stage attrition bars with drop-off counts |
| 04 · Slippage | 3-month carry resolution map — M1 → M2 → M3 normalization |
| 05 · Revenue | 3-scenario comparison (under / baseline / over) with Q ARR deltas |

All slides update live when sliders are adjusted (Close Rate 8–12%, ACV $40K–$75K, Leads 200–300).
