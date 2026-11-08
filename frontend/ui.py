"""Shared styling and reusable UI components.

Design notes
------------
* Palette is colour-blind safe (Okabe-Ito inspired): deep navy + blue as the
  brand, amber as the single contrast accent. No red/green pairs.
* Meaning is never carried by colour alone: every badge has a symbol and a
  text label, and confidence is also shown as a number and a ring/bar.
* Card rows are CSS grids, so cards in the same row always have equal height.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from ai.embedder import ModelLoadError
from ai.matcher import confidence_label, run_matching
from config import APP_TAGLINE
from utils import files

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
:root{
  --navy:#0A1F44; --navy2:#12306B; --blue:#0B5FFF; --blue-d:#0842B5; --sky:#E8F0FE;
  --amber:#E69F00; --amber-l:#FFF1D0; --amber-d:#7A4B00; --ink:#14213D; --muted:#5B6B8C; --line:#D6E2F7;
  --radius:16px; --shadow:0 3px 14px rgba(10,31,68,.07);
}
html, body, [class*="css"], .stApp { font-family:'Inter','Segoe UI',sans-serif; color:var(--ink); }
.stApp { background:linear-gradient(180deg,#F4F8FF 0%,#E9F0FD 100%); }
.block-container { padding:1rem 2rem 1.5rem 2rem; max-width:1200px; }
header[data-testid="stHeader"] { background:transparent; height:2.2rem; }
h1,h2,h3,h4 { color:var(--navy); letter-spacing:-.01em; }

/* ---- compact, consistent spacing ---- */
div[data-testid="stVerticalBlock"] { gap:.7rem; }
div[data-testid="stHorizontalBlock"] { gap:.9rem; }
div[data-testid="stForm"] div[data-testid="stVerticalBlock"] { gap:.55rem; }
div[data-testid="stMarkdownContainer"] p { margin-bottom:0; }
div[data-testid="stElementContainer"] { margin:0; }

/* ---- hide the "Press Enter to submit form" / counter hints ---- */
div[data-testid="InputInstructions"], [data-testid="stTextInput"] small,
[data-testid="stTextArea"] small { display:none !important; }

/* ================= Sidebar ================= */
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#071733 0%,#0A1F44 45%,#12306B 100%); border-right:none; }
section[data-testid="stSidebar"] > div { padding-top:.4rem; }
section[data-testid="stSidebar"] * { color:#E8F0FE; }
section[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.14); margin:.6rem 0; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap:.5rem; }
.fm-logo { display:flex; align-items:center; gap:.75rem; padding:.5rem .3rem .2rem .3rem; }
.fm-logo-mark { width:48px; height:48px; border-radius:14px; background:linear-gradient(135deg,#FFFFFF,#BFD6FF);
  display:flex; align-items:center; justify-content:center; font-size:1.55rem; box-shadow:0 6px 18px rgba(0,0,0,.35); }
.fm-logo-title { font-weight:800; font-size:1.35rem; color:#fff !important; line-height:1.1; }
.fm-logo-title span { color:#FFC857 !important; }
.fm-logo-sub { font-size:.72rem; color:#9FB6E3 !important; margin-top:2px; }
.fm-side-label { font-size:.68rem; font-weight:700; letter-spacing:.16em; color:#7F9BD3 !important; margin:.3rem .4rem 0 .4rem; }
section[data-testid="stSidebar"] [role="radiogroup"] { gap:.3rem; }
section[data-testid="stSidebar"] [role="radiogroup"] label { padding:.62rem .9rem; border-radius:12px; width:100%;
  border:1px solid transparent; transition:all .15s; background:rgba(255,255,255,.04); }
section[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:rgba(255,255,255,.13); border-color:rgba(255,255,255,.22); transform:translateX(3px); }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:#fff;
  border-left:5px solid #FFC857; box-shadow:0 6px 18px rgba(0,0,0,.3); }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * { color:var(--navy) !important; font-weight:800; }
section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display:none; }
section[data-testid="stSidebar"] [role="radiogroup"] label p { font-size:.95rem; font-weight:600; }
.fm-side-card { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.18); border-radius:14px;
  padding:.7rem .9rem; font-size:.78rem; line-height:1.4; }
.fm-side-card b { color:#FFC857 !important; }

/* ================= Hero ================= */
.fm-hero { position:relative; overflow:hidden; color:#fff; border-radius:20px; padding:1.25rem 1.6rem;
  background:radial-gradient(circle at 88% 15%,rgba(255,200,87,.30),transparent 42%),
             linear-gradient(120deg,#0A1F44 0%,#0842B5 58%,#0B5FFF 100%);
  box-shadow:0 10px 26px rgba(10,31,68,.28); }
.fm-hero::after { content:""; position:absolute; right:-50px; bottom:-80px; width:220px; height:220px;
  border-radius:50%; border:34px solid rgba(255,255,255,.07); }
.fm-hero h1 { color:#fff; margin:0; padding:0; font-family:'Playfair Display',Georgia,serif; font-size:1.9rem; font-weight:800; line-height:1.2; }
.fm-hero p { margin:.3rem 0 0 0; color:#D5E3FF; font-size:.95rem; max-width:680px; }
.fm-eyebrow { display:inline-block; font-size:.68rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:#FFC857; }
.fm-chips { margin-top:.7rem; }
.fm-chip { display:inline-block; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.28);
  color:#fff; padding:.2rem .75rem; border-radius:999px; font-size:.75rem; font-weight:600; margin-right:.4rem; }

/* ================= Section titles ================= */
.fm-section { display:flex; align-items:center; gap:.55rem; margin:.2rem 0 0 0; }
.fm-section .bar { width:5px; height:22px; border-radius:4px; background:linear-gradient(var(--blue),var(--amber)); }
.fm-section h3 { margin:0; padding:0; font-size:1.12rem; font-weight:800; }

/* ================= Grids (equal-height cards) ================= */
.fm-grid { display:grid; gap:.9rem; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); }
.fm-grid.two { grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); }

.fm-card { background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:1rem 1.2rem; box-shadow:var(--shadow); }
.fm-metric { position:relative; overflow:hidden; padding-top:1.15rem; transition:transform .15s, box-shadow .15s; }
.fm-metric:hover { transform:translateY(-3px); box-shadow:0 10px 24px rgba(10,31,68,.15); }
.fm-metric::before { content:""; position:absolute; left:0; top:0; right:0; height:5px; background:var(--accent,#0B5FFF); }
.fm-metric-top { display:flex; justify-content:space-between; align-items:center; }
.fm-metric-label { color:var(--muted); font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
.fm-metric-icon { width:40px; height:40px; border-radius:12px; background:var(--tint,#E8F0FE);
  display:flex; align-items:center; justify-content:center; font-size:1.2rem; }
.fm-metric-value { font-size:2.35rem; font-weight:800; color:var(--navy); line-height:1.1; margin-top:.35rem; }
.fm-metric-sub { color:var(--muted); font-size:.78rem; margin-top:.1rem; }

.fm-step .n { width:28px; height:28px; border-radius:50%; background:var(--navy); color:#fff; font-weight:800;
  display:flex; align-items:center; justify-content:center; margin-bottom:.4rem; font-size:.85rem; }
.fm-step b { color:var(--navy); } .fm-step .t { color:var(--muted); font-size:.82rem; margin-top:.15rem; }

/* ================= Item & match cards ================= */
.fm-item { background:#fff; border:1px solid var(--line); border-left:6px solid var(--blue); border-radius:var(--radius);
  padding:.85rem 1.1rem; box-shadow:var(--shadow); }
.fm-item.found { border-left-color:var(--amber); }
.fm-item h4 { margin:0 0 .3rem 0; padding:0; color:var(--navy); font-size:1.02rem; font-weight:700; }
.fm-item p { margin:.3rem 0; color:#33415F; font-size:.9rem; line-height:1.45; }
.fm-meta { color:var(--muted); font-size:.78rem; margin-top:.35rem; }
.fm-matchbox { background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:.9rem 1.1rem 1rem 1.1rem; box-shadow:var(--shadow); }
.fm-matchbox .fm-item { box-shadow:none; background:#F8FAFF; }
.fm-matchhead { display:flex; justify-content:space-between; align-items:center; gap:1rem; }
.fm-matchtitle { font-weight:700; color:var(--navy); margin-bottom:.25rem; }
.fm-pair { display:grid; grid-template-columns:1fr 1fr; gap:.8rem; margin-top:.6rem; }
@media (max-width:700px){ .fm-pair{ grid-template-columns:1fr; } }

/* ================= Badges (colour + symbol + text) ================= */
.fm-badge { display:inline-block; padding:.15rem .6rem; border-radius:999px; font-size:.68rem; font-weight:700;
  margin:0 .3rem .15rem 0; letter-spacing:.04em; border:1.5px solid transparent; }
.b-high { background:var(--navy); color:#fff; }
.b-medium { background:var(--amber-l); color:var(--amber-d); border-color:var(--amber); }
.b-low { background:#EEF1F6; color:#4A5568; border-color:#B8C2D6; border-style:dashed; }
.b-lost { background:#DCEBFF; color:#0842B5; border-color:#0B5FFF; }
.b-found { background:var(--amber-l); color:var(--amber-d); border-color:var(--amber); }
.b-open { background:#fff; color:#0842B5; border-color:#0B5FFF; }
.b-resolved { background:var(--navy); color:#fff; }
.b-pending { background:var(--amber-l); color:var(--amber-d); border-color:var(--amber); }
.b-cat { background:#F1F4FA; color:#44516E; border-color:#D5DDEC; }

/* ================= Score ring + bar ================= */
.fm-ring { --c:var(--blue); width:68px; height:68px; border-radius:50%; flex:none;
  background:conic-gradient(var(--c) calc(var(--p)*1%), #E3EAF8 0); display:flex; align-items:center; justify-content:center; }
.fm-ring.medium { --c:var(--amber); } .fm-ring.low { --c:#8A97B3; } .fm-ring.high { --c:var(--blue); }
.fm-ring > span { width:52px; height:52px; border-radius:50%; background:#fff; display:flex; align-items:center;
  justify-content:center; font-weight:800; font-size:.98rem; color:var(--navy); }
.fm-bar { background:#E3EAF8; border-radius:999px; height:8px; overflow:hidden; margin:.5rem 0 .25rem 0; }
.fm-bar > div { height:100%; background:linear-gradient(90deg,var(--blue),var(--navy2)); border-radius:999px; }

/* ================= Form chrome ================= */
div[data-testid="stForm"] { background:#fff; border:1px solid var(--line); border-top:5px solid var(--blue);
  border-radius:20px; padding:1.2rem 1.5rem 1.3rem 1.5rem; box-shadow:0 8px 26px rgba(10,31,68,.09); }
.fm-formhead { display:flex; align-items:center; gap:.65rem; padding:.15rem 0 .3rem 0; border-bottom:1px solid #E6EDFA; margin-bottom:.1rem; }
.fm-formhead .ico { width:34px; height:34px; border-radius:10px; background:var(--sky); display:flex;
  align-items:center; justify-content:center; font-size:1.05rem; }
.fm-formhead b { color:var(--navy); font-size:1rem; } .fm-formhead span.s { color:var(--muted); font-size:.8rem; display:block; }
.fm-formnote { color:var(--muted); font-size:.78rem; }

/* uniform field look: same height, radius, border, focus ring */
label[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] p { font-weight:600; font-size:.84rem; color:var(--navy); }
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
  border-radius:12px !important; background:#F7FAFF !important; border:1.5px solid #CBD9F2 !important; }
div[data-baseweb="input"], div[data-baseweb="select"] > div { min-height:46px; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="textarea"]:focus-within {
  border-color:var(--blue) !important; box-shadow:0 0 0 3px rgba(11,95,255,.18) !important; background:#fff !important; }
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { font-size:.93rem; }
section[data-testid="stSidebar"] div[data-baseweb="input"] { background:transparent !important; }
div[data-testid="stFileUploaderDropzone"] { border:2px dashed #9DB8EA; border-radius:14px; background:#F7FAFF; padding:.7rem 1rem; }

/* buttons: equal height, full width inside forms */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button, div.stDownloadButton > button {
  border-radius:12px; font-weight:700; min-height:46px; padding:.4rem 1.3rem; border:1.5px solid var(--blue);
  color:var(--blue-d); background:#fff; transition:all .15s; }
div[data-testid="stFormSubmitButton"] > button { width:100%; }
div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
  background:linear-gradient(135deg,#0B5FFF,#0842B5); color:#fff !important; border:none; box-shadow:0 6px 16px rgba(11,95,255,.35); }
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { transform:translateY(-1px); box-shadow:0 8px 18px rgba(11,95,255,.28); }
div.stButton > button[kind="primary"] p, div[data-testid="stFormSubmitButton"] > button[kind="primary"] p { color:#fff !important; }

/* admin session bar + sign-out */
.fm-adminbar { display:flex; align-items:center; gap:.7rem; min-height:46px; padding:0 1rem; border-radius:12px;
  background:#fff; border:1px solid var(--line); border-left:6px solid var(--amber); font-weight:600; color:var(--navy); box-shadow:var(--shadow); }
.fm-adminbar small { color:var(--muted); font-weight:500; }
.st-key-signout button { background:linear-gradient(135deg,#FFB627,#E69F00) !important; color:#2B1A00 !important; border:none !important;
  box-shadow:0 6px 16px rgba(230,159,0,.45) !important; font-weight:800 !important; }
.st-key-signout, .st-key-signout div.stButton, .st-key-signout button { width:100%; }
.st-key-signout button p { color:#2B1A00 !important; font-weight:800; }

/* tabs as pills */
.stTabs [data-baseweb="tab-list"] { gap:.4rem; border-bottom:none; background:#fff; padding:.35rem; border-radius:14px;
  border:1px solid var(--line); box-shadow:var(--shadow); }
.stTabs [data-baseweb="tab"] { font-weight:700; border-radius:10px; padding:.4rem 1.1rem; height:auto; }
.stTabs [aria-selected="true"] { background:var(--navy); color:#fff !important; }
.stTabs [aria-selected="true"] p { color:#fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
div[data-testid="stExpander"] { background:#fff; border-radius:14px; border:1px solid var(--line); box-shadow:var(--shadow); }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:14px; overflow:visible; box-shadow:var(--shadow); }
div[data-testid="stDataFrame"] > div, div[data-testid="stDataFrameResizable"] { overflow:visible !important; }
div[data-testid="stStatusWidget"] { display:none !important; }
div[data-testid="stAlert"] { border-radius:12px; }

/* ================= Empty state & notices ================= */
.fm-empty { text-align:center; background:#fff; border:2px dashed #B3C9F0; border-radius:var(--radius); padding:1.6rem 1rem; color:var(--muted); }
.fm-empty .ico { font-size:2.2rem; } .fm-empty h4 { color:var(--navy); margin:.2rem 0 .1rem 0; padding:0; font-size:1.05rem; }
.fm-disclaimer { background:var(--amber-l); border:1px solid var(--amber); border-left:6px solid var(--amber);
  color:#5A3800; border-radius:12px; padding:.6rem 1rem; font-size:.84rem; }
.fm-tips { color:var(--muted); font-size:.8rem; }
.fm-tip { display:inline-block; background:var(--sky); color:var(--blue-d); border-radius:999px; padding:.15rem .7rem; margin:.15rem .25rem 0 0; font-weight:600; }

/* ================= Overrides found during visual QA ================= */
/* explicit spacing between our own blocks (Streamlit's flex gap is not reliable for raw HTML) */
.fm-hero { margin-bottom:1rem; }
.fm-grid { margin-bottom:1rem; }
.fm-section { margin:.6rem 0 .7rem 0; }
.fm-item, .fm-matchbox, .fm-disclaimer, .fm-empty, .fm-adminbar { margin-bottom:.8rem; }
.fm-matchbox .fm-item, .fm-adminbar { margin-bottom:0; }
.fm-formhead { margin:.7rem 0 .8rem 0; padding-bottom:.55rem; }
div[data-testid="stForm"] > div > div[data-testid="stVerticalBlock"] > div:first-child .fm-formhead { margin-top:0; }
.fm-tips { margin:.1rem 0 .4rem 0; }

/* hide Streamlit's Deploy / toolbar so it never overlaps the hero */
/* (keep stToolbar itself: it also hosts the sidebar "expand" button) */
div[data-testid="stDeployButton"], div[data-testid="stAppDeployButton"], div[data-testid="stMainMenu"],
button[data-testid="stMainMenuButton"], div[data-testid="stToolbarActions"], #MainMenu { display:none !important; }
div[data-testid="stToolbar"] { background:transparent; }

/* primary + form buttons (new Streamlit test-ids), full width inside forms */
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {
  background:linear-gradient(135deg,#0B5FFF,#0842B5) !important; color:#fff !important; border:none !important;
  box-shadow:0 6px 16px rgba(11,95,255,.35); }
button[data-testid="stBaseButton-primary"] p, button[data-testid="stBaseButton-primaryFormSubmit"] p { color:#fff !important; font-weight:700; }
div[data-testid="stFormSubmitButton"], div[data-testid="stFormSubmitButton"] > button { width:100%; }
button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-secondaryFormSubmit"] { min-height:46px; }

/* sidebar: equal-width menu items, no radio dots, readable slider label */
section[data-testid="stSidebar"] [role="radiogroup"] { width:100%; align-items:stretch; }
section[data-testid="stSidebar"] [role="radiogroup"] > label, section[data-testid="stSidebar"] [data-baseweb="radio"] {
  width:100% !important; box-sizing:border-box; margin:0; }
section[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child { display:none !important; }
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child:not([data-testid]) { display:none !important; }
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] { width:100%; }
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] { background:#fff; border-left:5px solid #FFC857; box-shadow:0 6px 18px rgba(0,0,0,.3); }
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] p { color:var(--navy) !important; font-weight:800; }
section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p, section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stSliderThumbValue"], section[data-testid="stSidebar"] [data-testid="stTickBarMin"],
section[data-testid="stSidebar"] [data-testid="stTickBarMax"] { color:#E8F0FE !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color:var(--navy) !important; }
.fm-side-label { margin:.7rem .4rem .35rem .4rem; }

/* full-width submit buttons (form button sits in a shrink-wrapped container otherwise) */
div[data-testid="stFormSubmitButton"] { width:100% !important; }
div[data-testid="stFormSubmitButton"] button { width:100% !important; }
div[data-testid="stElementContainer"]:has(> div[data-testid="stFormSubmitButton"]) { width:100% !important; }

div[data-testid="stElementContainer"]:has(div[data-testid="stFormSubmitButton"]),
div[data-testid="stElementContainer"]:has(div[data-testid="stFormSubmitButton"]) > div,
div[data-testid="stElementContainer"]:has(div[data-testid="stRadio"]),
div[data-testid="stRadio"], div[data-testid="stRadio"] > div,
div[data-testid="stRadio"] [role="radiogroup"], div[data-testid="stRadio"] [role="radiogroup"] > div { width:100% !important; }
div[data-testid="stRadio"] [role="radiogroup"] { display:grid !important; grid-template-columns:100%; }
div[data-testid="stRadio"] label[data-testid="stRadioOption"] { width:100% !important; box-sizing:border-box; }

/* tabs as a white pill bar (selectors not scoped to .stTabs, which varies by version) */
div[role="tablist"] { gap:.4rem; background:#fff; padding:.35rem; border-radius:14px; border:1px solid var(--line);
  box-shadow:var(--shadow); }
div[role="tab"] { border-radius:10px; padding:.45rem 1.1rem !important; height:auto; font-weight:700; }
div[role="tab"][aria-selected="true"] { background:var(--navy) !important; }
div[role="tab"][aria-selected="true"], div[role="tab"][aria-selected="true"] * { color:#fff !important; }
div[data-baseweb="tab-list"] { gap:.4rem; background:#fff; padding:.35rem; border-radius:14px; border:1px solid var(--line);
  box-shadow:var(--shadow); }
button[data-baseweb="tab"] { border-radius:10px; padding:.45rem 1.1rem; height:auto; font-weight:700; }
button[data-baseweb="tab"][aria-selected="true"] { background:var(--navy); }
button[data-baseweb="tab"][aria-selected="true"] p, button[data-baseweb="tab"][aria-selected="true"] { color:#fff !important; }
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display:none !important; }

/* ---- tabs: remove the blue underline that follows the selected tab ---- */
.react-aria-SelectionIndicator, div[role="tablist"] [class*="SelectionIndicator"] { display:none !important; }
div[role="tab"] { border-bottom:none !important; }

/* ---- chart / table hover panel (Show data, Download as PNG, Copy, Fullscreen) ----
   Always visible (Streamlit fades it out on mouse-leave and after "Show data"),
   high contrast, with a full-text label on hover. */
div[data-testid="stElementToolbar"] { opacity:1 !important; visibility:visible !important; transition:none !important;
  background:#fff !important; border:1.5px solid var(--navy) !important; border-radius:12px !important; padding:3px !important;
  box-shadow:0 6px 16px rgba(10,31,68,.35); z-index:50; }
div[data-testid="stElementToolbarButtonContainer"] { gap:2px; background:#fff !important; border-radius:9px; }
button[data-testid="stBaseButton-elementToolbar"] { position:relative; width:34px; height:34px; border-radius:9px;
  color:var(--navy) !important; background:transparent !important; opacity:1 !important; }
button[data-testid="stBaseButton-elementToolbar"] { color:var(--navy) !important; }
button[data-testid="stBaseButton-elementToolbar"] svg { fill:var(--navy); color:var(--navy); }
button[data-testid="stBaseButton-elementToolbar"]:hover { background:var(--amber) !important; }
button[data-testid="stBaseButton-elementToolbar"]:hover { color:#2B1A00 !important; }
button[data-testid="stBaseButton-elementToolbar"]:hover svg { fill:#2B1A00; color:#2B1A00; }
button[data-testid="stBaseButton-elementToolbar"]:hover::after { content:attr(aria-label); position:absolute; top:calc(100% + 8px);
  right:0; background:#fff; color:var(--navy); border:1.5px solid var(--navy); font-size:.8rem; font-weight:700;
  padding:.35rem .7rem; border-radius:8px; white-space:nowrap; box-shadow:0 6px 16px rgba(10,31,68,.3); z-index:9999;
  pointer-events:none; }

/* ---- panel sits ABOVE every chart / table box (in its own reserved band), not on top of it ---- */
div[data-testid="stElementContainer"]:has([data-testid="stElementToolbar"]) { padding-top:46px; }
div[data-testid="stElementToolbar"] { top:-46px !important; right:0 !important; }

/* ---- visible, easy-to-grab scrollbars (vertical + horizontal) ---- */
[data-testid="stMain"] *::-webkit-scrollbar { width:12px; height:12px; }
[data-testid="stMain"] *::-webkit-scrollbar-track { background:#E3ECFB; border-radius:8px; }
[data-testid="stMain"] *::-webkit-scrollbar-thumb { background:#7FA3E6; border-radius:8px; border:2px solid #E3ECFB; }
[data-testid="stMain"] *::-webkit-scrollbar-thumb:hover { background:var(--blue); }
[data-testid="stMain"] *::-webkit-scrollbar-corner { background:#E3ECFB; }
/* standard properties: force a classic, always-visible scrollbar in Chromium + Firefox */
[data-testid="stMain"] * { scrollbar-width:auto; scrollbar-color:#6F97E3 #DCE8FB; }
div[data-testid="stVerticalBlockBorderWrapper"] { overflow-x:auto; }
.fm-matchbox { min-width:520px; }
.fm-pair { grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); }
.fm-item { min-width:340px; }
.fm-matchbox .fm-item { min-width:0; }

/* ---- admin sign-out button: full wording, never truncated ---- */
.st-key-signout button { white-space:nowrap !important; min-width:max-content; }
.st-key-signout button p { font-size:.98rem !important; overflow:visible !important; text-overflow:clip !important; }

/* ---- sidebar show/hide toggle: always visible, prominent, clickable ---- */
div[data-testid="stSidebarHeader"] { padding:.5rem .8rem 0 .8rem; min-height:2.6rem; justify-content:flex-end; }
div[data-testid="stSidebarCollapseButton"] { visibility:visible !important; opacity:1 !important; }
div[data-testid="stSidebarCollapseButton"] button, button[data-testid="stExpandSidebarButton"],
div[data-testid="stSidebarCollapsedControl"] button {
  visibility:visible !important; opacity:1 !important; cursor:pointer; width:38px; height:38px; border-radius:12px;
  background:#FFC857 !important; color:#0A1F44 !important; border:none !important;
  box-shadow:0 4px 12px rgba(10,31,68,.35); transition:transform .15s, box-shadow .15s; }
div[data-testid="stSidebarCollapseButton"] button:hover, button[data-testid="stExpandSidebarButton"]:hover,
div[data-testid="stSidebarCollapsedControl"] button:hover { transform:scale(1.08); box-shadow:0 6px 16px rgba(10,31,68,.45); }
div[data-testid="stSidebarCollapseButton"] button *, button[data-testid="stExpandSidebarButton"] *,
div[data-testid="stSidebarCollapsedControl"] button * { color:#0A1F44 !important; fill:#0A1F44 !important; }
div[data-testid="stSidebarCollapsedControl"], div[data-testid="stExpandSidebarButton"] { visibility:visible !important; opacity:1 !important; z-index:1000; }

:focus-visible { outline:3px solid var(--amber) !important; outline-offset:2px; }
@media (max-width:768px){ .block-container{padding:.8rem 1rem} .fm-hero h1{font-size:1.45rem} .fm-metric-value{font-size:2rem} }
</style>
"""

