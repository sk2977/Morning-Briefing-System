#!/usr/bin/env python3
"""
Generate a professional WSJ-style PDF from the morning briefing text file.
Usage: python generate_pdf.py [YYYYMMDD]
If no date given, uses today's date.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

SCRIPT_DIR = Path(__file__).parent
PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch

# -- Color palette --
CLR_NAVY = colors.HexColor("#1a1a2e")
CLR_DARK = colors.HexColor("#222222")
CLR_BODY = colors.HexColor("#333333")
CLR_MUTED = colors.HexColor("#666666")
CLR_LIGHT_GRAY = colors.HexColor("#e8e8e8")
CLR_RULE = colors.HexColor("#999999")
CLR_ACCENT = colors.HexColor("#8b0000")       # dark red for HIGH
CLR_AMBER = colors.HexColor("#b8860b")         # dark goldenrod for MEDIUM
CLR_CONTEXT_BG = colors.HexColor("#f5f5f0")    # warm off-white for context blocks
CLR_CONTEXT_BAR = colors.HexColor("#cccccc")


def build_styles():
    """Create all paragraph styles for the briefing PDF."""
    styles = getSampleStyleSheet()

    s = {}

    s["masthead_title"] = ParagraphStyle(
        "MastheadTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=26,
        leading=30,
        textColor=CLR_NAVY,
        alignment=TA_CENTER,
        spaceAfter=2,
        tracking=4,
    )

    s["masthead_sub"] = ParagraphStyle(
        "MastheadSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=CLR_MUTED,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    s["section_header"] = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=CLR_NAVY,
        spaceBefore=16,
        spaceAfter=4,
        tracking=2,
    )

    s["subsection_header"] = ParagraphStyle(
        "SubsectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=CLR_DARK,
        spaceBefore=10,
        spaceAfter=3,
    )

    s["body"] = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13.5,
        textColor=CLR_BODY,
        spaceBefore=2,
        spaceAfter=2,
    )

    s["body_bold"] = ParagraphStyle(
        "BodyBold",
        parent=s["body"],
        fontName="Times-Bold",
    )

    s["context"] = ParagraphStyle(
        "Context",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=12,
        textColor=CLR_MUTED,
        leftIndent=12,
        spaceBefore=1,
        spaceAfter=1,
    )

    s["bullet"] = ParagraphStyle(
        "Bullet",
        parent=s["body"],
        leftIndent=14,
        firstLineIndent=-14,
        spaceBefore=2,
        spaceAfter=2,
    )

    s["numbered"] = ParagraphStyle(
        "Numbered",
        parent=s["body"],
        leftIndent=18,
        firstLineIndent=-18,
        spaceBefore=4,
        spaceAfter=2,
    )

    s["high_tag"] = ParagraphStyle(
        "HighTag",
        parent=s["body"],
        fontSize=9.5,
        leading=12.5,
        leftIndent=14,
        firstLineIndent=-14,
    )

    s["footer"] = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=CLR_MUTED,
        alignment=TA_CENTER,
    )

    s["sources"] = ParagraphStyle(
        "Sources",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=CLR_MUTED,
        alignment=TA_CENTER,
        spaceBefore=12,
    )

    return s


def _esc(text):
    """Escape XML special chars for ReportLab Paragraph markup."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _bold_lead(text):
    """If a numbered point has a colon-delimited lead, bold it."""
    # Match patterns like "1. MACRO SHOCK:" or "2. TOP DEAL:"
    m = re.match(r"^(\d+\.)\s+(.+?):\s*(.*)$", text, re.DOTALL)
    if m:
        num, label, rest = m.group(1), m.group(2), m.group(3)
        return f"<b>{_esc(num)} {_esc(label)}:</b> {_esc(rest)}"
    return _esc(text)


def _tag_urgency(text):
    """Color-code HIGH/MEDIUM urgency tags."""
    escaped = _esc(text)
    escaped = escaped.replace(
        "HIGH |",
        '<font color="#8b0000"><b>HIGH</b></font> |',
    )
    escaped = escaped.replace(
        "MEDIUM |",
        '<font color="#b8860b"><b>MEDIUM</b></font> |',
    )
    return escaped


def _is_divider(stripped):
    """Check if a line is a visual divider (===... or ---...)."""
    return bool(re.match(r"^[=\-]{6,}$", stripped))


