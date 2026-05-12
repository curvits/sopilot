import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"


def _api_key():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            pass
    return key

SYSTEM_PROMPT = """Sa oled SOP (Standard Operating Procedure) loomise assistent eestikeelsetele VKE-dele.

Sinu ülesanne on aidata kasutajal dokumenteerida äriprotsesse struktureeritud SOP formaadis.

Vestluse käigus:
1. Küsi protsessi nime ja eesmärki
2. Selgita välja sammud järjekorras
3. Tuvasta vastutavad rollid iga sammu jaoks
4. Küsi täpsustavaid küsimusi (erandid, otsustuskohad, vajalikud vahendid/süsteemid)
5. Kui info on piisav, ütle kasutajale et ta vajutaks rohelist nuppu "Loo SOP dokument" lehe ülaosas — ära käsi kirjutada "loo SOP" ega ühtegi käsklust

NB! Kasutajal on eraldi nupp "Loo SOP dokument" — suuna alati sinna, mitte ära palu midagi tippida. Ära maini nupu asukohta (nt "lehe ülaosas") — ütle lihtsalt: vajutage nuppu "Loo SOP dokument".

Suurte tervikprotsesside tuvastamine ja jagamine:
Kui kasutaja kirjeldab suurt tervikprotsessi mis sisaldab selgelt mitu erinevat alamprotsessi (nt projektijuhtimine, müügitsükkel, tootmisprotsess jne), ÄRA alusta kohe küsimustega. Selle asemel:
1. Tuvasta kirjeldusest konkreetsed alamprotsessid — mõtle ise läbi, kuidas seda loogiliselt jagada
2. Vasta soovitusega jagada väiksemateks osadeks, kasutades seda struktuuri:
   "Kirjeldasid [protsessi nimi] — see sisaldab mitu eraldi protsessi. Soovitan dokumenteerida need ükshaaval, nii saab iga SOP olema selge ja kasutatav. Millisega alustame?
   1. [Alamprotsess 1 — lühike kirjeldus]
   2. [Alamprotsess 2 — lühike kirjeldus]
   3. [Alamprotsess 3 — lühike kirjeldus]
   [jätka vajadusel]"
3. Oota kasutaja valikut enne kui jätkad küsimustega.
Hea SOP katab ühe konkreetse protsessi — mitte tervet osakonda ega projekti elutsüklit.

Kui kasutaja palub SOP-i luua (nt kirjutab "loo SOP", "genereeri dokument", vms), genereeri struktureeritud SOP täpselt järgmises formaadis — ära lisa midagi enne ---SOP ALGUS--- ega pärast ---SOP LÕPP---:

---SOP ALGUS---
# [Protsessi nimi]

**Versioon:** 1.0
**Kuupäev:** [tänane kuupäev dd.mm.yyyy formaadis]
**Ettevõte:** [ettevõtte nimi]
**Vastutav roll:** [peamine vastutav roll]

## 1. Eesmärk
[Selge, lühike kirjeldus miks see protseduur on vajalik]

## 2. Reguleerimisala
[Kellele kehtib, millistel juhtudel rakendatakse]

## 3. Vastutus
[Kes vastutab protsessi täitmise ja uuendamise eest]

## 4. Protseduur

### 4.1 [Sammu pealkiri]
**Vastutav:** [roll]
[Sammu kirjeldus — selge ja konkreetne]

### 4.2 [Sammu pealkiri]
**Vastutav:** [roll]
[Sammu kirjeldus]

[jätka vajalike sammudega...]

## 5. Seotud dokumendid ja tööriistad
- [Dokument/tööriist 1]
- [Dokument/tööriist 2]
---SOP LÕPP---

Vasta alati eesti keeles. Ole sõbralik ja konkreetne."""


def _build_system(company_info):
    system = SYSTEM_PROMPT
    if company_info:
        parts = []
        if company_info.get("name"):
            parts.append(f"Nimi: {company_info['name']}")
        if company_info.get("industry"):
            parts.append(f"Valdkond: {company_info['industry']}")
        if company_info.get("roles"):
            parts.append(f"Rollid: {', '.join(company_info['roles'])}")
        if company_info.get("notes"):
            parts.append(f"Lisainfo: {company_info['notes']}")
        if parts:
            system += (
                "\n\nEttevõtte kontekst (kasutaja on selle ette täitnud — ära küsi uuesti infot, "
                "mis on juba lisainfos kirjas):\n"
                + "\n".join(f"- {p}" for p in parts)
            )
    return system


def chat(messages, company_info=None):
    client = Anthropic(api_key=_api_key())
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=_build_system(company_info),
        messages=messages,
    )
    return response.content[0].text


