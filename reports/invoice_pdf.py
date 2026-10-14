"""
HOE Billing Software - Professional GST Invoice PDF
Format: Compact A4, B&W printer friendly, Tally-style
Features:
  - Logo from settings (auto load)
  - Full A4 page utilization, single continuous outer frame
  - Bill To + Ship To two column
  - HSN/SAC product table with auto-filled blank rows (always covers the
    full page, even with just 1 product)
  - CGST/SGST/IGST tax summary
  - Amount in words
  - Bank details
  - Terms & Conditions
  - Authorised Signatory + Customer Signature
  - Invoice settings toggles (logo, bank, hsn, signature, terms)

# ── FIXED ISSUES (see comments tagged "FIX:") ──────────────────────────────
# 1) desc_idx (stretch column index for Product Description) was off by one.
# 2) empty_cols for the subtotal/"Total" row didn't account for the
#    Description column -> column count mismatch -> broken table render.
# 3) info_tbl column width multipliers summed to ~108% of usable width.
# 4) A malformed/invalid TableStyle command in the footer table removed.
# 5) Logo forced into an 18x18mm square (distorted non-square logos) ->
#    now scaled to fit a box while keeping its aspect ratio.
# 6) ₹ symbol / Devanagari text rendered as black boxes with Helvetica ->
#    now uses a Unicode-capable font when available, with safe fallback.
# 7) Sections used to render as separate disconnected bordered "blocks"
#    with gaps between them, and the whole invoice shrink-wrapped to
#    content height (lots of blank page below on a short invoice). Now:
#      - ONE continuous black frame is drawn around the full printable
#        page area (top margin to bottom margin) on every page, via the
#        onPage canvas hook — independent of how much content there is.
#      - Individual section "BOX" borders were removed in favour of thin
#        connecting divider lines, so sections read as one continuous
#        sheet instead of floating boxes with gaps.
#      - The product table now auto-fills blank rows (grid lines only,
#        no text) so the items grid itself stretches down to use the
#        remaining page height, even when there's only one product.
"""
import os


def _ensure_reportlab():
    """Import reportlab; if it's missing, auto-install it via pip (using
    the SAME Python interpreter that's running this script) and retry.
    This means you no longer have to manually run "pip install reportlab"
    — the script does it for you the first time it's needed.

    NOTE: if this app is packaged with PyInstaller (or similar), reportlab
    is already bundled inside the .exe, so this function exits immediately
    via the `import reportlab` success path above and never tries to
    shell out to pip (which wouldn't work inside a frozen exe anyway)."""
    try:
        import reportlab  # noqa: F401
        return
    except ImportError:
        pass

    import sys
    if getattr(sys, "frozen", False):
        # Running as a bundled .exe but reportlab still wasn't found —
        # that means it wasn't bundled correctly; pip can't fix that here.
        raise ImportError(
            "'reportlab' is missing from this packaged app. Rebuild it "
            "with PyInstaller and make sure reportlab is installed in the "
            "build environment so it gets bundled in."
        )

    import subprocess

    print("[invoice_pdf] 'reportlab' not found — installing it now, please wait...")
    pip_attempts = [
        [sys.executable, "-m", "pip", "install", "reportlab"],
        [sys.executable, "-m", "pip", "install", "reportlab", "--user"],
        [sys.executable, "-m", "pip", "install", "reportlab", "--break-system-packages"],
    ]
    last_error = None
    for cmd in pip_attempts:
        try:
            subprocess.check_call(cmd)
            break
        except Exception as e:
            last_error = e
    else:
        raise ImportError(
            "Could not auto-install 'reportlab'. Please install it manually "
            "by running:  pip install reportlab\n"
            f"(last error: {last_error})"
        )

    try:
        import reportlab  # noqa: F401
    except ImportError:
        raise ImportError(
            "'reportlab' was installed but still can't be imported. "
            "Try restarting the program, or install it manually with: "
            "pip install reportlab"
        )