def _is_section_header(stripped):
    """Check if a line is an ALL-CAPS section header.

    Allows parenthetical annotations with lowercase, e.g.:
    'CRITICAL EVENTS (next 48h)' or 'M&A / Deal Flow (past 7 days)'
    The main text (before any parenthesis) must be ALL CAPS.
    """
    if not stripped or len(stripped) < 3:
        return False
    if stripped.startswith(("=", "-", ">", "http", "HTTP")):
        return False
    if "|" in stripped:
        return False
    if stripped in ("ET", "AM", "PM"):
        return False
    # Strip parenthetical annotations for the caps check
    main_text = re.sub(r"\s*\(.*?\)\s*", " ", stripped).strip()
    # Extract only alphabetic characters -- must have at least 3 and all uppercase
    alpha_chars = re.findall(r"[a-zA-Z]", main_text)
    if len(alpha_chars) < 3:
        return False
    return all(c.isupper() for c in alpha_chars)


def parse_briefing(text):
    """Parse briefing text into structured sections.

    Divider lines (=== or ---) are treated as decoration and skipped.
    Section boundaries are determined by ALL-CAPS header lines.
    """
    lines = text.split("\n")
    sections = []
    current_section = "__PREAMBLE__"
    current_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip divider lines -- they are visual decoration
        if _is_divider(stripped):
            continue

        # Section headers: ALL CAPS lines
        if _is_section_header(stripped):
            # Save previous section
            if current_lines or current_section != "__PREAMBLE__":
                sections.append((current_section, current_lines))
            current_section = stripped
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        sections.append((current_section, current_lines))

    return sections


