# SOP Tool — Streamlit MVP

## Projekt
LLM-põhine SOP loomise tööriist VKE-dele. TalTech kursusetöö prototüüp.

## Tech stack
- Python + Streamlit (UI)
- Anthropic Claude API (claude-sonnet-4-6)
- JSON failid andmete salvestamiseks (ei ole vaja andmebaasi)

## MVP funktsioonid (järjekorras)
1. Ettevõtte profiili seadistamine (nimi, valdkond, rollid)
2. Vestlusbot SOP kaardistamiseks
3. SOP draft koos rollikaardistamisega
4. PDF eksport (reportlab)

## Disainiprintsiibid
- Lihtne, puhas UI — kasutajad ei ole arendajad
- Eestikeelne liides
- Kõik andmed salvestuvad lokaalsetesse JSON failidesse sessions/ kaustas
- Iga session on eraldi — ei ole user authentication

## Mida EI tee MVP
- Dokumendi upload
- Multi-user süsteem
- Andmebaas