# Symbol shown inside each badge so meaning never depends on colour alone.
_SYMBOL = {"high": "▲", "medium": "●", "low": "▼", "lost": "🔎", "found": "📦",
           "open": "◔", "resolved": "✔", "pending": "⏳"}


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def logo() -> None:
    st.markdown(
        f"""<div class="fm-logo"><div class="fm-logo-mark">🔍</div>
        <div><div class="fm-logo-title">FindMate<span> AI</span></div>
        <div class="fm-logo-sub">{escape(APP_TAGLINE)}</div></div></div>
        <hr/><div class="fm-side-label">MENU</div>""",
        unsafe_allow_html=True)


def sidebar_settings_header() -> None:
    st.markdown('<div class="fm-side-label">MATCH SETTINGS</div>', unsafe_allow_html=True)


def sidebar_footer() -> None:
    st.markdown('<div class="fm-side-card">💡 <b>Tip:</b> similarity is a guide, not proof of identity. '
                'Always verify ownership before returning an item.</div>', unsafe_allow_html=True)


def hero(title: str, subtitle: str, eyebrow: str = "FindMate AI", chips: list[str] | None = None) -> None:
    chip_html = "".join(f'<span class="fm-chip">{escape(c)}</span>' for c in (chips or []))
    chip_html = f'<div class="fm-chips">{chip_html}</div>' if chip_html else ""
    st.markdown(f'<div class="fm-hero"><span class="fm-eyebrow">{escape(eyebrow)}</span>'
                f'<h1>{escape(title)}</h1><p>{escape(subtitle)}</p>{chip_html}</div>',
                unsafe_allow_html=True)


