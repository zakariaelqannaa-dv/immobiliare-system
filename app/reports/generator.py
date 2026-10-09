"""PDF generation with ReportLab."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def _footer(canvas, doc):
    try:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#5b6b82"))
        canvas.drawString(15 * mm, 12 * mm, f"Pagina {doc.page}")
        canvas.drawRightString(A4[0] - 15 * mm, 12 * mm, datetime.now().strftime("%d/%m/%Y %H:%M"))
        canvas.restoreState()
    except Exception:
        pass


def build_pdf(path: str | Path, title: str, headers: list[str], rows: list[list],
              subtitle: str = "") -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(p), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=16 * mm)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"])]
    if subtitle:
        story.append(Paragraph(subtitle, styles["Normal"]))
    else:
        story.append(Paragraph(f"{len(rows)} righe — {datetime.now():%d/%m/%Y %H:%M}",
                               styles["Normal"]))
    story.append(Spacer(1, 12))
    if not rows:
        story.append(Paragraph("Nessun dato da mostrare per i filtri selezionati.",
                               styles["Normal"]))
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return p
    ncols = max(len(headers), 1)
    avail = A4[0] - 28 * mm
    col_w = avail / ncols
    widths = [col_w] * ncols
    # give first column a bit less, last a bit more for readability
    data = [[Paragraph(f"<b>{h}</b>", styles["Normal"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c)[:300], styles["Normal"]) for c in r])
    t = Table(data, repeatRows=1, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return p
