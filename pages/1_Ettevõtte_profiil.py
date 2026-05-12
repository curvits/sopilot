import streamlit as st
from utils.session_manager import load_session, save_session, create_session

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
company = session.get("company", {})

# ── Peamine sisu ──────────────────────────────────────────────────────────────
st.title("Ettevõtte profiil")
st.markdown("Sisesta ettevõtte põhiandmed. Need lisatakse automaatselt SOP dokumentidesse.")
st.markdown("---")

with st.form("company_form"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Ettevõtte nimi *",
            value=company.get("name", ""),
            placeholder="nt Muster OÜ",
        )
        industry = st.text_input(
            "Valdkond / tegevusala *",
            value=company.get("industry", ""),
            placeholder="nt Jaekaubandus, IT-teenused, Tootmine...",
        )

    with col2:
        contact = st.text_input(
            "Kontaktisik (SOP autor)",
            value=company.get("contact", ""),
            placeholder="nt Mari Mets",
        )
        email = st.text_input(
            "E-post",
            value=company.get("email", ""),
            placeholder="nt mari@muster.ee",
        )

    st.markdown("#### Rollid / ametinimetused")
    st.caption("Lisa kõik rollid, kes on seotud teie protsessidega (üks roll real).")

    existing_roles = company.get("roles", [""])
    roles_text = st.text_area(
        "Rollid",
        value="\n".join(existing_roles) if existing_roles else "",
        height=150,
        placeholder="Näiteks:\nJuht\nRaamatupidaja\nMüügiesindaja\nLaotöötaja",
        label_visibility="collapsed",
    )

    notes = st.text_area(
        "Lisainfo ettevõtte kohta (vabatahtlik)",
        value=company.get("notes", ""),
        height=80,
        placeholder="nt meie peamised kliendid on B2B, kasutame tarkvara X ja Y...",
    )

    submitted = st.form_submit_button("Salvesta profiil", type="primary", use_container_width=True)

if submitted:
    if not name.strip():
        st.error("Ettevõtte nimi on kohustuslik.")
    elif not industry.strip():
        st.error("Valdkond on kohustuslik.")
    else:
        roles = [r.strip() for r in roles_text.splitlines() if r.strip()]
        session["company"] = {
            "name": name.strip(),
            "industry": industry.strip(),
            "contact": contact.strip(),
            "email": email.strip(),
            "roles": roles,
            "notes": notes.strip(),
        }
        save_session(session_id, session)
        session = load_session(session_id)
        company = session.get("company", {})
        st.success("Profiil salvestatud!")
        st.balloons()

# ── Jätka nupp — kuvatud alati kui profiil on olemas ─────────────────────────
if company.get("name"):
    if st.button("Jätka SOP vestlusega", type="primary"):
        st.switch_page("pages/2_SOP_vestlus.py")

# ── Profiili eelvaade ─────────────────────────────────────────────────────────
if company.get("name"):
    st.markdown("---")
    st.markdown("### Salvestatud profiil")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ettevõte", company.get("name", "—"))
    with col2:
        st.metric("Valdkond", company.get("industry", "—"))
    with col3:
        st.metric("Rolle kokku", len(company.get("roles", [])))

    if company.get("roles"):
        st.markdown("**Rollid:** " + " · ".join(f"`{r}`" for r in company["roles"]))
