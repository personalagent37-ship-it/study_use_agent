import re
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
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

def _set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    """Set inner cell padding in twentieths of a point (dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def _add_callout_box(doc, title: str, text: str, bg_hex: str, title_color_rgb: RGBColor):
    """Create a styled callout box in Word for sticky notes and formulas."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.8)
    cell = tbl.cell(0, 0)
    _set_cell_background(cell, bg_hex)
    _set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15

    if title:
        r_title = p.add_run(f"{title}\n")
        r_title.font.name = "Calibri"
        r_title.font.size = Pt(10)
        r_title.font.bold = True
        r_title.font.color.rgb = title_color_rgb

    _add_formatted_runs(p, text.strip())

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(4)

def _add_formatted_runs(paragraph, text: str):
    """Parse inline highlighters, bold, code, and italic runs for docx paragraph."""
    pattern = r"(\[HL:\s*(?:yellow|green|pink)\s*\|\s*[^\]]+\]|\*\*.*?\*\*|`.*?`|\*.*?\*)"
    tokens = re.split(pattern, text)

    for token in tokens:
        if not token:
            continue

        # Highlighter
        hl_match = re.match(r"^\[HL:\s*(yellow|green|pink)\s*\|\s*([^\]]+)\]$", token, re.IGNORECASE)
        if hl_match:
            color_name = hl_match.group(1).lower()
            content = hl_match.group(2)
            r = paragraph.add_run(content)
            r.font.name = "Calibri"
            r.font.bold = True
            if color_name == "yellow":
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW
            elif color_name == "green":
                r.font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN
            elif color_name == "pink":
                r.font.highlight_color = WD_COLOR_INDEX.PINK
            continue

        # Bold
        if token.startswith("**") and token.endswith("**") and len(token) >= 4:
            clean = token[2:-2]
            r = paragraph.add_run(clean)
            r.font.name = "Calibri"
            r.font.bold = True
            continue

        # Code
        if token.startswith("`") and token.endswith("`") and len(token) >= 2:
            clean = token[1:-1]
            r = paragraph.add_run(clean)
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(15, 23, 42)
            continue

        # Italic
        if token.startswith("*") and token.endswith("*") and len(token) >= 2:
            clean = token[1:-1]
            r = paragraph.add_run(clean)
            r.font.name = "Calibri"
            r.font.italic = True
            continue

        # Regular text
        r = paragraph.add_run(token)
        r.font.name = "Calibri"

