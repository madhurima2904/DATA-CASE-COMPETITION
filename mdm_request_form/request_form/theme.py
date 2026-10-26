"""Power Apps / Microsoft Teams look for the Streamlit prototype (CSS + static chrome).
Purely visual: no Microsoft logos, and a banner marks the page as a mock-up."""

RAIL_ICONS = [
    ("Activity", '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21h4"/>'),
    ("Chat", '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.4A8 8 0 1 1 21 12z"/>'),
    ("Teams", '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.4"/><path d="M3 19c0-3.3 2.7-5 6-5s6 1.7 6 5"/><path d="M15 14.5c3 0 6 1.4 6 4.5"/>'),
    ("Calendar", '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
]

CSS = """
<style>
:root{--brand:#5b5fc7;--brand-dark:#4f52b2;--brand-soft:#e8ebfa;--line:#e0e0e0;--muted:#616161;--ink:#242424}
html,body,[class*="css"],.stApp{font-family:"Segoe UI","Segoe UI Web",-apple-system,BlinkMacSystemFont,Roboto,Arial,sans-serif!important}
.stApp{background:#f5f5f5}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important}
[data-testid="stMainBlockContainer"],.block-container{padding:0 28px 40px 96px!important;max-width:none!important}
/* fixed Teams chrome */
.mock-banner{position:fixed;top:0;left:0;right:0;z-index:1000;background:#fff8e1;color:#5d4200;border-bottom:1px solid #f0d78a;font-size:12px;padding:4px 16px;text-align:center}
.teams-top{position:fixed;top:25px;left:0;right:0;height:46px;z-index:999;background:#ebebeb;border-bottom:1px solid var(--line);display:flex;align-items:center;padding:0 16px}
.teams-top .search{margin:0 auto;width:min(560px,60vw);height:30px;border-radius:6px;background:#fff;border:1px solid var(--line);display:flex;align-items:center;gap:8px;padding:0 10px;color:var(--muted);font-size:13px}
.teams-top .av{width:30px;height:30px;border-radius:50%;background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:12px}
.teams-rail{position:fixed;top:71px;left:0;bottom:0;width:68px;z-index:998;background:#ebebeb;border-right:1px solid var(--line);display:flex;flex-direction:column;align-items:center;padding-top:6px;gap:2px}
.teams-rail div{width:60px;padding:8px 0;border-radius:6px;color:var(--muted);font-size:10px;display:flex;flex-direction:column;align-items:center;gap:3px}
.teams-rail svg{width:20px;height:20px}
.teams-rail .on{color:var(--brand);background:#fff}
.teams-rail .app{width:22px;height:22px;border-radius:5px;background:var(--brand);color:#fff;font-size:8px;font-weight:700;display:flex;align-items:center;justify-content:center}
.app-head{margin:84px 0 0;display:flex;align-items:center;gap:10px}
.app-head .ic{width:28px;height:28px;border-radius:6px;background:var(--brand);color:#fff;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center}
.app-head h1{font-size:18px!important;font-weight:600!important;margin:0!important;padding:0!important}
.app-head .pill{font-size:12px;font-weight:600;background:#f0f0f0;color:var(--muted);border-radius:10px;padding:2px 8px}
/* page titles inside the app */
h1{font-size:20px!important;font-weight:600!important;padding-top:4px!important}
h2,h3{font-size:16px!important;font-weight:600!important}
/* tab bar (horizontal radio) */
.st-key-tabnav div[data-testid="stRadio"] > label{display:none}
.st-key-tabnav div[data-testid="stRadio"] div[role="radiogroup"]{gap:4px;border-bottom:1px solid var(--line);margin-bottom:8px}
.st-key-tabnav div[data-testid="stRadio"] div[role="radiogroup"] > label{padding:8px 12px;margin:0;border-bottom:3px solid transparent;font-weight:600;color:var(--muted)}
.st-key-tabnav div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child{display:none}
.st-key-tabnav div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked){border-bottom-color:var(--brand);color:var(--ink)}
.st-key-tabnav [data-testid="stRadioOption"]{padding:8px 12px!important;margin:0 2px 0 0!important;border-bottom:3px solid transparent;color:var(--muted)}
.st-key-tabnav [data-testid="stRadioOption"] p{font-weight:600}
.st-key-tabnav [data-testid="stRadioOption"] > div > div:first-child{display:none!important}
.st-key-tabnav [data-testid="stRadioOption"][data-selected="true"]{border-bottom-color:var(--brand);color:var(--ink)}
.st-key-tabnav [data-testid="stRadioOption"]:hover{background:#fff}
/* cards */
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:8px!important;border-color:var(--line)!important}
/* Fluent-style inputs */
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{background:#fff!important;border-radius:4px!important;border:1px solid #c7c7c7!important;border-bottom:2px solid #8a8a8a!important}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-bottom-color:var(--brand)!important}
[data-baseweb="input"] input,[data-baseweb="select"] input{background:#fff!important}
label[data-testid="stWidgetLabel"] p{font-weight:600;font-size:13px}
/* buttons */
.stButton>button,[data-testid^="stBaseButton"]{border-radius:4px!important;font-weight:600!important}
[data-testid="stBaseButton-primary"]{background:var(--brand)!important;border-color:var(--brand)!important}
[data-testid="stBaseButton-primary"]:hover{background:var(--brand-dark)!important}
[data-testid="stBaseButton-primary"]:disabled{background:#e0e0e0!important;border-color:#e0e0e0!important;color:#9e9e9e!important}
[data-testid="stProgress"] div[role="progressbar"]>div>div>div{background:var(--brand)!important}
[data-testid="stMetricValue"]{font-size:24px!important}
/* segmented controls look like Fluent pills */
[data-testid="stButtonGroup"] button{border-radius:16px!important;margin-right:6px}
[data-testid="stButtonGroup"] button[kind="segmented_controlActive"],[data-testid="stBaseButton-segmented_controlActive"]{background:var(--brand-soft)!important;border-color:var(--brand)!important;color:var(--brand-dark)!important}
</style>
"""


def chrome_html(initials):
    icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">{}</svg>'
    rail = "".join(f"<div>{icon.format(p)}{n}</div>" for n, p in RAIL_ICONS)
    rail += '<div class="on"><span class="app">MDM</span>MDM</div>'
    return f"""
<div class="mock-banner">Prototype mock-up of a Power Apps form inside Microsoft Teams &middot; synthetic competition data &middot; not connected to Microsoft 365 or SAP B1</div>
<div class="teams-top"><div class="search">Search</div><div class="av">{initials}</div></div>
<nav class="teams-rail" aria-label="App bar">{rail}</nav>
<div class="app-head"><div class="ic">MDM</div><h1>MDM Requests</h1><span class="pill">Power Apps</span></div>
"""
