"""CSV / Excel export helpers."""
from __future__ import annotations

import csv
from pathlib import Path


def export_csv(path: str | Path, headers: list[str], rows: list[list]) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return p


def export_excel(path: str | Path, headers: list[str], rows: list[list], title: str = "Report") -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Font
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append(r)
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 20
    wb.save(p)
    return p
