"""
build.py — KeychainOS Pipeline Intelligence Dashboard
Generates index.html as a static site deployed via GitHub Pages.

CONFIGURATION
─────────────
All tunable parameters are in the CONFIG block below.
The generated index.html is the site — do not edit it manually.

ACCESS CODE
───────────
To change the access code:
  1. Pick a new code (any length matching CODE_LENGTH)
  2. Run: python3 -c "import hashlib; print(hashlib.sha256('YOURCODE'.encode()).hexdigest())"
  3. Paste the result into CODE_HASH below
  Current code: Pipeline2026
"""

import hashlib
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
OUTPUT_FILE   = "index.html"

# Access gate
# Current code: Pipeline2026
CODE_HASH     = hashlib.sha256("Pipeline2026".encode()).hexdigest()
CODE_LENGTH   = 12

# Model defaults (these become the slider start positions)
DEFAULT_CR    = 9.5    # Close rate % (slider: 8–12)
DEFAULT_ACV   = 51     # ACV in $K    (slider: 40–75)
DEFAULT_LEADS = 265    # Leads/month  (slider: 200–300)

# Scenario multipliers (applied to close rate only; lead volume stays constant)
UNDER_CR_MULT = 0.68   # e.g. 9.5% → 6.5%
OVER_CR_MULT  = 1.32   # e.g. 9.5% → 12.5%

# Deal structure (proportion of ACV)
SW_RATIO      = 36/51  # Software portion
IMPL_RATIO    = 15/51  # Implementation portion

# Carry model
CARRY_RATE    = 0.20   # % of projected closes that push to next month
CARRY_RESOLVE = 0.80   # % of carried deals that eventually close
M1_RESIDUAL   = True   # Whether ~1 M1 deal trickles to M3

# Funnel drop-off rates (approximate)
RESPONSE_RATE = 0.50   # % of raw leads that respond
MQL_RATE      = 0.305  # % of raw leads that reach MQL
SQL_RATE      = 0.196  # % of raw leads that reach SQL

# Generated timestamp
GENERATED_AT  = datetime.utcnow().strftime("%b %d, %Y")
# ──────────────────────────────────────────────────────────────────────────────


def build_html():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KeychainOS · Pipeline Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#F7F7F5;--white:#FFFFFF;--border:#E8E8E4;
  --accent:#F5D000;--text:#0A0A0A;--secondary:#6B6B6B;
  --red:#E03030;--green:#1A9E5F;--radius:10px;
}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;-webkit-font-smoothing:antialiased;}}

/* GATE */
#gate{{position:fixed;inset:0;background:var(--bg);z-index:9999;display:flex;align-items:center;justify-content:center;}}
.gate-inner{{text-align:center;max-width:380px;width:100%;padding:2rem;}}
.gate-brand{{font-size:22px;font-weight:800;letter-spacing:-0.5px;color:var(--text);margin-bottom:4px;}}
.gate-brand span{{color:var(--accent);background:var(--text);padding:0 6px;border-radius:4px;}}
.gate-sub{{font-size:10px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--secondary);margin-bottom:28px;}}
.gate-prompt{{font-size:12px;color:var(--secondary);margin-bottom:16px;}}
.gate-boxes{{display:flex;gap:6px;justify-content:center;margin-bottom:12px;flex-wrap:wrap;}}
.dbox{{width:34px;height:42px;border:1px solid var(--border);border-radius:6px;text-align:center;font-size:16px;font-family:'Inter',sans-serif;font-weight:700;color:var(--text);background:var(--white);outline:none;transition:border-color 0.15s;}}
.dbox:focus{{border-color:var(--accent);box-shadow:0 0 0 3px rgba(245,208,0,0.2);}}
.dbox.err{{border-color:var(--red);animation:shake 0.3s ease;}}
@keyframes shake{{0%,100%{{transform:translateX(0);}}25%{{transform:translateX(-4px);}}75%{{transform:translateX(4px);}}}}
#gate-error{{font-size:11px;color:var(--red);height:16px;}}

/* NAV */
nav{{position:fixed;top:0;left:0;right:0;z-index:100;background:var(--white);border-bottom:1px solid var(--border);padding:0 40px;height:52px;display:flex;align-items:center;gap:2px;}}
.nav-brand{{font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:var(--text);margin-right:20px;}}
.nav-btn{{background:none;border:none;font-family:'Inter',sans-serif;font-size:11px;font-weight:500;letter-spacing:0.8px;text-transform:uppercase;color:var(--secondary);padding:6px 12px;border-radius:6px;cursor:pointer;transition:all 0.15s;}}
.nav-btn:hover{{background:var(--bg);color:var(--text);}}
.nav-btn.active{{background:var(--accent);color:var(--text);font-weight:700;}}

/* CONTROLS BAR */
.cbar{{position:fixed;top:52px;left:0;right:0;z-index:99;background:var(--text);border-bottom:1px solid #222;padding:0 40px;height:60px;display:flex;align-items:center;gap:28px;}}
.cg{{display:flex;align-items:center;gap:10px;}}
.cl{{font-size:10px;font-weight:700;letter-spacing:0.9px;text-transform:uppercase;color:rgba(255,255,255,0.4);white-space:nowrap;}}
.cv{{font-size:14px;font-weight:800;letter-spacing:-0.3px;color:var(--accent);min-width:52px;text-align:right;}}
.csep{{width:1px;height:28px;background:#333;}}
.cbadge{{font-size:10px;font-weight:600;letter-spacing:0.7px;text-transform:uppercase;color:rgba(255,255,255,0.25);}}
input[type=range]{{-webkit-appearance:none;appearance:none;width:120px;height:3px;background:#333;border-radius:2px;outline:none;cursor:pointer;}}
input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--accent);cursor:pointer;border:2px solid var(--text);box-shadow:0 0 0 2px var(--accent);}}
input[type=range]::-moz-range-thumb{{width:14px;height:14px;border-radius:50%;background:var(--accent);cursor:pointer;border:2px solid var(--text);}}

/* PAGES */
.page{{display:none;padding:132px 40px 60px;animation:fadeIn 0.2s ease;}}
.page.active{{display:block;}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(4px);}}to{{opacity:1;transform:translateY(0);}}}}

/* TYPE */
.plabel{{font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--secondary);margin-bottom:6px;}}
h2{{font-size:26px;font-weight:800;letter-spacing:-0.6px;color:var(--text);line-height:1.1;}}
.sub{{font-size:12px;color:var(--secondary);margin-top:5px;}}