def generate_sop(chat_history, company_info=None):
    """Force-generate a clean SOP from the full conversation."""
    client = Anthropic(api_key=_api_key())
    messages = list(chat_history) + [
        {
            "role": "user",
            "content": (
                "Palun loo nüüd lõplik SOP dokument kogu meie vestluse põhjal. "
                "Kasuta täpset formaati koos ---SOP ALGUS--- ja ---SOP LÕPP--- märgistega."
            ),
        }
    ]
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=_build_system(company_info),
        messages=messages,
    )
    return response.content[0].text


def extract_sop_content(text):
    """Extract SOP markdown between the markers, or return full text if not found."""
    start = "---SOP ALGUS---"
    end = "---SOP LÕPP---"
    if start in text and end in text:
        return text[text.index(start) + len(start) : text.index(end)].strip()
    return text.strip()


def generate_automation_suggestions(sop_content, company_info=None):
    """Generate AI/automation opportunity suggestions for the given SOP."""
    client = Anthropic(api_key=_api_key())

    context = ""
    if company_info:
        parts = []
        if company_info.get("name"):
            parts.append(f"Ettevõte: {company_info['name']}")
        if company_info.get("industry"):
            parts.append(f"Valdkond: {company_info['industry']}")
        if parts:
            context = "\n".join(parts) + "\n\n"

    prompt = (
        f"{context}"
        f"Vaata seda äriprotsessi kirjeldust. Loetle 3-5 konkreetset kohta, kus AI või automatiseerimine "
        f"võiks selle protsessi efektiivsemaks muuta. Iga punkt peab olema: "
        f"1) konkreetne ja seotud just selle protsessiga, "
        f"2) praktiline VKE jaoks, "
        f"3) kuvatud formaadis: Võimalus + Miks kasulik + Näide tööriistast. "
        f"Vasta eesti keeles.\n\n"
        f"Protsessi kirjeldus:\n{sop_content[:3000]}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def generate_process_diagram(sop_content, company_info=None):
    """Return JSON list of process steps: [{"samm": "...", "roll": "..."}, ...]"""
    client = Anthropic(api_key=_api_key())

    roles = ""
    if company_info and company_info.get("roles"):
        roles = f"\nEttevõtte rollid: {', '.join(company_info['roles'])}"

    prompt = f"""Analüüsi järgmist SOP dokumenti ja eralda protsessi põhisammud.{roles}

Tagasta AINULT JSON massiiv, ilma selgituste, kommentaaride või koodi-märgistuseta:
[
  {{"samm": "Lühike sammu nimetus", "roll": "Vastutav roll"}},
  {{"samm": "Järgmine samm", "roll": "Vastutav roll"}}
]

Nõuded:
- Maksimaalselt 8 sammu
- Sammu nimetus maksimaalselt 35 tähemärki
- Rolli nimi maksimaalselt 28 tähemärki
- Kasuta eestikeelseid nimetusi
- Ainult puhas JSON massiiv

SOP dokument:
{sop_content[:3000]}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def generate_mermaid_diagram(sop_content, company_info=None):
    """Generate a Mermaid flowchart from SOP content. Returns raw Mermaid syntax string."""
    client = Anthropic(api_key=_api_key())

    roles = ""
    if company_info and company_info.get("roles"):
        roles = f"\nEttevõtte rollid: {', '.join(company_info['roles'])}"

    prompt = f"""Analüüsi järgmist SOP dokumenti ja loo sellest Mermaid flowchart joonis.{roles}

Iga protsessisamm koosneb KAHEST ühendatud sõlmest:
1. Sammu sõlm (ristkülik): sammu lühike nimi — tumesinine #1e3a5f
2. Rolli sõlm (staadion): vastutava rolli nimi — hele sinine #4a7ebb

Sõlmede nimetamise reegel:
- Sammu sõlmid: S1, S2, S3 ...
- Rolli sõlmid: R1, R2, R3 ... (vastab sammu numbrile)

Voog: S1 --> R1 --> S2 --> R2 --> S3 --> R3 ...

Kõik sõlmid kasutavad SAMA kahte classDef-i (mitte eri värve rollide järgi):
- classDef step fill:#1e3a5f,color:#fff,stroke:#1e3a5f,font-weight:bold
- classDef role fill:#4a7ebb,color:#fff,stroke:#4a7ebb,font-size:12px

Kasuta eestikeelseid silte. Hoia joonis selge (maks 8 sammu).

Näide struktuurist:
flowchart TD
    S1["Lao ülevaatus"]
    R1(["Laojuhataja"])
    S2["Tellimuse kinnitamine"]
    R2(["Müügijuht"])
    S1 --> R1 --> S2 --> R2
    classDef step fill:#1e3a5f,color:#fff,stroke:#1e3a5f,font-weight:bold
    classDef role fill:#4a7ebb,color:#fff,stroke:#4a7ebb,font-size:12px
    class S1,S2 step
    class R1,R2 role

Väljasta AINULT Mermaid kood, ilma ```mermaid märgistuseta ja ilma selgitusteta.

SOP dokument:
{sop_content[:3000]}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    # Eemalda võimalik ```mermaid ... ``` wrapper
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()
    return raw
