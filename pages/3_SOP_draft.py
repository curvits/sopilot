import re
import json as _json
import base64
from datetime import date
import streamlit as st
import streamlit.components.v1 as components
from utils.session_manager import load_session, save_session, create_session, migrate_session
from utils.claude_client import generate_process_diagram, generate_automation_suggestions
from utils.pdf_generator import generate_pdf

# ── Sessiooni initsialiseerimine ──────────────────────────────────────────────
if "session_id" not in st.session_state or not st.session_state["session_id"]:
    session_id, session = create_session()
    st.session_state["session_id"] = session_id
else:
    session = load_session(st.session_state["session_id"])
    if not session:
        session_id, session = create_session()
        st.session_state["session_id"] = session_id

session_id = st.session_state["session_id"]
session = migrate_session(session)
company = session.get("company", {})

# ── Vali SOP ──────────────────────────────────────────────────────────────────
finished = [(i, s) for i, s in enumerate(session["sops"]) if s.get("sop_draft")]

if not finished:
    st.title("SOP tulemused")
    st.info("SOP draft puudub. Esmalt genereeri SOP vestlusbotiga.")
    if st.button("Mine vestlusesse", type="primary"):
        st.switch_page("pages/2_SOP_vestlus.py")
    st.stop()

if len(finished) > 1:
    options = [f"SOP {j+1}: {s.get('sop_title', 'Nimetu')}" for j, (i, s) in enumerate(finished)]
    sel = st.selectbox("Vali SOP", range(len(finished)), format_func=lambda j: options[j])
    actual_idx, current_sop = finished[sel]
else:
    actual_idx, current_sop = finished[0]

sop_draft = current_sop.get("sop_draft", "")
automation = current_sop.get("automation_suggestions", "")
diagram_raw = current_sop.get("process_diagram", "")
sop_title = current_sop.get("sop_title", "SOP_dokument")
company_name = company.get("name", "")

st.title(f"SOP — {current_sop.get('sop_title', 'Draft')}")

# ── SVG abifunktsioonid ───────────────────────────────────────────────────────
def _esc(t):
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def _wrap(text, max_ch=30):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_ch:
            cur += " " + w
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines[:2]

def _build_svg(steps):
    BOX_W, BOT_H, ARROW_H, SVG_W, R = 240, 30, 38, 440, 7
    LINE_H, PAD_V = 17, 12
    X = (SVG_W - BOX_W) // 2
    parsed = []
    for s in steps:
        lines = _wrap(s.get("samm", ""))
        top_h = PAD_V * 2 + len(lines) * LINE_H
        parsed.append({"lines": lines, "roll": _esc(s.get("roll", "")), "top_h": top_h})
    total_h = sum(d["top_h"] + BOT_H for d in parsed) + (len(parsed) - 1) * ARROW_H + 24
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{total_h}" '
         f'style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">']
    y = 12
    for i, d in enumerate(parsed):
        th, nh, cx = d["top_h"], d["top_h"] + BOT_H, X + BOX_W // 2
        p.append(f'<path d="M{X+R},{y} H{X+BOX_W-R} Q{X+BOX_W},{y} {X+BOX_W},{y+R} '
                 f'V{y+th} H{X} V{y+R} Q{X},{y} {X+R},{y}Z" fill="#1e3a5f"/>')
        p.append(f'<path d="M{X},{y+th} H{X+BOX_W} V{y+nh-R} '
                 f'Q{X+BOX_W},{y+nh} {X+BOX_W-R},{y+nh} '
                 f'H{X+R} Q{X},{y+nh} {X},{y+nh-R} V{y+th}Z" fill="#4a7ebb"/>')
        n_lines = len(d["lines"])
        ty = y + (th - n_lines * LINE_H) // 2 + LINE_H - 1
        for j, line in enumerate(d["lines"]):
            p.append(f'<text x="{cx}" y="{ty + j*LINE_H}" text-anchor="middle" '
                     f'fill="white" font-size="13" font-weight="600">{_esc(line)}</text>')
        p.append(f'<text x="{cx}" y="{y+th+BOT_H//2+5}" text-anchor="middle" '
                 f'fill="white" font-size="11">{d["roll"]}</text>')
        if i < len(parsed) - 1:
            ay1, ay2 = y + nh, y + nh + ARROW_H
            p.append(f'<line x1="{cx}" y1="{ay1}" x2="{cx}" y2="{ay2-8}" '
                     f'stroke="#adb5bd" stroke-width="2"/>')
            p.append(f'<polygon points="{cx},{ay2} {cx-6},{ay2-9} {cx+6},{ay2-9}" fill="#adb5bd"/>')
        y += nh + ARROW_H
    p.append('</svg>')
    return '\n'.join(p), total_h