/* CARDS & GRIDS */
.card{{background:var(--white);border:1px solid var(--border);border-radius:var(--radius);padding:24px;}}
.g2{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}}
.g3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}}
.g4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}}
.divider{{height:1px;background:var(--border);margin:24px 0;}}

/* METRIC ROWS */
.mrow{{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--border);}}
.mrow:last-child{{border-bottom:none;}}
.mrl{{font-size:12px;color:var(--secondary);}}
.mrv{{font-size:20px;font-weight:800;letter-spacing:-0.4px;}}

/* STAT TILES */
.stat{{background:var(--white);border:1px solid var(--border);border-radius:var(--radius);padding:20px 22px;}}
.slabel{{font-size:11px;font-weight:600;letter-spacing:0.9px;text-transform:uppercase;color:var(--secondary);margin-bottom:6px;}}
.sval{{font-size:28px;font-weight:800;letter-spacing:-0.6px;color:var(--text);line-height:1;}}
.sval.green{{color:var(--green);}} .sval.red{{color:var(--red);}}
.snote{{font-size:11px;color:var(--secondary);margin-top:4px;}}

/* TOTAL BLOCK */
.tblock{{background:var(--text);border-radius:8px;padding:13px 16px;margin-top:14px;display:flex;justify-content:space-between;align-items:center;}}
.tblabel{{font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:rgba(255,255,255,0.35);}}
.tbval{{font-size:24px;font-weight:800;letter-spacing:-0.5px;color:var(--accent);}}

/* ALERT */
.ablock{{background:var(--text);border-radius:var(--radius);padding:16px 18px;display:flex;align-items:flex-start;gap:12px;margin-top:14px;}}
.aicon{{background:var(--accent);border-radius:6px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:13px;}}
.atext{{font-size:12px;color:rgba(255,255,255,0.7);line-height:1.6;}}
.atext strong{{color:white;font-weight:600;}}

/* BADGE */
.by{{background:var(--text) !important;color:var(--accent) !important;padding:2px 10px;border-radius:5px;font-weight:800;letter-spacing:-0.4px;display:inline-block;}}

