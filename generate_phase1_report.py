"""
Generate Comprehensive Phase 1 Completion Report in .docx format with Embedded Diagrams
Project: Verified Distressed Property Discovery & Buyer Assistance Platform (SKANDX)
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Directories
OUTPUT_DIR = Path("docs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DIAGRAMS_DIR = OUTPUT_DIR / "diagrams"
DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

DOCX_PATH = Path("PHASE_1_COMPLETION_REPORT_SKANDX.docx")

# Set up matplotlib style
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CBD5E1'

# ----------------------------------------------------------------------
# 1. GENERATE DIAGRAMS
# ----------------------------------------------------------------------

def generate_workflow_diagram():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_facecolor('#F8FAFC')
    fig.patch.set_facecolor('#F8FAFC')
    ax.axis('off')

    stages = [
        ("1. Property Source", "IBAPI & Bank Gazettes", "#071D35"),
        ("2. Ingestion & Collection", "Playwright Crawlers", "#071D35"),
        ("3. AI Multimodal OCR", "Gemini 2.5 Flash Vision", "#0A2540"),
        ("4. Back-Office Verification", "Split-Viewer Desk", "#D97706"),
        ("5. Published to Market", "Verified on skandx.com", "#16A34A"),
        ("6. Buyer Inquiry Capture", "Contact Modal (#SK-XXXX)", "#071D35"),
        ("7. Buyer Concierge Check", "Phone & WhatsApp Liaison", "#071D35"),
        ("8. Assisted Site Visit", "Officer Inspection Meet", "#071D35"),
        ("9. Statutory Auction", "Official Bank/IBAPI Bidding", "#2563EB"),
        ("10. Post-Purchase Support", "Sale Certificate & Section 14", "#4B5563"),
    ]

    # Two rows of 5 boxes
    box_w, box_h = 1.95, 0.95
    xs = [0.4 + i * 2.3 for i in range(5)]
    y_top = 2.4
    y_bottom = 0.6

    for i in range(5):
        # Top Row: 1 to 5 (Left to Right)
        x = xs[i]
        title, sub, col = stages[i]
        rect = patches.FancyBboxPatch((x, y_top), box_w, box_h, boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor=col, edgecolor="#CBD5E1", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + box_w/2, y_top + box_h * 0.62, title, ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=9.5)
        ax.text(x + box_w/2, y_top + box_h * 0.28, sub, ha='center', va='center', color='#E2E8F0', fontsize=7.5)

        if i < 4:
            ax.annotate('', xy=(xs[i+1], y_top + box_h/2), xytext=(x + box_w, y_top + box_h/2),
                        arrowprops=dict(arrowstyle="-|>", color="#D9A62E", lw=2, mutation_scale=14))

    # Downward arrow from stage 5 to stage 6
    ax.annotate('', xy=(xs[4] + box_w/2, y_bottom + box_h), xytext=(xs[4] + box_w/2, y_top),
                arrowprops=dict(arrowstyle="-|>", color="#D9A62E", lw=2, mutation_scale=14))

    # Bottom Row: 6 to 10 (Right to Left)
    for j in range(5):
        stage_idx = 5 + j
        x = xs[4 - j]
        title, sub, col = stages[stage_idx]
        rect = patches.FancyBboxPatch((x, y_bottom), box_w, box_h, boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor=col, edgecolor="#CBD5E1", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + box_w/2, y_bottom + box_h * 0.62, title, ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=9.5)
        ax.text(x + box_w/2, y_bottom + box_h * 0.28, sub, ha='center', va='center', color='#E2E8F0', fontsize=7.5)

        if j < 4:
            ax.annotate('', xy=(xs[3 - j] + box_w, y_bottom + box_h/2), xytext=(x, y_bottom + box_h/2),
                        arrowprops=dict(arrowstyle="-|>", color="#D9A62E", lw=2, mutation_scale=14))

    ax.set_xlim(0, 11.8)
    ax.set_ylim(0, 3.8)
    plt.title("SKANDX 10-Stage Distressed Property Discovery & Concierge Lifecycle", fontsize=14, weight='bold', pad=18, color="#071D35")
    plt.tight_layout()
    diagram_path = DIAGRAMS_DIR / "workflow_lifecycle.png"
    plt.savefig(diagram_path, bbox_inches='tight', dpi=300)
    plt.close()
    return diagram_path


def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_facecolor('#F8FAFC')
    fig.patch.set_facecolor('#F8FAFC')
    ax.axis('off')

    # 1. Client Browser Box
    rect_client = patches.FancyBboxPatch((0.5, 5.2), 9.8, 1.8, boxstyle="round,pad=0.1,rounding_size=0.2",
                                         facecolor='#FFFFFF', edgecolor='#071D35', linewidth=2)
    ax.add_patch(rect_client)
    ax.text(5.4, 6.7, "Unified React 19 Frontend SPA (Deployed on Vercel)", ha='center', va='center', color='#071D35', weight='bold', fontsize=12)

    # Subdomain Router
    rect_sub = patches.FancyBboxPatch((4.0, 5.5), 2.8, 0.7, boxstyle="round,pad=0.05,rounding_size=0.1",
                                     facecolor='#071D35', edgecolor='#D9A62E', linewidth=1.5)
    ax.add_patch(rect_sub)
    ax.text(5.4, 5.85, "Subdomain Router (domain.js)", ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=9.5)

    # Two portal boxes
    rect_cust = patches.FancyBboxPatch((0.8, 4.0), 4.2, 0.9, boxstyle="round,pad=0.08,rounding_size=0.15",
                                       facecolor='#0A2540', edgecolor='#CBD5E1', linewidth=1.5)
    ax.add_patch(rect_cust)
    ax.text(2.9, 4.55, "Customer Marketplace (skandx.com)", ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=10)
    ax.text(2.9, 4.25, "Verified Listings • Search/Filters • Lead Intake", ha='center', va='center', color='#E2E8F0', fontsize=8)

    rect_adm = patches.FancyBboxPatch((5.8, 4.0), 4.2, 0.9, boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor='#D97706', edgecolor='#CBD5E1', linewidth=1.5)
    ax.add_patch(rect_adm)
    ax.text(7.9, 4.55, "Admin Verification Desk (admin.skandx.com)", ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=10)
    ax.text(7.9, 4.25, "HMAC Gate • Notice PDF Split-Viewer • Leads Desk", ha='center', va='center', color='#FEF3C7', fontsize=8)

    # Connections from Router to Portals
    ax.annotate('', xy=(2.9, 4.9), xytext=(4.5, 5.5), arrowprops=dict(arrowstyle="-|>", color="#071D35", lw=1.8))
    ax.annotate('', xy=(7.9, 4.9), xytext=(6.3, 5.5), arrowprops=dict(arrowstyle="-|>", color="#071D35", lw=1.8))

    # 2. REST API Box
    rect_api = patches.FancyBboxPatch((2.2, 2.3), 6.4, 1.1, boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor='#071D35', edgecolor='#10B981', linewidth=2)
    ax.add_patch(rect_api)
    ax.text(5.4, 2.95, "Backend REST API Server (Python 3.12 / api.skandx.com)", ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=11)
    ax.text(5.4, 2.60, "HMAC-SHA256 Auth • Rate Limiting • Notice PDF Proxy • CORS Headers", ha='center', va='center', color='#A7F3D0', fontsize=8.5)

    # Connecting Portals to API
    ax.annotate('', xy=(4.2, 3.4), xytext=(2.9, 4.0), arrowprops=dict(arrowstyle="-|>", color="#071D35", lw=1.5))
    ax.annotate('', xy=(6.6, 3.4), xytext=(7.9, 4.0), arrowprops=dict(arrowstyle="-|>", color="#071D35", lw=1.5))

    # 3. Database & Ingestion Engine
    rect_db = patches.FancyBboxPatch((0.8, 0.4), 4.5, 1.3, boxstyle="round,pad=0.08,rounding_size=0.15",
                                     facecolor='#1E293B', edgecolor='#38BDF8', linewidth=1.5)
    ax.add_patch(rect_db)
    ax.text(3.05, 1.35, "Supabase PostgreSQL Database", ha='center', va='center', color='#38BDF8', weight='bold', fontsize=10.5)
    ax.text(3.05, 1.05, "• auction_properties (33 attributes)", ha='center', va='center', color='#F1F5F9', fontsize=8)
    ax.text(3.05, 0.80, "• customer_leads (Ref #SK-XXXX)", ha='center', va='center', color='#F1F5F9', fontsize=8)
    ax.text(3.05, 0.55, "• admin_users & property_audit_logs", ha='center', va='center', color='#F1F5F9', fontsize=8)

    rect_ingest = patches.FancyBboxPatch((5.7, 0.4), 4.5, 1.3, boxstyle="round,pad=0.08,rounding_size=0.15",
                                         facecolor='#1E293B', edgecolor='#F59E0B', linewidth=1.5)
    ax.add_patch(rect_ingest)
    ax.text(7.95, 1.35, "Asynchronous Ingestion Worker", ha='center', va='center', color='#F59E0B', weight='bold', fontsize=10.5)
    ax.text(7.95, 1.05, "• Playwright Automated Bank Scrapers", ha='center', va='center', color='#F1F5F9', fontsize=8)
    ax.text(7.95, 0.80, "• Gemini 2.5 Flash Multimodal OCR", ha='center', va='center', color='#F1F5F9', fontsize=8)
    ax.text(7.95, 0.55, "• Pydantic Schema Validator", ha='center', va='center', color='#F1F5F9', fontsize=8)

    # Connections to DB
    ax.annotate('', xy=(3.05, 1.7), xytext=(4.5, 2.3), arrowprops=dict(arrowstyle="<|-|>", color="#071D35", lw=1.8))
    ax.annotate('', xy=(5.3, 1.05), xytext=(5.7, 1.05), arrowprops=dict(arrowstyle="-|>", color="#D9A62E", lw=2))

    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    plt.title("SKANDX Cloud System Topology & Subdomain Architecture", fontsize=14, weight='bold', pad=18, color="#071D35")
    plt.tight_layout()
    diagram_path = DIAGRAMS_DIR / "architecture_topology.png"
    plt.savefig(diagram_path, bbox_inches='tight', dpi=300)
    plt.close()
    return diagram_path


def generate_er_diagram():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_facecolor('#F8FAFC')
    fig.patch.set_facecolor('#F8FAFC')
    ax.axis('off')

    # Entity Boxes
    # 1. AUCTION_PROPERTIES (Top Left)
    rect_prop = patches.FancyBboxPatch((0.5, 3.2), 4.8, 3.8, boxstyle="round,pad=0.05,rounding_size=0.15",
                                       facecolor='#FFFFFF', edgecolor='#071D35', linewidth=2)
    ax.add_patch(rect_prop)
    # Header bar
    rect_prop_hdr = patches.Rectangle((0.5, 6.4), 4.8, 0.6, facecolor='#071D35')
    ax.add_patch(rect_prop_hdr)
    ax.text(2.9, 6.7, "AUCTION_PROPERTIES", ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=11)
    
    prop_fields = [
        ("id", "TEXT (PK)", "#071D35"),
        ("property_title", "TEXT", "#475569"),
        ("bank_name / branch", "TEXT", "#475569"),
        ("borrower_name", "TEXT", "#475569"),
        ("reserve_price_inr", "NUMERIC(14,2)", "#071D35"),
        ("emd_amount_inr (10%)", "NUMERIC(14,2)", "#071D35"),
        ("auction_date", "TIMESTAMPTZ", "#D97706"),
        ("possession_type", "TEXT (Physical/Symbolic)", "#475569"),
        ("area_sqft / locality", "NUMERIC / TEXT", "#475569"),
        ("auction_event_hash", "TEXT (Unique)", "#071D35"),
        ("review_status", "NEEDS_REVIEW / PUBLISHED", "#16A34A"),
        ("source_pdf_url", "TEXT", "#475569"),
    ]
    for idx, (f_name, f_type, col) in enumerate(prop_fields):
        y = 6.15 - idx * 0.24
        ax.text(0.7, y, f_name, ha='left', va='center', color=col, weight='bold' if 'PK' in f_type or 'Unique' in f_type else 'normal', fontsize=8)
        ax.text(5.1, y, f_type, ha='right', va='center', color='#64748B', fontsize=7.5)

    # 2. CUSTOMER_LEADS (Top Right)
    rect_lead = patches.FancyBboxPatch((6.0, 3.8), 4.5, 3.2, boxstyle="round,pad=0.05,rounding_size=0.15",
                                       facecolor='#FFFFFF', edgecolor='#D9A62E', linewidth=2)
    ax.add_patch(rect_lead)
    rect_lead_hdr = patches.Rectangle((6.0, 6.4), 4.5, 0.6, facecolor='#D9A62E')
    ax.add_patch(rect_lead_hdr)
    ax.text(8.25, 6.7, "CUSTOMER_LEADS", ha='center', va='center', color='#071D35', weight='bold', fontsize=11)

    lead_fields = [
        ("id", "TEXT (PK e.g. #SK-8492)", "#071D35"),
        ("property_id", "TEXT (FK)", "#071D35"),
        ("customer_name", "TEXT", "#475569"),
        ("phone", "TEXT", "#071D35"),
        ("email", "TEXT", "#475569"),
        ("inquiry_type", "Site Visit/Legal/Notice", "#475569"),
        ("notes", "TEXT", "#475569"),
        ("status", "NEW/IN_REVIEW/CLOSED", "#D97706"),
        ("created_at", "TIMESTAMPTZ", "#475569"),
    ]
    for idx, (f_name, f_type, col) in enumerate(lead_fields):
        y = 6.15 - idx * 0.25
        ax.text(6.2, y, f_name, ha='left', va='center', color=col, weight='bold' if 'PK' in f_type or 'FK' in f_type else 'normal', fontsize=8)
        ax.text(10.3, y, f_type, ha='right', va='center', color='#64748B', fontsize=7.5)

    # 3. ADMIN_USERS (Bottom Left)
    rect_usr = patches.FancyBboxPatch((0.5, 0.4), 4.8, 2.4, boxstyle="round,pad=0.05,rounding_size=0.15",
                                      facecolor='#FFFFFF', edgecolor='#10B981', linewidth=2)
    ax.add_patch(rect_usr)
    rect_usr_hdr = patches.Rectangle((0.5, 2.2), 4.8, 0.6, facecolor='#10B981')
    ax.add_patch(rect_usr_hdr)
    ax.text(2.9, 2.5, "ADMIN_USERS", ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=11)

    user_fields = [
        ("id", "TEXT (PK UUID)", "#071D35"),
        ("email", "TEXT (Unique)", "#071D35"),
        ("full_name", "TEXT", "#475569"),
        ("role", "ENUM (7 Admin Roles)", "#16A34A"),
        ("is_active", "BOOLEAN", "#475569"),
        ("created_at", "TIMESTAMPTZ", "#475569"),
    ]
    for idx, (f_name, f_type, col) in enumerate(user_fields):
        y = 1.95 - idx * 0.25
        ax.text(0.7, y, f_name, ha='left', va='center', color=col, weight='bold' if 'PK' in f_type or 'Unique' in f_type else 'normal', fontsize=8)
        ax.text(5.1, y, f_type, ha='right', va='center', color='#64748B', fontsize=7.5)

    # 4. PROPERTY_AUDIT_LOGS (Bottom Right)
    rect_aud = patches.FancyBboxPatch((6.0, 0.4), 4.5, 2.8, boxstyle="round,pad=0.05,rounding_size=0.15",
                                      facecolor='#FFFFFF', edgecolor='#64748B', linewidth=2)
    ax.add_patch(rect_aud)
    rect_aud_hdr = patches.Rectangle((6.0, 2.6), 4.5, 0.6, facecolor='#64748B')
    ax.add_patch(rect_aud_hdr)
    ax.text(8.25, 2.9, "PROPERTY_AUDIT_LOGS", ha='center', va='center', color='#FFFFFF', weight='bold', fontsize=11)

    audit_fields = [
        ("id", "TEXT (PK UUID)", "#071D35"),
        ("property_id", "TEXT (FK)", "#071D35"),
        ("admin_id", "TEXT (FK)", "#071D35"),
        ("admin_email", "TEXT", "#475569"),
        ("action", "VERIFY/REJECT/UPDATE", "#D97706"),
        ("changes", "JSONB (Field Diff)", "#475569"),
        ("created_at", "TIMESTAMPTZ", "#475569"),
    ]
    for idx, (f_name, f_type, col) in enumerate(audit_fields):
        y = 2.35 - idx * 0.25
        ax.text(6.2, y, f_name, ha='left', va='center', color=col, weight='bold' if 'PK' in f_type or 'FK' in f_type else 'normal', fontsize=8)
        ax.text(10.3, y, f_type, ha='right', va='center', color='#64748B', fontsize=7.5)

    # Relationship Arrows
    # Properties -> Leads (1 to Many)
    ax.annotate('', xy=(6.0, 5.2), xytext=(5.3, 5.2),
                arrowprops=dict(arrowstyle="<|-|>", color="#071D35", lw=2))
    ax.text(5.65, 5.4, "1 : N", ha='center', va='center', color='#071D35', weight='bold', fontsize=8.5)

    # Properties -> Audit Logs (1 to Many)
    ax.annotate('', xy=(6.0, 1.8), xytext=(4.5, 3.2),
                arrowprops=dict(arrowstyle="<|-|>", color="#071D35", lw=2))
    ax.text(5.1, 2.4, "1 : N", ha='center', va='center', color='#071D35', weight='bold', fontsize=8.5)

    # Admin Users -> Audit Logs (1 to Many)
    ax.annotate('', xy=(6.0, 1.4), xytext=(5.3, 1.4),
                arrowprops=dict(arrowstyle="<|-|>", color="#071D35", lw=2))
    ax.text(5.65, 1.6, "1 : N", ha='center', va='center', color='#071D35', weight='bold', fontsize=8.5)

    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    plt.title("SKANDX Database Entity-Relationship (ER) Architecture", fontsize=14, weight='bold', pad=18, color="#071D35")
    plt.tight_layout()
    diagram_path = DIAGRAMS_DIR / "database_er_diagram.png"
    plt.savefig(diagram_path, bbox_inches='tight', dpi=300)
    plt.close()
    return diagram_path


# ----------------------------------------------------------------------
# 2. WORD DOCUMENT STYLING HELPERS
# ----------------------------------------------------------------------

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_heading_with_accent(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(16)
    h.paragraph_format.space_after = Pt(6)
    run = h.runs[0]
    run.font.name = 'Calibri'
    if level == 1:
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(7, 29, 53)  # Navy
    elif level == 2:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(217, 119, 6) # Gold/Amber
    return h

def create_styled_table(doc, headers, data, col_widths=None):
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Style Header
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        set_cell_background(hdr_cells[i], "071D35")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(9.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Style Data Rows
    for row_idx, row_data in enumerate(data):
        row_cells = table.rows[row_idx + 1].cells
        bg_color = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = str(cell_value)
            set_cell_background(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=90, bottom=90, left=140, right=140)
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = 'Calibri'
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(30, 41, 59)

    # Set column widths if provided
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    return table

def add_callout_box(doc, title, text, bg_color="FEF3C7", border_color="D97706"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    cell.width = Inches(6.5)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r_title = p.add_run(f"📌 {title}\n")
    r_title.font.name = 'Calibri'
    r_title.font.bold = True
    r_title.font.size = Pt(10)
    r_title.font.color.rgb = RGBColor(180, 83, 9)

    r_text = p.add_run(text)
    r_text.font.name = 'Calibri'
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = RGBColor(71, 85, 105)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


# ----------------------------------------------------------------------
# 3. BUILD COMPLETE PHASE 1 WORD DOCUMENT
# ----------------------------------------------------------------------

def build_phase1_word_document():
    print("Generating diagrams...")
    workflow_img = generate_workflow_diagram()
    arch_img = generate_architecture_diagram()
    er_img = generate_er_diagram()

    print("Assembling Word document...")
    doc = Document()

    # Page Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    # Document Header / Banner Block
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    r_tag = title_p.add_run("OFFICIAL CLIENT DELIVERABLE REPORT • PHASE 1\n")
    r_tag.font.name = 'Calibri'
    r_tag.font.size = Pt(9.5)
    r_tag.font.bold = True
    r_tag.font.color.rgb = RGBColor(217, 119, 6)

    r_main = title_p.add_run("Verified Distressed Property Discovery & Buyer Assistance Platform\n")
    r_main.font.name = 'Calibri'
    r_main.font.size = Pt(20)
    r_main.font.bold = True
    r_main.font.color.rgb = RGBColor(7, 29, 53)

    r_sub = title_p.add_run("Phase 1 Completion & Sign-off Package: Planning, Requirements & UI/UX\n")
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)

    # Document Metadata Table
    meta_headers = ["Project Name", "Phase Milestone", "Target Platforms", "Milestone Payment Due"]
    meta_data = [
        ["SKANDX Distressed Property Platform", "Phase 1: Planning, Requirement & UI/UX", "Website + Android + iOS + Admin Panel", "10% (₹15,000 – ₹17,500)"]
    ]
    create_styled_table(doc, meta_headers, meta_data, col_widths=[1.8, 1.8, 1.8, 1.3])

    add_callout_box(
        doc,
        "Executive Summary: Phase 1 Handover Status",
        "This document formally presents the completed deliverables for Phase 1 of the 50-Day development roadmap. All seven mandatory deliverables—Requirements Confirmation, User Roles & Permissions, 33-Attribute Database Architecture with ER Diagram, Responsive UI/UX Design System, Verification & Lead Workflows, Technical Topology, and Live Working Demo—have been fully produced, tested, and verified."
    )

    # -------------------------------------------------------------
    # SECTION 1: DELIVERABLES CHECKLIST
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "1. Phase 1 Deliverables Verification Matrix", level=1)
    
    chk_headers = ["#", "Proposal Deliverable", "Technical Output in Codebase", "Verification Status"]
    chk_data = [
        ["1", "Requirement Confirmation & Workflow", "10-stage distressed asset lifecycle from scraper ingestion to official bank bidding", "100% COMPLETE"],
        ["2", "User Roles & Permission Planning", "7 distinct operational roles defined with granular CRUD matrix and PostgreSQL ENUMs", "100% COMPLETE"],
        ["3", "Database Structure & ER Diagram", "33-attribute property table, customer leads, admin users, audit log & visual ER model", "100% COMPLETE"],
        ["4", "UI/UX Design for Web & Mobile", "Dark luxury navy & gold responsive SPA in React 19 + Vite with mobile drawers & modals", "100% COMPLETE"],
        ["5", "Property Verification & Buyer Workflow", "Admin split-pane notice verification desk, streaming PDF proxy, & inquiry capture engine", "100% COMPLETE"],
        ["6", "Technical Architecture & Plan", "Decoupled REST API, HMAC-SHA256 authentication, Pydantic schemas, & Gemini OCR", "100% COMPLETE"],
        ["7", "Phase-End Draft / Demo Presentation", "Live working web platform with 1-Click Test Mode bypass for password-free evaluation", "100% COMPLETE"],
    ]
    create_styled_table(doc, chk_headers, chk_data, col_widths=[0.4, 2.0, 3.0, 1.3])

    # -------------------------------------------------------------
    # SECTION 2: 10-STAGE BUSINESS WORKFLOW & DIAGRAM
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "2. Main Business Workflow (10-Stage Lifecycle)", level=1)
    doc.add_paragraph(
        "Under the SARFAESI Act 2002, Indian banks seize defaulted assets and sell them at 20% to 40% below market value. The platform operates as a verified discovery and buyer-assistance service. The statutory bidding remains with the bank, preserving full legal integrity."
    )

    # Embed Workflow Diagram
    doc.add_picture(str(workflow_img), width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p = doc.add_paragraph("Figure 1: End-to-End 10-Stage Distressed Property Lifecycle & Lead Concierge Workflow")
    caption_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p.runs[0].font.size = Pt(8.5)
    caption_p.runs[0].font.italic = True
    caption_p.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    flow_headers = ["Stage", "Operational Title", "Primary System Component", "Compliance & Business Logic"]
    flow_data = [
        ["1", "Property Source", "Playwright Web Crawlers", "Crawl official public bank portals (IBAPI, e-Bikray, Bank Gazettes)."],
        ["2", "Property Collection", "Ingestion Pipeline Worker", "Download raw scanned notice PDFs and extract tender circular metadata."],
        ["3", "AI Multimodal OCR", "Gemini 2.5 Flash Vision", "Extract 33 statutory fields: Reserve Price, 10% EMD, auction date, survey no."],
        ["4", "Back-Office Verification", "Admin Verification Desk", "Officers cross-verify extracted OCR values against original circular PDF."],
        ["5", "Publishing to Marketplace", "Public Marketplace", "Listing published to skandx.com with green '✓ Verified' compliance stamp."],
        ["6", "Buyer Inquiry Capture", "Contact Modal Desk", "Buyer submits name/phone/type; generates Reference Code (e.g. #SK-8492)."],
        ["7", "Buyer Verification", "Concierge Desk Outreach", "Concierge contacts buyer within 15 minutes; confirms budget readiness."],
        ["8", "Meeting & Site Visit", "Liaison Coordination", "Officer coordinates inspection date directly with the foreclosing bank branch."],
        ["9", "Official Statutory Auction", "Statutory Auction Portal", "Buyer deposits 10% EMD caution money and bids on official bank portal."],
        ["10", "Post-Purchase Support", "Title Concierge Desk", "Optional assistance with Sale Certificate registration and physical possession."],
    ]
    create_styled_table(doc, flow_headers, flow_data, col_widths=[0.5, 1.8, 1.9, 2.5])

    # -------------------------------------------------------------
    # SECTION 3: USER ROLES & PERMISSIONS MATRIX
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "3. Primary User Roles & Permission Matrix (Proposal Section 7)", level=1)
    doc.add_paragraph(
        "To enforce institutional security and operational segregation of duties, seven dedicated user roles are implemented in PostgreSQL migration 003_create_admin_roles_and_audit.sql:"
    )

    role_headers = ["Role Name", "Target Department", "System Access Level", "Permitted System Capabilities"]
    role_data = [
        ["Super Admin", "Executive Management", "Full System (Global)", "Manage staff accounts, grant roles, override verification decisions, view raw audit logs."],
        ["Property / Acquisition", "Data Operations", "Ingestion & Sources", "Trigger crawlers, upload raw auction notice PDFs, record source URLs and bank contact points."],
        ["Verification Officer", "Back-Office Verification", "Verification Desk", "Review pending OCR records against PDF circular, edit fields, approve (PUBLISHED) or reject."],
        ["Legal Reviewer", "Legal Department", "Legal Due Diligence", "Audit title encumbrances, review DRT / SARFAESI dispute history, attach legal notes and risk tags."],
        ["Field Executive", "Ground Operations", "Inspection Desk", "Upload physical site visit photos, neighborhood condition notes, verify physical vs symbolic possession."],
        ["Relationship / Buyer", "Concierge Desk", "Leads & Inquiries", "Receive customer leads, conduct 15-minute callbacks, update lead lifecycle (NEW -> CLOSED)."],
        ["Customer / Buyer", "General Public", "Public Marketplace", "Browse verified listings, filter by budget/bank/location, download brochures, submit inquiries."],
    ]
    create_styled_table(doc, role_headers, role_data, col_widths=[1.5, 1.5, 1.4, 2.3])

    # -------------------------------------------------------------
    # SECTION 4: DATABASE ARCHITECTURE & ER DIAGRAM
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "4. Database Architecture & Visual ER Diagram", level=1)
    doc.add_paragraph(
        "The relational database schema is built in PostgreSQL (Supabase) with Row Level Security (RLS) policies ensuring customers only read published listings while administrative mutations require service-role permissions."
    )

    # Embed ER Diagram
    doc.add_picture(str(er_img), width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p2 = doc.add_paragraph("Figure 2: PostgreSQL Database Entity-Relationship (ER) Architecture")
    caption_p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p2.runs[0].font.size = Pt(8.5)
    caption_p2.runs[0].font.italic = True
    caption_p2.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph("Summary of Production Database Migrations:")
    db_headers = ["Migration File", "Primary Table", "Key Attributes & Purpose", "Security Configuration"]
    db_data = [
        ["001_create_auction_properties.sql", "auction_properties", "33 statutory columns (Reserve Price, 10% EMD, survey numbers, possession, event hash)", "RLS Public Read for review_status = 'PUBLISHED'"],
        ["002_create_customer_leads.sql", "customer_leads", "Lead capture with generated IDs (#SK-XXXX), phone, email, inquiry type, status", "RLS Public Insert with check, Service Role Admin Access"],
        ["003_create_admin_roles_and_audit.sql", "admin_users & audit_logs", "7 admin role enums, user accounts, and immutable audit logs with JSONB diffs", "RLS Service Role access, foreign key cascades"],
    ]
    create_styled_table(doc, db_headers, db_data, col_widths=[2.1, 1.4, 2.0, 1.3])

    # -------------------------------------------------------------
    # SECTION 5: UI/UX DESIGN SYSTEM SPECIFICATION
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "5. UI/UX Design System Specification (Web + Mobile)", level=1)
    doc.add_paragraph(
        "The frontend user experience is built in React 19 + Vite using a luxury financial design system engineered specifically for high-value banking asset transactions:"
    )

    ui_headers = ["Design Element", "Color Code / Spec", "Psychological & Functional Role"]
    ui_data = [
        ["Primary Navy", "#071D35 / #0A2540", "Conveys institutional banking security, legal authority, and enterprise trust."],
        ["Gold / Amber Accent", "#D9A62E / #E8B849", "Represents premium distressed investment opportunities and high-priority CTAs."],
        ["Verified Green Stamp", "#16A34A / #22C55E", "Provides instant visual proof that property has undergone human and statutory legal review."],
        ["Alert / Cutoff Red", "#DC2626 / #EF4444", "Urgent notice for EMD deposit deadlines and statutory auction countdowns."],
        ["Desktop Viewport", "> 1024px", "Multi-column grid, split-pane PDF verification desk, comprehensive property filter bar."],
        ["Mobile Viewport", "< 768px (Android/iOS)", "Bottom navigation drawer, touch-friendly inquiry sheet, mobile search drawer."],
    ]
    create_styled_table(doc, ui_headers, ui_data, col_widths=[1.5, 1.7, 3.5])

    # -------------------------------------------------------------
    # SECTION 6: TECHNICAL ARCHITECTURE & TOPOLOGY
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "6. Technical Architecture & Security Topology", level=1)
    doc.add_paragraph(
        "The system deploys a decoupled microservices architecture with subdomain-level segregation between public buyers and administrative personnel:"
    )

    # Embed Architecture Diagram
    doc.add_picture(str(arch_img), width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p3 = doc.add_paragraph("Figure 3: SKANDX Cloud System Topology, Subdomain Routing & Asynchronous Workers")
    caption_p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p3.runs[0].font.size = Pt(8.5)
    caption_p3.runs[0].font.italic = True
    caption_p3.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    add_callout_box(
        doc,
        "Enterprise Security & Compliance Protections",
        "• Cryptographic HMAC-SHA256 Token Auth: Protects back-office mutation endpoints against session hijacking.\n• Notice PDF Streaming Proxy (/api/admin/pdf-proxy): Allows viewing third-party bank tender notices without CORS blocking.\n• Zero-Loss Offline Queue: Caches buyer inquiries in localStorage if connection drops and auto-flushes on reconnect.\n• Rate-Limiting: Contact endpoints are rate-limited to prevent automated spam bot attacks."
    )

    # -------------------------------------------------------------
    # SECTION 7: CLIENT DEMO WALKTHROUGH GUIDE
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "7. Client Live Demo Walkthrough Guide (5-Minute Script)", level=1)
    doc.add_paragraph(
        "A step-by-step presentation script to demonstrate the completed Phase 1 application to the client:"
    )

    demo_headers = ["Step", "Action to Demonstrate", "What the Client Sees & Evaluates"]
    demo_data = [
        ["1", "Open Customer Marketplace (skandx.com)", "Show luxury navy & gold design, bank logo badges (SBI, Canara), and verified asset inventory."],
        ["2", "Demonstrate Smart Filters", "Filter by bank, asset type (Residential/Commercial), and budget range (₹50 Lakhs – ₹1 Crore)."],
        ["3", "Submit Lead Inquiry", "Click 'Contact' on any listing. Enter name/phone, select 'Site Inspection', and submit."],
        ["4", "Show Inquiry Confirmation", "Show generated Reference Code (#SK-8492), callback ETA ('Within 15 minutes'), and 1-click WhatsApp."],
        ["5", "Switch to Mobile Viewport", "Press F12 in Chrome to show flawless mobile responsiveness on iPhone/Android screens."],
        ["6", "Open Admin Desk (admin.skandx.com)", "Click '⚡ Test Mode: Go Directly to Admin Page' for immediate password-free evaluation."],
        ["7", "Demonstrate Verification Desk", "Show pending listings in queue, split-viewer with tender PDF on left and OCR editable fields on right."],
        ["8", "Verify & Publish Listing", "Click 'Verify & Publish'—demonstrate real-time state transition into verified public inventory."],
        ["9", "Review Buyer Leads Desk", "Show inquiry submitted in Step 3 appearing in real-time on the administrative lead dashboard."],
    ]
    create_styled_table(doc, demo_headers, demo_data, col_widths=[0.5, 2.4, 3.8])

    # -------------------------------------------------------------
    # SECTION 8: MILESTONE SIGN-OFF & INVOICE TRIGGER
    # -------------------------------------------------------------
    add_heading_with_accent(doc, "8. Milestone Sign-off & Payment Release Acceptance", level=1)
    doc.add_paragraph(
        "By signing below, the client confirms that all Phase 1 deliverables (Planning, Requirements & UI/UX) have been demonstrated, verified, and accepted in accordance with the Project Proposal:"
    )

    sign_headers = ["Phase 1 Milestone Deliverable", "Agreed Completion Status", "Client Verification"]
    sign_data = [
        ["Requirements & 10-Stage Lifecycle Documented", "100% Complete (Section 2)", "[  ] ACCEPTED & APPROVED"],
        ["User Roles & Access Control Matrix (7 Roles)", "100% Complete (Section 3)", "[  ] ACCEPTED & APPROVED"],
        ["Database Schema & Visual ER Architecture", "100% Complete (Section 4)", "[  ] ACCEPTED & APPROVED"],
        ["Responsive UI/UX Design System (Web + Mobile)", "100% Complete (Section 5)", "[  ] ACCEPTED & APPROVED"],
        ["Technical Architecture & Security Topology", "100% Complete (Section 6)", "[  ] ACCEPTED & APPROVED"],
        ["Live Interactive Clickable Demo Presented", "100% Complete (Section 7)", "[  ] ACCEPTED & APPROVED"],
    ]
    create_styled_table(doc, sign_headers, sign_data, col_widths=[2.8, 1.8, 2.1])

    # Signatures Table
    sig_headers = ["Party", "Representative Name", "Signature", "Approval Date"]
    sig_data = [
        ["Client Reviewer", "___________________________", "___________________________", "____ / ____ / 2026"],
        ["Project Lead", "Raj (SKANDX Tech Lead)", "___________________________", "____ / ____ / 2026"],
    ]
    create_styled_table(doc, sig_headers, sig_data, col_widths=[1.5, 2.0, 2.0, 1.2])

    p_inv = doc.add_paragraph()
    r_inv = p_inv.add_run("Milestone Payment Release: 10% of Project Value = ₹15,000 – ₹17,500 due upon execution of this sign-off sheet.")
    r_inv.font.name = 'Calibri'
    r_inv.font.bold = True
    r_inv.font.size = Pt(10.5)
    r_inv.font.color.rgb = RGBColor(7, 29, 53)

    print(f"Saving report to {DOCX_PATH}...")
    doc.save(DOCX_PATH)
    print("Report generated successfully!")
    return DOCX_PATH

if __name__ == "__main__":
    build_phase1_word_document()
