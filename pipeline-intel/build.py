"""
build.py - KeychainOS Funnel Dashboard
Handles both pivoted (wide) and unpivoted (long) data formats from Google Sheets.
Supports a second ICP-filtered tab with a dataset toggle in the Cohort Filters section.
"""

import csv, io, hashlib, urllib.request
from datetime import datetime
from collections import defaultdict

# ── CONFIG ───────────────────────────────────────────────────────────────────
SHEET_ID    = "1beenLANcaT3YZkqnD8uh-KssmxDTpKVGXfakHFNNB7k"
DATA_URL    = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# ── SET THIS to your second tab's gid (number after gid= in the URL when on that tab) ──
ICP_GID     = "1467538758"
ICP_URL     = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ICP_GID}"

OUTPUT_FILE = "index.html"

# ── ACCESS CODE ──────────────────────────────────────────────────────────────
CODE_HASH  = "46de5fb173c5ab12d2bbe17bbd05db3d902d8b042bba7f171945eeb281ab9d39"
CODE_LENGTH = 12
# ─────────────────────────────────────────────────────────────────────────────

STAGE_META = {
    1:  {"label": "First Call Scheduled",      "short": "#first call"},
    2:  {"label": "First Meeting Completed",   "short": "#meeting done"},
    3:  {"label": "Initial Demo Scheduled",    "short": "#demo scheduled"},
    4:  {"label": "Initial Demo Completed",    "short": "#demo completed"},
    5:  {"label": "Second Demo Scheduled",     "short": "#2nd demo sched"},
    6:  {"label": "Second Demo Completed",     "short": "#2nd demo done"},
    7:  {"label": "Proposal Meeting Scheduled","short": "#proposal mtg"},
    8:  {"label": "Proposal Sent",             "short": "#proposal sent"},
    9:  {"label": "Service Agreement Sent",    "short": "#service agg"},
    10: {"label": "Closed Lost",               "short": "#closed lost"},
    11: {"label": "Closed Won",                "short": "#closed won"},
}

PALETTE = [
    "#1d4ed8","#7c3aed","#059669","#d97706","#dc2626",
    "#0891b2","#db2777","#65a30d","#ea580c","#6d28d9","#0f766e"
]

def fetch_data(url):
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8")

def parse_week_start(w):
    s = w.split(" - ")[0].strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try: return datetime.strptime(s, fmt)
        except ValueError: pass
    return datetime.min

def short_week(w):
    s = w.split(" - ")[0].strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try: return datetime.strptime(s, fmt).strftime("%b %d")
        except ValueError: pass
    return w[:6]

def is_week_col(h):
    return " - " in h and any(m in h for m in
        ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])

def parse_csv(raw):
    delimiter = "\t" if "\t" in raw.split("\n")[0] else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        raise ValueError("No data rows found")
    headers = list(rows[0].keys())
    print(f"Headers: {headers[:6]}...")

    week_headers = [h for h in headers if is_week_col(h)]
    has_count_col = any(h.strip().lower() == "count" for h in headers)

    if week_headers:
        print("Detected: PIVOTED (wide) format")
        return parse_pivoted(rows, headers, week_headers)
    elif has_count_col:
        print("Detected: LONG (unpivoted) format")
        return parse_long(rows, headers)
    else:
        raise ValueError(f"Cannot detect format. Headers: {headers}")

def parse_pivoted(rows, headers, week_headers):
    sn_col    = next((h for h in headers if h.strip().lower() == "sn"), None)
    stage_col = next((h for h in headers if "funnel" in h.lower() or "stage" in h.lower()), None)
    if not sn_col or not stage_col:
        raise ValueError(f"Missing sn or stage column. Found: {headers}")

    weeks_sorted = sorted(week_headers, key=parse_week_start)
    week_labels  = [short_week(w) for w in weeks_sorted]

    stages = []
    for row in rows:
        try:
            sn = int(float(row[sn_col]))
        except (ValueError, KeyError):
            continue
        if sn not in STAGE_META:
            continue
        values = []
        for wh in weeks_sorted:
            v = row.get(wh, "")
            try:
                values.append(int(float(v)) if str(v).strip() not in ("", "nan") else 0)
            except ValueError:
                values.append(0)
        stages.append({
            "sn": sn,
            "label": STAGE_META[sn]["label"],
            "short": STAGE_META[sn]["short"],
            "total": sum(values),
            "values": values,
        })
    stages.sort(key=lambda s: s["sn"])
    return week_labels, stages

def parse_long(rows, headers):
    week_col  = next((h for h in headers if "week" in h.lower()), None)
    sn_col    = next((h for h in headers if h.strip().lower() == "sn"), None)
    count_col = next((h for h in headers if h.strip().lower() == "count"), None)
    if not all([week_col, sn_col, count_col]):
        raise ValueError(f"Missing columns for long format. Found: {headers}")

    weeks_raw, seen = [], set()
    stage_data = defaultdict(lambda: defaultdict(int))
    for row in rows:
        week = row[week_col].strip()
        if not week: continue
        if week not in seen:
            weeks_raw.append(week)
            seen.add(week)
        try:
            sn    = int(float(row[sn_col]))
            count = int(float(row[count_col]))
            stage_data[sn][week] += count
        except (ValueError, KeyError):
            continue

    weeks_sorted = sorted(weeks_raw, key=parse_week_start)
    week_labels  = [short_week(w) for w in weeks_sorted]
    stages = []
    for sn in sorted(STAGE_META.keys()):
        if sn not in stage_data: continue
        values = [stage_data[sn].get(w, 0) for w in weeks_sorted]
        stages.append({"sn": sn, "label": STAGE_META[sn]["label"],
                       "short": STAGE_META[sn]["short"],
                       "total": sum(values), "values": values})
    return week_labels, stages

def peak_week(values, weeks):
    if not values or max(values) == 0: return "N/A"
    return weeks[values.index(max(values))]

def safe_pct(n, d):
    return f"{n/d*100:.1f}" if d else "N/A"

def stages_to_js(stages, weeks):
    js = "[\n"
    for s in stages:
        js += f'  {{sn:{s["sn"]},label:"{s["label"]}",short:"{s["short"]}",total:{s["total"]},values:{s["values"]},peak:"{peak_week(s["values"], weeks)}"}},\n'
    js += "]"
    return js