/* TAGS */
.tag{{display:inline-block;font-size:10px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;padding:3px 8px;border-radius:4px;margin-top:8px;}}
.tr{{background:#FFF0F0;color:var(--red);}} .tg{{background:#F0FBF6;color:var(--green);}} .tb{{background:var(--text);color:var(--accent);}}

/* FOOTER */
footer{{margin-top:40px;padding-top:16px;border-top:1px solid var(--border);display:flex;justify-content:space-between;}}
.fmeta{{font-size:11px;color:var(--secondary);}}
.fconf{{font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:var(--secondary);}}

/* TABLE */
table{{width:100%;border-collapse:collapse;}}
th{{font-size:11px;font-weight:600;letter-spacing:0.9px;text-transform:uppercase;color:var(--secondary);text-align:left;padding:8px 14px;border-bottom:1px solid var(--border);}}
td{{font-size:13px;padding:10px 14px;border-bottom:1px solid var(--border);color:var(--text);}}
tr:last-child td{{border-bottom:none;}} tr:hover td{{background:var(--bg);}}

/* PIPE FLOW */
.prow{{display:flex;align-items:stretch;margin-top:24px;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;}}
.ptile{{flex:1;background:var(--white);border-right:1px solid var(--border);padding:22px 18px;position:relative;}}
.ptile:last-child{{border-right:none;}}
.ptile.feat{{background:var(--accent);}}
.ptile.feat .psl{{color:rgba(0,0,0,0.45);}} .ptile.feat .psn{{color:var(--text);}} .ptile.feat .psd{{color:rgba(0,0,0,0.55);}} .ptile.feat .parr{{background:var(--text);color:var(--accent);}}
.parr{{position:absolute;right:-11px;top:50%;transform:translateY(-50%);z-index:3;width:22px;height:22px;background:var(--border);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--secondary);font-weight:700;}}
.ptile:last-child .parr{{display:none;}}
.psl{{font-size:11px;font-weight:600;letter-spacing:0.9px;text-transform:uppercase;color:var(--secondary);margin-bottom:6px;}}
.psn{{font-size:30px;font-weight:800;letter-spacing:-0.7px;color:var(--text);line-height:1;margin-bottom:6px;}}
.psd{{font-size:11px;color:var(--secondary);line-height:1.5;}}

/* FUNNEL */
.frow{{margin-bottom:3px;}}
.ftrack{{position:relative;height:46px;background:var(--white);border:1px solid var(--border);border-radius:6px;overflow:hidden;display:flex;align-items:center;padding:0 16px;}}
.ffill{{position:absolute;left:0;top:0;bottom:0;max-width:98%;background:var(--accent);opacity:0.18;border-radius:6px 0 0 6px;}}
.ffill.fg{{background:var(--green);opacity:0.14;}}
.fbl{{font-size:12px;font-weight:500;color:var(--secondary);z-index:1;position:relative;}}
.fbv{{font-size:20px;font-weight:800;letter-spacing:-0.4px;color:var(--text);margin-left:auto;z-index:10;position:relative;}}
.fbv.fg{{color:var(--green);}}
.fdrop{{font-size:11px;color:var(--secondary);padding:3px 16px 7px;display:flex;align-items:center;gap:5px;}}
.fdrop::before{{content:'↓';color:var(--red);font-size:10px;}}
.fdrop.fc::before{{content:'→';color:var(--green);}}

/* SLIPPAGE */
.sgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:24px;}}
.sc{{background:var(--white);border:1px solid var(--border);border-radius:var(--radius);padding:22px;}}
.smo{{font-size:11px;font-weight:700;letter-spacing:0.9px;text-transform:uppercase;color:var(--secondary);padding-bottom:12px;border-bottom:1px solid var(--border);margin-bottom:12px;}}
.srow{{display:flex;justify-content:space-between;align-items:baseline;padding:7px 0;border-bottom:1px solid var(--border);}}
.srow:last-of-type{{border-bottom:none;}}
.srl{{font-size:12px;color:var(--secondary);}}
.srv{{font-size:20px;font-weight:800;letter-spacing:-0.4px;color:var(--text);}}
.srv.green{{color:var(--green);}} .srv.red{{color:var(--red);}}
.stag{{display:inline-block;font-size:10px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;padding:3px 7px;border-radius:4px;margin-top:4px;margin-right:4px;}}
.stc{{background:#F0FBF6;color:var(--green);}} .stl{{background:#FFF0F0;color:var(--red);}} .sts{{background:var(--bg);border:1px solid var(--border);color:var(--secondary);}}
.lnote{{margin-top:12px;background:var(--accent);border-radius:6px;padding:8px 12px;font-size:11px;font-weight:700;color:var(--text);text-align:center;text-transform:uppercase;letter-spacing:0.4px;}}

/* SCENARIOS */
.scgrid{{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;margin-top:24px;}}
.sctile{{padding:28px 24px;border-right:1px solid var(--border);}}
.sctile:last-child{{border-right:none;}}
.sctile.under{{background:#FFF8F8;}} .sctile.base{{background:var(--white);}} .sctile.over{{background:#F5FFF9;}}
.schead{{font-size:11px;font-weight:700;letter-spacing:0.9px;text-transform:uppercase;margin-bottom:6px;}}
.sctile.under .schead{{color:var(--red);}} .sctile.base .schead{{color:var(--secondary);}} .sctile.over .schead{{color:var(--green);}}
.scdesc{{font-size:11px;color:var(--secondary);line-height:1.7;margin-bottom:16px;border-bottom:1px solid var(--border);padding-bottom:14px;}}
.scmr{{display:flex;justify-content:space-between;align-items:baseline;padding:6px 0;border-bottom:1px solid var(--border);}}
.scmr:last-of-type{{border-bottom:none;margin-bottom:16px;}}
.scml{{font-size:12px;color:var(--secondary);}}
.scmv{{font-size:19px;font-weight:800;letter-spacing:-0.4px;}}
.sctile.under .scmv{{color:var(--red);}} .sctile.base .scmv{{color:var(--text);}} .sctile.over .scmv{{color:var(--green);}}
.sccond{{margin-top:14px;font-size:11px;color:var(--secondary);line-height:1.8;}}
.sccond span{{display:block;}}
.changed{{animation:pulse 0.35s ease;}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.35;}}}}
</style>
</head>
<body>

<!-- ═══ ACCESS GATE ═══ -->
<div id="gate">
  <div class="gate-inner">
    <div class="gate-brand">Keychain<span>OS</span></div>
    <div class="gate-sub">Pipeline Intelligence</div>
    <div class="gate-prompt">Enter access code to continue</div>
    <div class="gate-boxes" id="gboxes">
      {"".join(['<input type="password" maxlength="1" class="dbox" inputmode="text" autocomplete="off">' for _ in range(CODE_LENGTH)])}
    </div>
    <div id="gate-error"></div>
  </div>
</div>

<script>
(function(){{
  const HASH="{CODE_HASH}";
  const LEN={CODE_LENGTH};
  const SK="kcos_pi_v1";
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


<!-- ═══ NAV ═══ -->
<nav>
  <span class="nav-brand">Pipeline Intel</span>
  <button class="nav-btn active" onclick="show(0)">01 · Flow</button>
  <button class="nav-btn" onclick="show(1)">02 · Metrics</button>
  <button class="nav-btn" onclick="show(2)">03 · Funnel</button>
  <button class="nav-btn" onclick="show(3)">04 · Slippage</button>
  <button class="nav-btn" onclick="show(4)">05 · Revenue</button>
</nav>

<!-- ═══ CONTROLS BAR ═══ -->
<div class="cbar">
  <div class="cg">
    <span class="cl">Close Rate</span>
    <input type="range" id="sl-cr" min="8" max="15" step="0.5" value="{DEFAULT_CR}" oninput="update()">
    <span class="cv" id="v-cr">{DEFAULT_CR}%</span>
  </div>
  <div class="csep"></div>
  <div class="cg">
    <span class="cl">ACV</span>
    <input type="range" id="sl-acv" min="40" max="75" step="1" value="{DEFAULT_ACV}" oninput="update()">
    <span class="cv" id="v-acv">${DEFAULT_ACV}K</span>
  </div>
  <div class="csep"></div>
  <div class="cg">
    <span class="cl">Leads / Mo</span>
    <input type="range" id="sl-leads" min="40" max="300" step="5" value="{DEFAULT_LEADS}" oninput="update()">
    <span class="cv" id="v-leads">{DEFAULT_LEADS}</span>
  </div>
  <div class="csep"></div>
  <span class="cbadge">All pages update live</span>
</div>


<!-- ═══════════════════════════════
     SLIDE 01 · PIPELINE FLOW
════════════════════════════════ -->
<div class="page active" id="page-0">
  <div class="plabel">Slide 01 · Architecture</div>
  <h2>Lead → Qualified → Closed</h2>
  <p class="sub" id="s1-sub">25 projected closes required each month · 5 planned carries are structural, not failure</p>

  <div class="prow">
    <div class="ptile">
      <div class="parr">→</div>
      <div class="psl">Raw Leads</div>
      <div class="psn" id="p1-leads">265</div>
      <div class="psd">Monthly lead volume to generate <span id="p1-proj">25</span> close-ready deals at <span id="p1-cr">9.5%</span> close rate. Planned carries priced in.</div>
      <span class="tag tb" id="p1-wk">~61 / wk</span>
    </div>
    <div class="ptile">
      <div class="parr">→</div>
      <div class="psl">MQL</div>
      <div class="psd" style="margin-top:6px;">CS/AM qualification layer. <span id="p1-cr2">9.5%</span> close rate applied to yield <span id="p1-proj2">25</span> projected closes.</div>
      <span class="tag tr">~60–65% drop</span>
    </div>
    <div class="ptile">
      <div class="parr">→</div>
      <div class="psl">SQL</div>
      <div class="psd" style="margin-top:6px;">Sales process initiates. Discovery, demo, scoping. ACV at <span id="p1-acv">$51K</span> ($36K software + $15K implementation).</div>
      <span class="tag tr">Significant attrition</span>
    </div>
    <div class="ptile feat">
      <div class="parr">→</div>
      <div class="psl">Projected Closes</div>
      <div class="psn" id="p1-proj3">25</div>
      <div class="psd">Monthly quota target. <span id="p1-cw">20</span> close in window. <span id="p1-carry">5</span> push to next month — designed into model.</div>
      <span class="tag tb" id="p1-carry-tag">5 carry → M+1</span>
    </div>
    <div class="ptile">
      <div class="psl">Closed Won</div>
      <div class="psn" id="p1-cw2">20</div>
      <div class="psd">Actual closed won. <span id="p1-arr">$1.02M</span> ARR at <span id="p1-cw3">20</span> × <span id="p1-acv2">$51K</span>.</div>
      <span class="tag tg" id="p1-arr-tag">$1.02M / mo</span>
    </div>
  </div>

  <div class="divider"></div>

  <div class="g4">
    <div class="stat"><div class="slabel">Proj. Closes / Mo</div><div class="sval by" id="s1-proj" style="font-size:28px;">25</div><div class="snote">Monthly quota benchmark</div></div>
    <div class="stat"><div class="slabel">Closed Won / Mo</div><div class="sval" id="s1-cw">20</div><div class="snote" id="s1-arr-note">20 × $51K = $1.02M ARR</div></div>
    <div class="stat"><div class="slabel">Leads Required / Mo</div><div class="sval" id="s1-leads">265</div><div class="snote" id="s1-leads-note">9.5% × 265 = 25 projected</div></div>
    <div class="stat"><div class="slabel">Close Rate</div><div class="sval" id="s1-cr">9.5%</div><div class="snote">MQL → Closed Won</div></div>
  </div>

  <footer><span class="fmeta">Pipeline Intelligence · KeychainOS · {GENERATED_AT}</span><span class="fconf">Confidential</span></footer>
</div>


<!-- ═══════════════════════════════
     SLIDE 02 · METRICS
════════════════════════════════ -->
<div class="page" id="page-1">
  <div class="plabel">Slide 02 · ACV & Velocity</div>
  <h2>ACV · Velocity · Rep Efficiency</h2>
  <p class="sub">Deal value structure, monthly targets, and rep productivity across headcount scenarios</p>

  <div class="g2" style="margin-top:22px;">
    <div class="card">
      <div class="plabel" style="margin-bottom:10px;">Deal Value Breakdown</div>
      <div style="font-size:42px;font-weight:800;letter-spacing:-1px;line-height:1;" id="s2-acv-big">$51,000</div>
      <div style="font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:var(--secondary);margin-top:4px;">Blended ACV Per Deal</div>
      <div class="g3" style="margin-top:14px;gap:8px;">
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;">
          <div style="font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:var(--secondary);margin-bottom:4px;">Software</div>
          <div style="font-size:22px;font-weight:800;letter-spacing:-0.5px;" id="s2-sw">$36K</div>
        </div>
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;">
          <div style="font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:var(--secondary);margin-bottom:4px;">Impl.</div>
          <div style="font-size:22px;font-weight:800;letter-spacing:-0.5px;" id="s2-impl">$15K</div>
        </div>
        <div style="background:var(--text);border-radius:8px;padding:12px;">
          <div style="font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:rgba(255,255,255,0.35);margin-bottom:4px;">Total</div>
          <div style="font-size:22px;font-weight:800;letter-spacing:-0.5px;color:var(--accent);" id="s2-acv-tot">$51K</div>
        </div>
      </div>
      <div class="ablock"><div class="aicon">→</div><div class="atext" id="s2-acv-note"><strong>ACV at $51K:</strong> $36K software + $15K implementation. Adjust slider to model different deal sizes.</div></div>
    </div>
    <div class="card">
      <div class="plabel" style="margin-bottom:10px;">Monthly Targets</div>
      <div class="mrow"><span class="mrl">Projected Closes / Month</span><span class="mrv" id="s2-proj" style="font-weight:800;">25</span></div>
      <div class="mrow"><span class="mrl">Closed Won / Month</span><span class="mrv" id="s2-cw">20</span></div>
      <div class="mrow"><span class="mrl">ARR / Month</span><span class="mrv" id="s2-arr-mo">$1.02M</span></div>
      <div class="mrow"><span class="mrl">ARR / Quarter (baseline)</span><span class="mrv" id="s2-arr-q">$3.52M</span></div>
      <div class="mrow"><span class="mrl">ARR / Year</span><span class="mrv" id="s2-arr-yr">$12.24M</span></div>
      <div class="mrow"><span class="mrl">Leads Required / Month</span><span class="mrv" id="s2-leads">265</span></div>
    </div>
  </div>

  <div class="divider"></div>
  <div class="plabel" style="margin-bottom:10px;">Rep Efficiency Matrix · Closed Won Per Rep Per Month</div>
  <div class="card" style="padding:0;overflow:hidden;">
    <table><thead><tr><th>Headcount</th><th>Target / Rep</th><th>Actual / Rep</th><th>Total Closed</th><th>Monthly ARR</th><th>Status</th></tr></thead>
    <tbody id="rep-tbody"></tbody></table>
  </div>
  <div class="ablock"><div class="aicon">→</div><div class="atext"><strong>Diagnosis:</strong> Past 8 reps, per-rep output degrades without additional lead volume. Pipeline capacity is the constraint, not headcount. Efficiency drops 47% from 6→11 reps while total closes remain flat.</div></div>

  <footer><span class="fmeta">Pipeline Intelligence · KeychainOS · {GENERATED_AT}</span><span class="fconf">Confidential</span></footer>
</div>


<!-- ═══════════════════════════════
     SLIDE 03 · FUNNEL
════════════════════════════════ -->
<div class="page" id="page-2">
  <div class="plabel">Slide 03 · Funnel</div>
  <h2>Leads → Stages → Closed</h2>
  <p class="sub" id="s3-sub">Month 1 stage-by-stage attrition</p>

  <div style="display:grid;grid-template-columns:1fr 290px;gap:20px;margin-top:22px;align-items:start;">
    <div>
      <div class="plabel" style="margin-bottom:12px;">Stage Attrition · Month 1</div>
      <div class="frow"><div class="ftrack"><div class="ffill" style="width:100%;"></div><span class="fbl">Raw Leads Injected</span><span class="fbv" id="f-leads">265</span></div></div>
      <div class="fdrop" id="f-d1">~133 lost at initial outreach / unresponsive</div>
      <div class="frow"><div class="ftrack"><div class="ffill" id="f-f2" style="width:50%;"></div><span class="fbl">Initial Response</span><span class="fbv" id="f-res">133</span></div></div>
      <div class="fdrop" id="f-d2">~52 disqualified at CS/AM qualification</div>
      <div class="frow"><div class="ftrack"><div class="ffill" id="f-f3" style="width:31%;"></div><span class="fbl">MQL · CS/AM Qualified</span><span class="fbv" id="f-mql">81</span></div></div>
      <div class="fdrop" id="f-d3">~29 lost in discovery / no product fit</div>
      <div class="frow"><div class="ftrack"><div class="ffill" id="f-f4" style="width:20%;"></div><span class="fbl">SQL · Sales Engaged</span><span class="fbv" id="f-sql">52</span></div></div>
      <div class="fdrop" id="f-d4">~27 lost during proposal / evaluation</div>
      <div class="frow"><div class="ftrack" style="border-color:rgba(245,208,0,0.5);background:rgba(245,208,0,0.04);"><div class="ffill" id="f-f5" style="width:9.5%;opacity:0.35;"></div><span class="fbl" style="font-weight:600;color:var(--text);">Projected Close Quota</span><span class="fbv" id="f-proj" style="font-weight:800;">25</span></div></div>
      <div class="fdrop fc" style="color:var(--green);" id="f-cn">5 of 25 carry to Month 2 — designed into model</div>
      <div class="frow"><div class="ftrack" style="border-color:rgba(26,158,95,0.3);"><div class="ffill fg" id="f-f6" style="width:7.5%;"></div><span class="fbl" style="color:var(--green);font-weight:600;">Closed Won · M1</span><span class="fbv fg" id="f-cw">20</span></div></div>
    </div>

    <div style="display:flex;flex-direction:column;gap:12px;">
      <div class="card">
        <div class="slabel">Leads per Proj. Close</div>
        <div style="font-size:36px;font-weight:800;letter-spacing:-1px;line-height:1;margin:4px 0;" id="f-ratio">10.6</div>
        <div style="font-size:11px;color:var(--secondary);" id="f-rn">265 ÷ 25 projected = 10.6:1</div>
        <div class="tblock"><span class="tblabel">ACV</span><span class="tbval" id="f-acv">$51K</span></div>
      </div>
      <div class="card">
        <div class="slabel">Monthly Lead Target</div>
        <div style="font-size:36px;font-weight:800;letter-spacing:-1px;line-height:1;margin:4px 0;" class="by" id="f-l2">265</div>
        <div style="font-size:11px;color:var(--secondary);margin-top:8px;" id="f-ln">9.5% × 265 = 25 closes<br>20 land · 5 carry → M2</div>
      </div>
      <div class="card">
        <div class="slabel">Weekly Benchmark</div>
        <div style="font-size:36px;font-weight:800;letter-spacing:-1px;line-height:1;margin:4px 0;" id="f-wk">~61</div>
        <div style="font-size:11px;color:var(--secondary);margin-top:6px;" id="f-wn">265 ÷ 4.33 weeks<br>5–6 projected closes/wk<br>4–5 actual closes/wk</div>
      </div>
    </div>
  </div>

  <footer><span class="fmeta">Pipeline Intelligence · KeychainOS · {GENERATED_AT}</span><span class="fconf">Confidential</span></footer>
</div>


<!-- ═══════════════════════════════
     SLIDE 04 · SLIPPAGE
════════════════════════════════ -->
<div class="page" id="page-3">
  <div class="plabel">Slide 04 · Carry Resolution</div>
  <h2>Slippage · Carry · Resolution</h2>
  <p class="sub" id="s4-sub">25 projected closes is the monthly quota · 5 planned carries are structural · 3-month map</p>

  <div class="sgrid">
    <div class="sc">
      <div class="smo">Month 1 · Close Window</div>
      <div class="srow"><span class="srl">Projected close quota</span><span class="srv" id="s4-p1" style="font-weight:800;">25</span></div>
      <div class="srow"><span class="srl">Closed Won M1</span><span class="srv green" id="s4-cw1">20</span></div>
      <div class="srow"><span class="srl">Planned carry (built-in)</span><span class="srv" id="s4-c1">5</span></div>
      <div class="srow"><span class="srl">Leads required</span><span class="srv" id="s4-l1">265</span></div>
      <div class="tblock"><span class="tblabel">Closed ARR · M1</span><span class="tbval" id="s4-a1">$1.02M</span></div>
      <div style="margin-top:10px;"><span class="stag stc" id="s4-ct">5 carry → M2</span></div>
      <div class="lnote" id="s4-w1">~61 leads / week</div>
    </div>
    <div class="sc">
      <div class="smo">Month 2 · Carryover + Base</div>
      <div class="srow"><span class="srl">New projected closes</span><span class="srv" id="s4-p2" style="font-weight:800;">25</span></div>
      <div class="srow"><span class="srl">M1 carryover closes</span><span class="srv green" id="s4-cr2">+4</span></div>
      <div class="srow"><span class="srl">Lost from M1 carry (20%)</span><span class="srv red">−1</span></div>
      <div class="srow"><span class="srl">Total closes M2</span><span class="srv green" id="s4-cw2">24</span></div>
      <div class="srow"><span class="srl">Fresh leads required</span><span class="srv" id="s4-l2">265</span></div>
      <div class="tblock"><span class="tblabel">Closed ARR · M2</span><span class="tbval" id="s4-a2">$1.22M</span></div>
      <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px;">
        <span class="stag stc" id="s4-m2t">4 close (M1)</span>
        <span class="stag stl">1 closed lost</span>
        <span class="stag stc">~1 → M3</span>
      </div>
      <div class="lnote" id="s4-w2">265 fresh + 4 carryover</div>
    </div>
    <div class="sc">
      <div class="smo">Month 3 · Normalized</div>
      <div class="srow"><span class="srl">New projected closes</span><span class="srv" id="s4-p3" style="font-weight:800;">25</span></div>
      <div class="srow"><span class="srl">M2 carryover closes</span><span class="srv green">+4</span></div>
      <div class="srow"><span class="srl">M1 residual to M3</span><span class="srv green">+1</span></div>
      <div class="srow"><span class="srl">Total closes M3</span><span class="srv green" id="s4-cw3">~25</span></div>
      <div class="srow"><span class="srl">Fresh leads required</span><span class="srv" id="s4-l3">265</span></div>
      <div class="tblock"><span class="tblabel">Closed ARR · M3</span><span class="tbval" id="s4-a3">$1.28M</span></div>
      <div style="margin-top:10px;"><span class="stag sts">Steady state</span></div>
      <div class="lnote" id="s4-w3">265 leads / mo · normalized</div>
    </div>
  </div>

  <div class="divider"></div>
  <div class="g4">
    <div class="stat"><div class="slabel">Total Q Deals</div><div class="sval" id="s4-tq">69</div><div class="snote" id="s4-tn">20 + 24 + 25</div></div>
    <div class="stat"><div class="slabel">Q ARR Baseline</div><div class="sval green" id="s4-aq">$3.52M</div><div class="snote">Carryover fully absorbed</div></div>
    <div class="stat"><div class="slabel">Deals Lost</div><div class="sval red">1</div><div class="snote">M1 carry → closed lost M2</div></div>
    <div class="stat"><div class="slabel">Monthly Proj. Quota</div><div class="sval by" id="s4-q" style="font-size:28px;">25</div><div class="snote">Steady-state · <span id="s4-ln">265</span> leads/mo</div></div>
  </div>

  <footer><span class="fmeta">Pipeline Intelligence · KeychainOS · {GENERATED_AT}</span><span class="fconf">Confidential</span></footer>
</div>


<!-- ═══════════════════════════════
     SLIDE 05 · REVENUE SCENARIOS
════════════════════════════════ -->
<div class="page" id="page-4">
  <div class="plabel">Slide 05 · Revenue Projection</div>
  <h2>Revenue Projection · 3 Scenarios</h2>
  <p class="sub">Monthly ARR trajectory across underperformance, baseline, and outperformance · Q comparison</p>

  <div class="scgrid">
    <div class="sctile under">
      <div class="schead">↓ Underperformance</div>
      <div class="scdesc" id="sc-ud">Close rate drops to ~6.5%<br>Lead debt: 20–30% below target<br>Process breakdown / rep churn<br>Carries unrecovered</div>
      <div class="scmr"><span class="scml">Month 1</span><span class="scmv" id="sc-u1">$714K</span></div>
      <div class="scmr"><span class="scml">Month 2</span><span class="scmv" id="sc-u2">$816K</span></div>
      <div class="scmr"><span class="scml">Month 3</span><span class="scmv" id="sc-u3">$867K</span></div>
      <div style="background:var(--text);border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:rgba(255,255,255,0.35);">Q ARR</span>
        <span style="font-size:24px;font-weight:800;letter-spacing:-0.5px;color:var(--red);" id="sc-uq">$2.40M</span>
      </div>
      <div class="sccond" id="sc-uc"><span>— 14 deals/mo avg</span><span>— 6.5% close rate</span><span>— Lead volume deficit</span><span>— Carries unrecovered</span></div>
    </div>
    <div class="sctile base">
      <div class="schead">→ Baseline</div>
      <div class="scdesc" id="sc-bd">Close rate holds at 9.5%<br>265 leads / mo sustained<br>25 projected closes hit<br>20 land · 5 carry resolved</div>
      <div class="scmr"><span class="scml">Month 1</span><span class="scmv" id="sc-b1">$1.02M</span></div>
      <div class="scmr"><span class="scml">Month 2</span><span class="scmv" id="sc-b2">$1.22M</span></div>
      <div class="scmr"><span class="scml">Month 3</span><span class="scmv" id="sc-b3">$1.28M</span></div>
      <div style="background:var(--text);border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:rgba(255,255,255,0.35);">Q ARR</span>
        <span style="font-size:24px;font-weight:800;letter-spacing:-0.5px;color:var(--accent);" id="sc-bq">$3.52M</span>
      </div>
      <div class="sccond" id="sc-bc"><span>— 25 projected closes / mo</span><span>— 9.5% close rate holds</span><span>— 265 leads / mo</span><span>— M1 carry resolved by M3</span></div>
    </div>
    <div class="sctile over">
      <div class="schead">↑ Outperformance</div>
      <div class="scdesc" id="sc-od">Close rate improves to ~12.5%<br>Lead volume sustained at 265<br>Compressed cycle · fewer carries<br>Carry rate drops to ~10%</div>
      <div class="scmr"><span class="scml">Month 1</span><span class="scmv" id="sc-o1">$1.33M</span></div>
      <div class="scmr"><span class="scml">Month 2</span><span class="scmv" id="sc-o2">$1.63M</span></div>
      <div class="scmr"><span class="scml">Month 3</span><span class="scmv" id="sc-o3">$1.68M</span></div>
      <div style="background:var(--text);border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:rgba(255,255,255,0.35);">Q ARR</span>
        <span style="font-size:24px;font-weight:800;letter-spacing:-0.5px;color:var(--green);" id="sc-oq">$4.64M</span>
      </div>
      <div class="sccond" id="sc-oc"><span>— 26 deals/mo avg</span><span>— 12.5% close rate</span><span>— 265 leads / mo sustained</span><span>— Carry rate drops to ~10%</span></div>
    </div>
  </div>

  <div class="divider"></div>
  <div class="g3">
    <div class="stat" style="background:#FFF8F8;border-color:#F5DADA;">
      <div class="slabel">Q Miss vs Baseline</div>
      <div class="sval red" id="sc-du">−$1.12M</div>
      <div class="snote" id="sc-dun">$2.40M vs $3.52M</div>
    </div>
    <div class="stat">
      <div class="slabel">Baseline Quarter</div>
      <div class="sval by" id="sc-bq2" style="font-size:26px;">$3.52M</div>
      <div class="snote" id="sc-bn">9.5% close · 265 leads / mo</div>
    </div>
    <div class="stat" style="background:#F5FFF9;border-color:#C8EDD9;">
      <div class="slabel">Q Upside vs Baseline</div>
      <div class="sval green" id="sc-do">+$1.12M</div>
      <div class="snote" id="sc-don">$4.64M vs $3.52M</div>
    </div>
  </div>

  <footer><span class="fmeta">Pipeline Intelligence · KeychainOS · {GENERATED_AT}</span><span class="fconf">Confidential</span></footer>
</div>


<script>
// ── HELPERS ──────────────────────────────────────────────
const SW_R = {SW_RATIO:.6f};
const IMPL_R = {IMPL_RATIO:.6f};
const UNDER_CR_MULT = {UNDER_CR_MULT};
const OVER_CR_MULT = {OVER_CR_MULT};

function fmtM(n) {{
  if(n>=1000000) return '$'+(n/1000000).toFixed(2)+'M';
  return '$'+(n/1000).toFixed(0)+'K';
}}
function fmtK(n) {{ return '$'+Math.round(n/1000)+'K'; }}
function set(id,val) {{
  const el=document.getElementById(id);
  if(!el)return;
  const v=String(val);
  if(el.textContent!==v){{el.textContent=v;el.classList.remove('changed');void el.offsetWidth;el.classList.add('changed');}}
}}
function setHtml(id,html) {{
  const el=document.getElementById(id);
  if(el)el.innerHTML=html;
}}

// ── CORE MODEL ────────────────────────────────────────────
function model(cr, acv, leads) {{
  const crd = cr/100;
  const proj = Math.round(leads * crd);
  const cw = Math.round(proj * 0.8);
  const carry = proj - cw;

  // M2: cw from fresh pipeline + resolved M1 carries
  const m1Resolved = Math.round(carry * 0.8);  // 4 of 5
  const m2cw = cw + m1Resolved;                 // 20 + 4 = 24
  const arrM2 = m2cw * acv;

  // M3: fresh pipeline closes + M2 carries resolving + M1 deal that slipped past M2
  // M2 carry = same 20% rate applied to M2's new projected closes
  const m2Carry = carry;                         // M2 generates same carry count as M1
  const m2Resolved = Math.round(m2Carry * 0.8); // 80% of M2 carries close in M3
  const m1SlippedToM3 = carry - m1Resolved;      // M1 deals that didn't close in M2 (1)
  const m3cw = cw + m2Resolved + m1SlippedToM3; // 20 + 4 + 1 = 25
  const arrM3 = m3cw * acv;

  const arrM1 = cw * acv;
  const arrQ = arrM1 + arrM2 + arrM3;
  const totalQ = cw + m2cw + m3cw;

  // Funnel
  const response = Math.round(leads * 0.50);
  const mql = Math.round(leads * 0.305);
  const sql = Math.round(leads * 0.196);

  // Scenarios — vary CR only, same leads
  function sc(crMult) {{
    const sCr = crd * crMult;
    const sProj = Math.round(leads * sCr);
    const sCw = Math.round(sProj * 0.8);
    const sCarry = sProj - sCw;
    const sM1r = Math.round(sCarry * 0.8);
    const sM2cw = sCw + sM1r;
    const sM2carry = sCarry;                        // M2 carry rate same as M1
    const sM2r = Math.round(sM2carry * 0.8);        // 80% of M2 carries close in M3
    const sM1slipped = sCarry - sM1r;               // M1 deals that slipped past M2
    const sM3cw = sCw + sM2r + sM1slipped;
    return {{
      cr: (sCr*100).toFixed(1),
      cw: sCw,
      m1: sCw * acv,
      m2: sM2cw * acv,
      m3: sM3cw * acv,
      q: (sCw + sM2cw + sM3cw) * acv
    }};
  }}

  const under = sc(UNDER_CR_MULT);
  const over  = sc(OVER_CR_MULT);

  const wk = Math.round(leads / 4.33);
  const swAmt = Math.round(acv * SW_R / 1000);
  const implAmt = Math.round(acv * IMPL_R / 1000);

  return {{
    cr,acv,leads,proj,cw,carry,
    m1Resolved,m1SlippedToM3,m2cw,m3cw,
    arrM1,arrM2,arrM3,arrQ,totalQ,
    response,mql,sql,
    under,over,wk,swAmt,implAmt
  }};
}}

// ── BUILD REP TABLE ───────────────────────────────────────
function statusBadge(val) {{
  const v = parseFloat(val);
  if (v >= 3.5) return `<span style="background:#F0FBF6;color:#1A9E5F;font-size:10px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;padding:3px 8px;border-radius:4px;">Efficient</span>`;
  if (v >= 2.5) return `<span style="background:#0A0A0A;color:#F5D000;font-size:10px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;padding:3px 8px;border-radius:4px;">Optimal</span>`;
  if (v >= 2.0) return `<span style="background:#FFF4E8;color:#B05010;font-size:10px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;padding:3px 8px;border-radius:4px;">Diminishing</span>`;
  return `<span style="background:#FFF0F0;color:#E03030;font-size:10px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;padding:3px 8px;border-radius:4px;">Lead-constrained</span>`;
}}

function buildRepTable(d) {{
  const rows=[
    {{r:6,  t:4, a:(d.cw/6).toFixed(1)}},
    {{r:8,  t:3, a:(d.cw/8).toFixed(1)}},
    {{r:10, t:2, a:(d.cw/10).toFixed(1)}},
    {{r:11, t:2, a:(d.cw/11).toFixed(1)}},
  ];
  const tb=document.getElementById('rep-tbody');
  tb.innerHTML=rows.map(r=>`
    <tr>
      <td>${{r.r}} Reps</td>
      <td>${{r.t}} / mo</td>
      <td style="font-size:18px;font-weight:800;letter-spacing:-0.3px;color:${{parseFloat(r.a)<2?'#E03030':parseFloat(r.a)<2.5?'#B05010':parseFloat(r.a)<3.5?'inherit':'#1A9E5F'}}">${{r.a}}</td>
      <td>~${{d.cw}}</td>
      <td>${{fmtM(d.arrM1)}}</td>
      <td>${{statusBadge(r.a)}}</td>
    </tr>
  `).join('');
}}

// ── MAIN UPDATE ───────────────────────────────────────────
function update() {{
  const cr    = parseFloat(document.getElementById('sl-cr').value);
  const acv   = parseInt(document.getElementById('sl-acv').value) * 1000;
  const leads = parseInt(document.getElementById('sl-leads').value);

  document.getElementById('v-cr').textContent    = cr + '%';
  document.getElementById('v-acv').textContent   = '$' + (acv/1000) + 'K';
  document.getElementById('v-leads').textContent = leads;

  const d = model(cr, acv, leads);

  // SLIDE 1
  set('s1-sub', d.proj+' projected closes required each month · '+d.carry+' planned carries are structural, not failure');
  set('p1-leads', d.leads);
  set('p1-proj', d.proj); set('p1-cr', cr+'%'); set('p1-cr2', cr+'%'); set('p1-proj2', d.proj);
  set('p1-acv', fmtK(acv));
  set('p1-proj3', d.proj); set('p1-cw', d.cw); set('p1-carry', d.carry);
  set('p1-carry-tag', d.carry+' carry → M+1');
  set('p1-cw2', d.cw); set('p1-arr', fmtM(d.arrM1)); set('p1-cw3', d.cw); set('p1-acv2', fmtK(acv));
  set('p1-arr-tag', fmtM(d.arrM1)+' / mo'); set('p1-wk', '~'+d.wk+' / wk');
  set('s1-proj', d.proj); set('s1-cw', d.cw);
  set('s1-arr-note', d.cw+' × '+fmtK(acv)+' = '+fmtM(d.arrM1)+' ARR');
  set('s1-leads', d.leads);
  set('s1-leads-note', cr+'% × '+d.leads+' = '+d.proj+' projected');
  set('s1-cr', cr+'%');

  // SLIDE 2
  set('s2-acv-big', '$'+(acv).toLocaleString());
  set('s2-sw', '$'+d.swAmt+'K'); set('s2-impl', '$'+d.implAmt+'K'); set('s2-acv-tot', fmtK(acv));
  setHtml('s2-acv-note', '<strong>ACV at '+fmtK(acv)+':</strong> $'+d.swAmt+'K software + $'+d.implAmt+'K implementation. Sliders adjust live across all pages.');
  set('s2-proj', d.proj); set('s2-cw', d.cw);
  set('s2-arr-mo', fmtM(d.arrM1)); set('s2-arr-q', fmtM(d.arrQ));
  set('s2-arr-yr', fmtM(d.arrM1*12)); set('s2-leads', d.leads);
  buildRepTable(d);

  // SLIDE 3
  set('s3-sub', 'Month 1 attrition · '+d.leads+' raw leads → '+d.proj+' projected closes → '+d.cw+' closed won');
  set('f-leads', d.leads);
  set('f-d1', '~'+Math.round(d.leads*0.50)+' lost at initial outreach / unresponsive');
  set('f-res', d.response);
  document.getElementById('f-f2').style.width=Math.min(d.response/d.leads*100,98)+'%';
  set('f-d2', '~'+(d.response-d.mql)+' disqualified at CS/AM qualification');
  set('f-mql', d.mql);
  document.getElementById('f-f3').style.width=Math.min(d.mql/d.leads*100,98)+'%';
  set('f-d3', '~'+(d.mql-d.sql)+' lost in discovery / no product fit');
  set('f-sql', d.sql);
  document.getElementById('f-f4').style.width=Math.min(d.sql/d.leads*100,98)+'%';
  set('f-d4', '~'+(d.sql-d.proj)+' lost during proposal / evaluation');
  set('f-proj', d.proj);
  document.getElementById('f-f5').style.width=Math.min(d.proj/d.leads*100,98)+'%';
  set('f-cn', d.carry+' of '+d.proj+' carry to Month 2 — designed into model');
  set('f-cw', d.cw);
  document.getElementById('f-f6').style.width=Math.min(d.cw/d.leads*100,98)+'%';
  set('f-ratio', (d.leads/d.proj).toFixed(1));
  set('f-rn', d.leads+' ÷ '+d.proj+' projected = '+(d.leads/d.proj).toFixed(1)+':1');
  set('f-acv', fmtK(acv));
  set('f-l2', d.leads);
  setHtml('f-ln', cr+'% × '+d.leads+' = '+d.proj+' closes<br>'+d.cw+' land · '+d.carry+' carry → M2');
  set('f-wk', '~'+d.wk);
  setHtml('f-wn', d.leads+' ÷ 4.33 weeks<br>'+Math.ceil(d.proj/4.33)+'–'+(Math.ceil(d.proj/4.33)+1)+' projected/wk<br>'+Math.ceil(d.cw/4.33)+'–'+(Math.ceil(d.cw/4.33)+1)+' actual/wk');

  // SLIDE 4
  set('s4-sub', d.proj+' projected closes is the monthly quota · '+d.carry+' planned carries are structural · 3-month map');
  set('s4-p1', d.proj); set('s4-cw1', d.cw); set('s4-c1', d.carry); set('s4-l1', d.leads);
  set('s4-a1', fmtM(d.arrM1)); set('s4-ct', d.carry+' carry → M2'); set('s4-w1', '~'+d.wk+' leads / week');
  set('s4-p2', d.proj); set('s4-cr2', '+'+d.m1Resolved);
  set('s4-cw2', d.m2cw); set('s4-l2', d.leads); set('s4-a2', fmtM(d.arrM2));
  set('s4-m2t', d.m1Resolved+' close (M1)');
  set('s4-w2', d.leads+' fresh + '+d.m1Resolved+' carryover');
  set('s4-p3', d.proj); set('s4-cw3', '~'+d.m3cw); set('s4-l3', d.leads); set('s4-a3', fmtM(d.arrM3));
  set('s4-tq', d.totalQ); set('s4-tn', d.cw+' + '+d.m2cw+' + '+d.m3cw);
  set('s4-aq', fmtM(d.arrQ)); set('s4-q', d.proj); set('s4-ln', d.leads);

  // SLIDE 5
  const u=d.under, b=d, o=d.over;
  setHtml('sc-ud', 'Close rate drops to ~'+u.cr+'%<br>Lead debt: 20–30% below target<br>Process breakdown / rep churn<br>Carries unrecovered');
  setHtml('sc-bd', 'Close rate holds at '+cr+'%<br>'+d.leads+' leads / mo sustained<br>'+d.proj+' projected closes hit<br>'+d.cw+' land · '+d.carry+' carry resolved');
  setHtml('sc-od', 'Close rate improves to ~'+o.cr+'%<br>Lead volume sustained at '+d.leads+'<br>Compressed cycle · fewer carries<br>Carry rate drops to ~10%');
  set('sc-u1', fmtM(u.m1)); set('sc-u2', fmtM(u.m2)); set('sc-u3', fmtM(u.m3)); set('sc-uq', fmtM(u.q));
  set('sc-b1', fmtM(b.arrM1)); set('sc-b2', fmtM(b.arrM2)); set('sc-b3', fmtM(b.arrM3)); set('sc-bq', fmtM(b.arrQ)); set('sc-bq2', fmtM(b.arrQ));
  set('sc-o1', fmtM(o.m1)); set('sc-o2', fmtM(o.m2)); set('sc-o3', fmtM(o.m3)); set('sc-oq', fmtM(o.q));
  setHtml('sc-uc', '<span>— '+u.cw+' deals/mo avg</span><span>— '+u.cr+'% close rate</span><span>— Lead volume deficit</span><span>— Carries unrecovered</span>');
  setHtml('sc-bc', '<span>— '+d.proj+' projected closes / mo</span><span>— '+cr+'% close rate holds</span><span>— '+d.leads+' leads / mo</span><span>— M1 carry resolved by M3</span>');
  setHtml('sc-oc', '<span>— '+o.cw+' deals/mo avg</span><span>— '+o.cr+'% close rate</span><span>— '+d.leads+' leads / mo sustained</span><span>— Carry rate drops to ~10%</span>');
  const deltaU = b.arrQ - u.q;
  const deltaO = o.q - b.arrQ;
  set('sc-du', '−'+fmtM(deltaU)); set('sc-dun', fmtM(u.q)+' vs '+fmtM(b.arrQ));
  set('sc-do', '+'+fmtM(deltaO)); set('sc-don', fmtM(o.q)+' vs '+fmtM(b.arrQ));
  set('sc-bn', cr+'% close · '+d.leads+' leads / mo');
}}

function show(idx) {{
  document.querySelectorAll('.page').forEach((p,i)=>p.classList.toggle('active',i===idx));
  document.querySelectorAll('.nav-btn').forEach((b,i)=>b.classList.toggle('active',i===idx));
}}

update();
</script>
</body>
</html>"""


def main():
    html = build_html()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Built {OUTPUT_FILE} — {GENERATED_AT}")
    print(f"Access code hash: {CODE_HASH[:16]}...")


if __name__ == "__main__":
    main()
