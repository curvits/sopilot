import re
import streamlit as st
from utils.session_manager import load_session, save_session, create_session, migrate_session
from utils.claude_client import chat, generate_sop, extract_sop_content, generate_process_diagram, generate_automation_suggestions

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

active_idx = session.get("active_sop_idx", 0)
if active_idx >= len(session["sops"]):
    active_idx = len(session["sops"]) - 1
    session["active_sop_idx"] = active_idx

current_sop = session["sops"][active_idx]


def _extract_process_plan(text):
    """Detect AI split suggestion and extract the numbered process list."""
    if "mitu eraldi protsessi" not in text and "ükshaaval" not in text:
        return []
    items = re.findall(r'^\s*\d+\.\s+(.+)', text, re.MULTILINE)
    return [item.strip() for item in items if len(item.strip()) > 3]


def _build_continuation_welcome(company_name, sops, process_plan):
    """Build a contextual welcome for new SOPs referencing the plan and completed SOPs."""
    done = [s.get("sop_title", "") for s in sops if s.get("sop_draft") and s.get("sop_title")]

    lines = [f"Jätkame **{company_name}** protsesside dokumenteerimist.\n"]

    if done:
        lines.append("**Valminud SOPid:**")
        for title in done:
            lines.append(f"- ✓ {title}")
        lines.append("")

    if process_plan:
        remaining = [
            p for p in process_plan
            if not any(p.split("—")[0].strip().lower() in t.lower() for t in done)
        ]
        if remaining:
            lines.append("**Plaanitud protsessid, mis on veel dokumenteerimata:**")
            for p in remaining:
                lines.append(f"- {p}")
            lines.append("\nMillisega soovite jätkata?")
        else:
            lines.append("Millise protsessiga soovite järgmisena jätkata?")
    else:
        lines.append("Millise protsessiga soovite järgmisena jätkata?")

    return "\n".join(lines)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<hr style="border:none;border-top:1px solid #dee2e6;margin:0.5rem 0">', unsafe_allow_html=True)
    if st.button("Tühjenda vestlus", use_container_width=True):
        session["sops"][active_idx]["chat_history"] = []
        save_session(session_id, session)
        st.rerun()

# ── Peamine sisu ──────────────────────────────────────────────────────────────
sop_count = len(session["sops"])
sop_label = f"SOP {active_idx + 1}/{sop_count}" if sop_count > 1 else ""
st.title(f"SOP Vestlus{f'  —  {sop_label}' if sop_label else ''}")
st.markdown(
    "Kirjelda protsess, mida soovid dokumenteerida. "
    "Assistent aitab sul seda struktureerida ja lõpuks SOP dokumendi luua."
)

if not company.get("name"):
    st.warning("Palun täida esmalt ettevõtte profiil.")
    st.stop()

st.markdown("---")

# ── Vestluse ajalugu ──────────────────────────────────────────────────────────
chat_history = current_sop.get("chat_history", [])
is_continuation = active_idx > 0 and not chat_history

if not chat_history:
    with st.chat_message("assistant"):
        if is_continuation:
            welcome = _build_continuation_welcome(
                company.get("name", "teie ettevõte"),
                session["sops"],
                session.get("process_plan", []),
            )
        else:
            welcome = (
                f"Tere! Olen siin, et aidata **{company.get('name', 'teie ettevõttel')}** "
                f"protsesse dokumenteerida.\n\n"
                f"Millist protsessi soovite täna SOP-iks vormistada? "
                f"Kirjeldage lühidalt, mida see protsess hõlmab."
            )
        st.markdown(welcome)

for msg in chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── SOP genereerimine nupuga ──────────────────────────────────────────────────
if len(chat_history) >= 6 and not current_sop.get("sop_draft"):
    col1, col2 = st.columns([3, 1])
    with col2:
        generate_clicked = st.button(
            "Loo SOP dokument",
            use_container_width=True,
            type="primary",
            help="Genereeri SOP kogu vestluse põhjal",
        )
    if generate_clicked:
        with st.chat_message("assistant"):
            with st.spinner("Genereerin SOP dokumenti..."):
                raw = generate_sop(chat_history, company)
            sop_content = extract_sop_content(raw)

            current_sop["sop_draft"] = sop_content
            for line in sop_content.splitlines():
                if line.startswith("# "):
                    current_sop["sop_title"] = line[2:].strip()
                    break

            with st.spinner("Genereerin protsessijoonist..."):
                current_sop["process_diagram"] = generate_process_diagram(sop_content, company)

            with st.spinner("Analüüsin automatiseerimisvõimalusi..."):
                current_sop["automation_suggestions"] = generate_automation_suggestions(sop_content, company)

            current_sop["chat_history"].append({"role": "assistant", "content": raw})
            session["sops"][active_idx] = current_sop
            save_session(session_id, session)

            st.markdown(raw)
            st.success("SOP dokument loodud! Ava 'SOP' leht vaatamiseks ja redigeerimiseks.")

        st.rerun()

# ── Nupud kui SOP on loodud ───────────────────────────────────────────────────
if current_sop.get("sop_draft"):
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Vaata tulemusi SOP lehel", type="primary", use_container_width=True):
            st.switch_page("pages/3_SOP_draft.py")
    with btn_col2:
        if st.button("Alusta järgmist SOP-i", use_container_width=True,
                     help="Lisa uus SOP sama ettevõtte alla"):
            from utils.session_manager import _empty_sop
            session["sops"].append(_empty_sop())
            session["active_sop_idx"] = len(session["sops"]) - 1
            save_session(session_id, session)
            st.rerun()

# ── Chat sisend ───────────────────────────────────────────────────────────────
user_input = st.chat_input("Kirjuta siia... (nt 'Kirjelda kauba vastuvõtu protsessi')")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Mõtlen..."):
            response = chat(chat_history, company)

        st.markdown(response)

        # Tuvasta alamprotsesside jaotussoovitus ja salvesta plaan
        detected_plan = _extract_process_plan(response)
        if detected_plan and not session.get("process_plan"):
            session["process_plan"] = detected_plan

        if "---SOP ALGUS---" in response:
            sop_content = extract_sop_content(response)
            current_sop["sop_draft"] = sop_content
            for line in sop_content.splitlines():
                if line.startswith("# "):
                    current_sop["sop_title"] = line[2:].strip()
                    break
            current_sop["process_diagram"] = generate_process_diagram(sop_content, company)
            current_sop["automation_suggestions"] = generate_automation_suggestions(sop_content, company)
            st.success("SOP dokument tuvastatud! Ava 'SOP' leht.")

    chat_history.append({"role": "assistant", "content": response})
    current_sop["chat_history"] = chat_history
    session["sops"][active_idx] = current_sop
    save_session(session_id, session)
    st.rerun()