def build_sales_motion_section():
    AE   = '<span style="font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:2px 7px;border-radius:3px;background:#0A0A0A;color:#FFFFFF;font-family:Inter,sans-serif;">AE</span>'
    CS   = '<span style="font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:2px 7px;border-radius:3px;background:#F5D000;color:#0A0A0A;font-family:Inter,sans-serif;">CS Team</span>'
    PRE  = '<span style="font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:2px 7px;border-radius:3px;background:#E8E8E4;color:#6B6B6B;font-family:Inter,sans-serif;">Pre-Pipeline</span>'
    INF  = '<span style="font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:2px 7px;border-radius:3px;background:#E8E8E4;color:#6B6B6B;font-family:Inter,sans-serif;">CS-Informed</span>'
    CLO  = '<span style="font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:2px 7px;border-radius:3px;background:#1A9E5F;color:#FFFFFF;font-family:Inter,sans-serif;">Close</span>'

    def alert_red(msg):
        return f'<div style="margin-top:7px;font-size:0.68rem;font-family:Inter,monospace;color:#E03030;background:#FFF8F8;border:1px solid #E03030;padding:3px 8px;border-radius:3px;display:inline-block;letter-spacing:0.02em;">{msg}</div>'

    def alert_green(msg):
        return f'<div style="margin-top:7px;font-size:0.68rem;font-family:Inter,monospace;color:#1A9E5F;background:#F5FFF9;border:1px solid #1A9E5F;padding:3px 8px;border-radius:3px;display:inline-block;letter-spacing:0.02em;">{msg}</div>'

    def step_row(n, badges, name, desc, alert="", bg="", numbg=""):
        return f"""<div style="display:flex;border-bottom:1px solid #E8E8E4;{bg}">
            <div style="width:48px;flex-shrink:0;border-right:1px solid #E8E8E4;display:flex;align-items:flex-start;justify-content:center;padding:18px 0;font-size:0.65rem;font-weight:700;font-family:Inter,sans-serif;letter-spacing:0.08em;color:#6B6B6B;{numbg}">{n}</div>
            <div style="padding:14px 18px;flex:1;">
              <div style="margin-bottom:7px;display:flex;gap:6px;flex-wrap:wrap;">{badges}</div>
              <div style="font-size:0.82rem;font-weight:600;margin-bottom:3px;color:#0A0A0A;letter-spacing:-0.01em;font-family:Inter,sans-serif;">{name}</div>
              <div style="font-size:0.72rem;color:#6B6B6B;line-height:1.6;font-family:Inter,sans-serif;">{desc}</div>
              {alert}
            </div>
          </div>"""

    current_steps = "".join([
        step_row("01", AE, "Intro Call",
            "AE runs all qualification and discovery from scratch — no prior context. ICP fit, pain, and interest assessed entirely on the AE&#39;s time before pipeline is confirmed.",
            alert_red("↑ AE capacity consumed on unqualified leads")),
        step_row("02", AE, "1st Demo Call",
            "Linear, scripted product walkthrough. Generalized overview not anchored to specific customer pain. Discovery continues here, late in the cycle.",
            alert_red("↓ Largest drop-off in funnel at this stage")),
        step_row("03", AE, "2nd Demo Call",
            "Broader stakeholder demo. Additional use-case detail and discovery. Pain framing built on the fly rather than established upstream."),
        step_row("04", AE, "Proposal Call",
            "Proposal reviewed with customer. Weak connection between solution and stated pain due to shallow earlier discovery."),
        step_row("05", AE, "Next Steps Call",
            "Address outstanding hurdles and roadblocks. Work toward contract signature."),
        step_row("06", AE, "Contract Sent",
            "Service agreement delivered to prospect."),
        step_row("07", CLO, "Closed Won",
            "Deal closed."),
    ])

    proposed_steps = "".join([
        step_row("—", CS + "&nbsp;" + PRE, "CS Qualification",
            "Before AE engagement, CS vets the opportunity using a structured question set. Pain, urgency, stakeholder map, and implementation readiness are documented and passed to the AE as a pre-call brief.",
            alert_green("Pipeline clock starts at Step 1 →"),
            bg="background:#F5FFF9;", numbg="background:#F5FFF9;"),
        step_row("01", AE + "&nbsp;" + INF, "Intro Call / 1st Demo",
            "AE opens with targeted discovery to validate and deepen the CS findings — connecting identified pain directly to solution capability. Demo is built around confirmed problems, not a generic script.",
            alert_green("↑ Demo relevance drives higher Stage 1→2 conversion")),
        step_row("02", AE, "2nd Demo Call",
            "Full stakeholder and decision-maker session. Demo is scoped to the use cases and objections most relevant to the economic buyer and key influencers — not a repeat of the first call."),
        step_row("03", AE, "Proposal Call",
            "Proposal is anchored to pain surfaced in CS qualification and confirmed in the intro call. Discussion is structured around anticipated objections — addressing concerns head-on rather than presenting features.",
            alert_green("↑ Objection-led discussion replaces generic proposal walkthrough")),
        step_row("04", AE, "Next Steps Call",
            "Address outstanding hurdles and roadblocks. Work toward contract signature."),
        step_row("05", AE, "Contract Sent",
            "Service agreement delivered to customer."),
        step_row("06", CLO, "Closed Won",
            "Target: higher close rate through better qualification, demo precision, and proactive objection handling."),
    ])

    return f"""
<section id="motion" style="padding:4rem 3rem;border-bottom:1px solid #E8E8E4;">
  <div style="display:flex;align-items:baseline;gap:1rem;margin-bottom:2.5rem;">
    <span style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6B6B6B;font-family:Inter,sans-serif;min-width:2rem;">06</span>
    <h2 style="font-family:Inter,sans-serif;font-size:1.4rem;font-weight:700;letter-spacing:-0.6px;color:#0A0A0A;">Sales Motion Redesign</h2>
    <span style="font-size:0.78rem;color:#6B6B6B;margin-left:auto;max-width:340px;text-align:right;line-height:1.5;font-family:Inter,sans-serif;">Recommendation to leadership — not subject to data refresh</span>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#E8E8E4;border:1px solid #E8E8E4;border-radius:10px;overflow:hidden;margin-bottom:1.5rem;">
    <div style="background:#FFFFFF;">
      <div style="padding:1.25rem 1.5rem;border-bottom:1px solid #E8E8E4;display:flex;align-items:center;justify-content:space-between;">
        <div>
          <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6B6B6B;margin-bottom:4px;font-family:Inter,sans-serif;">01 — Current State</div>
          <div style="font-size:1rem;font-weight:700;letter-spacing:-0.5px;color:#0A0A0A;font-family:Inter,sans-serif;">AE-Owned Full Cycle</div>
          <div style="font-size:0.72rem;color:#6B6B6B;margin-top:2px;font-family:Inter,sans-serif;">Qualification through close carried entirely by AE</div>
        </div>
        <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:4px 10px;border-radius:4px;background:#FFF8F8;color:#E03030;border:1px solid #E03030;white-space:nowrap;font-family:Inter,sans-serif;">Current</span>
      </div>
      <div>{current_steps}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #E8E8E4;">
        <div style="padding:14px 18px;border-right:1px solid #E8E8E4;">
          <div style="font-size:1.4rem;font-weight:700;color:#E03030;margin-bottom:2px;letter-spacing:-0.5px;font-family:Inter,sans-serif;">1.5–3 mo</div>
          <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#6B6B6B;font-family:Inter,sans-serif;">Avg. Cycle Length</div>
        </div>
        <div style="padding:14px 18px;">
          <div style="font-size:1.4rem;font-weight:700;color:#E03030;margin-bottom:2px;letter-spacing:-0.5px;font-family:Inter,sans-serif;">7 Steps</div>
          <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#6B6B6B;font-family:Inter,sans-serif;">AE-Owned Stages</div>
        </div>
      </div>
    </div>
    <div style="background:#FFFFFF;">
      <div style="padding:1.25rem 1.5rem;border-bottom:1px solid #E8E8E4;display:flex;align-items:center;justify-content:space-between;">
        <div>
          <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6B6B6B;margin-bottom:4px;font-family:Inter,sans-serif;">02 — Proposed State</div>
          <div style="font-size:1rem;font-weight:700;letter-spacing:-0.5px;color:#0A0A0A;font-family:Inter,sans-serif;">CS-Qualified, AE Closes</div>
          <div style="font-size:0.72rem;color:#6B6B6B;margin-top:2px;font-family:Inter,sans-serif;">CS qualifies pre-pipeline — AE enters demo-ready</div>
        </div>
        <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:4px 10px;border-radius:4px;background:#F5FFF9;color:#1A9E5F;border:1px solid #1A9E5F;white-space:nowrap;font-family:Inter,sans-serif;">Proposed</span>
      </div>
      <div>{proposed_steps}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #E8E8E4;">
        <div style="padding:14px 18px;border-right:1px solid #E8E8E4;">
          <div style="font-size:1.4rem;font-weight:700;color:#1A9E5F;margin-bottom:2px;letter-spacing:-0.5px;font-family:Inter,sans-serif;">1–2 mo</div>
          <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#6B6B6B;font-family:Inter,sans-serif;">Target Cycle Length</div>
        </div>
        <div style="padding:14px 18px;">
          <div style="font-size:1.4rem;font-weight:700;color:#1A9E5F;margin-bottom:2px;letter-spacing:-0.5px;font-family:Inter,sans-serif;">↑ Close %</div>
          <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#6B6B6B;font-family:Inter,sans-serif;">Via Qualification + Demo Quality</div>
        </div>
      </div>
    </div>
  </div>

  <div style="background:#0A0A0A;border:1px solid #0A0A0A;border-radius:10px;overflow:hidden;">
    <div style="padding:14px 20px;border-bottom:1px solid #1E1E1E;display:flex;align-items:center;gap:10px;">
      <div style="width:28px;height:28px;background:#F5D000;border-radius:4px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="5" stroke="#0A0A0A" stroke-width="1.5"/><path d="M6 4v3M6 8.5v.5" stroke="#0A0A0A" stroke-width="1.5" stroke-linecap="round"/></svg>
      </div>
      <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.4);font-family:Inter,sans-serif;">Key Funnel Findings — Basis for Recommendation</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;padding:1.5rem;gap:2rem;">
      <div>
        <div style="font-size:2rem;font-weight:700;color:#F5D000;margin-bottom:4px;letter-spacing:-0.8px;font-family:Inter,sans-serif;">25.3%</div>
        <div style="font-size:0.8rem;font-weight:600;margin-bottom:6px;color:#FFFFFF;letter-spacing:-0.3px;font-family:Inter,sans-serif;">Demo-to-2nd Demo Conversion</div>
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);line-height:1.7;font-family:Inter,sans-serif;">79 Initial Demos Completed → 20 Second Demos Scheduled. Largest absolute volume drop in the funnel. Root cause: generic, scripted demos with no pain-specific positioning established before the call.</div>
      </div>
      <div style="border-left:1px solid #1E1E1E;padding-left:2rem;">
        <div style="font-size:2rem;font-weight:700;color:#F5D000;margin-bottom:4px;letter-spacing:-0.8px;font-family:Inter,sans-serif;">47.4%</div>
        <div style="font-size:0.8rem;font-weight:600;margin-bottom:6px;color:#FFFFFF;letter-spacing:-0.3px;font-family:Inter,sans-serif;">Proposal-to-Contract Conversion</div>
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);line-height:1.7;font-family:Inter,sans-serif;">38 Proposals Sent → 18 Service Agreements. Late-stage dropout indicates unresolved objections entering the proposal stage. Structured objection handling in the proposal discussion directly addresses this gap.</div>
      </div>
    </div>
  </div>
</section>"""


