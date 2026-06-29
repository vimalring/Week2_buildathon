import html as html_lib
import time
import streamlit as st
import streamlit.components.v1 as components
import markdown as md_lib
from query_pipeline import rewrite_farmer_query, retrieve_relevant_context, stream_grounded_answer

# ── Helpers ───────────────────────────────────────────────────────────────────

def render_ai_content(text: str) -> str:
    """Convert LLM markdown output to HTML. Uses markdown library (nl2br + sane_lists)."""
    return md_lib.markdown(text, extensions=["nl2br", "sane_lists"])

def safe_html(text: str) -> str:
    """Escape user-supplied strings to prevent XSS before HTML injection."""
    return html_lib.escape(text)

# ── SVG assets ────────────────────────────────────────────────────────────────

WHEAT_SVG = """
<svg width="56" height="56" viewBox="0 0 24 24" fill="none"
     xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M12 22V11" stroke="#16A34A" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M12 11c0-3.5-3.5-5.5-6.5-3.5 1 3.5 3.5 5.5 6.5 3.5z"
        stroke="#16A34A" stroke-width="1.5" stroke-linejoin="round"
        fill="rgba(22,163,74,0.12)"/>
  <path d="M12 11c0-3.5 3.5-5.5 6.5-3.5-1 3.5-3.5 5.5-6.5 3.5z"
        stroke="#16A34A" stroke-width="1.5" stroke-linejoin="round"
        fill="rgba(22,163,74,0.12)"/>
  <path d="M12 7c0-2.5-2.5-4-5-2.5.8 2.5 2.8 4 5 2.5z"
        stroke="#16A34A" stroke-width="1.5" stroke-linejoin="round"
        fill="rgba(22,163,74,0.12)"/>
  <path d="M12 7c0-2.5 2.5-4 5-2.5-.8 2.5-2.8 4-5 2.5z"
        stroke="#16A34A" stroke-width="1.5" stroke-linejoin="round"
        fill="rgba(22,163,74,0.12)"/>
  <circle cx="12" cy="3.5" r="1.2" fill="#16A34A"/>
</svg>
"""

LOGO_SVG = """
<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="20" fill="rgba(255,255,255,0.10)"/>
  <circle cx="20" cy="20" r="19" stroke="rgba(255,255,255,0.18)" stroke-width="1"/>
  <path d="M20 31V20" stroke="#4ADE80" stroke-width="2" stroke-linecap="round"/>
  <path d="M20 20c0-3.5-3-5.5-6.5-3.5 1 3.5 3.5 5.5 6.5 3.5z"
        fill="rgba(74,222,128,0.20)" stroke="#4ADE80" stroke-width="1.4" stroke-linejoin="round"/>
  <path d="M20 20c0-3.5 3-5.5 6.5-3.5-1 3.5-3.5 5.5-6.5 3.5z"
        fill="rgba(74,222,128,0.20)" stroke="#4ADE80" stroke-width="1.4" stroke-linejoin="round"/>
  <path d="M20 15c0-2.5-2.5-4-5-2.5 1 2.5 2.8 4 5 2.5z"
        fill="rgba(74,222,128,0.20)" stroke="#4ADE80" stroke-width="1.4" stroke-linejoin="round"/>
  <path d="M20 15c0-2.5 2.5-4 5-2.5-1 2.5-2.8 4-5 2.5z"
        fill="rgba(74,222,128,0.20)" stroke="#4ADE80" stroke-width="1.4" stroke-linejoin="round"/>
  <circle cx="20" cy="10" r="1.3" fill="#4ADE80"/>
</svg>
"""

COPY_JS = (
    "var b=this,t=b.closest('.assistant-bubble').querySelector('.bubble-text');"
    "if(navigator.clipboard&&t){"
    "navigator.clipboard.writeText(t.innerText)"
    ".then(function(){b.textContent='Copied!';b.classList.add('copied');"
    "setTimeout(function(){b.textContent='Copy';b.classList.remove('copied');},2000);})"
    ".catch(function(){});}"
)