def section(title: str) -> None:
    st.markdown(f'<div class="fm-section"><div class="bar"></div><h3>{escape(title)}</h3></div>',
                unsafe_allow_html=True)


def infobar(html: str, accent: bool = False) -> None:
    """Single-line status bar, 46px tall to line up with inputs and buttons. `html` must be trusted."""
    color = "var(--amber)" if accent else "var(--blue)"
    st.markdown(f'<div class="fm-adminbar" style="border-left-color:{color}"><span>{html}</span></div>',
                unsafe_allow_html=True)


def form_header(icon: str, title: str, sub: str = "") -> None:
    st.markdown(f'<div class="fm-formhead"><div class="ico">{icon}</div><div><b>{escape(title)}</b>'
                f'<span class="s">{escape(sub)}</span></div></div>', unsafe_allow_html=True)


def metric_row(cards: list[tuple]) -> None:
    """cards = (label, value, icon, sub, accent, tint). Rendered as one equal-height grid."""
    inner = "".join(
        f"""<div class="fm-card fm-metric" style="--accent:{accent};--tint:{tint}">
        <div class="fm-metric-top"><span class="fm-metric-label">{escape(label)}</span>
        <span class="fm-metric-icon">{icon}</span></div>
        <div class="fm-metric-value">{value}</div><div class="fm-metric-sub">{escape(sub)}</div></div>"""
        for label, value, icon, sub, accent, tint in cards)
    st.markdown(f'<div class="fm-grid">{inner}</div>', unsafe_allow_html=True)