def build_html(weeks, stages, icp_weeks, icp_stages, generated_at):
    kpi  = {s["sn"]: s for s in stages}
    top  = kpi[1]["total"] if 1 in kpi else 1

    show_rate     = safe_pct(kpi[2]["total"], kpi[1]["total"]) if 2 in kpi and 1 in kpi else "N/A"
    close_rate    = safe_pct(kpi[11]["total"], top) if 11 in kpi else "N/A"
    prop_to_close = safe_pct(kpi[11]["total"], kpi[8]["total"]) if 11 in kpi and 8 in kpi else "N/A"
    prop_top      = safe_pct(kpi[8]["total"], top) if 8 in kpi else "N/A"
    demo_top      = safe_pct(kpi[4]["total"], top) if 4 in kpi else "N/A"
    second_demo_r = safe_pct(kpi[5]["total"], kpi[4]["total"]) if 5 in kpi and 4 in kpi else "N/A"
    loss_ratio    = f"{kpi[10]['total']/kpi[11]['total']:.1f}x" if 11 in kpi and kpi[11]["total"] else "N/A"
    close_meeting = safe_pct(kpi[11]["total"], kpi[2]["total"]) if 11 in kpi and 2 in kpi else "N/A"
    close_demo_rate = safe_pct(kpi[11]["total"], kpi[3]["total"]) if 11 in kpi and 3 in kpi else "N/A"
    avg_weekly    = f"{top/len(weeks):.1f}" if weeks else "N/A"
    peak_val      = max(kpi[1]["values"]) if 1 in kpi else 0
    peak_wk       = peak_week(kpi[1]["values"], weeks) if 1 in kpi else "N/A"
    vals_excl     = [v for v in kpi[1]["values"] if v != peak_val] if 1 in kpi else []
    avg_excl      = f"{sum(vals_excl)/len(vals_excl):.1f}" if vals_excl else "N/A"
    spike_mult    = f"{peak_val/(top/len(weeks)):.1f}" if weeks and top else "N/A"

    sales_motion_html = build_sales_motion_section()

    js_weeks      = str(weeks).replace("'", '"')
    js_icp_weeks  = str(icp_weeks).replace("'", '"')
    js_pal        = str(PALETTE).replace("'", '"')
    js_stages     = stages_to_js(stages, weeks)
    js_icp_stages = stages_to_js(icp_stages, icp_weeks)

    # ICP summary stats for the toggle bar
    icp_kpi = {s["sn"]: s for s in icp_stages}
    icp_top = icp_kpi[1]["total"] if 1 in icp_kpi else 0
    icp_close = safe_pct(icp_kpi[11]["total"], icp_top) if 11 in icp_kpi and icp_top else "N/A"
    icp_won = icp_kpi[11]["total"] if 11 in icp_kpi else 0
    icp_weeks_count = len(icp_weeks)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KeychainOS — Sales Funnel Review</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #F7F7F5;
    --surface: #FFFFFF;
    --border: #E8E8E4;
    --text: #0A0A0A;
    --muted: #6B6B6B;
    --accent: #F5D000;
    --red: #E03030;
    --red-bg: #FFF8F8;
    --green: #1A9E5F;
    --green-bg: #F5FFF9;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Inter',sans-serif; line-height:1.6; }}

  nav {{
    position:sticky; top:0; z-index:100;
    background:rgba(247,247,245,0.95);
    backdrop-filter:blur(8px);
    border-bottom:1px solid var(--border);
    padding:0 3rem;
    display:flex; align-items:center; justify-content:space-between;
    height:52px;
  }}
  .nav-brand {{ font-size:0.88rem; font-weight:700; letter-spacing:-0.3px; color:var(--text); }}
  .nav-brand span {{ color:var(--muted); font-weight:400; }}
  .nav-links {{ display:flex; gap:2rem; list-style:none; }}
  .nav-links a {{
    font-size:0.65rem; font-weight:700; letter-spacing:0.08em;
    text-transform:uppercase; color:var(--muted);
    text-decoration:none; transition:color 0.15s;
  }}
  .nav-links a:hover {{ color:var(--text); }}
  .nav-date {{ font-size:0.65rem; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted); }}

  .hero {{
    padding:4rem 3rem 3.5rem;
    border-bottom:1px solid var(--border);
    display:grid; grid-template-columns:1fr 1fr;
    gap:4rem; align-items:end;
  }}
  .hero-eyebrow {{
    font-size:0.65rem; font-weight:700; letter-spacing:0.1em;
    text-transform:uppercase; color:var(--muted); margin-bottom:1rem;
  }}
  .hero h1 {{
    font-size:3rem; font-weight:700; line-height:1.05;
    letter-spacing:-0.8px; color:var(--text);
  }}
  .hero h1 em {{ font-style:normal; color:var(--muted); font-weight:300; }}
  .hero-desc {{ font-size:0.88rem; color:var(--muted); margin-top:1.25rem; max-width:400px; line-height:1.7; }}
  .hero-meta {{ display:flex; flex-direction:column; gap:0; border:1px solid var(--border); border-radius:10px; overflow:hidden; background:var(--surface); }}
  .meta-item {{
    padding:1rem 1.25rem;
    border-bottom:1px solid var(--border);
    display:flex; justify-content:space-between; align-items:center;
  }}
  .meta-item:last-child {{ border-bottom:none; }}
  .meta-label {{ font-size:0.65rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--muted); }}
  .meta-value {{ font-size:0.95rem; font-weight:700; letter-spacing:-0.3px; color:var(--text); }}
  .meta-value.accent {{ color:var(--text); background:var(--accent); padding:2px 8px; border-radius:3px; }}

  section {{ padding:4rem 3rem; border-bottom:1px solid var(--border); }}
  .section-header {{ display:flex; align-items:baseline; gap:1rem; margin-bottom:2.5rem; }}
  .section-num {{ font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:var(--muted); min-width:2rem; }}
  .section-title {{ font-size:1.4rem; font-weight:700; letter-spacing:-0.6px; color:var(--text); }}
  .section-subtitle {{ font-size:0.78rem; color:var(--muted); margin-left:auto; max-width:340px; text-align:right; line-height:1.5; }}

  .kpi-grid {{
    display:grid; grid-template-columns:repeat(4,1fr);
    gap:1px; background:var(--border);
    border:1px solid var(--border); border-radius:10px;
    overflow:hidden; margin-bottom:1.5rem;
  }}
  .kpi-card {{ background:var(--surface); padding:1.5rem; }}
  .kpi-label {{ font-size:0.62rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--muted); margin-bottom:0.5rem; }}
  .kpi-value {{ font-size:2.2rem; font-weight:700; letter-spacing:-0.8px; color:var(--text); line-height:1; }}
  .kpi-sub {{ font-size:0.72rem; color:var(--muted); margin-top:0.35rem; }}
  .kpi-badge {{
    display:inline-flex; font-size:0.62rem; font-weight:700;
    letter-spacing:0.06em; text-transform:uppercase;
    padding:2px 7px; border-radius:3px;
    width:fit-content; margin-top:0.5rem;
  }}
  .kpi-badge.green {{ background:var(--green-bg); color:var(--green); border:1px solid var(--green); }}
  .kpi-badge.amber {{ background:#FFFBEB; color:#92400E; border:1px solid #D97706; }}
  .kpi-badge.featured {{ background:var(--accent); color:var(--text); }}

  .pipeline-table {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
  .pipeline-table th {{
    font-size:0.62rem; font-weight:700; letter-spacing:0.08em;
    text-transform:uppercase; color:var(--muted);
    text-align:left; padding:0.6rem 1rem;
    border-bottom:2px solid var(--border);
    background:var(--bg);
  }}
  .pipeline-table td {{ padding:0.85rem 1rem; border-bottom:1px solid var(--border); vertical-align:middle; }}
  .pipeline-table tr:last-child td {{ border-bottom:none; }}
  .pipeline-table tr:hover td {{ background:var(--bg); }}
  .stage-dot {{ display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:0.5rem; }}
  .stage-name {{ display:flex; align-items:center; font-weight:600; color:var(--text); font-size:0.8rem; }}
  .conv-bar-wrap {{ display:flex; align-items:center; gap:0.75rem; }}
  .conv-bar-bg {{ flex:1; height:4px; background:var(--border); border-radius:2px; overflow:hidden; }}
  .conv-bar-fill {{ height:100%; border-radius:2px; }}
  .conv-pct {{ font-size:0.75rem; font-weight:700; min-width:38px; text-align:right; }}
  .total-num {{ font-weight:700; font-size:0.9rem; color:var(--text); }}
  .peak-week {{ font-size:0.72rem; color:var(--muted); font-weight:500; }}
  .hide-row-btn {{
    background:none; border:1px solid var(--border); border-radius:4px;
    font-size:0.62rem; font-weight:700; color:var(--muted);
    padding:0.2rem 0.45rem; cursor:pointer;
    font-family:'Inter',sans-serif; letter-spacing:0.06em;
    text-transform:uppercase; transition:all 0.15s;
  }}
  .hide-row-btn:hover {{ border-color:var(--red); color:var(--red); }}
  .conv-row-hidden {{ display:none; }}
  .show-hidden-btn {{
    font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700;
    letter-spacing:0.08em; text-transform:uppercase; color:var(--muted);
    background:none; border:1px solid var(--border); border-radius:4px;
    padding:0.35rem 0.85rem; cursor:pointer; margin-top:0.75rem;
    transition:all 0.15s;
  }}
  .show-hidden-btn:hover {{ color:var(--text); border-color:var(--text); }}

  .chart-controls {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:1.25rem; flex-wrap:wrap; gap:1rem; }}
  .chart-actions {{ display:flex; gap:0.5rem; }}
  .btn {{
    font-family:'Inter',sans-serif; font-size:0.62rem; font-weight:700;
    letter-spacing:0.08em; text-transform:uppercase;
    padding:0.35rem 0.85rem; border:1px solid var(--border);
    border-radius:4px; cursor:pointer; background:var(--surface);
    color:var(--muted); transition:all 0.15s;
  }}
  .btn:hover {{ background:var(--text); color:var(--accent); border-color:var(--text); }}
  .chart-layout {{ display:grid; grid-template-columns:1fr 200px; gap:1.5rem; align-items:start; }}
  .chart-box {{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:1.5rem; height:420px; }}
  .legend-panel {{ display:flex; flex-direction:column; gap:0; border:1px solid var(--border); border-radius:10px; overflow:hidden; background:var(--surface); }}
  .leg-item {{
    display:flex; align-items:center; gap:0.6rem;
    padding:0.5rem 0.75rem; cursor:pointer; transition:all 0.15s;
    border-bottom:1px solid var(--border); user-select:none;
  }}
  .leg-item:last-child {{ border-bottom:none; }}
  .leg-item:hover {{ background:var(--bg); }}
  .leg-item.off {{ opacity:0.3; }}
  .leg-swatch {{ width:16px; height:3px; border-radius:1px; flex-shrink:0; }}
  .leg-label {{ font-size:0.62rem; font-weight:600; flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; color:var(--text); }}
  .leg-total {{ font-size:0.62rem; font-weight:700; color:var(--muted); }}

  .trend-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--border); border:1px solid var(--border); border-radius:10px; overflow:hidden; margin-bottom:1px; }}
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--border); border:1px solid var(--border); border-radius:10px; overflow:hidden; margin-bottom:1.5rem; }}
  .trend-card {{ background:var(--surface); padding:1.5rem; }}
  .trend-card-header {{ display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:1rem; }}
  .trend-icon {{
    width:32px; height:32px; border-radius:4px;
    display:flex; align-items:center; justify-content:center; font-size:0.9rem;
    flex-shrink:0;
  }}
  .trend-icon.yellow {{ background:var(--accent); }}
  .trend-icon.green {{ background:var(--green-bg); border:1px solid var(--green); }}
  .trend-icon.amber {{ background:#FFFBEB; border:1px solid #D97706; }}
  .trend-tag {{
    font-size:0.6rem; font-weight:700; letter-spacing:0.1em;
    text-transform:uppercase; padding:2px 7px; border-radius:3px;
  }}
  .trend-tag.positive {{ background:var(--green-bg); color:var(--green); border:1px solid var(--green); }}
  .trend-tag.watch {{ background:#FFFBEB; color:#92400E; border:1px solid #D97706; }}
  .trend-tag.insight {{ background:var(--accent); color:var(--text); }}
  .trend-card h3 {{ font-size:0.88rem; font-weight:700; letter-spacing:-0.3px; margin-bottom:0.5rem; color:var(--text); }}
  .trend-card p {{ font-size:0.75rem; color:var(--muted); line-height:1.65; }}
  .trend-card strong {{ color:var(--text); font-weight:700; }}
  .corr-box {{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:1.5rem; height:280px; margin-top:1.5rem; }}

  .alert-block {{
    display:flex; gap:0.75rem; padding:1rem 1.25rem;
    background:#0A0A0A; border-radius:10px;
    margin-top:1.5rem; font-size:0.78rem; line-height:1.6;
    color:rgba(255,255,255,0.6);
  }}
  .alert-icon {{
    width:28px; height:28px; background:var(--accent); border-radius:4px;
    display:flex; align-items:center; justify-content:center;
    font-size:0.8rem; flex-shrink:0; margin-top:0.1rem;
  }}
  .alert-block strong {{ color:#FFFFFF; font-weight:700; }}

  /* ── DATASET TOGGLE (ICP) ── */
  .ds-toggle-bar {{
    display:flex; align-items:center; gap:0;
    border:1px solid var(--border); border-radius:8px;
    overflow:hidden; background:var(--surface);
    margin-bottom:1.5rem;
  }}
  .ds-tab {{
    flex:1; padding:0.75rem 1.25rem;
    display:flex; align-items:center; justify-content:space-between;
    cursor:pointer; transition:background 0.15s; user-select:none;
    border-right:1px solid var(--border);
  }}
  .ds-tab:last-child {{ border-right:none; }}
  .ds-tab:hover {{ background:var(--bg); }}
  .ds-tab.ds-active {{ background:var(--accent); }}
  .ds-tab.ds-active .ds-tab-label {{ color:var(--text); }}
  .ds-tab.ds-active .ds-tab-meta {{ color:rgba(10,10,10,0.55); }}
  .ds-tab-label {{
    font-size:0.78rem; font-weight:700; letter-spacing:-0.2px;
    color:var(--text);
  }}
  .ds-tab-meta {{
    font-size:0.62rem; font-weight:600; letter-spacing:0.06em;
    text-transform:uppercase; color:var(--muted);
    text-align:right;
  }}
  .ds-tab-sub {{
    font-size:0.62rem; color:var(--muted); margin-top:1px;
  }}
  .ds-tab.ds-active .ds-tab-sub {{ color:rgba(10,10,10,0.5); }}

  /* ── COHORT FILTERS ── */
  .cf-grid {{
    display:grid; grid-template-columns:1fr 1fr;
    gap:1px; background:var(--border);
    border:1px solid var(--border); border-radius:10px;
    overflow:hidden; margin-bottom:1.5rem;
  }}
  .cf-row {{
    display:flex; align-items:center; gap:0.85rem;
    padding:0.85rem 1.25rem;
    border-bottom:1px solid var(--border);
    cursor:pointer; transition:background 0.12s;
    user-select:none; background:var(--surface);
  }}
  .cf-row:last-child {{ border-bottom:none; }}
  .cf-row:nth-child(3) {{ border-bottom:none; }}
  .cf-row:hover {{ background:var(--bg); }}
  .cf-row.cf-active {{ background:var(--red-bg); }}
  .cf-toggle {{
    width:34px; height:19px; border-radius:10px;
    background:var(--border); position:relative;
    transition:background 0.2s; flex-shrink:0;
    border:1px solid var(--border);
  }}
  .cf-toggle::after {{
    content:''; position:absolute;
    width:13px; height:13px; border-radius:50%;
    background:#fff; top:2px; left:2px;
    transition:transform 0.2s;
    box-shadow:0 1px 2px rgba(0,0,0,0.2);
  }}
  .cf-row.cf-active .cf-toggle {{ background:var(--red); border-color:var(--red); }}
  .cf-row.cf-active .cf-toggle::after {{ transform:translateX(15px); }}
  .cf-info {{ flex:1; min-width:0; }}
  .cf-name {{ font-size:0.78rem; font-weight:700; color:var(--text); letter-spacing:-0.2px; }}
  .cf-row.cf-active .cf-name {{ color:var(--red); }}
  .cf-desc {{ font-size:0.65rem; color:var(--muted); margin-top:1px; line-height:1.4; }}
  .cf-tag {{
    font-size:0.58rem; font-weight:700; letter-spacing:0.07em; text-transform:uppercase;
    padding:2px 6px; border-radius:3px; white-space:nowrap; flex-shrink:0;
  }}
  .cf-tag-week {{ background:var(--bg); color:var(--muted); border:1px solid var(--border); }}
  .cf-tag-stage {{ background:#EEF2FF; color:#3730a3; border:1px solid #C7D2FE; }}
  .cf-bar {{
    border-top:1px solid var(--border);
    background:#0A0A0A; padding:0.85rem 1.5rem;
    display:flex; align-items:center; gap:2rem;
    border-radius:0 0 10px 10px;
  }}
  .cf-bar-label {{ font-size:0.6rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:rgba(255,255,255,0.35); white-space:nowrap; }}
  .cf-metrics {{ display:flex; gap:2rem; flex:1; }}
  .cf-metric-val {{ font-size:1rem; font-weight:700; letter-spacing:-0.3px; color:#fff; }}
  .cf-metric-val.y {{ color:var(--accent); }}
  .cf-metric-val.r {{ color:var(--red); }}
  .cf-metric-lbl {{ font-size:0.58rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:rgba(255,255,255,0.35); margin-top:1px; }}
  .cf-apply {{
    font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
    padding:7px 16px; border-radius:4px;
    background:var(--accent); color:#0A0A0A;
    border:none; cursor:pointer; font-family:'Inter',sans-serif;
    transition:opacity 0.15s; white-space:nowrap;
  }}
  .cf-apply:hover {{ opacity:0.85; }}
  .cf-apply:disabled {{ background:var(--border); color:var(--muted); cursor:default; opacity:1; }}
  .cf-chips {{
    display:flex; gap:0.4rem; flex-wrap:wrap; align-items:center;
    padding:0.7rem 1.25rem; border-top:1px solid var(--border);
    background:var(--bg); min-height:40px;
  }}
  .cf-chips-lbl {{ font-size:0.6rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--muted); flex-shrink:0; }}
  .cf-chip {{
    display:inline-flex; align-items:center; gap:4px;
    font-size:0.62rem; font-weight:600;
    padding:2px 7px; border-radius:3px;
    background:var(--red-bg); color:var(--red); border:1px solid #FCCACA;
  }}
  .cf-chip-x {{
    width:11px; height:11px; border-radius:50%;
    background:var(--red); color:#fff;
    display:inline-flex; align-items:center; justify-content:center;
    font-size:0.5rem; cursor:pointer; font-weight:700; line-height:1;
  }}
  .cf-none {{ font-size:0.65rem; color:var(--muted); font-style:italic; }}

  /* ── CLOSE RATE BASE TOGGLE ── */
  .cr-toggle-bar {{
    display:flex; align-items:stretch;
    border:1px solid var(--border); border-radius:8px;
    overflow:hidden; background:var(--surface);
    margin-bottom:1rem;
  }}
  .cr-tab {{
    flex:1; padding:0.65rem 1.25rem;
    display:flex; align-items:center; justify-content:space-between;
    cursor:pointer; transition:background 0.15s; user-select:none;
    border-right:1px solid var(--border);
  }}
  .cr-tab:last-child {{ border-right:none; }}
  .cr-tab:hover {{ background:var(--bg); }}
  .cr-tab.cr-active {{ background:#0A0A0A; }}
  .cr-tab.cr-active .cr-tab-label {{ color:#FFFFFF; }}
  .cr-tab.cr-active .cr-tab-sub {{ color:rgba(255,255,255,0.4); }}
  .cr-tab.cr-active .cr-tab-meta {{ color:var(--accent); }}
  .cr-tab-label {{
    font-size:0.78rem; font-weight:700; letter-spacing:-0.2px; color:var(--text);
  }}
  .cr-tab-sub {{ font-size:0.62rem; color:var(--muted); margin-top:1px; }}
  .cr-tab-meta {{
    font-size:0.65rem; font-weight:700; letter-spacing:0.04em;
    color:var(--muted); white-space:nowrap; margin-left:1.5rem; flex-shrink:0;
  }}

  /* ICP banner shown when ICP mode is active */
  .icp-banner {{
    display:none; align-items:center; gap:0.75rem;
    padding:0.65rem 1.25rem;
    background:var(--accent); border-radius:8px;
    margin-bottom:1.5rem;
    font-size:0.72rem; font-weight:600; color:#0A0A0A;
    font-family:'Inter',sans-serif;
  }}
  .icp-banner.visible {{ display:flex; }}
  .icp-banner-dot {{
    width:8px; height:8px; border-radius:50%;
    background:#0A0A0A; flex-shrink:0;
  }}

  footer {{
    padding:1.5rem 3rem;
    display:flex; align-items:center; justify-content:space-between;
    border-top:1px solid var(--border);
  }}
  .footer-left {{ font-size:0.65rem; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted); }}
  .footer-right {{ font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:var(--muted); }}

  .dbox {{
    width:36px; height:44px;
    border:1px solid var(--border); border-radius:6px;
    text-align:center; font-size:1.1rem;
    font-family:'Inter',sans-serif; font-weight:700;
    color:var(--text); background:var(--surface);
    outline:none; transition:border-color 0.15s;
  }}
  .dbox:focus {{ border-color:var(--text); box-shadow:0 0 0 3px rgba(245,208,0,0.25); }}
  .dbox.err {{ border-color:var(--red); animation:shake 0.3s ease; }}
  @keyframes shake {{ 0%,100%{{transform:translateX(0);}} 25%{{transform:translateX(-4px);}} 75%{{transform:translateX(4px);}} }}

  @media(max-width:900px) {{
    nav {{ padding:0 1.5rem; }}
    .hero, section {{ padding:3rem 1.5rem; }}
    .hero {{ grid-template-columns:1fr; }}
    .kpi-grid {{ grid-template-columns:repeat(2,1fr); }}
    .chart-layout {{ grid-template-columns:1fr; }}
    .trend-grid, .two-col {{ grid-template-columns:1fr; }}
    footer {{ padding:1.5rem; flex-direction:column; gap:0.5rem; }}
    .ds-toggle-bar {{ flex-direction:column; }}
    .ds-tab {{ border-right:none; border-bottom:1px solid var(--border); }}
  }}
</style>
</head>
<body>

<!-- ── ACCESS GATE ── -->
<div id="gate" style="position:fixed;inset:0;background:var(--bg);z-index:9999;display:flex;align-items:center;justify-content:center;">
  <div style="text-align:center;max-width:400px;width:100%;padding:2rem;">
    <div style="font-size:1.4rem;font-weight:700;letter-spacing:-0.5px;margin-bottom:0.25rem;font-family:'Inter',sans-serif;color:#0A0A0A;">Keychain<span style="font-weight:300;color:#6B6B6B;">OS</span></div>
    <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#6B6B6B;margin-bottom:2rem;font-family:'Inter',sans-serif;">Sales Funnel Review</div>
    <div style="font-size:0.78rem;color:#6B6B6B;margin-bottom:1.25rem;font-family:'Inter',sans-serif;">Enter access code to continue</div>
    <div style="display:flex;gap:0.4rem;justify-content:center;margin-bottom:1rem;flex-wrap:wrap;" id="digits">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
      <input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">
    </div>
    <div id="gate-error" style="font-size:0.72rem;color:var(--red);height:1rem;margin-bottom:0.5rem;font-family:'Inter',sans-serif;"></div>
  </div>
</div>

<script>
(function(){{
  const HASH="{CODE_HASH}";
  const LEN={CODE_LENGTH};
  const SK="kcos_v2";
  if(sessionStorage.getItem(SK)==="1"){{document.getElementById('gate').style.display='none';return;}}
  const boxes=document.querySelectorAll('.dbox');
  boxes[0].focus();
  async function sha256(msg){{
    const buf=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(msg));
    return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
  }}
  boxes.forEach((box,i)=>{{
    box.addEventListener('input',e=>{{
      box.value=e.target.value.slice(-1);
      if(box.value&&i<LEN-1)boxes[i+1].focus();
      const code=Array.from(boxes).map(b=>b.value).join('');
      if(code.length===LEN)check(code);
    }});
    box.addEventListener('keydown',e=>{{
      if(e.key==='Backspace'&&!box.value&&i>0)boxes[i-1].focus();
    }});
    box.addEventListener('paste',e=>{{
      e.preventDefault();
      const p=(e.clipboardData||window.clipboardData).getData('text').slice(0,LEN);
      p.split('').forEach((c,j)=>{{if(boxes[j])boxes[j].value=c;}});
      if(p.length===LEN)check(p);
    }});
  }});
  async function check(code){{
    const h=await sha256(code);
    if(h===HASH){{
      sessionStorage.setItem(SK,"1");
      const g=document.getElementById('gate');
      g.style.transition='opacity 0.3s';g.style.opacity='0';
      setTimeout(()=>g.style.display='none',300);
    }}else{{
      document.getElementById('gate-error').textContent='Incorrect code. Try again.';
      boxes.forEach(b=>{{b.value='';b.classList.add('err');}});
      setTimeout(()=>boxes.forEach(b=>b.classList.remove('err')),500);
      boxes[0].focus();
    }}
  }}
}})();
</script>

<!-- ── NAV ── -->
<nav>
  <div class="nav-brand">Keychain<span>OS</span></div>
  <ul class="nav-links">
    <li><a href="#filters">Filters</a></li>
    <li><a href="#kpis">KPIs</a></li>
    <li><a href="#chart">Trend</a></li>
    <li><a href="#conversion">Conversion</a></li>
    <li><a href="#insights">Insights</a></li>
    <li><a href="#motion">Motion</a></li>
  </ul>
  <div class="nav-date">Updated {generated_at}</div>
</nav>

<!-- ── HERO ── -->
<div class="hero">
  <div>
    <div class="hero-eyebrow">Sales Funnel Review · Weekly Cohort</div>
    <h1>First Intro<br><em>Funnel</em><br>Performance</h1>
    <p class="hero-desc">Week-over-week analysis across {len(stages)} funnel stages. Prepared for internal team and executive leadership.</p>
  </div>
  <div class="hero-meta">
    <div class="meta-item"><div class="meta-label">Weeks Tracked</div><div class="meta-value" id="hmWeeks">{len(weeks)} weeks</div></div>
    <div class="meta-item"><div class="meta-label">Funnel Stages</div><div class="meta-value" id="hmStages">{len(stages)} stages</div></div>
    <div class="meta-item"><div class="meta-label">Top-of-Funnel Volume</div><div class="meta-value" id="hmTof">{top} first calls</div></div>
    <div class="meta-item"><div class="meta-label">Overall Close Rate</div><div class="meta-value accent" id="hmClose">{close_rate}% ({kpi[11]['total'] if 11 in kpi else 'N/A'} won)</div></div>
  </div>
</div>

<!-- ── SECTION 01: COHORT FILTERS ── -->
<section id="filters">
  <div class="section-header">
    <span class="section-num">01</span>
    <h2 class="section-title">Cohort Filters</h2>
    <span class="section-subtitle">Select dataset, then apply week/stage exclusions</span>
  </div>

  <!-- ── DATASET TOGGLE ── -->
  <div class="ds-toggle-bar" id="dsToggle">
    <div class="ds-tab ds-active" id="dsTabAll" onclick="switchDataset('all')">
      <div>
        <div class="ds-tab-label">All Leads</div>
        <div class="ds-tab-sub">Full funnel dataset — all leads regardless of ICP fit</div>
      </div>
      <div class="ds-tab-meta">
        {top} calls · {close_rate}% close<br>
        {len(weeks)} weeks
      </div>
    </div>
    <div class="ds-tab" id="dsTabIcp" onclick="switchDataset('icp')">
      <div>
        <div class="ds-tab-label">ICP Only</div>
        <div class="ds-tab-sub">Close rate and cohort metrics on ICP-qualified leads only</div>
      </div>
      <div class="ds-tab-meta">
        {icp_top} calls · {icp_close}% close<br>
        {icp_weeks_count} weeks
      </div>
    </div>
  </div>

  <!-- ICP active banner -->
  <div class="icp-banner" id="icpBanner">
    <div class="icp-banner-dot"></div>
    ICP Filter Active — all KPIs, charts, and conversion rates reflect ICP-qualified leads only
  </div>

  <!-- ── CLOSE RATE BASE TOGGLE ── -->
  <div class="cr-toggle-bar" id="crToggle">
    <div class="cr-tab cr-active" id="crTabTof" onclick="switchCRBase(&apos;tof&apos;)">
      <div>
        <div class="cr-tab-label">vs. First Call Scheduled</div>
        <div class="cr-tab-sub">Close rate measured against top-of-funnel entries (sn 01)</div>
      </div>
      <div class="cr-tab-meta" id="crMetaTof">{close_rate}% close &middot; {kpi[1]["total"] if 1 in kpi else "N/A"} calls</div>
    </div>
    <div class="cr-tab" id="crTabDemo" onclick="switchCRBase(&apos;demo&apos;)">
      <div>
        <div class="cr-tab-label">vs. Initial Demo Scheduled</div>
        <div class="cr-tab-sub">Close rate measured against initial demo scheduled volume (sn 03)</div>
      </div>
      <div class="cr-tab-meta" id="crMetaDemo">{close_demo_rate}% close &middot; {kpi[3]["total"] if 3 in kpi else "N/A"} demos</div>
    </div>
  </div>

  <div class="cf-grid" id="cfGrid"></div>

  <div class="cf-chips" id="cfChips">
    <span class="cf-chips-lbl">Excluded:</span>
    <span class="cf-none" id="cfNone">None — all data included</span>
  </div>

  <div class="cf-bar">
    <span class="cf-bar-label">Impact</span>
    <div class="cf-metrics">
      <div>
        <div class="cf-metric-val y" id="cfWeeksVal">—</div>
        <div class="cf-metric-lbl">Weeks Removed</div>
      </div>
      <div>
        <div class="cf-metric-val r" id="cfStagesVal">—</div>
        <div class="cf-metric-lbl">Stages Hidden</div>
      </div>
      <div>
        <div class="cf-metric-val" id="cfRetainVal">100%</div>
        <div class="cf-metric-lbl">Data Retained</div>
      </div>
    </div>
    <button class="cf-apply" id="cfApply" disabled onclick="applyFilters()">Apply Filters</button>
  </div>
</section>

<!-- ── SECTION 02: KPIs ── -->
<section id="kpis">
  <div class="section-header">
    <span class="section-num">02</span>
    <h2 class="section-title">Summary KPIs</h2>
    <span class="section-subtitle">Key volume and efficiency metrics across the full period</span>
  </div>
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">First Calls Scheduled</div>
      <div class="kpi-value" id="kv1">{kpi[1]['total'] if 1 in kpi else 'N/A'}</div>
      <div class="kpi-sub">Top of funnel entries</div>
      <div class="kpi-badge featured" id="ksPeak">Peak: {peak_wk} ({peak_val})</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Meetings Completed</div>
      <div class="kpi-value" id="kv2">{kpi[2]['total'] if 2 in kpi else 'N/A'}</div>
      <div class="kpi-sub" id="ks1">{show_rate}% show rate</div>
      <div class="kpi-badge green">Strong attendance</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Proposals Sent</div>
      <div class="kpi-value" id="kv8">{kpi[8]['total'] if 8 in kpi else 'N/A'}</div>
      <div class="kpi-sub" id="ks8">{prop_top}% of top-of-funnel</div>
      <div class="kpi-badge amber">Watch drop-off</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Closed Won</div>
      <div class="kpi-value" id="kv11">{kpi[11]['total'] if 11 in kpi else 'N/A'}</div>
      <div class="kpi-sub" id="ks11">{close_rate}% overall close rate</div>
      <div class="kpi-badge green">{prop_to_close}% of proposals</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Initial Demos Completed</div>
      <div class="kpi-value" id="kv4">{kpi[4]['total'] if 4 in kpi else 'N/A'}</div>
      <div class="kpi-sub">{demo_top}% of top-of-funnel</div>
      <div class="kpi-badge featured">Peak: {peak_week(kpi[4]['values'], weeks) if 4 in kpi else 'N/A'}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Second Demos Scheduled</div>
      <div class="kpi-value" id="kv5">{kpi[5]['total'] if 5 in kpi else 'N/A'}</div>
      <div class="kpi-sub" id="ks5">{second_demo_r}% of initial demos</div>
      <div class="kpi-badge amber">Key drop-off point</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Closed Lost</div>
      <div class="kpi-value" id="kv10" style="color:var(--red);">{kpi[10]['total'] if 10 in kpi else 'N/A'}</div>
      <div class="kpi-sub">vs. {kpi[11]['total'] if 11 in kpi else 'N/A'} closed won</div>
      <div class="kpi-badge amber">{loss_ratio} loss ratio</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Avg Weekly Entries</div>
      <div class="kpi-value" id="kvAvg">{avg_weekly}</div>
      <div class="kpi-sub">First calls per week</div>
      <div class="kpi-badge featured">Excl. peak: ~{avg_excl}</div>
    </div>
  </div>
  <div class="alert-block">
    <div class="alert-icon">!</div>
    <div id="kpiAlert"><strong>Key signal:</strong> The week of {peak_wk} was a clear outlier with {peak_val} first calls — {spike_mult}x the weekly average. Excluding it, average weekly volume is ~{avg_excl}.</div>
  </div>
</section>

<!-- ── SECTION 03: CHART ── -->
<section id="chart">
  <div class="section-header">
    <span class="section-num">03</span>
    <h2 class="section-title">Week-over-Week Trend</h2>
    <span class="section-subtitle">All stages overlaid. Click legend to toggle.</span>
  </div>
  <div class="chart-controls">
    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted);">Toggle stages using the legend</div>
    <div class="chart-actions">
      <button class="btn" onclick="showAll()">Show All</button>
      <button class="btn" onclick="hideAll()">Hide All</button>
    </div>
  </div>
  <div class="chart-layout">
    <div class="chart-box"><canvas id="mainChart"></canvas></div>
    <div class="legend-panel" id="legend"></div>
  </div>
</section>

<!-- ── SECTION 04: CONVERSION ── -->
<section id="conversion">
  <div class="section-header">
    <span class="section-num">04</span>
    <h2 class="section-title">Stage Conversion Rates</h2>
    <span class="section-subtitle">Step-by-step and vs. first meeting completed</span>
  </div>
  <table class="pipeline-table">
    <thead>
      <tr>
        <th style="width:2.5rem">#</th>
        <th>Stage</th>
        <th>Total</th>
        <th>vs. Previous Stage</th>
        <th>vs. First Meeting Completed</th>
        <th>Peak Week</th>
        <th style="width:3rem"></th>
      </tr>
    </thead>
    <tbody id="convTable"></tbody>
  </table>
  <div class="alert-block">
    <div class="alert-icon">↓</div>
    <div><strong>Largest drop-off:</strong> Initial demo completed to second demo scheduled drops to {second_demo_r}%. Investigate whether prospects are disengaging or the team is not pursuing second demos.</div>
  </div>
</section>

<!-- ── SECTION 05: INSIGHTS ── -->
<section id="insights">
  <div class="section-header">
    <span class="section-num">05</span>
    <h2 class="section-title">Trends & Correlations</h2>
    <span class="section-subtitle">Patterns and relationship to closed won outcomes</span>
  </div>
  <div class="trend-grid" style="margin-bottom:1px;">
    <div class="trend-card">
      <div class="trend-card-header">
        <div class="trend-icon yellow">↑</div>
        <div class="trend-tag insight">Correlation</div>
      </div>
      <h3>Volume Spikes Drive Wins</h3>
      <p>High top-of-funnel weeks show closed won activity <strong>3–5 weeks later</strong>. The {peak_wk} spike aligns with downstream proposal and close activity in subsequent weeks.</p>
    </div>
    <div class="trend-card">
      <div class="trend-card-header">
        <div class="trend-icon green">✓</div>
        <div class="trend-tag positive">Strength</div>
      </div>
      <h3>High Meeting Attendance</h3>
      <p>The <strong>{show_rate}% show rate</strong> signals strong prospect quality. Deals reaching a completed meeting close at <strong>{close_meeting}%</strong>.</p>
    </div>
    <div class="trend-card">
      <div class="trend-card-header">
        <div class="trend-icon amber">→</div>
        <div class="trend-tag watch">Watch</div>
      </div>
      <h3>Proposal Efficiency</h3>
      <p>Of {kpi[8]['total'] if 8 in kpi else 'N/A'} proposals sent, <strong>{kpi[11]['total'] if 11 in kpi else 'N/A'} won vs. {kpi[10]['total'] if 10 in kpi else 'N/A'} lost</strong> — a {loss_ratio} loss ratio. Earlier disqualification could improve close rate.</p>
    </div>
  </div>
  <div class="two-col">
    <div class="trend-card">
      <div class="trend-card-header">
        <div class="trend-icon yellow">→</div>
        <div class="trend-tag insight">Pattern</div>
      </div>
      <h3>Second Demo Predicts Close</h3>
      <p>Service agreements ({kpi[9]['total'] if 9 in kpi else 'N/A'}) and closed won ({kpi[11]['total'] if 11 in kpi else 'N/A'}) match exactly. <strong>Getting to a second demo is the strongest win predictor.</strong></p>
    </div>
    <div class="trend-card">
      <div class="trend-card-header">
        <div class="trend-icon amber">↓</div>
        <div class="trend-tag watch">Risk</div>
      </div>
      <h3>Seasonal Volume Dip</h3>
      <p>Late November through mid-December saw <strong>40–60% below average</strong> weekly volume. Monitor downstream closed won outcomes in subsequent weeks.</p>
    </div>
  </div>
  <div class="corr-box"><canvas id="corrChart"></canvas></div>
  <div class="alert-block">
    <div class="alert-icon">→</div>
    <div><strong>Focus areas:</strong> (1) Structured follow-up after initial demos to drive second demo rate above {second_demo_r}%. (2) Move disqualification earlier to improve proposal close rate. (3) Use {peak_wk} volume as a leading indicator — expect elevated closes 3–5 weeks out.</div>
  </div>
</section>

{sales_motion_html}

<!-- ── FOOTER ── -->
<footer>
  <div class="footer-left">KeychainOS · Sales Funnel Review · Auto-generated {generated_at} · <span id="footerMeta">{len(weeks)} weeks · {len(stages)} stages</span></div>
  <div class="footer-right">Confidential</div>
</footer>

<script>
const palette={js_pal};

// ── SOURCE DATASETS ──
const SOURCE = {{
  all: {{
    weeks: {js_weeks},
    stages: {js_stages}
  }},
  icp: {{
    weeks: {js_icp_weeks},
    stages: {js_icp_stages}
  }}
}};

// ── ACTIVE DATASET STATE ──
let activeDataset = 'all';
let baseWeeks  = SOURCE.all.weeks.slice();
let baseStages = SOURCE.all.stages.map(s => ({{...s, values: s.values.slice()}}));

// ── FILTERED STATE (applied on top of active dataset) ──
let filteredWeeks  = baseWeeks.slice();
let filteredStages = baseStages.map(s => ({{...s}}));
const activeFilters = {{}};
let crBase = 'tof';

// ── DATASET SWITCH ──
function switchDataset(ds) {{
  activeDataset = ds;

  // Reset cohort filters when switching datasets
  Object.keys(activeFilters).forEach(k => activeFilters[k] = null);
  document.querySelectorAll('.cf-row.cf-active').forEach(r => r.classList.remove('cf-active'));
  updateCFPanel();

  baseWeeks  = SOURCE[ds].weeks.slice();
  baseStages = SOURCE[ds].stages.map(s => ({{...s, values: s.values.slice()}}));
  filteredWeeks  = baseWeeks.slice();
  filteredStages = baseStages.map(s => ({{...s}}));

  // Toggle button states
  document.getElementById('dsTabAll').classList.toggle('ds-active', ds === 'all');
  document.getElementById('dsTabIcp').classList.toggle('ds-active', ds === 'icp');

  // ICP banner
  document.getElementById('icpBanner').classList.toggle('visible', ds === 'icp');

  // Rebuild the week/stage filter grid for the new dataset
  buildFilterGrid();
  rebuildAll();
}}

// ── CLOSE RATE BASE TOGGLE ──
function switchCRBase(base) {{
  crBase = base;
  document.getElementById('crTabTof').classList.toggle('cr-active', base === 'tof');
  document.getElementById('crTabDemo').classList.toggle('cr-active', base === 'demo');
  rebuildAll();
}}

// ── WEEK / STAGE FILTER ENGINE ──
function getWeekFilters() {{
  return baseWeeks.map((w, i) => ({{
    id: 'week-' + i,
    label: w,
    desc: 'Exclude week of ' + w + ' from all visualizations',
    type: 'week',
    weekIdx: i
  }}));
}}

function getStageFilters() {{
  return baseStages.map(s => ({{
    id: 'stage-' + s.sn,
    label: s.label,
    desc: 'Remove stage ' + String(s.sn).padStart(2,'0') + ' from trend chart and conversion table',
    type: 'stage',
    sn: s.sn
  }}));
}}

function buildFilterGrid() {{
  const grid = document.getElementById('cfGrid');
  grid.innerHTML = '';

  const WEEK_FILTERS  = getWeekFilters();
  const STAGE_FILTERS = getStageFilters();

  const weeksByVol = WEEK_FILTERS.map(f => ({{
    ...f,
    vol: baseStages[0] ? baseStages[0].values[f.weekIdx] : 0
  }})).sort((a,b) => b.vol - a.vol).slice(0, 3);

  const stagePicks = STAGE_FILTERS.slice(0, 3);

  const leftCol = document.createElement('div');
  leftCol.style.cssText = 'display:flex;flex-direction:column;border-right:1px solid var(--border);';
  const rightCol = document.createElement('div');
  rightCol.style.cssText = 'display:flex;flex-direction:column;';

  weeksByVol.forEach(f => leftCol.appendChild(makeFilterRow(f, 'cf-tag-week', 'Week')));
  stagePicks.forEach(f => rightCol.appendChild(makeFilterRow(f, 'cf-tag-stage', 'Stage')));

  grid.appendChild(leftCol);
  grid.appendChild(rightCol);
}}

function makeFilterRow(f, tagClass, tagLabel) {{
  const row = document.createElement('div');
  row.className = 'cf-row';
  row.id = 'cfrow-' + f.id;
  row.innerHTML = `
    <div class="cf-toggle"></div>
    <div class="cf-info">
      <div class="cf-name">${{f.label}}</div>
      <div class="cf-desc">${{f.desc}}</div>
    </div>
    <span class="cf-tag ${{tagClass}}">${{tagLabel}}</span>`;
  row.addEventListener('click', () => toggleCF(f.id, f, row));
  return row;
}}

function toggleCF(id, f, row) {{
  const isActive = row.classList.toggle('cf-active');
  activeFilters[id] = isActive ? f : null;
  updateCFPanel();
}}

function updateCFPanel() {{
  const active = Object.values(activeFilters).filter(Boolean);
  const wCount = active.filter(f => f.type === 'week').length;
  const sCount = active.filter(f => f.type === 'stage').length;
  const totalWeeks = baseWeeks.length;
  const retained = totalWeeks > 0
    ? Math.round(((totalWeeks - wCount) / totalWeeks) * 100)
    : 100;

  document.getElementById('cfWeeksVal').textContent  = active.length ? wCount  : '—';
  document.getElementById('cfStagesVal').textContent = active.length ? sCount  : '—';
  document.getElementById('cfRetainVal').textContent = active.length ? retained + '%' : '100%';

  const chipBar = document.getElementById('cfChips');
  chipBar.querySelectorAll('.cf-chip').forEach(c => c.remove());
  const noMsg = document.getElementById('cfNone');
  if (active.length === 0) {{
    noMsg.style.display = '';
  }} else {{
    noMsg.style.display = 'none';
    active.forEach(f => {{
      const chip = document.createElement('span');
      chip.className = 'cf-chip';
      chip.innerHTML = f.label + `<span class="cf-chip-x" onclick="removeCF('${{f.id}}')">✕</span>`;
      chipBar.appendChild(chip);
    }});
  }}
  document.getElementById('cfApply').disabled = active.length === 0;
}}

function removeCF(id) {{
  activeFilters[id] = null;
  const row = document.getElementById('cfrow-' + id);
  if (row) row.classList.remove('cf-active');
  updateCFPanel();
}}

function applyFilters() {{
  const active = Object.values(activeFilters).filter(Boolean);
  const excludeWeekIdxs = new Set(active.filter(f=>f.type==='week').map(f=>f.weekIdx));
  const excludeSns      = new Set(active.filter(f=>f.type==='stage').map(f=>f.sn));

  filteredWeeks = baseWeeks.filter((_,i) => !excludeWeekIdxs.has(i));
  filteredStages = baseStages
    .filter(s => !excludeSns.has(s.sn))
    .map(s => ({{
      ...s,
      values: s.values.filter((_,i) => !excludeWeekIdxs.has(i))
    }}));
  filteredStages = filteredStages.map(s => ({{...s, total: s.values.reduce((a,b)=>a+b,0)}}));

  rebuildAll();
}}

function rebuildAll() {{
  rebuildHeroMeta();
  rebuildKPIs();
  rebuildChart();
  rebuildConvTable();
  rebuildCorrChart();
  // Footer
  const fm = document.getElementById('footerMeta');
  if (fm) fm.textContent = filteredWeeks.length + ' weeks · ' + filteredStages.length + ' stages' + (activeDataset === 'icp' ? ' · ICP' : '');
}}

function rebuildHeroMeta() {{
  const ws = filteredWeeks;
  const ss = filteredStages;
  const s1  = ss.find(s=>s.sn===1);
  const s11 = ss.find(s=>s.sn===11);
  const top   = s1  ? s1.total  : 0;
  const s3    = ss.find(s=>s.sn===3);
  const demoN = s3  ? s3.total  : 0;
  const crDenom = crBase === 'demo' ? demoN : top;
  const crLabel = crBase === 'demo' ? 'vs demo sched' : 'overall';
  const cr  = (s11 && crDenom) ? (s11.total/crDenom*100).toFixed(1)+'%' : 'N/A';
  const won = s11 ? s11.total : 'N/A';
  document.getElementById('hmWeeks').textContent  = ws.length + ' weeks' + (activeDataset === 'icp' ? ' · ICP' : '');
  document.getElementById('hmStages').textContent = ss.length + ' stages';
  document.getElementById('hmTof').textContent    = top + ' first calls';
  document.getElementById('hmClose').textContent  = cr + ' (' + won + ' won \u00b7 ' + crLabel + ')';
  const tofPct  = (s1 && s11 && top)   ? (s11.total/top*100).toFixed(1)+'% close \u00b7 '+top+' calls'   : '\u2014';
  const demoPct = (s3 && s11 && demoN) ? (s11.total/demoN*100).toFixed(1)+'% close \u00b7 '+demoN+' demos' : '\u2014';
  const mtof  = document.getElementById('crMetaTof');
  const mdemo = document.getElementById('crMetaDemo');
  if (mtof)  mtof.textContent  = tofPct;
  if (mdemo) mdemo.textContent = demoPct;
}}

function rebuildKPIs() {{
  const ss  = filteredStages;
  const ws  = filteredWeeks;
  const kpi = {{}};
  ss.forEach(s => kpi[s.sn] = s);
  const top = kpi[1] ? kpi[1].total : 1;
  const pct = (n,d) => d ? (n/d*100).toFixed(1)+'%' : 'N/A';

  function setKPI(id, val) {{
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }}

  setKPI('kv1',  kpi[1]  ? kpi[1].total  : 'N/A');
  setKPI('ks1',  kpi[1] && kpi[2] ? pct(kpi[2].total, kpi[1].total) + ' show rate' : '');
  setKPI('kv2',  kpi[2]  ? kpi[2].total  : 'N/A');
  setKPI('kv8',  kpi[8]  ? kpi[8].total  : 'N/A');
  setKPI('ks8',  kpi[8]  ? pct(kpi[8].total, top) + ' of top-of-funnel' : '');
  setKPI('kv11', kpi[11] ? kpi[11].total : 'N/A');
  const crDenomKpi = (crBase === 'demo' && kpi[3]) ? kpi[3].total : top;
  const crLabelKpi = crBase === 'demo' ? '% close vs. initial demo sched' : '% overall close rate';
  setKPI('ks11', kpi[11] ? pct(kpi[11].total, crDenomKpi) + crLabelKpi : '');
  setKPI('kv4',  kpi[4]  ? kpi[4].total  : 'N/A');
  setKPI('kv5',  kpi[5]  ? kpi[5].total  : 'N/A');
  setKPI('ks5',  kpi[4] && kpi[5] ? pct(kpi[5].total, kpi[4].total) + ' of initial demos' : '');
  setKPI('kv10', kpi[10] ? kpi[10].total : 'N/A');
  const avgW = ws.length ? (top/ws.length).toFixed(1) : 'N/A';
  setKPI('kvAvg', avgW);

  if (kpi[1]) {{
    const vals = kpi[1].values;
    const maxV = Math.max(...vals);
    const peakW = ws[vals.indexOf(maxV)] || 'N/A';
    setKPI('ksPeak', 'Peak: ' + peakW + ' (' + maxV + ')');
  }}

  if (kpi[1] && ws.length) {{
    const vals = kpi[1].values;
    const maxV = Math.max(...vals);
    const peakW = ws[vals.indexOf(maxV)];
    const excl = vals.filter(v=>v!==maxV);
    const avgExcl = excl.length ? (excl.reduce((a,b)=>a+b,0)/excl.length).toFixed(1) : 'N/A';
    const mult = top ? (maxV/(top/ws.length)).toFixed(1) : 'N/A';
    const el = document.getElementById('kpiAlert');
    if (el) el.innerHTML = '<strong>Key signal:</strong> The week of ' + peakW + ' was a clear outlier with ' + maxV + ' first calls — ' + mult + 'x the weekly average. Excluding it, average weekly volume is ~' + avgExcl + '.';
  }}
}}

let mainChart = null;
function rebuildChart() {{
  const ws = filteredWeeks;
  const ss = filteredStages;
  const ctx = document.getElementById('mainChart').getContext('2d');
  if (mainChart) mainChart.destroy();
  const ds = ss.map((s,i) => ({{
    label:s.label, data:s.values,
    borderColor:palette[i % palette.length],
    backgroundColor:palette[i % palette.length]+'18',
    pointBackgroundColor:palette[i % palette.length],
    pointRadius:3, pointHoverRadius:5, borderWidth:1.5, fill:false, tension:0.35
  }}));
  mainChart = new Chart(ctx, {{
    type:'line', data:{{labels:ws, datasets:ds}},
    options:{{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'#0A0A0A', borderColor:'#1E1E1E', borderWidth:1,
          titleFont:{{family:'Inter',size:11,weight:'700'}},
          bodyFont:{{family:'Inter',size:11}},
          titleColor:'#F5D000', bodyColor:'rgba(255,255,255,0.6)',
          padding:12, boxPadding:4,
          callbacks:{{
            title: c => 'Week of '+c[0].label,
            label: c => mainChart.isDatasetVisible(c.datasetIndex) ? '  '+ds[c.datasetIndex].label+': '+c.raw : null
          }},
          filter: i => mainChart.isDatasetVisible(i.datasetIndex) && i.raw > 0
        }}
      }},
      scales:{{
        x:{{ ticks:{{color:'#6B6B6B',font:{{family:'Inter',size:10}},maxRotation:45,minRotation:45}}, grid:{{color:'#E8E8E4'}}, border:{{color:'#E8E8E4'}} }},
        y:{{ beginAtZero:true, ticks:{{color:'#6B6B6B',font:{{family:'Inter',size:10}},precision:0}}, grid:{{color:'#E8E8E4'}}, border:{{color:'#E8E8E4'}} }}
      }}
    }}
  }});
  const legendEl = document.getElementById('legend');
  legendEl.innerHTML = '';
  ss.forEach((s,i) => {{
    const item = document.createElement('div');
    item.className = 'leg-item'; item.id = 'leg-'+s.sn;
    item.innerHTML = `<span class="leg-swatch" style="background:${{palette[i%palette.length]}}"></span><span class="leg-label">${{s.short}}</span><span class="leg-total">${{s.total}}</span>`;
    item.addEventListener('click', () => {{
      const vis = mainChart.isDatasetVisible(i);
      mainChart.setDatasetVisibility(i, !vis);
      mainChart.update();
      item.classList.toggle('off', vis);
    }});
    legendEl.appendChild(item);
  }});
}}

function showAll() {{ if(!mainChart) return; filteredStages.forEach((_,i)=>{{mainChart.setDatasetVisibility(i,true);const l=document.getElementById('leg-'+filteredStages[i].sn);if(l)l.classList.remove('off');}});mainChart.update(); }}
function hideAll() {{ if(!mainChart) return; filteredStages.forEach((_,i)=>{{mainChart.setDatasetVisibility(i,false);const l=document.getElementById('leg-'+filteredStages[i].sn);if(l)l.classList.add('off');}});mainChart.update(); }}

function rebuildConvTable() {{
  const ss  = filteredStages;
  const tbl = document.getElementById('convTable');
  tbl.innerHTML = '';
  const fmc = ss.find(s=>s.sn===2);
  const fmcTotal = fmc ? fmc.total : (ss[0] ? ss[0].total : 1);
  const ws = filteredWeeks;
  ss.forEach((s,i) => {{
    const prev = i===0 ? null : ss[i-1];
    const vsFmc = (s.total/fmcTotal*100).toFixed(1);
    const vsPrev = prev ? (s.total/prev.total*100).toFixed(1) : null;
    const pct = parseFloat(vsPrev)||100;
    const fmcPct = parseFloat(vsFmc);
    const cFmc = fmcPct>80?'#1A9E5F':fmcPct>50?'#D97706':'#E03030';
    const cPrev = i===0?'#0A0A0A':pct>80?'#1A9E5F':pct>50?'#D97706':'#E03030';
    const peakWk = s.values.length ? (ws[s.values.indexOf(Math.max(...s.values))]||'N/A') : 'N/A';
    const row = document.createElement('tr');
    row.setAttribute('data-sn', s.sn);
    row.innerHTML = `
      <td style="color:#6B6B6B;font-size:0.65rem;font-weight:700;letter-spacing:0.06em;">${{String(s.sn).padStart(2,'0')}}</td>
      <td><div class="stage-name"><span class="stage-dot" style="background:${{palette[i%palette.length]}}"></span>${{s.label}}</div></td>
      <td><span class="total-num">${{s.total}}</span></td>
      <td>${{i===0?'<span style="font-size:0.65rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#6B6B6B;">Baseline</span>':`<div class="conv-bar-wrap"><div class="conv-bar-bg"><div class="conv-bar-fill" style="width:${{Math.min(pct,100)}}%;background:${{cPrev}}"></div></div><span class="conv-pct" style="color:${{cPrev}}">${{vsPrev}}%</span></div>`}}</td>
      <td>${{s.sn===2?'<span style="font-size:0.65rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#6B6B6B;">Baseline</span>':`<div class="conv-bar-wrap"><div class="conv-bar-bg"><div class="conv-bar-fill" style="width:${{Math.min(fmcPct,100)}}%;background:${{cFmc}}"></div></div><span class="conv-pct" style="color:${{cFmc}}">${{vsFmc}}%</span></div>`}}</td>
      <td><span class="peak-week">${{peakWk}}</span></td>
      <td><button class="hide-row-btn" onclick="hideConvRow(${{s.sn}},this)">Hide</button></td>`;
    tbl.appendChild(row);
  }});
}}

let corrChart = null;
function rebuildCorrChart() {{
  const ws = filteredWeeks;
  const ss = filteredStages;
  const s1  = ss.find(s=>s.sn===1);
  const s11 = ss.find(s=>s.sn===11);
  const corrCtx = document.getElementById('corrChart').getContext('2d');
  if (corrChart) corrChart.destroy();
  corrChart = new Chart(corrCtx, {{
    type:'bar',
    data:{{
      labels:ws,
      datasets:[
        {{ label:'First Calls Scheduled', data:s1?s1.values:[], backgroundColor:'rgba(245,208,0,0.15)', borderColor:'#F5D000', borderWidth:1.5, yAxisID:'y', type:'bar', order:2 }},
        {{ label:'Closed Won', data:s11?s11.values:[], borderColor:'#1A9E5F', backgroundColor:'rgba(26,158,95,0.15)', pointBackgroundColor:'#1A9E5F', pointRadius:4, borderWidth:2, yAxisID:'y1', type:'line', tension:0.4, fill:false, order:1 }}
      ]
    }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:true,position:'top',align:'end',labels:{{font:{{family:'Inter',size:10,weight:'600'}},color:'#6B6B6B',boxWidth:12,padding:16}}}},
        tooltip:{{backgroundColor:'#0A0A0A',borderColor:'#1E1E1E',borderWidth:1,titleFont:{{family:'Inter',size:10,weight:'700'}},bodyFont:{{family:'Inter',size:10}},titleColor:'#F5D000',bodyColor:'rgba(255,255,255,0.6)',padding:10}},
        title:{{display:true,text:'Top-of-Funnel vs. Closed Won — Lag Effect',font:{{family:'Inter',size:11,weight:'700'}},color:'#0A0A0A',padding:{{bottom:12}},align:'start'}}
      }},
      scales:{{
        x:{{ticks:{{color:'#6B6B6B',font:{{family:'Inter',size:9}},maxRotation:45,minRotation:45}},grid:{{display:false}},border:{{color:'#E8E8E4'}}}},
        y:{{beginAtZero:true,position:'left',ticks:{{color:'#6B6B6B',font:{{family:'Inter',size:9}},precision:0}},grid:{{color:'#E8E8E4'}},border:{{color:'#E8E8E4'}},title:{{display:true,text:'First Calls',color:'#6B6B6B',font:{{size:9,weight:'700',family:'Inter'}}}}}},
        y1:{{beginAtZero:true,position:'right',ticks:{{color:'#1A9E5F',font:{{family:'Inter',size:9}},precision:0}},grid:{{display:false}},border:{{color:'#E8E8E4'}},title:{{display:true,text:'Closed Won',color:'#1A9E5F',font:{{size:9,weight:'700',family:'Inter'}}}}}}
      }}
    }}
  }});
}}

// ── INIT ──
buildFilterGrid();
rebuildAll();

function hideConvRow(sn, btn) {{
  const row = document.querySelector('#convTable tr[data-sn="'+sn+'"]');
  if (row) {{ row.classList.add('conv-row-hidden'); }}
  let showBtn = document.getElementById('showHiddenBtn');
  if (!showBtn) {{
    showBtn = document.createElement('button');
    showBtn.id = 'showHiddenBtn';
    showBtn.className = 'show-hidden-btn';
    showBtn.textContent = 'Show hidden rows';
    showBtn.onclick = showAllConvRows;
    document.getElementById('convTable').closest('table').after(showBtn);
  }}
  showBtn.textContent = 'Show hidden rows (' + document.querySelectorAll('.conv-row-hidden').length + ')';
}}
function showAllConvRows() {{
  document.querySelectorAll('.conv-row-hidden').forEach(r => r.classList.remove('conv-row-hidden'));
  const btn = document.getElementById('showHiddenBtn');
  if (btn) btn.remove();
}}
</script>
</body>
</html>"""


def main():
    # Fetch main dataset (all leads)
    raw = fetch_data(DATA_URL)
    weeks, stages = parse_csv(raw)
    print(f"Main dataset: {len(stages)} stages x {len(weeks)} weeks")

    # Fetch ICP dataset from second tab (gid=1467538758)
    # Only ICP-qualified leads — same stage/week format as main tab
    try:
        icp_raw = fetch_data(ICP_URL)
        icp_weeks, icp_stages = parse_csv(icp_raw)
        print(f"ICP dataset: {len(icp_stages)} stages x {len(icp_weeks)} weeks")
    except Exception as e:
        print(f"WARNING: Could not load ICP tab — {e}. ICP toggle will show empty data.")
        icp_weeks = weeks
        icp_stages = [{**s, "total": 0, "values": [0]*len(weeks)} for s in stages]

    generated_at = datetime.utcnow().strftime("%b %d, %Y")
    html = build_html(weeks, stages, icp_weeks, icp_stages, generated_at)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Built {OUTPUT_FILE} — {len(stages)} stages x {len(weeks)} weeks + ICP tab")


if __name__ == "__main__":
    main()