def generate_notes_docx(topic: str, markdown_content: str, output_path: str | Path) -> str:
    """Generate a clean, structured Microsoft Word (.docx) study notes document."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()

    # Configure 0.8-inch margins
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    # Document Title
    clean_topic = topic.strip().title()
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    run_title = title_p.add_run(f"Study Notes: {clean_topic}")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(30, 58, 138)  # Deep Navy

    # Subtitle with branding and date
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    date_str = datetime.now().strftime("%B %d, %Y")
    run_sub = sub_p.add_run(f"Alexandria Studio • Universal Academic & Engineering Study Studio • {date_str}")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(10)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    # Split lines and preprocess special blocks
    lines = markdown_content.split("\n")
    i = 0
    total_lines = len(lines)

    while i < total_lines:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # 1. Custom Callout Blocks: [STICKY_THINK: ...], [STICKY_REMEMBER: ...], [FORMULA_BOX: ...], etc.
        sticky_match = re.match(r"^\[(STICKY_THINK|STICKY_REMEMBER|STICKY_EXAM|STICKY_FACT|FORMULA_BOX|MEMORY_TRICK|FLOW_STEP):\s*(.*)", stripped, re.IGNORECASE)
        if sticky_match:
            tag_type = sticky_match.group(1).upper()
            initial_text = sticky_match.group(2)
            
            block_lines = [initial_text]
            if not initial_text.endswith("]"):
                i += 1
                while i < total_lines:
                    nxt = lines[i]
                    if "]" in nxt:
                        block_lines.append(nxt[:nxt.find("]")])
                        break
                    else:
                        block_lines.append(nxt)
                    i += 1
            else:
                block_lines[0] = initial_text[:-1]

            full_block_text = "\n".join(block_lines).strip()

            if tag_type == "STICKY_THINK":
                _add_callout_box(doc, "💡 INTUITIVE THINKING / MENTAL MODEL", full_block_text, "FFE4E6", RGBColor(190, 18, 60))
            elif tag_type == "STICKY_REMEMBER":
                _add_callout_box(doc, "⭐ MUST REMEMBER / CORE DEFINITION", full_block_text, "FEF3C7", RGBColor(180, 83, 9))
            elif tag_type == "STICKY_EXAM":
                _add_callout_box(doc, "🎯 UNIVERSITY EXAM HINT", full_block_text, "FFEDD5", RGBColor(194, 65, 12))
            elif tag_type == "STICKY_FACT":
                _add_callout_box(doc, "📌 CORE FACT & CITATION", full_block_text, "D1FAE5", RGBColor(4, 120, 87))
            elif tag_type == "FORMULA_BOX":
                _add_callout_box(doc, "📐 KEY MATHEMATICAL FORMULA / EQUATION", full_block_text, "EFF6FF", RGBColor(29, 78, 216))
            elif tag_type == "MEMORY_TRICK":
                _add_callout_box(doc, "🧠 MNEMONIC & MEMORY TRICK", full_block_text, "FAF5FF", RGBColor(126, 34, 206))
            elif tag_type == "FLOW_STEP":
                _add_callout_box(doc, "🔄 EXECUTION FLOW & MECHANISM", full_block_text, "F8FAFC", RGBColor(51, 65, 85))

            i += 1
            continue

        # 2. Markdown Tables (| col1 | col2 |)
        if stripped.startswith("|") and stripped.endswith("|") and i + 1 < total_lines and ("---" in lines[i+1] or "|" in lines[i+1]):
            table_lines = []
            while i < total_lines and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2:
                raw_header = [c.strip() for c in table_lines[0].strip("|").split("|")]
                data_rows = []
                for t_line in table_lines[1:]:
                    if re.match(r"^\|[\s\-:|]+\|$", t_line):
                        continue
                    cells = [c.strip() for c in t_line.strip("|").split("|")]
                    data_rows.append(cells)

                if raw_header and data_rows:
                    col_count = len(raw_header)
                    t_word = doc.add_table(rows=len(data_rows) + 1, cols=col_count)
                    t_word.autofit = True

                    # Header row
                    hdr_cells = t_word.rows[0].cells
                    for col_idx, col_name in enumerate(raw_header):
                        if col_idx < len(hdr_cells):
                            hdr_cells[col_idx].text = col_name
                            _set_cell_background(hdr_cells[col_idx], "F1F5F9")
                            _set_cell_margins(hdr_cells[col_idx], top=80, bottom=80, left=100, right=100)
                            p = hdr_cells[col_idx].paragraphs[0]
                            if p.runs:
                                p.runs[0].font.bold = True
                                p.runs[0].font.name = "Calibri"
                                p.runs[0].font.color.rgb = RGBColor(30, 41, 59)

                    # Data rows
                    for row_idx, r_data in enumerate(data_rows):
                        row_cells = t_word.rows[row_idx + 1].cells
                        for col_idx, val in enumerate(r_data):
                            if col_idx < len(row_cells):
                                row_cells[col_idx].text = val
                                _set_cell_margins(row_cells[col_idx], top=60, bottom=60, left=100, right=100)
                                p = row_cells[col_idx].paragraphs[0]
                                if p.runs:
                                    p.runs[0].font.name = "Calibri"

                    spacer = doc.add_paragraph()
                    spacer.paragraph_format.space_before = Pt(2)
                    spacer.paragraph_format.space_after = Pt(4)
                    continue

        # 3. Horizontal Rule
        if stripped in ["---", "***", "___"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run("―" * 48)
            r.font.name = "Calibri"
            r.font.color.rgb = RGBColor(203, 213, 225)
            i += 1
            continue

        # 4. Heading 1
        if stripped.startswith("# "):
            text = stripped.lstrip("# ").strip()
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(4)
            r = h.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(16)
            r.font.bold = True
            r.font.color.rgb = RGBColor(30, 58, 138)
            i += 1
            continue

        # 5. Heading 2
        if stripped.startswith("## "):
            text = stripped.lstrip("# ").strip()
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            r = h.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(14)
            r.font.bold = True
            r.font.color.rgb = RGBColor(37, 99, 235)
            i += 1
            continue

        # 6. Heading 3
        if stripped.startswith("### "):
            text = stripped.lstrip("# ").strip()
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            r = h.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.color.rgb = RGBColor(51, 65, 85)
            i += 1
            continue

        # 7. Blockquote / Callout (> ...)
        if stripped.startswith(">"):
            text = stripped.lstrip("> ").strip()
            _add_callout_box(doc, "", text, "F8FAFC", RGBColor(71, 85, 105))
            i += 1
            continue

        # 8. Bullet lists (- or *)
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            _add_formatted_runs(p, text)
            i += 1
            continue

        # 9. Numbered lists (1. , 2. )
        if re.match(r"^\d+\.\s", stripped):
            match = re.match(r"^\d+\.\s+(.*)", stripped)
            text = match.group(1) if match else stripped
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            _add_formatted_runs(p, text)
            i += 1
            continue

        # 10. Regular paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        _add_formatted_runs(p, stripped)
        i += 1

    doc.save(str(output_path))
    return str(output_path)