def build_flowables(text, styles):
    """Convert parsed briefing text into ReportLab flowables."""
    story = []
    sections = parse_briefing(text)
    lines = text.split("\n")

    # -- Masthead --
    # Extract date from first few lines
    date_str = ""
    sub_str = ""
    for line in lines[:5]:
        if "MORNING BRIEFING" in line:
            # Extract date portion
            m = re.search(r"--\s*(.+)", line)
            if m:
                date_str = m.group(1).strip()
        if "min read" in line.lower():
            sub_str = line.strip()

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        HRFlowable(
            width="100%", thickness=2, color=CLR_NAVY, spaceAfter=8, spaceBefore=0
        )
    )
    story.append(Paragraph("MORNING BRIEFING", styles["masthead_title"]))
    if date_str:
        story.append(Paragraph(_esc(date_str), styles["masthead_sub"]))
    if sub_str:
        story.append(Paragraph(_esc(sub_str), styles["masthead_sub"]))
    story.append(
        HRFlowable(
            width="100%", thickness=2, color=CLR_NAVY, spaceBefore=6, spaceAfter=12
        )
    )

    # -- Process sections --
    for section_name, section_lines in sections:
        # Skip internal/preamble sections (masthead already rendered above)
        if section_name.startswith("__") or "MORNING BRIEFING" in section_name:
            continue

        # Render section header
        clean_name = section_name.strip()
        if clean_name and len(clean_name) > 2:
            # Determine if major or sub section
            is_major = clean_name in (
                "BIOPHARMA",
                "MACRO ENVIRONMENT",
                "AI TECHNOLOGY",
                "COMPOUNDING EDUCATION",
                "JOB MARKET",
                "WHAT TO WATCH",
            )

            if is_major:
                story.append(Spacer(1, 6))
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=1.5,
                        color=CLR_NAVY,
                        spaceBefore=4,
                        spaceAfter=2,
                    )
                )
                story.append(Paragraph(_esc(clean_name), styles["section_header"]))
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.5,
                        color=CLR_RULE,
                        spaceBefore=2,
                        spaceAfter=8,
                    )
                )
            else:
                story.append(
                    Paragraph(_esc(clean_name), styles["subsection_header"])
                )
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.5,
                        color=CLR_LIGHT_GRAY,
                        spaceBefore=0,
                        spaceAfter=4,
                    )
                )

        # Render section content
        i = 0
        content_lines = section_lines
        while i < len(content_lines):
            line = content_lines[i]
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                i += 1
                continue

            # Skip divider lines that leaked through
            if _is_divider(stripped):
                i += 1
                continue

            # Mixed-case sub-headers (e.g., "M&A / Deal Flow (past 7 days)")
            # Heuristic: short line, title-case-ish, no bullet/number prefix
            if (
                len(stripped) < 80
                and not stripped.startswith(("-", "*", ">"))
                and not re.match(r"^\d+\.", stripped)
                and not stripped.startswith("  ")
                and re.match(
                    r"^[A-Z][A-Za-z&/\s\-]+(?: \(.*\))?$", stripped
                )
                and any(c.isupper() for c in stripped[:3])
            ):
                # Check if next line is empty or starts a new block (not continuation)
                next_i = i + 1
                if next_i >= len(content_lines) or not content_lines[next_i].strip():
                    story.append(
                        Paragraph(_esc(stripped), styles["subsection_header"])
                    )
                    story.append(
                        HRFlowable(
                            width="100%",
                            thickness=0.5,
                            color=CLR_LIGHT_GRAY,
                            spaceBefore=0,
                            spaceAfter=4,
                        )
                    )
                    i += 1
                    continue

            # Context block lines (start with >)
            if stripped.startswith(">"):
                # Collect consecutive context lines into one block
                ctx_lines = []
                while i < len(content_lines):
                    s = content_lines[i].strip()
                    if not s.startswith(">"):
                        break
                    ctx_lines.append(s.lstrip("> ").strip())
                    i += 1
                ctx_text = "<br/>".join(_esc(c) for c in ctx_lines)
                ctx_para = Paragraph(ctx_text, styles["context"])
                tbl = Table(
                    [[ctx_para]],
                    colWidths=[PAGE_W - 2 * MARGIN - 24],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), CLR_CONTEXT_BG),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ("LINEBEFORE", (0, 0), (0, -1), 3, CLR_CONTEXT_BAR),
                        ]
                    ),
                )
                story.append(tbl)
                continue

            # Urgency-tagged email lines
            if stripped.startswith("HIGH |") or stripped.startswith("MEDIUM |"):
                story.append(
                    Paragraph(_tag_urgency(stripped), styles["high_tag"])
                )
                i += 1
                continue

            # Deal headers (e.g., "1. Sanofi / Sino Biopharm -- $1.53B...")
            # Must check BEFORE generic numbered points
            deal_m = re.match(r"^(\d+)\.\s+(.+?)\s+--\s+(.+)", stripped)
            if deal_m:
                deal_num = deal_m.group(1)
                deal_parties = deal_m.group(2)
                deal_detail = deal_m.group(3)
                story.append(Spacer(1, 4))
                story.append(
                    Paragraph(
                        f"<b>{_esc(deal_num)}. {_esc(deal_parties)}</b> -- {_esc(deal_detail)}",
                        styles["body_bold"],
                    )
                )
                i += 1
                continue

            # Numbered points (1. 2. etc.) -- for the 10 Points section and WHAT TO WATCH
            m = re.match(r"^(\d+)\.\s+(.+)", stripped)
            if m:
                num = m.group(1)
                rest = m.group(2)
                full_text = f"{num}. {rest}"
                # Collect continuation lines
                j = i + 1
                while j < len(content_lines):
                    next_line = content_lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped:
                        break
                    if next_stripped.startswith(">"):
                        break
                    if re.match(r"^\d+\.\s+", next_stripped):
                        break
                    if next_stripped.startswith("-"):
                        break
                    if _is_divider(next_stripped):
                        break
                    full_text += " " + next_stripped
                    j += 1

                formatted = _bold_lead(full_text)
                story.append(Paragraph(formatted, styles["numbered"]))
                i = j
                continue

            # Bullet points
            if stripped.startswith("- ") or stripped.startswith("* "):
                bullet_text = stripped[2:]
                j = i + 1
                while j < len(content_lines):
                    next_line = content_lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped:
                        break
                    if next_stripped.startswith(("-", "*", ">")):
                        break
                    if re.match(r"^\d+\.\s+", next_stripped):
                        break
                    if _is_divider(next_stripped):
                        break
                    if next_line.startswith("  ") or next_line.startswith("\t"):
                        bullet_text += " " + next_stripped
                        j += 1
                    else:
                        break

                story.append(
                    Paragraph(
                        f"&#8226;  {_esc(bullet_text)}", styles["bullet"]
                    )
                )
                i = j
                continue

            # Indented data lines (like macro stats: "  Fed Funds Rate: 3.64%")
            if line.startswith("  ") and ":" in stripped:
                story.append(Paragraph(_esc(stripped), styles["body"]))
                i += 1
                continue

            # Sources line
            if stripped.startswith("Sources:"):
                story.append(Paragraph(_esc(stripped), styles["sources"]))
                i += 1
                continue

            # Label: value lines (e.g., "Drug: Azetukalner...")
            label_m = re.match(r"^([A-Z][A-Za-z\s/]+):\s+(.+)", stripped)
            if label_m and len(label_m.group(1)) < 30:
                label = label_m.group(1)
                value = label_m.group(2)
                story.append(
                    Paragraph(
                        f"<b>{_esc(label)}:</b> {_esc(value)}", styles["body"]
                    )
                )
                i += 1
                continue

            # Default: body paragraph
            para_text = stripped
            j = i + 1
            while j < len(content_lines):
                next_line = content_lines[j]
                next_stripped = next_line.strip()
                if not next_stripped:
                    break
                if next_stripped.startswith((">", "-", "*")):
                    break
                if re.match(r"^\d+\.\s+", next_stripped):
                    break
                if _is_divider(next_stripped):
                    break
                if _is_section_header(next_stripped):
                    break
                para_text += " " + next_stripped
                j += 1

            story.append(Paragraph(_esc(para_text), styles["body"]))
            i = j
            continue

    # Final rule
    story.append(Spacer(1, 12))
    story.append(
        HRFlowable(width="100%", thickness=2, color=CLR_NAVY, spaceBefore=4)
    )

    return story


