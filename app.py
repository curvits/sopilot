import base64
import streamlit as st
from utils.session_manager import create_session, load_session, list_sessions

def _img_b64(path):
    import os
    abs_path = os.path.join(os.path.dirname(__file__), path)
    with open(abs_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

st.set_page_config(
    page_title="SOPilot",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS — jookseb igal lehel, kuna app.py käivitub alati
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #f8f9fa;
    border-right: 1px solid #dee2e6;
}

/* Aktiivse tab'i värv — tumesinine */
[data-testid="stTab"][aria-selected="true"],
button[role="tab"][aria-selected="true"],
[data-baseweb="tab"][aria-selected="true"] {
    color: #1e3a5f !important;
    border-bottom-color: #1e3a5f !important;
    border-bottom-width: 2px !important;
}

/* h2 eraldusjooon SOP eelvaates */
[data-testid="stTabPanel"] h2 {
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 0.35rem;
    margin-top: 1.5rem;
}

/* SOP dokumendi max-width eelvaates */
[data-testid="stTabPanel"] [data-testid="stMarkdownContainer"],
[data-testid="stTabPanel"] .stMarkdownContainer {
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}

/* Sidebar nav: eemalda kõik vaikimisi padding/margin erinevused */
[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    padding-top: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul {
    padding: 0 !important;
    margin: 0 !important;
    list-style: none !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] li {
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
[data-testid="stSidebar"] [data-testid="stSidebarNav"] span {
    display: block !important;
    padding: 0.45rem 1rem !important;
    margin: 0 !important;
    line-height: 1.4 !important;
    font-size: 0.9rem !important;
}

/* Sidebar üldine sisu: ühtlane padding */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem !important;
}
[data-testid="stSidebar"] .block-container,
[data-testid="stSidebar"] .element-container {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* Primary nupud ja form submit — tumesinine */
[data-testid="baseButton-primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] > button,
button[kind="primary"],
button[kind="formSubmit"],
.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background-color: #1e3a5f !important;
    border-color: #1e3a5f !important;
    color: #ffffff !important;
    box-shadow: none !important;
}
[data-testid="baseButton-primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primary"]:hover,
button[kind="formSubmit"]:hover,
.stFormSubmitButton > button:hover {
    background-color: #16304f !important;
    border-color: #16304f !important;
    color: #ffffff !important;
}

</style>
""", unsafe_allow_html=True)

_logo_b64 = _img_b64("assets/curv_logo.png")
st.sidebar.markdown(
    f'<div style="position:fixed;bottom:18px;left:1rem;z-index:99999;opacity:0.75">'
    f'<a href="https://www.curv.ee" target="_blank" rel="noopener noreferrer">'
    f'<img src="data:image/png;base64,{_logo_b64}" style="height:80px;width:auto;display:block" alt="Curv Consulting">'
    f'</a>'
    f'</div>',
    unsafe_allow_html=True,
)

# Globaalne sessiooni info sidebar'is — nähtav kõigil lehtedel
if st.session_state.get("session_id"):
    session = load_session(st.session_state["session_id"])
    if session:
        company_name = session.get("company", {}).get("name", "")
        label = company_name if company_name else st.session_state["session_id"][:8] + "..."
        st.sidebar.markdown(f"**{label}**")
        st.sidebar.markdown('<hr style="border:none;border-top:1px solid #dee2e6;margin:0.5rem 0">', unsafe_allow_html=True)


def home():
    st.markdown("""
<div style="display:flex;align-items:center;gap:1.1rem;margin-bottom:0.25rem;margin-top:0.5rem">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 50" width="90" height="38">
    <polygon points="46,25 4,11 15,25 4,39"   fill="#1e3a5f" opacity="0.35"/>
    <polygon points="46,25 19,11 28,25 19,39"  fill="#1e3a5f" opacity="0.6"/>
    <polygon points="46,25 33,13 39,25 33,37"  fill="#1e3a5f" opacity="0.85"/>
    <polygon points="74,25 116,11 105,25 116,39" fill="#1e3a5f" opacity="0.35"/>
    <polygon points="74,25 101,11 92,25 101,39"  fill="#1e3a5f" opacity="0.6"/>
    <polygon points="74,25 87,13 81,25 87,37"    fill="#1e3a5f" opacity="0.85"/>
    <circle cx="60" cy="25" r="14" fill="#1e3a5f"/>
    <circle cx="60" cy="25" r="8"  fill="#ffffff"/>
    <circle cx="60" cy="25" r="4"  fill="#1e3a5f"/>
  </svg>
  <span style="font-size:2.6rem;font-weight:800;color:#1e3a5f;letter-spacing:-0.5px;line-height:1">SOPilot</span>
</div>
<p style="font-size:1.05rem;color:#6c757d;margin:0 0 1.25rem 0;font-weight:400">
  Dokumenteeri protsessid. Leia automatiseerimisvõimalused. Minutitega.
</p>
<p style="font-size:0.97rem;color:#374151;line-height:1.7;max-width:720px;margin:0 0 0.25rem 0">
  <strong>SOP (Standard Operating Procedure)</strong> on kirjalik juhend, mis kirjeldab samm-sammult, kuidas teie ettevõttes üks töölõik toimib — kes mida teeb, mis järjekorras ja mis on oodatav tulemus. SOPid aitavad uusi töötajaid kiiremini tööle saada, vähendada vigu ja tagada et protsessid toimivad ühtmoodi ka siis, kui võtmeisik on eemal. <strong>SOPilot</strong> aitab sul need dokumendid luua vestluse käigus — ilma tühja lehega alustamise valuta.
</p>
""", unsafe_allow_html=True)
    st.markdown('<hr style="border:none;border-top:1px solid #dee2e6">', unsafe_allow_html=True)

    if st.button("Alusta SOP loomist", type="primary"):
        session_id, _ = create_session()
        st.session_state["session_id"] = session_id
        st.switch_page("pages/1_Ettevõtte_profiil.py")

    st.markdown('<hr style="border:none;border-top:1px solid #dee2e6;margin-top:1.5rem">', unsafe_allow_html=True)

    st.markdown("""
**SOPilot** on AI-põhine tööriist, mis aitab väikese ja keskmise suurusega ettevõtetel (VKE) oma äriprotsesse kiiresti ja lihtsalt dokumenteerida. Kirjelda protsess vestluse kaudu — SOPilot loob struktureeritud SOP dokumendi, tuvastab automatiseerimisvõimalused ja joonistab protsessikaardi.
""")

    st.markdown("### Kuidas see toimib?")

    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.markdown("""**1. Ettevõtte profiil**

Sisesta ettevõtte nimi, valdkond ja töötajate rollid. Need andmed lisatakse automaatselt igasse SOP dokumenti ja aitavad AI-l anda täpsemaid soovitusi.""")
    with col2:
        st.markdown("""**2. SOP vestlus**

AI juhib sind läbi protsessi kirjeldamise struktureeritud vestlusega. Vasta küsimustele nii täpselt kui oskad — mida rohkem detaile, seda parem on lõpptulemus.""")
    with col3:
        st.markdown("""**3. SOP draft**

Vaata AI loodud SOP-i, protsessijoonist ja AI automatiseerimisvõimalusi. Redigeeri vajadusel ja laadi alla PDF-ina.""")

    st.markdown('<hr style="border:none;border-top:1px solid #dee2e6">', unsafe_allow_html=True)
    st.markdown("""
<div style="border:1px solid #ffc107;border-radius:6px;padding:1rem 1.25rem;background:#fffdf0">
<strong>Oluline märkus:</strong> SOPilot on sessioonipõhine tööriist. Kui sulgead brauseriakna, kaovad kõik andmed. Laadi SOP alla enne akna sulgemist.
</div>
""", unsafe_allow_html=True)


_session_id = st.session_state.get("session_id")
_session_data = load_session(_session_id) if _session_id else {}
_sops = _session_data.get("sops", [])
_has_chat = any(s.get("chat_history") for s in _sops) or bool(_session_data.get("chat_history"))
_has_sop = any(s.get("sop_draft") for s in _sops) or bool(_session_data.get("sop_draft"))

pg = st.navigation([
    st.Page(home, title="SOPilot", default=True),
    st.Page("pages/1_Ettevõtte_profiil.py", title="Ettevõtte profiil"),
    st.Page("pages/2_SOP_vestlus.py", title="SOP vestlus ✓" if _has_chat else "SOP vestlus"),
    st.Page("pages/3_SOP_draft.py", title="SOP tulemused ✓" if _has_sop else "SOP tulemused"),
])
pg.run()