# ── Neli vahekaarti ülaosas ───────────────────────────────────────────────────
tab_preview, tab_edit, tab_ai, tab_diagram = st.tabs([
    "SOP eelvaade", "Redigeeri", "AI ettepanekud", "Protsessijoonis"
])

# ── 1. SOP eelvaade ───────────────────────────────────────────────────────────
with tab_preview:
    meta_keys = ["Versioon", "Kuupäev", "Ettevõte", "Vastutav roll"]
    meta = {}
    for key in meta_keys:
        m = re.search(rf'\*\*{key}:\*\*\s*(.+)', sop_draft)
        if m:
            meta[key] = m.group(1).strip()

    sop_title_text = current_sop.get("sop_title", "")
    title_row = (
        f'<tr><td style="color:#6c757d;padding:5px 16px 8px 0;white-space:nowrap;font-size:0.85rem;vertical-align:top">Pealkiri</td>'
        f'<td style="padding:5px 0 8px 0;font-size:1.1rem;font-weight:700;color:#1e3a5f">{sop_title_text or "—"}</td></tr>'
    ) if sop_title_text else ""
    meta_rows = "".join(
        f'<tr><td style="color:#6c757d;padding:4px 16px 4px 0;white-space:nowrap;font-size:0.85rem;vertical-align:top">{k}</td>'
        f'<td style="padding:4px 0;font-weight:600;font-size:0.85rem">{v}</td></tr>'
        for k, v in meta.items()
    )
    if title_row or meta_rows:
        st.markdown(
            f'<div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:6px;'
            f'padding:0.9rem 1.25rem;margin-bottom:1.5rem;max-width:800px">'
            f'<table style="border-collapse:collapse;width:100%">{title_row}{meta_rows}</table></div>',
            unsafe_allow_html=True,
        )
    meta_pattern = re.compile(r'^\*\*(?:Versioon|Kuupäev|Ettevõte|Vastutav roll):\*\*.*$', re.MULTILINE)
    sop_body = meta_pattern.sub("", sop_draft).strip()
    sop_body = re.sub(r'\n{3,}', '\n\n', sop_body)
    st.markdown(sop_body)

# ── 2. Redigeeri ─────────────────────────────────────────────────────────────
with tab_edit:
    st.markdown("Muuda SOP dokumenti allpool. Muudatused salvestatakse sessiooni.")
    edited = st.text_area(
        "SOP sisu (Markdown formaadis)",
        value=sop_draft,
        height=600,
        label_visibility="collapsed",
    )
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Salvesta muudatused", type="primary", use_container_width=True):
            session["sops"][actual_idx]["sop_draft"] = edited
            for line in edited.splitlines():
                if line.startswith("# "):
                    session["sops"][actual_idx]["sop_title"] = line[2:].strip()
                    break
            save_session(session_id, session)
            st.success("Salvestatud!")
            st.rerun()
    with col2:
        if st.button("Lähtesta", use_container_width=True, help="Taasta viimati salvestatud versioon"):
            st.rerun()

# ── 3. AI ettepanekud ─────────────────────────────────────────────────────────
with tab_ai:
    if automation:
        st.markdown('<div style="border:2px solid #28a745;border-radius:8px;padding:1.25rem 1.5rem;background:#f6fff8">', unsafe_allow_html=True)
        st.markdown(automation)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Uuenda analüüs", help="Genereerib automatiseerimisvõimalused uuesti"):
            with st.spinner("Analüüsin..."):
                new_automation = generate_automation_suggestions(sop_draft, company)
            session["sops"][actual_idx]["automation_suggestions"] = new_automation
            save_session(session_id, session)
            st.rerun()
    else:
        st.info("AI ettepanekud puuduvad.")
        if st.button("Genereeri AI ettepanekud", type="primary"):
            with st.spinner("Analüüsin..."):
                new_automation = generate_automation_suggestions(sop_draft, company)
            session["sops"][actual_idx]["automation_suggestions"] = new_automation
            save_session(session_id, session)
            st.rerun()