# ── 1. Page config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TN AgriScheme AI - Farmer Support Portal",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. CSS ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@400;500;700&display=swap');

    /* ── Tokens ─────────────────────────────── */
    :root {
        --color-primary:     #16A34A;
        --color-primary-dk:  #15803D;
        --color-bg:          #F0FDF4;
        --color-surface:     #FFFFFF;
        --color-text:        #14532D;
        --color-muted:       #4A7C59;
        --color-border:      rgba(22, 163, 74, 0.18);
        --color-error:       #DC2626;
        --color-error-bg:    #FEF2F2;
        --color-error-bdr:   rgba(220, 38, 38, 0.22);
        --radius-sm: 10px;
        --radius-md: 16px;
        --radius-lg: 20px;
        --space-xs:  4px;
        --space-sm:  8px;
        --space-md:  16px;
        --space-lg:  24px;
        --space-xl:  32px;
        --space-2xl: 48px;
        --shadow-sm: 0 2px 8px rgba(22, 163, 74, 0.08);
        --shadow-md: 0 4px 20px rgba(22, 163, 74, 0.12);
        /* FIX #16 — value-only, not a declaration */
        --glass-blur:   blur(16px);
        --glass-bg:     rgba(255, 255, 255, 0.72);
        --glass-border: 1px solid rgba(255, 255, 255, 0.5);
    }

    /* ── Base ───────────────────────────────── */
    html, body, .stApp {
        background-color: var(--color-bg) !important;
        font-family: 'Lato', system-ui, sans-serif !important;
        color: var(--color-text) !important;
        font-size: 16px;
        line-height: 1.7;
    }

    /* ══ Sidebar ════════════════════════════════════════════════════════════ */

    [data-testid="stSidebar"] {
        background: linear-gradient(175deg, #0F3D22 0%, #14532D 40%, #166534 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }
    /* Scrollbar */
    [data-testid="stSidebar"]::-webkit-scrollbar { width: 3px; }
    [data-testid="stSidebar"]::-webkit-scrollbar-track { background: transparent; }
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.14); border-radius: 999px;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.28);
    }
    /* Global text colour reset */
    [data-testid="stSidebar"] * { color: #C6F0D8 !important; }

    /* ── Brand block ─────────────────────── */
    .sb-brand {
        display: flex; align-items: center; gap: 12px;
        padding: 6px 0 14px;
    }
    .sb-logo { flex-shrink: 0; }
    .sb-name {
        font-family: 'Playfair Display', serif;
        font-size: 1.1rem; font-weight: 700;
        color: #ECFDF5 !important;
        line-height: 1.2; margin-bottom: 2px;
    }
    .sb-tagline {
        font-size: 0.72rem; font-weight: 500;
        color: rgba(255,255,255,0.45) !important;
        letter-spacing: 0.04em; text-transform: uppercase;
    }

    /* Status pill */
    /* ── System status card ─────────────────── */
    .sys-status-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(74,222,128,0.18);
        border-top: 2px solid rgba(74,222,128,0.55);
        border-radius: 12px;
        padding: 14px 16px 12px;
        margin-bottom: 20px;
    }
    .sys-status-header {
        display: flex; align-items: center; gap: 9px;
        font-weight: 700; font-size: 0.92rem;
        color: #ECFDF5 !important;
        margin-bottom: 12px;
    }
    .status-dot {
        width: 8px; height: 8px; flex-shrink: 0;
        background: #4ADE80; border-radius: 50%;
        box-shadow: 0 0 0 2px rgba(74,222,128,0.30), 0 0 8px rgba(74,222,128,0.65);
        animation: pulse-dot 2.4s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { box-shadow: 0 0 0 2px rgba(74,222,128,0.30), 0 0 8px rgba(74,222,128,0.65); }
        50%       { box-shadow: 0 0 0 4px rgba(74,222,128,0.15), 0 0 14px rgba(74,222,128,0.45); }
    }
    @media (prefers-reduced-motion: reduce) { .status-dot { animation: none; } }
    .sys-status-divider {
        height: 1px; background: rgba(255,255,255,0.07); margin-bottom: 10px;
    }
    .sys-status-rows { display: flex; flex-direction: column; gap: 7px; }
    .sys-status-row {
        display: flex; justify-content: space-between; align-items: center;
    }
    .sys-status-key {
        font-size: 0.72rem; font-weight: 500;
        color: rgba(255,255,255,0.42) !important;
        letter-spacing: 0.03em;
    }
    .sys-status-val {
        font-size: 0.78rem; font-weight: 700;
        color: #A7F3D0 !important;
        letter-spacing: 0.01em;
    }
    .sys-status-val.green { color: #4ADE80 !important; }

    /* ── Section labels ──────────────────── */
    .sb-section-label {
        font-size: 0.65rem; font-weight: 700;
        letter-spacing: 0.12em; text-transform: uppercase;
        color: rgba(255,255,255,0.35) !important;
        padding: 18px 0 8px;
        border-top: 1px solid rgba(255,255,255,0.07);
        margin-top: 2px;
    }
    .sb-section-label:first-of-type { border-top: none; padding-top: 4px; }

    /* ── Stats cards ─────────────────────── */
    .stats-row {
        display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 7px; margin: 8px 0 10px;
    }
    .stat-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px; padding: 10px 6px 9px;
        text-align: center; transition: background 0.15s ease;
    }
    .stat-card:hover { background: rgba(255,255,255,0.10); }
    .stat-number {
        font-family: 'Playfair Display', serif;
        font-size: 1.25rem; font-weight: 700;
        color: #4ADE80 !important;
        line-height: 1; margin-bottom: 4px;
    }
    .stat-label {
        font-size: 0.60rem; font-weight: 700;
        letter-spacing: 0.07em; text-transform: uppercase;
        color: rgba(255,255,255,0.40) !important;
    }
    .sb-source-line {
        font-size: 0.71rem;
        color: rgba(255,255,255,0.35) !important;
        margin-top: 2px; padding-bottom: 2px;
    }

    /* ── Suggestion chip buttons ─────────── */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-left: 2px solid rgba(74,222,128,0.20) !important;
        border-radius: 8px !important;
        color: #C6F0D8 !important;
        font-size: 0.80rem !important; font-weight: 400 !important;
        text-align: left !important;
        padding: 8px 12px 8px 10px !important;
        margin-bottom: 5px !important;
        line-height: 1.4 !important;
        transition: background 0.15s ease, border-color 0.15s ease,
                    border-left-color 0.15s ease !important;
        box-shadow: none !important;
    }
    /* Arrow prefix via pseudo-element */
    [data-testid="stSidebar"] .stButton > button::before {
        content: "›  ";
        font-size: 1.05em; font-weight: 700;
        opacity: 0.45;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(74,222,128,0.08) !important;
        border-color: rgba(255,255,255,0.16) !important;
        border-left-color: rgba(74,222,128,0.60) !important;
        color: #ECFDF5 !important;
        transform: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover::before { opacity: 0.80; }
    [data-testid="stSidebar"] .stButton > button:focus-visible {
        outline: 2px solid rgba(74,222,128,0.55) !important;
        outline-offset: 2px !important;
    }

    /* ── Danger/ghost clear button ───────── */
    .danger-btn .stButton > button {
        background: transparent !important;
        border: 1px solid rgba(220,38,38,0.32) !important;
        border-left: 1px solid rgba(220,38,38,0.32) !important;
        color: #FCA5A5 !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.01em;
    }
    .danger-btn .stButton > button::before { content: none !important; }
    .danger-btn .stButton > button:hover {
        background: rgba(220,38,38,0.10) !important;
        border-color: rgba(220,38,38,0.55) !important;
        border-left-color: rgba(220,38,38,0.55) !important;
    }

    /* ── Confirm delete box ──────────────── */
    .confirm-box {
        background: rgba(220,38,38,0.08);
        border: 1px solid rgba(220,38,38,0.22);
        border-radius: var(--radius-sm);
        padding: var(--space-sm) var(--space-md);
        margin-bottom: var(--space-sm);
        font-size: 0.78rem; color: #FCA5A5 !important;
        line-height: 1.5;
    }

    /* ── Session info ────────────────────── */
    .sb-session-info {
        display: flex; align-items: center; gap: 8px;
        padding: 14px 0 4px;
        font-size: 0.75rem; color: rgba(255,255,255,0.38) !important;
    }
    .sb-session-dot {
        width: 5px; height: 5px; flex-shrink: 0;
        background: rgba(74,222,128,0.55);
        border-radius: 50%; display: inline-block;
    }

    /* ── Clear button footer separator ──── */
    .sb-footer-sep {
        border-top: 1px solid rgba(255,255,255,0.07);
        margin: 16px 0 12px;
    }

    /* ── Header ─────────────────────────────── */
    .portal-header {
        padding: var(--space-xl) 0 var(--space-md);
        border-bottom: 1px solid var(--color-border);
        margin-bottom: var(--space-xl);
    }
    .portal-header.compact {
        padding: var(--space-md) 0 var(--space-sm);
        margin-bottom: var(--space-md);
    }
    .main-title {
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        font-size: clamp(1.6rem, 3vw, 2.4rem);
        line-height: 1.15; margin: 0 0 var(--space-xs);
    }
    .main-title span { color: var(--color-primary); }
    .sub-title { color: var(--color-muted); font-size: 0.975rem; margin: 0; }

    /* FIX #15 — badge row hidden once chat starts */
    .badge-row {
        display: flex; gap: var(--space-sm);
        margin-top: var(--space-md); flex-wrap: wrap;
    }
    .badge-row.hidden { display: none; }
    .badge {
        background: rgba(22,163,74,0.10);
        border: 1px solid rgba(22,163,74,0.20);
        border-radius: 999px; padding: 2px 12px;
        font-size: 0.78rem; color: var(--color-primary); font-weight: 500;
    }

    /* FIX #19 — message counter */
    .msg-counter {
        font-size: 0.75rem; color: var(--color-muted);
        text-align: right;
        padding-bottom: var(--space-sm);
        border-bottom: 1px solid var(--color-border);
        margin-bottom: var(--space-md);
    }

    /* ── Chat rows ──────────────────────────── */
    .chat-row {
        display: flex; margin-bottom: var(--space-md);
        animation: fadeUp 0.22s ease-out both;
    }
    .chat-row.user      { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @media (prefers-reduced-motion: reduce) { .chat-row { animation: none; } }

    /* FIX #9 — max-width capped for readability */
    .chat-bubble {
        max-width: min(78%, 700px);
        padding: var(--space-md) var(--space-lg);
        border-radius: var(--radius-lg);
        font-size: 0.975rem; line-height: 1.65;
        position: relative; word-break: break-word;
    }

    /* User bubble */
    .user-bubble {
        background: linear-gradient(135deg, #16A34A 0%, #15803D 100%);
        color: #FFFFFF;
        border-bottom-right-radius: var(--space-xs);
        box-shadow: var(--shadow-md);
    }
    .user-bubble .bubble-label {
        font-size: 0.72rem; font-weight: 700;
        letter-spacing: 0.06em; text-transform: uppercase;
        color: rgba(255,255,255,0.70); margin-bottom: var(--space-xs);
    }

    /* FIX #10 — Firefox @supports fallback */
    .assistant-bubble {
        background: var(--glass-bg);
        backdrop-filter: var(--glass-blur);
        -webkit-backdrop-filter: var(--glass-blur);
        border: var(--glass-border);
        color: var(--color-text);
        border-bottom-left-radius: var(--space-xs);
        box-shadow: var(--shadow-sm);
    }
    @supports not (backdrop-filter: blur(1px)) {
        .assistant-bubble { background: #F0FDF4; border: 1px solid var(--color-border); }
    }
    .assistant-bubble .bubble-label {
        font-size: 0.72rem; font-weight: 700;
        letter-spacing: 0.06em; text-transform: uppercase;
        color: var(--color-primary); margin-bottom: var(--space-xs);
    }

    /* FIX #8 — error bubble */
    .error-bubble {
        background: var(--color-error-bg) !important;
        border: 1px solid var(--color-error-bdr) !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }
    .error-bubble .bubble-label { color: var(--color-error) !important; }
    .error-bubble .bubble-text  { color: #7F1D1D !important; }

    /* FIX #18 — copy button */
    .copy-btn {
        position: absolute; top: 8px; right: 8px;
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: 6px; padding: 2px 8px;
        font-size: 0.7rem; font-weight: 600;
        color: var(--color-muted); cursor: pointer;
        opacity: 0; transition: opacity 0.15s ease, color 0.15s ease;
        font-family: 'Lato', sans-serif;
    }
    .assistant-bubble:hover .copy-btn,
    .copy-btn:focus-visible { opacity: 1; }
    .copy-btn:hover { color: var(--color-primary); border-color: var(--color-primary); }
    .copy-btn:focus-visible {
        outline: 2px solid var(--color-primary);
        outline-offset: 2px;
    }
    .copy-btn.copied { color: var(--color-primary); opacity: 1; }

    /* Markdown content inside bubbles — FIX #1 */
    .bubble-text p { margin: 0 0 0.45em; }
    .bubble-text p:last-child { margin-bottom: 0; }
    .bubble-text ul, .bubble-text ol { padding-left: 1.25em; margin: 0.4em 0; }
    .bubble-text li { margin-bottom: 0.2em; }
    .bubble-text strong { font-weight: 700; }
    .user-bubble   .bubble-text strong { color: rgba(255,255,255,0.95); }
    .assistant-bubble .bubble-text strong { color: var(--color-text); }

    /* ── Streaming output ──────────────────────────────────────────────── */
    /* Plain-text during live stream; newlines preserved via pre-wrap */
    .bubble-text.stream-live {
        white-space: pre-wrap;
    }
    /* Blinking block cursor shown while tokens arrive */
    .stream-cursor {
        display: inline-block;
        width: 0.55em;
        height: 1.05em;
        background: var(--color-primary);
        border-radius: 2px;
        margin-left: 2px;
        vertical-align: text-bottom;
        opacity: 1;
        animation: blink-cursor 0.75s step-end infinite;
    }
    @keyframes blink-cursor {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0; }
    }
    @media (prefers-reduced-motion: reduce) {
        .stream-cursor { animation: none; opacity: 1; }
    }

    /* FIX #5 — typing indicator */
    /* ── Retrieval process steps ──────────────────────────── */
    .proc-steps {
        display: flex; flex-direction: column; gap: 9px;
        padding: 2px 0; min-width: 200px;
    }
    .proc-step {
        display: flex; align-items: center; gap: 10px;
        font-size: 0.875rem; line-height: 1.3;
        animation: proc-fadein 0.22s ease both;
    }
    @keyframes proc-fadein {
        from { opacity: 0; transform: translateX(-6px); }
        to   { opacity: 1; transform: translateX(0);    }
    }
    /* Completed step */
    .proc-done { color: var(--color-text); }
    .proc-check {
        width: 18px; height: 18px; flex-shrink: 0;
        background: var(--color-primary); border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        color: #fff; font-size: 0.65rem; font-weight: 800;
        box-shadow: 0 2px 6px rgba(22,163,74,0.30);
    }
    /* Active step */
    .proc-active { color: var(--color-primary); font-weight: 600; }
    .proc-spinner {
        width: 18px; height: 18px; flex-shrink: 0;
        border: 2.5px solid rgba(22,163,74,0.20);
        border-top-color: var(--color-primary);
        border-radius: 50%;
        animation: spin-step 0.75s linear infinite;
    }
    @keyframes spin-step { to { transform: rotate(360deg); } }
    @media (prefers-reduced-motion: reduce) {
        .proc-spinner { animation: none; border-top-color: var(--color-primary); }
        .proc-step    { animation: none; }
    }

    /* FIX #11 — expander visually connected to assistant bubble */
    [data-testid="stExpander"] {
        background: rgba(240,253,244,0.75) !important;
        border: 1px solid var(--color-border) !important;
        border-top: none !important;
        border-left: 3px solid var(--color-primary) !important;
        border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
        margin-top: -10px !important;
        max-width: min(78%, 700px);
    }
    [data-testid="stExpander"] summary {
        font-size: 0.82rem !important;
        color: var(--color-muted) !important;
        font-weight: 600 !important;
    }
    .chunk-card {
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-sm);
        padding: var(--space-md); margin-bottom: var(--space-sm);
    }
    .chunk-label { font-size: 0.78rem; font-weight: 700; color: var(--color-primary); margin-bottom: var(--space-xs); }
    .chunk-text  { font-size: 0.84rem; color: var(--color-muted); line-height: 1.6; }

    /* ══ Chat input area ════════════════════════════════════════════════════ */

    /* 1 — Fixed bar: frosted-glass elevation, upward shadow */
    [data-testid="stChatInputContainer"] {
        background: rgba(255, 255, 255, 0.90) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-top: 1px solid rgba(22, 163, 74, 0.12) !important;
        box-shadow: 0 -2px 16px rgba(22, 163, 74, 0.07),
                    0 -8px 32px rgba(0, 0, 0, 0.04) !important;
        padding: 14px 20px 10px !important;
    }
    /* Keyboard hint injected via pseudo-element — always visible in the bar */
    [data-testid="stChatInputContainer"]::after {
        content: "Enter to send  ·  Shift+Enter for new line";
        display: block;
        font-size: 0.68rem;
        font-family: 'Lato', sans-serif;
        color: #4A7C59;
        text-align: right;
        padding-top: 5px;
        opacity: 0.60;
        letter-spacing: 0.015em;
    }
    /* Kill red outline Streamlit fires on container focus-within */
    [data-testid="stChatInputContainer"]:focus-within {
        outline: none !important;
        box-shadow: 0 -2px 16px rgba(22, 163, 74, 0.07),
                    0 -8px 32px rgba(0, 0, 0, 0.04) !important;
    }

    /* 2 — Strip Streamlit/BaseWeb borders from inner wrappers */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] [data-baseweb="textarea"] {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* ── isStacked override ────────────────────────────────────────────
       Streamlit's ChatInput has an "isStacked" mode (triggered by narrow
       widths) that sets flex-wrap:wrap on the row container (e1vtqrcf3)
       and flex:none;width:100% on the textarea wrapper (e1vtqrcf4),
       causing the submit button to drop to a second line.

       We identify these internal divs precisely using the stable testids
       stChatInputTextArea (inside e1vtqrcf4) and stChatInputSubmitButton.

       e1vtqrcf3 selector: div whose direct grandchild is stChatInputTextArea
       e1vtqrcf4 selector: div whose direct child is stChatInputTextArea    */

    /* e1vtqrcf3 — the row container: force nowrap row regardless of isStacked */
    [data-testid="stChatInput"] div:has(> div > [data-testid="stChatInputTextArea"]),
    [data-testid="stChatInput"] div:has(> [data-testid="stChatInputTextArea"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 8px !important;
        width: 100% !important;
    }

    /* e1vtqrcf4 — textarea wrapper: override flex:none and width:100% */
    [data-testid="stChatInputTextArea"],
    [data-testid="stChatInput"] div:has(> [data-baseweb="textarea"]) {
        flex: 1 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
        order: 0 !important;
    }

    /* [data-baseweb="textarea"] inner wrapper: also flex-grow */
    [data-testid="stChatInput"] [data-baseweb="textarea"] {
        flex: 1 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }

    /* 3 — Textarea */
    [data-testid="stChatInput"] textarea {
        width: 100% !important;
        background: #FFFFFF !important;
        border: 1.5px solid rgba(22, 163, 74, 0.18) !important;
        border-radius: 14px !important;
        color: var(--color-text) !important;
        caret-color: var(--color-primary) !important;
        font-family: 'Lato', sans-serif !important;
        font-size: 1rem !important;
        line-height: 1.55 !important;
        padding: 13px 18px !important;
        min-height: 52px !important;
        resize: none !important;
        box-shadow: 0 1px 4px rgba(22, 163, 74, 0.06),
                    inset 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        transition: border-color 0.22s ease,
                    box-shadow 0.22s ease,
                    background 0.22s ease !important;
    }
    /* 4 — Placeholder */
    [data-testid="stChatInput"] textarea::placeholder {
        color: #5A8A6A !important;
        opacity: 1 !important;
        font-style: italic;
    }
    /* 5 — Focus: blue glow */
    [data-testid="stChatInput"] textarea:focus {
        border-color: #3B82F6 !important;
        background: #FAFEFF !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.16),
                    0 2px 10px rgba(59, 130, 246, 0.10) !important;
        outline: none !important;
    }

    /* 6 — Send button: fixed-size, never wraps */
    [data-testid="stChatInputSubmitButton"] {
        flex: 0 0 auto !important;
        align-self: center !important;
        position: static !important;
        order: 1 !important;
    }
    [data-testid="stChatInputSubmitButton"] button {
        background: linear-gradient(135deg, #16A34A 0%, #15803D 100%) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 44px !important;
        height: 44px !important;
        min-width: 44px !important;
        padding: 0 !important;
        color: #fff !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 10px rgba(22, 163, 74, 0.38) !important;
        transition: transform 0.15s cubic-bezier(0.34,1.56,0.64,1),
                    box-shadow 0.15s ease,
                    background 0.15s ease !important;
        cursor: pointer !important;
    }
    [data-testid="stChatInputSubmitButton"] button:hover {
        background: linear-gradient(135deg, #15803D 0%, #14532D 100%) !important;
        transform: scale(1.08) !important;
        box-shadow: 0 4px 18px rgba(22, 163, 74, 0.48) !important;
    }
    [data-testid="stChatInputSubmitButton"] button:active {
        transform: scale(0.92) !important;
        box-shadow: 0 1px 5px rgba(22, 163, 74, 0.28) !important;
        transition-duration: 0.08s !important;
    }
    [data-testid="stChatInputSubmitButton"] button:focus-visible {
        outline: 2px solid #3B82F6 !important;
        outline-offset: 3px !important;
        transform: none !important;
    }

    /* Input hint — visible on empty state, hidden once chat starts */
    .input-hint {
        text-align: center;
        font-size: 0.78rem;
        color: var(--color-muted);
        letter-spacing: 0.03em;
        margin-bottom: 6px;
        animation: hint-fade 0.6s ease both;
    }
    @keyframes hint-fade {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0);   }
    }
    /* Chat input bar — pulse glow on empty state to draw attention */
    .has-no-messages [data-testid="stChatInputContainer"] {
        box-shadow: 0 -2px 16px rgba(22,163,74,0.10),
                    0 0 0 2px rgba(22,163,74,0.12) !important;
        animation: input-pulse 2.8s ease-in-out infinite;
    }
    @keyframes input-pulse {
        0%, 100% { box-shadow: 0 -2px 16px rgba(22,163,74,0.10), 0 0 0 2px rgba(22,163,74,0.10); }
        50%       { box-shadow: 0 -2px 24px rgba(22,163,74,0.18), 0 0 0 3px rgba(22,163,74,0.20); }
    }
    @media (prefers-reduced-motion: reduce) {
        .has-no-messages [data-testid="stChatInputContainer"] { animation: none; }
    }

    /* ── Main buttons (outside sidebar) ─────── */
    .stButton > button {
        background: var(--color-primary) !important;
        color: #FFFFFF !important; border: none !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Lato', sans-serif !important;
        font-weight: 700 !important; font-size: 0.875rem !important;
        padding: 10px 22px !important;
        transition: background 0.2s ease, transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton > button:hover {
        background: var(--color-primary-dk) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(22,163,74,0.3) !important;
    }
    .stButton > button:focus-visible {
        outline: 2px solid var(--color-primary) !important; outline-offset: 3px !important;
    }

    /* ── Hero section (empty state) ─────────────────────── */
    .hero-wrap {
        max-width: 640px;
        margin: 32px auto 0;
        padding: 0 16px;
    }
    /* ── Header card ── */
    .hero-card {
        background: #FFFFFF;
        border: 1px solid rgba(22,163,74,0.14);
        border-radius: 20px;
        padding: 36px 36px 32px;
        box-shadow: 0 4px 24px rgba(22,163,74,0.07);
        text-align: center;
        margin-bottom: 0;
    }
    .hero-icon-row {
        display: flex; align-items: center; justify-content: center;
        gap: 14px; margin-bottom: 16px;
    }
    .hero-icon-row svg { width: 52px; height: 52px; flex-shrink: 0; }
    .hero-icon-label {
        font-family: 'Playfair Display', serif;
        font-size: clamp(1.55rem, 3vw, 2.1rem);
        font-weight: 700; color: var(--color-text); line-height: 1.2;
        text-align: left;
    }
    .hero-tagline {
        font-size: 0.93rem; color: var(--color-muted);
        margin: 0 0 24px; line-height: 1.6;
    }
    /* ── Trust checkmarks ── */
    .hero-checks {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px 20px;
        text-align: left;
        margin-bottom: 28px;
    }
    .hero-check {
        display: flex; align-items: center; gap: 9px;
        font-size: 0.88rem; font-weight: 600; color: var(--color-text);
    }
    .hero-check-dot {
        width: 18px; height: 18px; flex-shrink: 0;
        background: var(--color-primary); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-size: 0.7rem; font-weight: 800;
        box-shadow: 0 2px 6px rgba(22,163,74,0.30);
    }
    /* ── Divider + Popular Questions label ── */
    .hero-divider {
        display: flex; align-items: center; gap: 12px;
        margin: 0 -36px;                    /* bleed to card edges */
        padding: 0 36px 0;
    }
    .hero-divider-line {
        flex: 1; height: 1px;
        background: rgba(22,163,74,0.15);
    }
    .hero-divider-label {
        font-size: 0.68rem; font-weight: 700;
        letter-spacing: 0.13em; text-transform: uppercase;
        color: var(--color-muted); white-space: nowrap;
    }

    /* ── Popular Questions chips (st.button type=secondary) ── */
    /* Higher specificity (0,1,1+attr) beats .stButton>button (0,1,1) */
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background: #F6FEF9 !important;
        color: var(--color-text) !important;
        border: 1.5px solid rgba(22,163,74,0.22) !important;
        border-radius: 10px !important;
        font-family: 'Lato', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        padding: 11px 16px 11px 14px !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        box-shadow: 0 1px 3px rgba(22,163,74,0.06) !important;
        transition: all 0.18s ease !important;
    }
    /* Green dot prefix via pseudo-element */
    .stButton > button[data-testid="stBaseButton-secondary"]::before {
        content: '' !important;
        display: inline-block !important;
        width: 9px !important; height: 9px !important;
        background: var(--color-primary) !important;
        border-radius: 50% !important;
        flex-shrink: 0 !important;
        box-shadow: 0 0 0 2px rgba(22,163,74,0.20) !important;
    }
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(22,163,74,0.08) !important;
        border-color: var(--color-primary) !important;
        color: var(--color-primary) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(22,163,74,0.15) !important;
    }
    .stButton > button[data-testid="stBaseButton-secondary"]:hover::before {
        background: var(--color-primary-dk) !important;
        box-shadow: 0 0 0 3px rgba(22,163,74,0.25) !important;
    }
    /* Restore sidebar secondary buttons */
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        border-color: rgba(74,222,128,0.28) !important;
        color: #C6F0D8 !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* ── Spinner hidden — typing indicator is the signal ── */
    [data-testid="stSpinner"] > div { display: none !important; }

    /* ── Scrollbar ──────────────────────────── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: var(--color-bg); }
    ::-webkit-scrollbar-thumb { background: rgba(22,163,74,0.25); border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--color-primary); }

    hr { border-color: var(--color-border) !important; }
</style>
""", unsafe_allow_html=True)

# ── 3. Session state ──────────────────────────────────────────────────────────

if "chat_history"   not in st.session_state: st.session_state.chat_history   = []
if "confirm_clear"  not in st.session_state: st.session_state.confirm_clear  = False
if "preset_query"   not in st.session_state: st.session_state.preset_query   = None
if "should_scroll"  not in st.session_state: st.session_state.should_scroll  = False

# Handle category card clicks routed via URL query param from components.html JS
if "chip" in st.query_params:
    _chip = st.query_params.get("chip", "")
    st.query_params.clear()
    if _chip:
        st.session_state.preset_query = _chip
        st.rerun()

# ── 4. Sidebar ────────────────────────────────────────────────────────────────

SUGGESTIONS = [
    "Where to go for polythene mulch demo?",
    "Is there a subsidy for seed maize?",
    "Support for oilseeds in Trichy?",
    "Can I get funding for a pesticide drone?",
]

with st.sidebar:

    # ── Brand ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sb-brand">
        <div class="sb-logo">{LOGO_SVG}</div>
        <div>
            <div class="sb-name">TN AgriScheme AI</div>
            <div class="sb-tagline">Farmer Support Portal</div>
        </div>
    </div>
    <div class="sys-status-card">
        <div class="sys-status-header">
            <span class="status-dot"></span> AI Ready
        </div>
        <div class="sys-status-divider"></div>
        <div class="sys-status-rows">
            <div class="sys-status-row">
                <span class="sys-status-key">Model</span>
                <span class="sys-status-val">GPT-4o-mini</span>
            </div>
            <div class="sys-status-row">
                <span class="sys-status-key">Schemes</span>
                <span class="sys-status-val green">54 Loaded</span>
            </div>
            <div class="sys-status-row">
                <span class="sys-status-key">Updated</span>
                <span class="sys-status-val">Today</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Knowledge base ─────────────────────────────────────────────────────
    st.markdown('<div class="sb-section-label">Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-number">54</div>
            <div class="stat-label">Schemes</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">155</div>
            <div class="stat-label">Chunks</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">2</div>
            <div class="stat-label">Depts</div>
        </div>
    </div>
    <div class="sb-source-line">Tamil Nadu Govt. Agriculture Portal</div>
    """, unsafe_allow_html=True)

    # ── Quick queries ──────────────────────────────────────────────────────
    st.markdown('<div class="sb-section-label">Quick Queries</div>', unsafe_allow_html=True)
    for s in SUGGESTIONS:
        if st.button(s, key=f"chip_{s[:28]}", use_container_width=True):
            st.session_state.preset_query = s
            st.rerun()

    # ── Session info ───────────────────────────────────────────────────────
    n_turns = len([m for m in st.session_state.chat_history if m["role"] == "user"])
    if n_turns:
        st.markdown(f"""
        <div class="sb-session-info">
            <span class="sb-session-dot"></span>
            {n_turns} question{"s" if n_turns != 1 else ""} this session
        </div>
        """, unsafe_allow_html=True)

    # ── Clear conversation ─────────────────────────────────────────────────
    st.markdown('<div class="sb-footer-sep"></div>', unsafe_allow_html=True)

    if not st.session_state.confirm_clear:
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button("Clear Conversation", use_container_width=True, key="clear_btn"):
            st.session_state.confirm_clear = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="confirm-box">'
            'This will permanently delete all messages. Are you sure?'
            '</div>',
            unsafe_allow_html=True,
        )
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, clear", use_container_width=True, key="confirm_yes"):
                st.session_state.chat_history  = []
                st.session_state.confirm_clear = False
                st.rerun()
        with col_no:
            if st.button("Cancel", use_container_width=True, key="confirm_no"):
                st.session_state.confirm_clear = False
                st.rerun()

# ── 5. Header ─────────────────────────────────────────────────────────────────

has_messages = bool(st.session_state.chat_history)

st.markdown(f"""
<div class="portal-header {'compact' if has_messages else ''}">
    <div class="main-title">Tamil Nadu <span>Agricultural Schemes</span></div>
    <p class="sub-title">AI-powered guidance grounded in verified government policy records</p>
    <div class="badge-row {'hidden' if has_messages else ''}">
        <span class="badge">Zero Hallucination</span>
        <span class="badge">54 Schemes Indexed</span>
        <span class="badge">Source-Cited Answers</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 6. Chat history ───────────────────────────────────────────────────────────

def render_assistant_bubble(content: str, is_error: bool) -> str:
    bubble_cls = "assistant-bubble error-bubble" if is_error else "assistant-bubble"
    label      = "Error" if is_error else "AI Assistant"
    rendered   = safe_html(content) if is_error else render_ai_content(content)
    return (
        f'<div class="chat-row assistant" role="listitem">'
        f'<div class="chat-bubble {bubble_cls}" aria-label="AI response">'
        f'<div class="bubble-label">{label}</div>'
        f'<div class="bubble-text">{rendered}</div>'
        f'<button class="copy-btn" onclick="{COPY_JS}" '
        f'aria-label="Copy response to clipboard" title="Copy">Copy</button>'
        f'</div></div>'
    )

HERO_CHIPS = [
    "Seed Subsidy schemes",
    "Crop Insurance",
    "PM-KISAN",
    "Solar Pump subsidy",
    "Organic Farming support",
    "Micro Irrigation scheme",
]

CATEGORIES = [
    ("🌾", "Crop Schemes",    "What crop schemes are available in Tamil Nadu?"),
    ("💰", "Subsidies",       "What subsidies are available for farmers in Tamil Nadu?"),
    ("🚜", "Farm Machinery",  "What farm machinery subsidies are available?"),
    ("🌱", "Organic Farming", "What support is available for organic farming in Tamil Nadu?"),
    ("🐄", "Livestock",       "What livestock or animal husbandry schemes are available?"),
    ("💧", "Irrigation",      "What irrigation schemes and subsidies are available?"),
]

if not st.session_state.chat_history:
   
    components.html(f"""
    <style>
     
    </style>
   
    <script>
      function selectCat(q){{
        var u=new URL(window.parent.location.href);
        u.searchParams.set('chip',q);
        window.parent.location.href=u.toString();
      }}
    </script>
    """, height=232)

    # ── Popular Questions chips ───────────────────────────────────────────────
    st.markdown(
        '<div class="hero-wrap" style="margin-top:0">'
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">'
        '<div style="flex:1;height:1px;background:rgba(22,163,74,.18)"></div>'
        '<span style="font-size:.68rem;font-weight:700;letter-spacing:.12em;'
        'text-transform:uppercase;color:#4A7C59;white-space:nowrap">Popular Questions</span>'
        '<div style="flex:1;height:1px;background:rgba(22,163,74,.18)"></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2, gap="small")
    chip_cols = [col_a, col_b]
    for i, chip_label in enumerate(HERO_CHIPS):
        if chip_cols[i % 2].button(chip_label, key=f"hero_chip_{i}",
                                   use_container_width=True, type="secondary"):
            st.session_state.preset_query = chip_label
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # FIX #19 — message counter
    total = len(st.session_state.chat_history)
    st.markdown(
        f'<div class="msg-counter">{total} message{"s" if total != 1 else ""}'
        f' &middot; Scroll up to review earlier answers</div>',
        unsafe_allow_html=True,
    )

    for message in st.session_state.chat_history:
        if message["role"] == "user":
            # FIX #2 — html.escape on user content
            st.markdown(
                f'<div class="chat-row user" role="listitem">'
                f'<div class="chat-bubble user-bubble" aria-label="Farmer question">'
                f'<div class="bubble-label">Farmer</div>'
                f'<div class="bubble-text">{safe_html(message["content"])}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        else:
            content  = message["content"]
            is_error = content.startswith("[!")
            # FIX #1 — markdown conversion; FIX #8 — error detection
            st.markdown(render_assistant_bubble(content, is_error), unsafe_allow_html=True)

            # FIX #11 + #12 + #13 — expander: connected, renamed, conditional ellipsis
            if not is_error and message.get("context_info"):
                with st.expander("Where did this answer come from?"):
                    for idx, chunk in enumerate(message["context_info"], 1):
                        scheme  = safe_html(chunk.metadata.get("scheme_name", "Unknown Scheme"))
                        text    = chunk.page_content
                        preview = safe_html(text[:280] + ("…" if len(text) > 280 else ""))
                        st.markdown(
                            f'<div class="chunk-card">'
                            f'<div class="chunk-label">Source {idx} — {scheme}</div>'
                            f'<div class="chunk-text">{preview}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

# FIX #4 — auto-scroll: fires after rerun, placed here so DOM is populated
if st.session_state.should_scroll:
    st.session_state.should_scroll = False
    components.html("""
    <script>
        (function() {
            function doScroll() {
                var c = window.parent.document.querySelector('[data-testid="stAppViewContainer"]')
                     || window.parent.document.querySelector('.main')
                     || window.parent.document.body;
                if (c) c.scrollTop = c.scrollHeight;
            }
            doScroll();
            setTimeout(doScroll, 150);
            setTimeout(doScroll, 350);
        })();
    </script>
    """, height=0)

# ── 7. Input ──────────────────────────────────────────────────────────────────

has_messages = bool(st.session_state.chat_history)

# Pulse-glow the input bar on empty state; add keyboard hint otherwise
if not has_messages:
    # Inject body class so CSS can target the chat input container
    components.html("""
    <script>
        window.parent.document.body.classList.add('has-no-messages');
    </script>
    """, height=0)
    st.markdown(
        '<div class="input-hint">Type your question below or pick one above &darr;</div>',
        unsafe_allow_html=True,
    )
else:
    components.html("""
    <script>
        window.parent.document.body.classList.remove('has-no-messages');
    </script>
    """, height=0)
    st.markdown(
        '<div class="input-hint">Press Enter to send &middot; Shift+Enter for a new line</div>',
        unsafe_allow_html=True,
    )

user_query = st.chat_input("Ask about subsidies, seeds, machinery, crop insurance, training…")

# FIX #7 — resolve preset query from sidebar chips
if st.session_state.preset_query:
    user_query = st.session_state.preset_query
    st.session_state.preset_query = None

# ── 8. Processing ─────────────────────────────────────────────────────────────

if user_query:
    # Show user bubble immediately
    st.markdown(
        f'<div class="chat-row user">'
        f'<div class="chat-bubble user-bubble">'
        f'<div class="bubble-label">Farmer</div>'
        f'<div class="bubble-text">{safe_html(user_query)}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    # Phase 1 — rewrite + retrieve with live step-by-step progress
    def _proc_html(steps: list) -> str:
        rows = ""
        for status, text in steps:
            if status == "done":
                rows += (
                    f'<div class="proc-step proc-done">'
                    f'<span class="proc-check">&#10003;</span>{text}</div>'
                )
            else:
                rows += (
                    f'<div class="proc-step proc-active">'
                    f'<span class="proc-spinner"></span>{text}</div>'
                )
        return (
            '<div class="chat-row assistant">'
            '<div class="chat-bubble assistant-bubble">'
            '<div class="bubble-label">AI Assistant</div>'
            f'<div class="proc-steps">{rows}</div>'
            '</div></div>'
        )

    proc_slot = st.empty()

    proc_slot.markdown(
        _proc_html([("active", "Searching knowledge base…")]),
        unsafe_allow_html=True,
    )
    optimized = rewrite_farmer_query(user_query)

    proc_slot.markdown(
        _proc_html([
            ("done",   "Query Optimized"),
            ("active", "Running vector search…"),
        ]),
        unsafe_allow_html=True,
    )
    chunks = retrieve_relevant_context(optimized, top_k=3)
    n_docs = len(chunks)

    proc_slot.markdown(
        _proc_html([
            ("done",   "Query Optimized"),
            ("done",   f"Retrieved {n_docs} Document{'s' if n_docs != 1 else ''}"),
            ("active", "Generating answer…"),
        ]),
        unsafe_allow_html=True,
    )
    proc_slot.empty()

    # Phase 2 — stream the GPT answer token-by-token into the bubble
    stream_slot = st.empty()
    full_text   = ""
    last_render = 0.0

    def _stream_bubble(text: str, cursor: bool = True) -> str:
        cur = '<span class="stream-cursor">&#x2587;</span>' if cursor else ""
        return (
            '<div class="chat-row assistant">'
            '<div class="chat-bubble assistant-bubble">'
            '<div class="bubble-label">AI Assistant</div>'
            f'<div class="bubble-text stream-live">{safe_html(text)}{cur}</div>'
            '</div></div>'
        )

    stream_slot.markdown(_stream_bubble(""), unsafe_allow_html=True)

    for delta in stream_grounded_answer(user_query, chunks):
        full_text += delta
        now = time.monotonic()
        if now - last_render >= 0.05:          # refresh UI at most every 50 ms
            stream_slot.markdown(_stream_bubble(full_text), unsafe_allow_html=True)
            last_render = now

    # Final render — remove cursor
    stream_slot.markdown(_stream_bubble(full_text, cursor=False), unsafe_allow_html=True)

    is_error = full_text.startswith("[!")
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": full_text,
        "context_info": chunks,
    })
    st.session_state.should_scroll = True
    st.rerun()