def steps(items: list[tuple[str, str]]) -> None:
    inner = "".join(f'<div class="fm-card fm-step"><div class="n">{i}</div><b>{escape(t)}</b>'
                    f'<div class="t">{escape(x)}</div></div>' for i, (t, x) in enumerate(items, 1))
    st.markdown(f'<div class="fm-grid">{inner}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str) -> str:
    sym = _SYMBOL.get(kind, "")
    return f'<span class="fm-badge b-{kind}">{sym + " " if sym else ""}{escape(str(text))}</span>'


def empty_state(icon: str, title: str, text: str) -> None:
    st.markdown(f'<div class="fm-empty"><div class="ico">{icon}</div><h4>{escape(title)}</h4>'
                f'<div>{escape(text)}</div></div>', unsafe_allow_html=True)


def disclaimer() -> None:
    st.markdown(
        '<div class="fm-disclaimer">⚠️ <b>Similarity is not proof of identity.</b> Scores show how closely '
        'two descriptions match in meaning. Always verify ownership (unique marks, contents, proof of '
        'purchase) before returning an item.</div>', unsafe_allow_html=True)


def _ring(score: float, level: str) -> str:
    pct = int(round(score * 100))
    return f'<div class="fm-ring {level}" style="--p:{pct}"><span>{pct}%</span></div>'


def item_card(item: dict, similarity: float | None = None) -> None:
    """Render a report as a card (all user text is HTML-escaped)."""
    desc = escape(item.get("description") or "No description provided.")
    right = _ring(similarity, confidence_label(similarity).lower()) if similarity is not None else ""
    html = f"""<div class="fm-item {escape(item['kind'])}">
      <div class="fm-matchhead">
        <div><h4>{escape(item['name'])}</h4>
        {badge(item['kind'].upper(), item['kind'])}{badge(item['status'].upper(), item['status'])}
        {badge(item['category'], 'cat')}</div>{right}</div>
      <p>{desc}</p>
      <div class="fm-meta">📍 {escape(item['location'])} &nbsp;•&nbsp; 📅 {escape(str(item['event_date']))}
      &nbsp;•&nbsp; 👤 {escape(item.get('contact_name') or '-')}</div></div>"""
    img = files.resolve(item.get("image_path"))
    if img:
        c1, c2 = st.columns([1, 4])
        c1.image(str(img))
        c2.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


def match_card(m: dict, show_contacts: bool = False) -> None:
    """One self-contained card: header + score + lost/found side by side (equal height)."""
    label = confidence_label(m["score"])
    lvl = label.lower()
    bar = f'<div class="fm-bar"><div style="width:{max(2, int(m["score"] * 100))}%"></div></div>'
    sides = ""
    for tag, p in (("LOST", "lost"), ("FOUND", "found")):
        contact = ""
        if show_contacts:
            contact = (f"<br/>✉️ {escape(m[p + '_contact'] or '-')} • {escape(m[p + '_email'] or '-')}"
                       f" • 📞 {escape(m.get(p + '_phone') or '-')}")
        sides += f"""<div class="fm-item {p}"><h4>{badge(tag, p)} {escape(m[p + '_name'])}</h4>
            <p>{escape(m[p + '_desc'] or 'No description provided.')}</p>
            <div class="fm-meta">📍 {escape(m[p + '_location'])} • {escape(m[p + '_category'])}{contact}</div></div>"""
    st.markdown(
        f"""<div class="fm-matchbox"><div class="fm-matchhead"><div>
          <div class="fm-matchtitle">{escape(m['lost_name'])} &nbsp;⇄&nbsp; {escape(m['found_name'])}</div>
          {badge(label.upper() + ' CONFIDENCE', lvl)}{badge(m['status'].upper(), m['status'])}</div>
          {_ring(m['score'], lvl)}</div>{bar}
        <div class="fm-metric-sub">Semantic similarity {m['semantic']:.0%} · location/category add a small bounded bonus</div>
        <div class="fm-pair">{sides}</div></div>""", unsafe_allow_html=True)
    imgs = [(files.resolve(m.get(p + "_image")), p) for p in ("lost", "found")]
    if any(i for i, _ in imgs):
        cols = st.columns(2)
        for col, (img, p) in zip(cols, imgs):
            if img:
                col.image(str(img), width=140, caption=p.title())


def safe_run_matching() -> bool:
    """Run the engine, showing a friendly error if the model is unavailable."""
    try:
        run_matching()
        return True
    except ModelLoadError as exc:
        st.error("AI model unavailable - matching skipped.")
        st.code(str(exc))
        return False
