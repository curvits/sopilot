import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


PAGE_W, PAGE_H = A4
MARGIN = 2 * cm

# Colours
BLUE = colors.HexColor("#1a56db")
LIGHT_GREY = colors.HexColor("#f3f4f6")
MID_GREY = colors.HexColor("#6b7280")
DARK = colors.HexColor("#111827")


def _styles():
    base = getSampleStyleSheet()

    title = ParagraphStyle(
        "SOPTitle",
        parent=base["Title"],
        fontSize=20,
        textColor=BLUE,
        spaceAfter=6,
        leading=26,
    )
    h1 = ParagraphStyle(
        "SOPH1",
        parent=base["Heading1"],
        fontSize=13,
        textColor=BLUE,
        spaceBefore=14,
        spaceAfter=4,
        borderPad=0,
    )
    h2 = ParagraphStyle(
        "SOPH2",
        parent=base["Heading2"],
        fontSize=11,
        textColor=DARK,
        spaceBefore=10,
        spaceAfter=3,
    )
    body = ParagraphStyle(
        "SOPBody",
        parent=base["Normal"],
        fontSize=10,
        textColor=DARK,
        leading=15,
        spaceAfter=4,
    )
    meta = ParagraphStyle(
        "SOPMeta",
        parent=base["Normal"],
        fontSize=9,
        textColor=MID_GREY,
        leading=14,
        spaceAfter=2,
    )
    bold_label = ParagraphStyle(
        "SOPBoldLabel",
        parent=body,
        fontSize=10,
        textColor=DARK,
    )
    return {
        "title": title,
        "h1": h1,
        "h2": h2,
        "body": body,
        "meta": meta,
        "bold_label": bold_label,
    }


def _parse_inline(text):
    """Convert **bold** and basic markdown inline to ReportLab XML."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


def generate_pdf(sop_markdown: str, company_name: str = "") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="SOP dokument",
        author=company_name or "SOP Tööriist",
    )

    s = _styles()
    story = []

    lines = sop_markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # H1
        if line.startswith("# "):
            story.append(Paragraph(_parse_inline(line[2:]), s["title"]))
            story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=8))
            i += 1
            continue

        # H2 (##)
        if line.startswith("## "):
            story.append(Paragraph(_parse_inline(line[3:]), s["h1"]))
            i += 1
            continue

        # H3 (###)
        if line.startswith("### "):
            story.append(Paragraph(_parse_inline(line[4:]), s["h2"]))
            i += 1
            continue

        # Bold meta lines  **Key:** value
        if line.startswith("**") and ":**" in line:
            story.append(Paragraph(_parse_inline(line), s["meta"]))
            i += 1
            continue

        # Bullet
        if line.startswith("- ") or line.startswith("* "):
            story.append(Paragraph("• " + _parse_inline(line[2:]), s["body"]))
            i += 1
            continue

        # Numbered list
        m = re.match(r"^(\d+)\.\s+(.*)", line)
        if m:
            story.append(Paragraph(f"{m.group(1)}. {_parse_inline(m.group(2))}", s["body"]))
            i += 1
            continue

        # Horizontal rule
        if line.strip() in ("---", "***", "___"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY, spaceAfter=4))
            i += 1
            continue

        # Empty line → small spacer
        if line.strip() == "":
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Default body paragraph
        story.append(Paragraph(_parse_inline(line), s["body"]))
        i += 1

    # Footer note
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))
    story.append(
        Paragraph(
            f"Genereeritud SOP tööriistaga · {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            s["meta"],
        )
    )

    doc.build(story)
    return buf.getvalue()
