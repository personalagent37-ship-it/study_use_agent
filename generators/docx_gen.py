import re
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def _set_cell_background(cell, fill_hex: str):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def generate_notes_docx(topic: str, markdown_content: str, output_path: str | Path) -> str:
    """Generate a clean, structured Microsoft Word (.docx) study notes document."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()

    # Configure 1-inch margins
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    # Document Title
    clean_topic = topic.strip().title()
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(2)
    run_title = title_p.add_run(f"Study Notes: {clean_topic}")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(26, 54, 93)

    # Subtitle with date
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    date_str = datetime.now().strftime("%B %d, %Y")
    run_sub = sub_p.add_run(f"Prepared by WhatsApp AI Study Assistant • {date_str}")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(10)
    run_sub.font.color.rgb = RGBColor(113, 128, 150)

    # Parse lines
    lines = markdown_content.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Heading 1 / 2
        if stripped.startswith("# ") or stripped.startswith("## "):
            text = stripped.lstrip("# ").strip()
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            r = h.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(14)
            r.font.bold = True
            r.font.color.rgb = RGBColor(43, 108, 176)

        # Heading 3
        elif stripped.startswith("### "):
            text = stripped.lstrip("# ").strip()
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            r = h.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.color.rgb = RGBColor(45, 55, 72)

        # Callouts / Quotes
        elif stripped.startswith(">"):
            text = stripped.lstrip("> ").strip()
            tbl = doc.add_table(rows=1, cols=1)
            tbl.autofit = False
            tbl.columns[0].width = Inches(6.8)
            cell = tbl.cell(0, 0)
            _set_cell_background(cell, "EBF8FF")
            cell_p = cell.paragraphs[0]
            cell_p.paragraph_format.space_before = Pt(4)
            cell_p.paragraph_format.space_after = Pt(4)
            r = cell_p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(10)
            r.font.italic = True
            r.font.color.rgb = RGBColor(44, 82, 130)
            # Add spacer
            doc.add_paragraph().paragraph_format.space_after = Pt(4)

        # Bullet lists
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            _add_formatted_runs(p, text)

        # Numbered lists
        elif re.match(r"^\d+\.\s", stripped):
            match = re.match(r"^\d+\.\s+(.*)", stripped)
            text = match.group(1) if match else stripped
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_after = Pt(2)
            _add_formatted_runs(p, text)

        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            _add_formatted_runs(p, stripped)

    doc.save(str(output_path))
    return str(output_path)

def _add_formatted_runs(paragraph, text: str):
    """Parse inline bold **text** and add runs to docx paragraph."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            clean = part[2:-2]
            r = paragraph.add_run(clean)
            r.font.name = "Calibri"
            r.font.bold = True
        else:
            r = paragraph.add_run(part)
            r.font.name = "Calibri"
