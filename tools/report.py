from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
import json, os
def _wrap(text, width=100):
    words = text.split(); lines, cur = [], ""
    for w in words:
        if len(cur)+len(w)+1 > width: lines.append(cur); cur = w
        else: cur = f"{cur} {w}".strip()
    if cur: lines.append(cur)
    return lines
def generate_pdf_report(dest_pdf_path: str, repo_path: str, summary: dict, events_path: str | None = None) -> str:
    os.makedirs(os.path.dirname(dest_pdf_path), exist_ok=True)
    c = canvas.Canvas(dest_pdf_path, pagesize=A4)
    width, height = A4; y = height - 2*cm
    def line(txt, size=11, dy=14):
        nonlocal y; c.setFont("Helvetica", size)
        for ln in _wrap(txt, width=100): c.drawString(2*cm, y, ln); y -= dy
    c.setFont("Helvetica-Bold", 16); c.drawString(2*cm, y, "RouteForge Migration Report"); y -= 24
    c.setFont("Helvetica", 10); c.drawString(2*cm, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"); y -= 16
    c.drawString(2*cm, y, f"Repository: {repo_path}"); y -= 20
    c.setFont("Helvetica-Bold", 12); c.drawString(2*cm, y, "Summary"); y -= 18
    c.setFont("Helvetica", 11)
    line(f"Success: {summary.get('success')}"); line(f"Message: {summary.get('message','')}")
    arts = summary.get("artifacts", {})
    for k in ["branch","current_branch","action","source_path","report_pdf"]:
        if k in arts: line(f"{k}: {arts[k]}")
    y -= 10; c.setFont("Helvetica-Bold", 12); c.drawString(2*cm, y, "Tasks Completed"); y -= 18
    c.setFont("Helvetica", 11)
    for t in summary.get("tasks_completed", []): line(f"• {t}")
    if events_path and os.path.exists(events_path):
        try:
            y -= 10; c.setFont("Helvetica-Bold", 12); c.drawString(2*cm, y, "Phase Timings"); y -= 18
            c.setFont("Helvetica", 11)
            with open(events_path) as f: events = [json.loads(x) for x in f if x.strip()]
            last = {}
            for e in events: last[e.get("phase")] = e
            for phase, e in last.items():
                if not phase: continue
                dur = e.get("duration_ms"); status = e.get("status"); msg = e.get("message", "")
                line(f"{phase}: {status} ({dur} ms) - {msg}")
        except Exception as ex:
            y -= 10; c.setFont("Helvetica", 10); line(f"(Could not parse events: {ex})")
    c.showPage(); c.save(); return dest_pdf_path