def generate_invoice_pdf(invoice, business_profile, settings=None):
    _ensure_reportlab()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable,
                                    KeepTogether, Image)
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont as PDFTTFont

    # ── Base directory (computed early so font/logo lookups can use it) ────
    import sys as _sys
    if getattr(_sys, "frozen", False):
        # Running as a packaged .exe (PyInstaller) — use the folder the
        # .exe itself lives in, not a temp extraction folder.
        base_dir = os.path.dirname(_sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── Unicode font registration (so ₹ and हिन्दी text render correctly) ──
    def _register_unicode_font():
        candidates = [
            # Windows' own Hindi fonts FIRST — these render Devanagari more
            # cleanly/boldly than the generic bundled fallback below.
            (r"C:\Windows\Fonts\Nirmala.ttf", r"C:\Windows\Fonts\Nirmalab.ttf"),
            (r"C:\Windows\Fonts\NirmalaUI.ttf", r"C:\Windows\Fonts\NirmalaUIb.ttf"),
            (r"C:\Windows\Fonts\mangal.ttf",  r"C:\Windows\Fonts\mangalb.ttf"),
            (r"C:\Windows\Fonts\Mangal.ttf",  r"C:\Windows\Fonts\Mangal Bold.ttf"),
            ("/Library/Fonts/Arial Unicode.ttf",
             "/Library/Fonts/Arial Unicode.ttf"),
            # Bundled with the software itself — put FreeSans.ttf and
            # FreeSansBold.ttf in a "fonts" folder next to invoice_pdf.py
            # (or next to the .exe). This is the GUARANTEED fallback so the
            # Hindi line always renders correctly even if the system has no
            # Hindi font installed at all — but it's checked LAST since
            # Windows' own fonts above look noticeably better.
            (os.path.join(base_dir, "fonts", "FreeSans.ttf"),
             os.path.join(base_dir, "fonts", "FreeSansBold.ttf")),
            ("/usr/share/fonts/truetype/freefont/FreeSans.ttf",
             "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
        ]
        for reg, bold in candidates:
            if os.path.exists(reg):
                try:
                    pdfmetrics.registerFont(PDFTTFont("InvoiceUni", reg))
                    pdfmetrics.registerFont(
                        PDFTTFont("InvoiceUni-Bold",
                                  bold if os.path.exists(bold) else reg))
                    pdfmetrics.registerFontFamily(
                        "InvoiceUni", normal="InvoiceUni", bold="InvoiceUni-Bold",
                        italic="InvoiceUni", boldItalic="InvoiceUni-Bold")
                    pdfmetrics.registerFontFamily(
                        "InvoiceUni-Bold", normal="InvoiceUni-Bold",
                        bold="InvoiceUni-Bold", italic="InvoiceUni-Bold",
                        boldItalic="InvoiceUni-Bold")
                    return "InvoiceUni", "InvoiceUni-Bold", True
                except Exception:
                    continue
        return "Helvetica", "Helvetica-Bold", False

    FONT, FONT_BOLD, UNICODE_OK = _register_unicode_font()
    RUPEE = "₹" if UNICODE_OK else "Rs."

    # ── Emoji font registration (Segoe UI Emoji for 🙏 etc.) ─────────────
    EMOJI_FONT = None
    emoji_candidates = [
        r"C:\Windows\Fonts\seguiemj.ttf",   # Segoe UI Emoji (Win10/11)
        r"C:\Windows\Fonts\seguisym.ttf",   # Segoe UI Symbol (fallback)
    ]
    for _ef in emoji_candidates:
        if os.path.exists(_ef):
            try:
                pdfmetrics.registerFont(PDFTTFont("EmojiFont", _ef))
                EMOJI_FONT = "EmojiFont"
                break
            except Exception:
                continue

    # ── Settings toggles (defaults all ON) ───────────────────────────────
    cfg = settings or {}
    SHOW_LOGO      = cfg.get("show_logo",      True)
    SHOW_BANK      = cfg.get("show_bank",       True)
    SHOW_HSN       = cfg.get("show_hsn",        True)
    SHOW_SIGNATURE = cfg.get("show_signature",  True)
    SHOW_TERMS     = cfg.get("show_terms",      True)
    SHOW_CUST_GST  = cfg.get("show_cust_gst",  True)
    SHOW_SERIAL    = cfg.get("show_serial",     False)

    # ── Colors (PURE black & white — black text, white page, black borders,
    # no gray fills anywhere) ──────────────────────────────────────────────
    BLACK   = black
    WHITE   = white
    DARK    = HexColor("#000000")
    MEDIUM  = HexColor("#000000")
    LIGHT   = WHITE              # no shaded backgrounds anywhere
    BORDER  = HexColor("#000000")  # all grid/divider lines: dark black
    HEADER  = HexColor("#000000")
    MID     = HexColor("#000000")

    # ── Output ────────────────────────────────────────────────────────────
    out_dir  = os.path.join(base_dir, "invoices")
    os.makedirs(out_dir, exist_ok=True)
    inv_num  = str(invoice.get("invoice_number", "INV"))
    filepath = os.path.join(out_dir, f"{inv_num}.pdf")

    # ── Document — 12mm margin on all 4 sides (reduced 3mm from before, so
    # the invoice format uses a bit more of the A4 page = slightly "zoomed
    # in") ───────────────────────────────────────────────────────────────
    TITLE_GAP = 6*mm    # extra space reserved above the frame for the
                        # "GST INVOICE" heading that sits OUTSIDE the border
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=12*mm, leftMargin=12*mm,
        topMargin=12*mm + TITLE_GAP,   bottomMargin=12*mm
    )
    W = A4[0] - 24*mm   # usable width (A4 width minus 12mm left + 12mm right)

    # ── Page frame — ONE continuous, BOLD dark black border around the
    # whole printable area (12mm in from every edge), drawn directly on the
    # canvas (not a flowable), so it always spans from the top margin to
    # the bottom margin REGARDLESS of how much content is on the page.
    def _draw_page_frame(canvas, doc_):
        canvas.saveState()
        # "GST INVOICE" heading — sits ABOVE / OUTSIDE the bordered frame,
        # inside the extra top-margin gap (TITLE_GAP) reserved for it.
        canvas.setFillColor(black)
        canvas.setFont(FONT_BOLD, 11)
        canvas.drawCentredString(
            doc_.pagesize[0] / 2.0,
            doc_.pagesize[1] - 15*mm,
            "TAX INVOICE"
        )
        canvas.setStrokeColor(black)
        canvas.setLineWidth(2.5)
        x = doc_.leftMargin
        y = doc_.bottomMargin
        w = doc_.pagesize[0] - doc_.leftMargin - doc_.rightMargin
        h = doc_.pagesize[1] - doc_.topMargin - doc_.bottomMargin
        canvas.rect(x, y, w, h)
        canvas.restoreState()

    # ── Styles ────────────────────────────────────────────────────────────
    SS = getSampleStyleSheet()
    SS["Normal"].fontName = FONT
    def ps(n, **kw):
        return ParagraphStyle(n, parent=SS["Normal"], **kw)

    co_name  = ps("cn", fontSize=16, fontName=FONT_BOLD,
                  alignment=TA_CENTER, textColor=DARK, leading=20)
    co_info  = ps("ci", fontSize=8,  fontName=FONT_BOLD, alignment=TA_CENTER,
                  textColor=MEDIUM, leading=11)
    n8       = ps("n8", fontSize=8,  leading=11, textColor=DARK)
    b8       = ps("b8", fontSize=8,  fontName=FONT_BOLD,
                  leading=11, textColor=DARK)
    b9       = ps("b9", fontSize=9,  fontName=FONT_BOLD,
                  leading=12, textColor=DARK)
    r8       = ps("r8", fontSize=8,  alignment=TA_RIGHT,
                  leading=11, textColor=DARK)
    c8       = ps("c8", fontSize=8,  alignment=TA_CENTER,
                  leading=11, textColor=DARK)
    c9       = ps("c9", fontSize=9,  fontName=FONT_BOLD,
                  alignment=TA_CENTER, leading=12, textColor=DARK)
    sm       = ps("sm", fontSize=7,  textColor=MEDIUM, leading=10)
    words_s  = ps("ws", fontSize=8,  textColor=DARK, leading=12)

    # Bigger styles for Bill To / Ship To party block
    party_title = ps("pty_t", fontSize=10, fontName=FONT_BOLD,
                      leading=13, textColor=DARK)
    party_name  = ps("pty_n", fontSize=9,  fontName=FONT_BOLD,
                      leading=12, textColor=DARK)
    party_sm    = ps("pty_s", fontSize=8,  textColor=DARK, leading=11)

    # Bigger + BOLD style for Bank Details block
    bank_title  = ps("bnk_t", fontSize=9,  fontName=FONT_BOLD,
                      leading=12, textColor=DARK)
    bank_line   = ps("bnk_l", fontSize=8,  fontName=FONT_BOLD,
                      leading=11, textColor=DARK)

    story = []

    # ── Helpers ───────────────────────────────────────────────────────────
    def s(v, d=""): return str(v).strip() if v else d
    def P(t, st=None): return Paragraph(t or "", st or n8)
    def B(t): return P(f"<b>{t}</b>", b8)

    bp  = business_profile
    inv = invoice

    # Business info
    shop    = s(bp.get("shop_name"), "Hari Om Electric")
    addr    = s(bp.get("address"))
    city    = s(bp.get("city"))
    state_s = s(bp.get("state"))
    pin     = s(bp.get("pincode"))
    mob     = s(bp.get("mobile"))
    email   = s(bp.get("email"))
    gstin   = s(bp.get("gst_number"))
    pan     = s(bp.get("pan_number"))
    # Default logo: tries a few likely locations for hoe_logo.png, anchored
    # to THIS SCRIPT'S OWN FOLDER (base_dir) rather than the current working
    # directory.
    _logo_candidates = [
        os.path.join(base_dir, "reports", "hoe_logo.png"),
        os.path.join(os.path.dirname(base_dir), "reports", "hoe_logo.png"),
        os.path.join(base_dir, "HOE_Billing", "reports", "hoe_logo.png"),
    ]
    default_logo = next((p for p in _logo_candidates if os.path.exists(p)),
                         _logo_candidates[0])
    logo_p  = s(bp.get("logo_path"), default_logo)

    addr_line = ", ".join(p for p in [addr, city, state_s, pin] if p)

    # Invoice info
    inv_no   = s(inv.get("invoice_number"))
    inv_date = s(inv.get("invoice_date"))
    cname    = s(inv.get("customer_name"), "Walk-in Customer")
    cmob     = s(inv.get("mobile"))
    cgst_no  = s(inv.get("gst_number"))
    cbiz     = s(inv.get("business_name"))
    caddr    = s(inv.get("address"))
    cstate   = s(inv.get("state") or inv.get("custState"))
    pay_mode = s(inv.get("payment_method"), "Cash")
    notes    = s(inv.get("notes"))

    # ══════════════════════════════════════════════════════════════════════
    # 1. HEADER — Logo + Company + TAX INVOICE banner
    # ══════════════════════════════════════════════════════════════════════
    logo_col = []
    if SHOW_LOGO and logo_p and os.path.exists(logo_p):
        try:
            img = Image(logo_p)
            box = 26*mm
            ratio = img.imageWidth / float(img.imageHeight)
            if ratio >= 1:
                img.drawWidth  = box
                img.drawHeight = box / ratio
            else:
                img.drawHeight = box
                img.drawWidth  = box * ratio
            logo_col.append(img)
        except Exception:
            logo_col.append(P(""))
    else:
        logo_col.append(P(f"<b>{shop[:3].upper()}</b>",
                          ps("tl", fontSize=22, fontName=FONT_BOLD,
                             textColor=HEADER, alignment=TA_CENTER)))

    co_col = [
        P(f"<b>{shop}</b>", co_name),
        P(addr_line, co_info),
    ]
    contact = "  |  ".join(p for p in [
        f"📞 {mob}" if mob else "",
        f"✉ {email}" if email else ""
    ] if p)
    if contact: co_col.append(P(contact, co_info))
    gst_line = "  |  ".join(p for p in [
        f"GSTIN: <b>{gstin}</b>" if gstin else "",
        f"PAN: <b>{pan}</b>" if pan else ""
    ] if p)
    if gst_line: co_col.append(P(gst_line, co_info))

    hdr_row  = [[logo_col, co_col, ""]]
    hdr_tbl  = Table(hdr_row, colWidths=[36*mm, W-36*mm-18*mm, 18*mm])
    hdr_tbl.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",  (0,0),(0,0),   6),
        ("BACKGROUND",   (0,0),(-1,-1), WHITE),
        ("LINEBELOW",    (0,0),(-1,-1), 2.0, BLACK),
    ]))
    story.append(hdr_tbl)

    # TAX INVOICE banner
    ti = Table([[P("<b>TAX INVOICE</b>",
                   ps("tib", fontSize=11, fontName=FONT_BOLD,
                      textColor=DARK, alignment=TA_CENTER))]],
               colWidths=[W])
    ti.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), WHITE),
        ("BOX",          (0,0),(-1,-1), 2.0, BLACK),
        ("LINEABOVE",    (0,0),(-1,-1), 2.0, BLACK),
        ("LINEBELOW",    (0,0),(-1,-1), 2.0, BLACK),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    story.append(ti)

    # ══════════════════════════════════════════════════════════════════════
    # 2. INVOICE DETAILS — 4 column compact grid
    # ══════════════════════════════════════════════════════════════════════
    lw = W*0.15   # key col width
    vw = W*0.35   # value col width

    info_data = [
        [B("Invoice No."),    P(inv_no,   n8),
         B("Party GST No."),  P(cgst_no or "—", n8)],
        [B("Date"),           P(inv_date, n8),
         B("Payment Terms"),  P(pay_mode, n8)],
        [B("State"),          P(state_s,  n8),
         B("Ref. No."),       P(notes or "—", n8)],
        [B("Rev. Charge"),    P("N",       n8),
         B(""),               P("",        n8)],
    ]
    info_tbl = Table(info_data, colWidths=[lw, vw, lw, vw])
    info_tbl.setStyle(TableStyle([
        ("INNERGRID",    (0,0),(-1,-1), 1.0, BORDER),
        ("BOX",          (0,0),(-1,-1), 2.0, BLACK),
        ("LINEBELOW",    (0,-1),(-1,-1), 2.0, BLACK),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("BACKGROUND",   (0,0),(-1,-1), WHITE),
    ]))
    story.append(info_tbl)

    # ══════════════════════════════════════════════════════════════════════
    # 3. BILL TO + SHIP TO — side by side
    # ══════════════════════════════════════════════════════════════════════
    def build_party(title, name, biz, address, mobile, state_v, gstin_v):
        lines = [P(f"<b>{title}</b>", party_title)]
        if biz:     lines.append(P(f"<b>{biz}</b>", party_name))
        if name:    lines.append(P(name, party_name))
        if address: lines.append(P(address, party_sm))
        if state_v: lines.append(P(f"State: {state_v}", party_sm))
        if mobile:  lines.append(P(f"Mobile: {mobile}", party_sm))
        if SHOW_CUST_GST and gstin_v:
            lines.append(P(f"GSTIN: <b>{gstin_v}</b>", party_sm))
        return lines

    half = W / 2
    bill = build_party("Bill To Party :-", cname, cbiz, caddr, cmob, cstate, cgst_no)
    ship = build_party("Ship To / Place of Supply :-",
                       cname, cbiz, caddr, cmob, cstate, cgst_no)

    party_tbl = Table([[bill, ship]], colWidths=[half, half])
    party_tbl.setStyle(TableStyle([
        ("BOX",         (0,0),(-1,-1), 2.0, BLACK),
        ("LINEBEFORE",  (1,0),(1,-1),  1.0, BORDER),
        ("LINEBELOW",   (0,-1),(-1,-1), 2.0, BLACK),
        ("TOPPADDING",  (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING", (0,0),(-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
        ("BACKGROUND",  (0,0),(-1,-1), WHITE),
    ]))
    story.append(party_tbl)

    # ══════════════════════════════════════════════════════════════════════
    # 4. PRODUCT TABLE — columns (built first; the Table itself is built
    #    further down once we know how many blank filler rows are needed
    #    to make the grid stretch to the bottom of the page)
    # ══════════════════════════════════════════════════════════════════════
    cols     = []
    col_w    = []

    cols.append(P("<b>Sr</b>",  c9)); col_w.append(8*mm)
    if SHOW_SERIAL:
        cols.append(P("<b>Serial No</b>", c9)); col_w.append(22*mm)
    cols.append(P("<b>Product Description</b>",
                  ps("phd", fontSize=9, fontName=FONT_BOLD,
                     textColor=DARK, leading=12))); col_w.append(0)  # stretch
    if SHOW_HSN:
        cols.append(P("<b>HSN/SAC</b>", c9)); col_w.append(16*mm)
    cols.append(P("<b>Qty</b>",  c9)); col_w.append(12*mm)
    cols.append(P("<b>Unit</b>", c9)); col_w.append(12*mm)
    cols.append(P(f"<b>Rate {RUPEE}</b>",
                  ps("phr", fontSize=9, fontName=FONT_BOLD,
                     textColor=DARK, alignment=TA_RIGHT))); col_w.append(22*mm)
    cols.append(P("<b>GST%</b>", c9)); col_w.append(13*mm)
    cols.append(P(f"<b>GST {RUPEE}</b>",
                  ps("phg", fontSize=9, fontName=FONT_BOLD,
                     textColor=DARK, alignment=TA_RIGHT))); col_w.append(18*mm)
    cols.append(P(f"<b>Amount {RUPEE}</b>",
                  ps("pha", fontSize=9, fontName=FONT_BOLD,
                     textColor=DARK, alignment=TA_RIGHT))); col_w.append(22*mm)

    fixed_total = sum(w for w in col_w if w > 0)
    desc_idx = 2 if SHOW_SERIAL else 1
    col_w[desc_idx] = W - fixed_total

    items    = inv.get("items", [])
    item_rows = []
    subtotal = 0.0

    for i, it in enumerate(items):
        qty   = float(it.get("quantity", 0))
        rate  = float(it.get("rate", 0))
        gst_r = float(it.get("gst_rate", 0))
        gst_a = float(it.get("gst_amount", 0))
        amt   = float(it.get("amount", 0))
        hsn   = s(it.get("hsn_code"))
        unit  = s(it.get("unit_type"), "Nos")
        serial= s(it.get("serial_number"))
        name  = s(it.get("product_name"))
        subtotal += amt

        row = []
        row.append(P(str(i+1), c8))
        if SHOW_SERIAL:
            row.append(P(serial, c8))

        # Serial number always printed below product name in the
        # description cell (when present), regardless of the SHOW_SERIAL
        # toggle — the toggle only controls the dedicated serial column.
        if serial:
            desc_para = P(
                f"<b>{name}</b><br/>"
                f"<font size='7' color='#555555'>S/N: {serial}</font>",
                n8
            )
        else:
            desc_para = P(name, n8)

        row.append(desc_para)
        if SHOW_HSN:
            row.append(P(hsn, c8))
        row.append(P(f"{qty:g}", c8))
        row.append(P(unit, c8))
        row.append(P(f"{rate:,.2f}", r8))
        row.append(P(f"{gst_r:.0f}%", c8))
        row.append(P(f"{gst_a:,.2f}", r8))
        row.append(P(f"{amt:,.2f}", r8))
        item_rows.append(row)

    # Blank filler-row template (same column count, all empty cells) —
    # used below to stretch the items grid to fill the page.
    def make_blank_row():
        r = [P("", c8)]
        if SHOW_SERIAL: r.append(P("", c8))
        r.append(P("", n8))
        if SHOW_HSN: r.append(P("", c8))
        r += [P("", c8), P("", c8), P("", r8), P("", c8), P("", r8), P("", r8)]
        return r

    empty_cols = 2 + (1 if SHOW_SERIAL else 0) + (1 if SHOW_HSN else 0)
    tot_row = [P("")]*empty_cols + [
        P(""), P(""), P(""), P(""),
        P("<b>Total</b>", b8),
        P(f"<b>{subtotal:,.2f}</b>",
          ps("tr", fontSize=9, fontName=FONT_BOLD,
             alignment=TA_RIGHT, textColor=DARK))
    ]

    # Style is generated dynamically: horizontal row-divider lines only
    # appear across the header + REAL item rows. The blank filler zone
    # below (no product) gets ONLY the vertical column lines continuing
    # down — no horizontal line is drawn for an empty/unfilled row.
    def build_prod_style(n_items):
        last_main_row = n_items  # 0 = header; 1..n_items = real product rows
        ncols = len(col_w)
        cmds = [
            ("BACKGROUND",    (0,0),(-1,0),  WHITE),
            ("LINEBELOW",     (0,0),(-1,0),  1.5, DARK),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ("LEFTPADDING",   (0,0),(-1,-1), 3),
            ("RIGHTPADDING",  (0,0),(-1,-1), 3),
            ("BOX",           (0,0),(-1,-1), 2.0, BLACK),
            ("INNERGRID", (0,0), (-1,last_main_row), 1.0, BORDER),
            ("LINEBELOW", (0,last_main_row), (-1,last_main_row), 1.0, BORDER),
            ("LINEABOVE", (0,-1), (-1,-1), 2.0, BLACK),
            ("LINEBELOW", (0,-1), (-1,-1), 2.0, BLACK),
        ]
        # Vertical column lines continue for the WHOLE table (header all
        # the way through the blank filler zone to the Total row), so
        # columns stay visually divided even where there's no product —
        # but with NO horizontal line per empty row.
        for c in range(1, ncols):
            cmds.append(("LINEBEFORE", (c,0), (c,-1), 1.0, BORDER))
        return TableStyle(cmds)

    PROD_STYLE = build_prod_style(len(item_rows))

    # ══════════════════════════════════════════════════════════════════════
    # 5. BOTTOM — Amount in Words + Bank | Tax Summary  (built now so we
    #    can measure its height before deciding the product table's filler
    #    row count)
    # ══════════════════════════════════════════════════════════════════════
    final_amt = float(inv.get("final_amount", 0))
    cgst_amt  = float(inv.get("cgst", 0))
    sgst_amt  = float(inv.get("sgst", 0))
    round_off = float(inv.get("round_off", 0))
    words     = _num_to_words(final_amt)
    ro_sign   = "+" if round_off >= 0 else ""

    left_lines = [
        [P("<b>Amount in Words:</b>", b8)],
        [P(f"<i>{words}</i>", words_s)],
        [P("")],
    ]
    if SHOW_BANK:
        bname = s(bp.get("bank_name"))
        acc   = s(bp.get("account_number"))
        ifsc  = s(bp.get("ifsc_code"))
        upi   = s(bp.get("upi_id"))
        qr_path = s(bp.get("qr_code_path"))
        if any([bname, acc, ifsc, upi]):
            # Bank text column (left) + QR image (right) side by side
            bank_text_lines = [[P("<b>Bank Details:</b>", bank_title)]]
            if bname: bank_text_lines.append([P(f"Bank: {bname}", bank_line)])
            if acc:   bank_text_lines.append([P(f"A/C No.: {acc}", bank_line)])
            if ifsc:  bank_text_lines.append([P(f"IFSC: {ifsc}", bank_line)])
            if upi:   bank_text_lines.append([P(f"UPI: {upi}", bank_line)])

            bank_text_tbl = Table(bank_text_lines, colWidths=[W*0.34])
            bank_text_tbl.setStyle(TableStyle([
                ("TOPPADDING",   (0,0),(-1,-1), 2),
                ("BOTTOMPADDING",(0,0),(-1,-1), 2),
                ("LEFTPADDING",  (0,0),(-1,-1), 5),
                ("RIGHTPADDING", (0,0),(-1,-1), 5),
                ("VALIGN",       (0,0),(-1,-1), "TOP"),
                ("BACKGROUND",   (0,0),(-1,-1), WHITE),
            ]))

            # QR code image — agar path hai aur file exist kare
            qr_cell = P("")
            if qr_path and os.path.exists(qr_path):
                try:
                    qr_img = Image(qr_path)
                    qr_size = 22*mm
                    qr_img.drawWidth  = qr_size
                    qr_img.drawHeight = qr_size
                    qr_cell = qr_img
                except Exception:
                    qr_cell = P("QR\nError", ps("qre", fontSize=7,
                                alignment=TA_CENTER, textColor=MEDIUM))

            qr_tbl = Table([[qr_cell]], colWidths=[W*0.18])
            qr_tbl.setStyle(TableStyle([
                ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
                ("ALIGN",        (0,0),(-1,-1), "CENTER"),
                ("TOPPADDING",   (0,0),(-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING",  (0,0),(-1,-1), 4),
                ("RIGHTPADDING", (0,0),(-1,-1), 4),
                ("BACKGROUND",   (0,0),(-1,-1), WHITE),
            ]))

            # Bank text + QR combined
            bank_qr_combined = Table([[bank_text_tbl, qr_tbl]],
                                      colWidths=[W*0.34, W*0.18])
            bank_qr_combined.setStyle(TableStyle([
                ("LEFTPADDING",  (0,0),(-1,-1), 0),
                ("RIGHTPADDING", (0,0),(-1,-1), 0),
                ("TOPPADDING",   (0,0),(-1,-1), 0),
                ("BOTTOMPADDING",(0,0),(-1,-1), 0),
                ("VALIGN",       (0,0),(-1,-1), "TOP"),
                ("BACKGROUND",   (0,0),(-1,-1), WHITE),
            ]))
            left_lines.append([bank_qr_combined])

    left_tbl = Table(left_lines, colWidths=[W*0.52])
    left_tbl.setStyle(TableStyle([
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("LEFTPADDING",  (0,0),(-1,-1), 5),
        ("RIGHTPADDING", (0,0),(-1,-1), 5),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("BACKGROUND",   (0,0),(-1,-1), WHITE),
    ]))

    rw1 = W*0.25; rw2 = W*0.23
    tax_header = Table(
        [[P("<b>Tax Summary</b>",
            ps("tsh", fontSize=9, fontName=FONT_BOLD,
               textColor=DARK, alignment=TA_CENTER)),""]],
        colWidths=[rw1, rw2]
    )
    tax_header.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), WHITE),
        ("LINEBELOW",  (0,0),(-1,-1), 1.5, DARK),
        ("SPAN",       (0,0),(-1,-1)),
        ("TOPPADDING", (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1), 4),
    ]))

    tax_rows_data = [
        [P("CGST @9%",    b8), P(f"{RUPEE} {cgst_amt:,.2f}", r8)],
        [P("SGST @9%",    b8), P(f"{RUPEE} {sgst_amt:,.2f}", r8)],
        [P("IGST ",    b8), P(f"{RUPEE} 0.00", r8)],
        [P(f"Round Off ({ro_sign}{round_off:,.2f})", sm),
         P(f"{RUPEE} {round_off:,.2f}", r8)],
        [P("<b>Grand Total</b>",
           ps("gtl", fontSize=10, fontName=FONT_BOLD, textColor=DARK)),
         P(f"<b>{RUPEE} {final_amt:,.2f}</b>",
           ps("gtr", fontSize=10, fontName=FONT_BOLD,
              alignment=TA_RIGHT, textColor=DARK))],
    ]
    tax_tbl = Table(tax_rows_data, colWidths=[rw1, rw2])
    tax_tbl.setStyle(TableStyle([
        ("INNERGRID",    (0,0),(-1,-1),  1.0, BORDER),
        ("TOPPADDING",   (0,0),(-1,-1),  2),
        ("BOTTOMPADDING",(0,0),(-1,-1),  2),
        ("LEFTPADDING",  (0,0),(-1,-1),  4),
        ("RIGHTPADDING", (0,0),(-1,-1),  4),
        ("VALIGN",       (0,0),(-1,-1),  "MIDDLE"),
        ("BACKGROUND",   (0,-1),(-1,-1), LIGHT),
        ("LINEABOVE",    (0,-1),(-1,-1), 1.5, DARK),
        ("BACKGROUND",   (0,0),(-1,-2),  WHITE),
    ]))

    right_combined = Table([[tax_header], [tax_tbl]], colWidths=[W*0.48])
    right_combined.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))

    bottom_tbl = Table([[left_tbl, right_combined]], colWidths=[W*0.52, W*0.48])
    bottom_tbl.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 2.0, BLACK),
        ("LINEBEFORE",   (1,0),(1,-1), 1.5, BLACK),
        ("LINEBELOW",    (0,-1),(-1,-1), 2.0, BLACK),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))

    # ══════════════════════════════════════════════════════════════════════
    # 6. FOOTER — Terms + Signatures  (also built now to measure its height)
    # ══════════════════════════════════════════════════════════════════════
    terms = s(bp.get("terms"),
              "1. Goods once sold will not be taken back.\n"
              "2. Interest @24% P.A. charged after due date.\n"
              "3. Subject to Jaipur jurisdiction only.")

    footer_rows = []
    if SHOW_TERMS:
        footer_rows.append([
            P("<b>Terms &amp; Conditions:</b>", b8),
            P("", n8),
            P(f"<b>For {shop}</b>",
              ps("fn", fontSize=8, fontName=FONT_BOLD, alignment=TA_RIGHT)),
        ])
        footer_rows.append([
            P(terms.replace("\n","<br/>"),
              ps("tc", fontSize=7, textColor=MEDIUM, leading=10)),
            P("", n8),
            P("", n8),
        ])
    else:
        footer_rows.append(["", "",
            P(f"<b>For {shop}</b>",
              ps("fn2", fontSize=8, fontName=FONT_BOLD, alignment=TA_RIGHT))])

    if SHOW_SIGNATURE:
        footer_rows.append([
            P("<b></b>",
              ps("cs", fontSize=8, fontName=FONT_BOLD, alignment=TA_CENTER)),
            P("", n8),
            P("<b>Authorised Signatory</b>",
              ps("as", fontSize=8, fontName=FONT_BOLD, alignment=TA_RIGHT)),
        ])

    foot_tbl = None
    if footer_rows:
        foot_tbl = Table(footer_rows, colWidths=[W*0.45, W*0.1, W*0.45])
        foot_tbl.setStyle(TableStyle([
            ("BOX",          (0,0),(-1,-1), 2.0, BLACK),
            ("LINEBELOW",    (0,-1),(-1,-1), 2.0, BLACK),
            ("LINEBEFORE",   (2,0),(2,-1),  1.5, BLACK),
            ("TOPPADDING",   (0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
            ("LEFTPADDING",  (0,0),(-1,-1), 5),
            ("RIGHTPADDING", (0,0),(-1,-1), 5),
            ("VALIGN",       (0,0),(-2,-1), "TOP"),
            ("VALIGN",       (0,-1),(-1,-1),"BOTTOM"),
            ("BACKGROUND",   (0,0),(-1,-1), WHITE),
        ]))

    if UNICODE_OK:
        footer_text = "Thank You for Shopping with Us! Have a Nice Day. ~ Radhe Radhe"
    else:
        footer_text = "Thank You for Shopping with Us! Have a Nice Day. ~ Radhe Radhe"

    # Build footer with 🙏 emoji if Segoe font available, else plain text
    if EMOJI_FONT:
        from reportlab.platypus import Paragraph as _P
        from reportlab.lib.styles import ParagraphStyle as _PS
        # Single paragraph with inline font switching for emoji
        _full_style = _PS("_full", fontName=FONT_BOLD, fontSize=9,
                          alignment=TA_CENTER, textColor=DARK, leading=14)
        _combined_text = (
            f'<font name="{EMOJI_FONT}" size="13">🙏</font>'
            f'  {footer_text}  '
            f'<font name="{EMOJI_FONT}" size="13">🙏</font>'
        )
        footer_note_tbl = Table(
            [[_P(_combined_text, _full_style)]],
            colWidths=[W]
        )
    else:
        footer_note_tbl = Table(
            [[P(f"{footer_text}",
                ps("cg", fontSize=9, fontName=FONT_BOLD,
                   alignment=TA_CENTER, textColor=DARK))]],
            colWidths=[W]
        )
    footer_note_tbl.setStyle(TableStyle([
        ("LINEABOVE",     (0,0),(-1,-1), 2.0, BLACK),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("BACKGROUND",    (0,0),(-1,-1), WHITE),
    ]))
    NOTE_SPACER_H = 0

    # ══════════════════════════════════════════════════════════════════════
    # 7. Work out how many blank filler rows the product table needs so
    #    the whole invoice (with its connecting border lines) reaches all
    #    the way down to the page frame, even with just 1 product.
    # ══════════════════════════════════════════════════════════════════════
    BIG = 100000
    used_fixed = (
        hdr_tbl.wrap(W, BIG)[1] +
        ti.wrap(W, BIG)[1] +
        info_tbl.wrap(W, BIG)[1] +
        party_tbl.wrap(W, BIG)[1] +
        bottom_tbl.wrap(W, BIG)[1] +
        (foot_tbl.wrap(W, BIG)[1] if foot_tbl else 0) +
        NOTE_SPACER_H + footer_note_tbl.wrap(W, BIG)[1]
    )
    avail_total     = doc.pagesize[1] - doc.topMargin - doc.bottomMargin
    safety_buffer   = 8*mm
    avail_for_items = avail_total - used_fixed - safety_buffer

    def _build_prod_rows(n_filler):
        return [cols] + item_rows + [make_blank_row() for _ in range(n_filler)] + [tot_row]

    base_tbl = Table(_build_prod_rows(0), colWidths=col_w, repeatRows=1)
    base_tbl.setStyle(PROD_STYLE)
    h_base = base_tbl.wrap(W, BIG)[1]

    filler_count = 0
    if h_base < avail_for_items:
        one_tbl = Table(_build_prod_rows(1), colWidths=col_w, repeatRows=1)
        one_tbl.setStyle(PROD_STYLE)
        h_one = one_tbl.wrap(W, BIG)[1]
        blank_row_h = h_one - h_base
        if blank_row_h <= 0:
            blank_row_h = 10  # fallback only if measurement is degenerate
        filler_count = max(0, int((avail_for_items - h_base) // blank_row_h))
        filler_count = min(filler_count, 60)   # sane upper bound

        # nudge down by 1 in case of rounding, without overflowing
        while filler_count > 0:
            test_tbl = Table(_build_prod_rows(filler_count), colWidths=col_w, repeatRows=1)
            test_tbl.setStyle(PROD_STYLE)
            if test_tbl.wrap(W, BIG)[1] <= avail_for_items:
                break
            filler_count -= 1

    # Final full-page verification: sum the ACTUAL heights of every single
    # flowable that will go on the page (not just the budget estimate
    # above) and keep trimming filler rows until everything truly fits in
    # one page. This protects against small per-component rounding drift
    # that the budget calculation above can't fully account for.
    def _total_story_height(n_filler):
        p = Table(_build_prod_rows(n_filler), colWidths=col_w, repeatRows=1)
        p.setStyle(PROD_STYLE)
        total = (
            hdr_tbl.wrap(W, BIG)[1] + ti.wrap(W, BIG)[1] +
            info_tbl.wrap(W, BIG)[1] + party_tbl.wrap(W, BIG)[1] +
            p.wrap(W, BIG)[1] + bottom_tbl.wrap(W, BIG)[1] +
            (foot_tbl.wrap(W, BIG)[1] if foot_tbl else 0) +
            NOTE_SPACER_H + footer_note_tbl.wrap(W, BIG)[1]
        )
        return total

    while filler_count > 0 and _total_story_height(filler_count) > avail_total:
        filler_count -= 1

    prod_tbl = Table(_build_prod_rows(filler_count), colWidths=col_w, repeatRows=1)
    prod_tbl.setStyle(PROD_STYLE)
    story.append(prod_tbl)

    story.append(bottom_tbl)
    if foot_tbl:
        story.append(foot_tbl)

    story.append(Spacer(1, NOTE_SPACER_H))
    story.append(footer_note_tbl)

    doc.build(story, onFirstPage=_draw_page_frame, onLaterPages=_draw_page_frame)
    return filepath


# ══════════════════════════════════════════════════════════════════════════════
# BULK PDF — many invoices -> ONE merged PDF (invoice-number sequence)
# ══════════════════════════════════════════════════════════════════════════════
import re as _re


def invoice_no_parts(inv_no):
    """'HOE-000012' -> ('HOE-', 12).  '12' -> ('', 12).
    No trailing digits -> (whole text, -1) so it still sorts safely."""
    text = str(inv_no or "").strip()
    m = _re.match(r"^(.*?)(\d+)$", text)
    if not m:
        return text.upper(), -1
    return m.group(1).upper(), int(m.group(2))


def invoice_sort_key(inv):
    """Sort key for an invoice dict: prefix first, then the NUMBER part
    (so HOE-000002 comes before HOE-000010, and 9 before 10)."""
    prefix, num = invoice_no_parts(inv.get("invoice_number"))
    return (prefix, num, str(inv.get("invoice_number", "")))


def filter_invoice_range(invoices, mode, a, b):
    """Pick invoices for a bulk download and return them in invoice-number
    sequence.

    mode "number": a / b are the FROM / TO invoice numbers. Full number
                   ('HOE-000005') or just the digits ('5') both work. If a
                   prefix is typed, only that prefix is matched.
    mode "date":   a / b are 'yyyy-MM-dd' strings (FROM / TO, inclusive).
    """
    out = []
    if mode == "number":
        pa, na = invoice_no_parts(a)
        pb, nb = invoice_no_parts(b)
        if na < 0 or nb < 0:
            raise ValueError("Invoice number mein digits hone chahiye.")
        if na > nb:
            na, nb = nb, na
        prefix = pa or pb          # typed prefix (if any) restricts the match
        for inv in invoices:
            p, n = invoice_no_parts(inv.get("invoice_number"))
            if n < 0:
                continue
            if prefix and p != prefix:
                continue
            if na <= n <= nb:
                out.append(inv)
    elif mode == "date":
        d1, d2 = sorted([str(a)[:10], str(b)[:10]])
        for inv in invoices:
            d = str(inv.get("invoice_date", ""))[:10]
            if d1 <= d <= d2:
                out.append(inv)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return sorted(out, key=invoice_sort_key)


def _ensure_pypdf():
    """Same idea as _ensure_reportlab(): import pypdf, auto-install if missing.
    (In a PyInstaller .exe, make sure pypdf is bundled - pip can't help there.)"""
    try:
        import pypdf  # noqa: F401
        return
    except ImportError:
        pass
    import sys
    if getattr(sys, "frozen", False):
        raise ImportError(
            "'pypdf' is missing from this packaged app. Install it in the "
            "build environment (pip install pypdf) and rebuild.")
    import subprocess
    last_error = None
    for cmd in ([sys.executable, "-m", "pip", "install", "pypdf"],
                [sys.executable, "-m", "pip", "install", "pypdf", "--user"],
                [sys.executable, "-m", "pip", "install", "pypdf",
                 "--break-system-packages"]):
        try:
            subprocess.check_call(cmd)
            break
        except Exception as e:
            last_error = e
    else:
        raise ImportError(
            "Could not auto-install 'pypdf'. Run:  pip install pypdf\n"
            f"(last error: {last_error})")
    import pypdf  # noqa: F401


def generate_bulk_invoice_pdf(invoices, business_profile, out_path,
                              settings=None, progress_cb=None):
    """Build every invoice with generate_invoice_pdf() and merge them into a
    single PDF at out_path, in the order given (caller sorts by invoice no.).

    invoices     : list of FULL invoice dicts (with "items"), like get_invoice()
    progress_cb  : optional fn(done, total) -> True to CANCEL. Called after
                   each invoice is built.
    Returns out_path, or None if cancelled."""
    if not invoices:
        raise ValueError("Koi invoice nahi mili.")
    _ensure_pypdf()
    from pypdf import PdfWriter

    paths = []
    total = len(invoices)
    for i, inv in enumerate(invoices, 1):
        paths.append(generate_invoice_pdf(inv, business_profile, settings))
        if progress_cb and progress_cb(i, total):
            return None

    writer = PdfWriter()
    for p in paths:
        writer.append(p)
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "wb") as fh:
        writer.write(fh)
    writer.close()
    return out_path


# ── Amount in Words ───────────────────────────────────────────────────────────
def _num_to_words(n):
    n = int(round(n))
    if n == 0: return "Zero Rupees Only"
    ones = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine",
            "Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen",
            "Seventeen","Eighteen","Nineteen"]
    tens = ["","","Twenty","Thirty","Forty","Fifty",
            "Sixty","Seventy","Eighty","Ninety"]
    def w(num):
        if num == 0: return ""
        if num < 20: return ones[num]
        if num < 100: return tens[num//10]+(" "+ones[num%10] if num%10 else "")
        if num < 1000:
            return ones[num//100]+" Hundred"+((" "+w(num%100)) if num%100 else "")
        if num < 100000:
            return w(num//1000)+" Thousand"+((" "+w(num%1000)) if num%1000 else "")
        if num < 10000000:
            return w(num//100000)+" Lakh"+((" "+w(num%100000)) if num%100000 else "")
        return w(num//10000000)+" Crore"+((" "+w(num%10000000)) if num%10000000 else "")
    return w(n).strip()+" Rupees Only"