def _header_footer(canvas, doc):
    """Draw page header and footer on each page."""
    canvas.saveState()

    # Footer: page number
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CLR_MUTED)
    canvas.drawCentredString(
        PAGE_W / 2, 0.45 * inch, f"Page {doc.page}"
    )

    # Thin top rule on pages after the first
    if doc.page > 1:
        canvas.setStrokeColor(CLR_LIGHT_GRAY)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_H - 0.55 * inch, PAGE_W - MARGIN, PAGE_H - 0.55 * inch)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(CLR_MUTED)
        canvas.drawString(MARGIN, PAGE_H - 0.5 * inch, "MORNING BRIEFING")
        canvas.drawRightString(
            PAGE_W - MARGIN, PAGE_H - 0.5 * inch, f"Page {doc.page}"
        )

    canvas.restoreState()


def generate_pdf(date_str):
    """Main entry point: read briefing text, generate PDF."""
    input_file = SCRIPT_DIR / f"briefing_output_{date_str}.txt"
    output_file = SCRIPT_DIR / f"briefing_{date_str}.pdf"

    if not input_file.exists():
        print(f"[ERROR] Input file not found: {input_file}")
        sys.exit(1)

    print(f"[INFO] Reading {input_file}...")
    text = input_file.read_text(encoding="utf-8")

    styles = build_styles()
    story = build_flowables(text, styles)

    # Build document
    frame_first = Frame(
        MARGIN,
        MARGIN,
        PAGE_W - 2 * MARGIN,
        PAGE_H - 2 * MARGIN,
        id="first",
    )
    frame_rest = Frame(
        MARGIN,
        MARGIN,
        PAGE_W - 2 * MARGIN,
        PAGE_H - 2 * MARGIN - 0.15 * inch,  # slightly less for header
        id="rest",
    )

    doc = BaseDocTemplate(
        str(output_file),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Morning Briefing - {date_str}",
        author="Morning Briefing System",
    )

    doc.addPageTemplates(
        [
            PageTemplate(id="First", frames=[frame_first], onPage=_header_footer),
            PageTemplate(id="Later", frames=[frame_rest], onPage=_header_footer),
        ]
    )

    # Switch to "Later" template after first page
    story.insert(1, NextPageTemplate("Later"))

    print(f"[INFO] Generating PDF...")
    doc.build(story)
    print(f"[OK] PDF saved to {output_file}")
    return output_file


if __name__ == "__main__":
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
    else:
        date_arg = datetime.now().strftime("%Y%m%d")

    generate_pdf(date_arg)
