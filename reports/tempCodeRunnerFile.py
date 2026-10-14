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