# ── 4. Protsessijoonis ────────────────────────────────────────────────────────
with tab_diagram:
    if diagram_raw:
        try:
            m = re.search(r'\[.*\]', diagram_raw, re.DOTALL)
            steps = _json.loads(m.group(0)) if m else []
        except Exception:
            steps = []
        if steps:
            svg_str, svg_h = _build_svg(steps)
            components.html(
                f'<div style="background:#fff;border:1px solid #dee2e6;border-radius:6px;'
                f'padding:1.5rem;text-align:center">{svg_str}</div>',
                height=svg_h + 50,
                scrolling=False,
            )
        else:
            st.warning("Joonise andmed on vigased. Uuenda joonis.")
        if st.button("Uuenda joonis", help="Genereerib protsessijoonise uuesti"):
            with st.spinner("Genereerin joonist..."):
                new_diagram = generate_process_diagram(sop_draft, company)
            session["sops"][actual_idx]["process_diagram"] = new_diagram
            save_session(session_id, session)
            st.rerun()
    else:
        st.info("Protsessijoonis puudub.")
        if st.button("Genereeri joonis", type="primary"):
            with st.spinner("Genereerin joonist..."):
                new_diagram = generate_process_diagram(sop_draft, company)
            session["sops"][actual_idx]["process_diagram"] = new_diagram
            save_session(session_id, session)
            st.rerun()

# ── Allalaadimine ─────────────────────────────────────────────────────────────
safe_title = (
    sop_title.replace(" ", "_").replace("/", "-").replace("\\", "-")[:50]
) if sop_title else "SOP_dokument"

st.markdown('<hr style="border:none;border-top:1px solid #dee2e6">', unsafe_allow_html=True)
st.markdown("### Allalaadimine")

dl_col1, dl_col2, dl_col3 = st.columns(3)

with dl_col1:
    try:
        pdf_bytes = generate_pdf(sop_draft, company_name)
        st.download_button(
            label="Laadi alla SOP",
            data=pdf_bytes,
            file_name=f"{safe_title}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"PDF viga: {e}")

with dl_col2:
    if automation:
        st.download_button(
            label="Laadi alla AI ettepanekud",
            data=automation.encode("utf-8"),
            file_name=f"{safe_title}_AI_ettepanekud.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.button("Laadi alla AI ettepanekud", disabled=True, use_container_width=True,
                  help="Genereeri esmalt AI ettepanekud")

with dl_col3:
    _diag_steps = []
    if diagram_raw:
        try:
            _m = re.search(r'\[.*\]', diagram_raw, re.DOTALL)
            _diag_steps = _json.loads(_m.group(0)) if _m else []
        except Exception:
            pass
    if _diag_steps:
        _svg_dl, _ = _build_svg(_diag_steps)
        try:
            import cairosvg
            _png_bytes = cairosvg.svg2png(bytestring=_svg_dl.encode("utf-8"), scale=2)
            st.download_button(
                label="Laadi alla protsessijoonis",
                data=_png_bytes,
                file_name=f"{safe_title}_joonis.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception:
            st.download_button(
                label="Laadi alla protsessijoonis",
                data=_svg_dl.encode("utf-8"),
                file_name=f"{safe_title}_joonis.svg",
                mime="image/svg+xml",
                use_container_width=True,
            )
    else:
        st.button("Laadi alla protsessijoonis", disabled=True, use_container_width=True,
                  help="Genereeri esmalt protsessijoonis")

today = date.today().strftime("%d.%m.%Y")
st.markdown('<hr style="border:none;border-top:1px solid #dee2e6">', unsafe_allow_html=True)
st.markdown("**Faili info:**")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"- **Pealkiri:** {sop_title or '—'}")
    st.markdown(f"- **Ettevõte:** {company_name or '—'}")
with col2:
    st.markdown(f"- **Sõnu dokumendis:** {len(sop_draft.split())}")
    st.markdown(f"- **Loodud:** {today}")
