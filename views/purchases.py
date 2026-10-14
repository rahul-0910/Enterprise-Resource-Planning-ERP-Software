from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QMessageBox,
    QHeaderView, QAbstractItemView, QComboBox, QDoubleSpinBox, QDateEdit, QGroupBox,
    QFrame, QCompleter)
from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QFont, QColor


class PurchasesWidget(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db; self.user = user
        layout = QVBoxLayout(self); layout.setContentsMargins(16,16,16,16); layout.setSpacing(12)
        hr = QHBoxLayout()
        t = QLabel("Purchase Management"); t.setFont(QFont("Segoe UI",16,700)); t.setStyleSheet("color:#1A2A4A;")
        b = QPushButton("+ New Purchase"); b.setFixedHeight(38); b.setObjectName("btn_success"); b.clicked.connect(self._new_purchase);b.setStyleSheet("color:#1f2A4A;")
        hr.addWidget(t); hr.addStretch(); hr.addWidget(b); layout.addLayout(hr)
        search_container = QFrame()
        search_container.setFixedHeight(38)
        search_container.setStyleSheet("""
            QFrame { border: 1.5px solid #CBD5E0; border-radius: 8px; background: white; }
            QFrame:focus-within { border: 1.5px solid #1A2A4A; }
        """)
        sc_lay = QHBoxLayout(search_container)
        sc_lay.setContentsMargins(10, 0, 10, 0); sc_lay.setSpacing(6)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("background:transparent; border:none; font-size:13px;")
        search_icon.setFixedWidth(18)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Purchase number ya supplier search karein...")
        self.search.setStyleSheet("border:none; background:transparent; font-size:13px; color:#374151;")
        self.search.setFixedHeight(36)
        self._purchase_completer = QCompleter([])
        self._purchase_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._purchase_completer.setFilterMode(Qt.MatchContains)
        self._purchase_completer.setCompletionMode(QCompleter.PopupCompletion)
        self._purchase_completer.popup().setStyleSheet("""
            QListView { border: 1.5px solid #CBD5E0; border-radius: 6px; background: white;
                font-size: 13px; color: #1A2A4A; padding: 4px; }
            QListView::item { padding: 6px 12px; border-radius: 4px; }
            QListView::item:hover { background: #EEF2FF; color: #1A2A4A; }
            QListView::item:selected { background: #1A2A4A; color: white; }
        """)
        self.search.setCompleter(self._purchase_completer)
        self.search.textChanged.connect(self._on_search_changed)
        sc_lay.addWidget(search_icon); sc_lay.addWidget(self.search)
        layout.addWidget(search_container)
        self._refresh_completer()
        self.table = QTableWidget(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Purchase #","Supplier","Date","Total","Paid","Status","View","Pay"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setColumnWidth(6, 80); self.table.setColumnWidth(7, 80)
        layout.addWidget(self.table)
        self._load()

    def refresh(self):
        self._refresh_completer(); self._load()

    def _refresh_completer(self):
        try:
            all_purchases = self.db.get_purchases("")
            suggestions = []
            for p in all_purchases:
                pnum = p.get("purchase_number", ""); sup = p.get("supplier_name", "") or ""
                if pnum: suggestions.append(pnum)
                if sup and sup not in suggestions: suggestions.append(sup)
            model = QStringListModel(suggestions)
            self._purchase_completer.setModel(model)
        except Exception:
            pass

    def _on_search_changed(self, text): self._load()

    def _load(self):
        rows = self.db.get_purchases(self.search.text())
        self.table.setRowCount(len(rows))
        for i, p in enumerate(rows):
            self.table.setItem(i,0,QTableWidgetItem(p["purchase_number"]))
            self.table.setItem(i,1,QTableWidgetItem(p.get("supplier_name","") or ""))
            self.table.setItem(i,2,QTableWidgetItem(str(p["purchase_date"])))
            for j, key in [(3,"grand_total"),(4,"paid_amount")]:
                it = QTableWidgetItem(f"₹{p.get(key,0):,.2f}"); it.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                self.table.setItem(i,j,it)
            status = p.get("payment_status","").upper()
            self.table.setItem(i,5,QTableWidgetItem(status))
            view_btn = QPushButton("👁 View"); view_btn.setFixedHeight(28)
            view_btn.setStyleSheet("background:#2980B9;color:white;border-radius:5px;font-weight:600;")
            view_btn.clicked.connect(lambda _, pid=p["id"], pnum=p["purchase_number"], pdate=str(p["purchase_date"]), sup=p.get("supplier_name",""), tot=p.get("grand_total",0): self._view_purchase(pid, pnum, pdate, sup, tot))
            self.table.setCellWidget(i, 6, view_btn)
            pay_btn = QPushButton("💰 Pay"); pay_btn.setFixedHeight(28)
            pay_btn.setEnabled(status != "PAID")
            pay_btn.setStyleSheet(
                "background:#27AE60;color:white;border-radius:5px;font-weight:600;"
                if status != "PAID" else "background:#95a5a6;color:white;border-radius:5px;")
            pay_btn.clicked.connect(lambda _, pid=p["id"], pnum=p["purchase_number"], bal=p.get("balance_amount",0): self._pay_purchase(pid, pnum, bal))
            self.table.setCellWidget(i, 7, pay_btn)

    def _pay_purchase(self, purchase_id, purchase_number, balance):
        from PyQt5.QtWidgets import QInputDialog
        if balance <= 0:
            QMessageBox.information(self, "Paid", "Yeh purchase already paid hai!"); return
        amount, ok = QInputDialog.getDouble(
            self, f"Payment - {purchase_number}",
            f"Balance: Rs.{balance:,.2f}\nPayment amount darj karein:",
            value=balance, min=0.01, max=balance, decimals=2)
        if ok and amount > 0:
            try:
                self.db.record_purchase_payment(purchase_id, amount)
                QMessageBox.information(self, "Success", f"✅ ₹{amount:,.2f} payment saved!")
                self._load()
            except Exception as e:
                try:
                    import sqlite3
                    conn = sqlite3.connect(self.db.db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT paid_amount, grand_total FROM purchases WHERE id=?", (purchase_id,))
                    row = cur.fetchone()
                    if row:
                        new_paid = round(row[0] + amount, 2); new_bal = round(row[1] - new_paid, 2)
                        new_bal = max(new_bal, 0); status = "paid" if new_bal == 0 else "partial"
                        cur.execute("UPDATE purchases SET paid_amount=?, balance_amount=?, payment_status=? WHERE id=?",
                            (new_paid, new_bal, status, purchase_id))
                        conn.commit()
                    conn.close()
                    QMessageBox.information(self, "Success", f"✅ ₹{amount:,.2f} payment saved!")
                    self._load()
                except Exception as e2:
                    QMessageBox.critical(self, "Error", f"Payment save nahi hui: {e2}")

    def _view_purchase(self, purchase_id, purchase_number, purchase_date, supplier, grand_total):
        dlg = PurchaseDetailDialog(self.db, purchase_id, purchase_number, purchase_date, supplier, grand_total, self)
        dlg.exec_()

    def _new_purchase(self):
        dlg = NewPurchaseDialog(self.db, self.user, self)
        if dlg.exec_(): self._load()


class NewPurchaseDialog(QDialog):
    def __init__(self, db, user, parent=None):
        super().__init__(parent)
        self.db = db; self.user = user; self.items = []
        self.setWindowTitle("New Purchase"); self.setMinimumSize(820, 700)
        self.setStyleSheet("""
            QDialog { background: #F8F9FB; }
            QLabel { color: #1A2A4A; font-size: 13px; }
            QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit {
                border: 1px solid #D1D5DB; border-radius: 6px;
                padding: 4px 8px; background: white; font-size: 13px;
            }
            QTableWidget { background: white; border: 1px solid #E5E7EB; border-radius: 8px; }
            QHeaderView::section {
                background: #F9FAFB; color: #374151; padding: 8px;
                font-weight: 700; border: none; border-bottom: 1px solid #E5E7EB;
            }
        """)
        layout = QVBoxLayout(self); layout.setSpacing(12); layout.setContentsMargins(20,20,20,20)

        # ── Header: Purchase # and Date ──────────────────────────────
        top = QHBoxLayout()
        pnum_lbl = QLabel("Purchase #:"); pnum_lbl.setStyleSheet("font-weight:700;")
        self.pur_num = QLineEdit(self.db.get_next_purchase_number().upper())
        self.pur_num.setStyleSheet("background:#EBF5FB;color:#2980B9;border-radius:6px;padding:6px 14px;font-weight:700;font-size:14px;")
        self.pur_num.setFixedHeight(38)
        date_lbl = QLabel("Date:"); date_lbl.setStyleSheet("font-weight:700;")
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(38)
        self.date_edit.setFixedWidth(150)
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        top.addWidget(pnum_lbl); top.addWidget(self.pur_num)
        top.addStretch()
        top.addWidget(date_lbl); top.addWidget(self.date_edit)
        layout.addLayout(top)

        # ── Supplier ─────────────────────────────────────────────────
        sr = QHBoxLayout()
        sup_lbl = QLabel("Supplier:"); sup_lbl.setStyleSheet("font-weight:700;")
        self.sup_combo = QComboBox(); self.sup_combo.setFixedHeight(38); self.sup_combo.setMinimumWidth(260)
        self.sup_combo.addItem("-- Select Supplier --", None)
        for s in self.db.get_suppliers(): self.sup_combo.addItem(s["supplier_name"], s["id"])
        sr.addWidget(sup_lbl); sr.addWidget(self.sup_combo); sr.addStretch()
        layout.addLayout(sr)

        # ── Product Add Row ──────────────────────────────────────────
        pr = QHBoxLayout(); pr.setSpacing(10)
        prod_lbl = QLabel("Product:"); prod_lbl.setStyleSheet("font-weight:700;")
        self.prod_search = QLineEdit()
        self.prod_search.setPlaceholderText("Product naam se search karein...")
        self.prod_search.setFixedHeight(38)
        products = self.db.get_products()
        product_names = [p["product_name"] for p in products]
        self.completer = QCompleter(product_names)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.prod_search.setCompleter(self.completer)
        self.prod_search.editingFinished.connect(self.load_product_details)

        qty_lbl = QLabel("Qty:"); qty_lbl.setStyleSheet("font-weight:700;")
        self.qty = QDoubleSpinBox(); self.qty.setRange(0.01,99999); self.qty.setValue(1)
        self.qty.setFixedWidth(90); self.qty.setFixedHeight(38)

        rate_lbl = QLabel("Rate (₹):"); rate_lbl.setStyleSheet("font-weight:700;")
        self.rate = QDoubleSpinBox(); self.rate.setRange(0,99999999); self.rate.setPrefix("₹ ")
        self.rate.setFixedWidth(130); self.rate.setFixedHeight(38)

        add_btn = QPushButton("+ Add"); add_btn.setFixedHeight(38); add_btn.setFixedWidth(90)
        add_btn.setStyleSheet("background:#27AE60;color:white;border-radius:6px;font-weight:700;border:none;")
        add_btn.clicked.connect(self._add_item)

        pr.addWidget(prod_lbl); pr.addWidget(self.prod_search, 3)
        pr.addWidget(qty_lbl); pr.addWidget(self.qty)
        pr.addWidget(rate_lbl); pr.addWidget(self.rate)

        # GST Optional
        from PyQt5.QtWidgets import QCheckBox, QSpinBox
        self.gst_check = QCheckBox("GST")
        self.gst_check.setStyleSheet("font-weight:700; color:#1A2A4A; font-size:13px;")
        self.gst_check.setChecked(False)
        self.gst_spin = QSpinBox()
        self.gst_spin.setRange(0, 28)
        self.gst_spin.setValue(18)
        self.gst_spin.setSuffix(" %")
        self.gst_spin.setFixedWidth(75)
        self.gst_spin.setFixedHeight(38)
        self.gst_spin.setEnabled(False)
        self.gst_spin.setStyleSheet("color:#9CA3AF;")
        self.gst_check.toggled.connect(lambda checked: (
            self.gst_spin.setEnabled(checked),
            self.gst_spin.setStyleSheet("color:#1A2A4A;" if checked else "color:#9CA3AF;")
        ))
        pr.addWidget(self.gst_check)
        pr.addWidget(self.gst_spin)
        pr.addWidget(add_btn)
        layout.addLayout(pr)

        # ── Items Table (GST column hata diya, Edit+Remove add kiya) ─
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(["Product","Qty","Rate","GST%","Amount","Edit","Remove"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.setColumnWidth(1, 70)
        self.items_table.setColumnWidth(2, 100)
        self.items_table.setColumnWidth(3, 70)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setColumnWidth(5, 70)
        self.items_table.setColumnWidth(6, 80)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setMinimumHeight(220)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(False)
        self.items_table.setAlternatingRowColors(True)
        layout.addWidget(self.items_table)

        # ── Total ────────────────────────────────────────────────────
        total_row = QHBoxLayout(); total_row.addStretch()
        self.total_lbl = QLabel("Total: ₹ 0.00")
        self.total_lbl.setFont(QFont("Segoe UI", 14, 700))
        self.total_lbl.setStyleSheet(
            "color:white;background:#1A2A4A;border-radius:8px;padding:8px 20px;")
        total_row.addWidget(self.total_lbl)
        layout.addLayout(total_row)

        # ── Save / Cancel ────────────────────────────────────────────
        br = QHBoxLayout()
        sv = QPushButton("💾  Save Purchase"); sv.setFixedHeight(44)
        sv.setStyleSheet("background:#27AE60;color:white;font-weight:700;font-size:13px;border-radius:8px;border:none;")
        sv.clicked.connect(self._save)
        ca = QPushButton("Cancel"); ca.setFixedHeight(44)
        ca.setStyleSheet("background:#95a5a6;color:white;font-weight:700;font-size:13px;border-radius:8px;border:none;")
        ca.clicked.connect(self.reject)
        br.addWidget(sv); br.addWidget(ca)
        layout.addLayout(br)

        self._total = 0.0

    # ── Product auto-fill ────────────────────────────────────────────────
    def load_product_details(self):
        product_name = self.prod_search.text().strip()
        if not product_name: return
        products = self.db.get_products(search=product_name)
        for p in products:
            if p["product_name"].lower() == product_name.lower():
                self.rate.setValue(float(p.get("purchase_price", 0)))
                return

    # ── Add Item ─────────────────────────────────────────────────────────
    def _add_item(self):
        search_text = self.prod_search.text().strip()
        if not search_text:
            QMessageBox.warning(self, "Khaali", "Pehle product ka naam likho."); return
        products = self.db.get_products(search=search_text)
        if not products:
            QMessageBox.warning(self, "Nahi Mila", f"'{search_text}' product nahi mila."); return
        p = products[0]
        qty  = self.qty.value()
        rate = self.rate.value() if self.rate.value() > 0 else float(p.get("purchase_price") or 0)

        # GST optional — checkbox tick ho toh lagao
        if self.gst_check.isChecked():
            gst_rate = self.gst_spin.value()
            gst_amt  = round(qty * rate * gst_rate / 100, 2)
        else:
            gst_rate = 0
            gst_amt  = 0

        amount = round(qty * rate + gst_amt, 2)
        item = {
            "product_id":   p["id"],
            "product_name": p["product_name"],
            "quantity":     qty,
            "rate":         rate,
            "gst_rate":     gst_rate,
            "gst_amount":   gst_amt,
            "amount":       amount,
        }
        self.items.append(item)
        self._refresh_table()
        self.prod_search.clear(); self.qty.setValue(1); self.rate.setValue(0)

    # ── Edit Item ────────────────────────────────────────────────────────
    def _edit_item(self, index):
        item = self.items[index]
        dlg = QDialog(self)
        dlg.setWindowTitle("Item Edit Karein")
        dlg.setFixedSize(320, 230)
        dlg.setStyleSheet("""
            QDialog { background: #F8F9FB; }
            QLabel { color: #1A2A4A; font-size: 13px; }
            QDoubleSpinBox, QSpinBox { border: 1px solid #D1D5DB; border-radius: 6px;
                padding: 4px 8px; background: white; font-size: 13px; }
            QPushButton { border-radius: 6px; font-weight: 700;
                border: none; color: white; padding: 8px 16px; }
        """)
        from PyQt5.QtWidgets import QCheckBox, QSpinBox
        fl = QFormLayout(dlg)
        fl.setContentsMargins(16,16,16,16); fl.setSpacing(12)

        name_lbl = QLabel(item["product_name"])
        name_lbl.setStyleSheet("font-weight:700;color:#1A2A4A;")
        fl.addRow("Product:", name_lbl)

        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.01, 99999); qty_spin.setValue(item["quantity"]); qty_spin.setFixedHeight(36)
        fl.addRow("Qty:", qty_spin)

        rate_spin = QDoubleSpinBox()
        rate_spin.setRange(0, 99999999); rate_spin.setPrefix("₹ ")
        rate_spin.setValue(item["rate"]); rate_spin.setFixedHeight(36)
        fl.addRow("Rate (₹):", rate_spin)

        # GST optional in edit
        gst_row = QHBoxLayout()
        gst_chk = QCheckBox("GST lagao")
        gst_chk.setStyleSheet("font-weight:600;color:#1A2A4A;")
        gst_chk.setChecked(item.get("gst_rate", 0) > 0)
        gst_sp = QSpinBox()
        gst_sp.setRange(0, 28); gst_sp.setValue(item.get("gst_rate", 18) or 18)
        gst_sp.setSuffix(" %"); gst_sp.setFixedWidth(75); gst_sp.setFixedHeight(36)
        gst_sp.setEnabled(gst_chk.isChecked())
        gst_chk.toggled.connect(gst_sp.setEnabled)
        gst_row.addWidget(gst_chk); gst_row.addWidget(gst_sp)
        fl.addRow("GST:", gst_row)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("✅ Update"); ok_btn.setStyleSheet("background:#27AE60;"); ok_btn.clicked.connect(dlg.accept)
        cn_btn = QPushButton("Cancel");   cn_btn.setStyleSheet("background:#6B7280;"); cn_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(ok_btn); btn_row.addWidget(cn_btn)
        fl.addRow(btn_row)

        if dlg.exec_():
            qty  = qty_spin.value()
            rate = rate_spin.value()
            gst_rate = gst_sp.value() if gst_chk.isChecked() else 0
            gst_amt  = round(qty * rate * gst_rate / 100, 2) if gst_rate > 0 else 0
            self.items[index]["quantity"]   = qty
            self.items[index]["rate"]       = rate
            self.items[index]["gst_rate"]   = gst_rate
            self.items[index]["gst_amount"] = gst_amt
            self.items[index]["amount"]     = round(qty * rate + gst_amt, 2)
            self._refresh_table()

    # ── Remove Item ──────────────────────────────────────────────────────
    def _remove_item(self, index):
        name = self.items[index]["product_name"]
        reply = QMessageBox.question(self, "Confirm", f"'{name}' hatana chahte hain?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.items.pop(index)
            self._refresh_table()

    # ── Refresh Table ────────────────────────────────────────────────────
    def _refresh_table(self):
        self.items_table.setRowCount(len(self.items))
        total = 0
        for i, it in enumerate(self.items):
            self.items_table.setRowHeight(i, 40)

            name_item = QTableWidgetItem(it["product_name"])
            name_item.setForeground(QColor("#1A2A4A"))
            self.items_table.setItem(i, 0, name_item)

            qty_item = QTableWidgetItem(str(it["quantity"]))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(i, 1, qty_item)

            rate_item = QTableWidgetItem(f"₹{it['rate']:,.2f}")
            rate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(i, 2, rate_item)

            # GST — 0% ho toh "No GST" dikhao
            gst = it.get("gst_rate", 0)
            gst_item = QTableWidgetItem("—" if gst == 0 else f"{gst}%")
            gst_item.setTextAlignment(Qt.AlignCenter)
            gst_item.setForeground(QColor("#9CA3AF") if gst == 0 else QColor("#F59E0B"))
            self.items_table.setItem(i, 3, gst_item)

            amt_item = QTableWidgetItem(f"₹{it['amount']:,.2f}")
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt_item.setForeground(QColor("#1A2A4A"))
            self.items_table.setItem(i, 4, amt_item)

            # Edit button
            edit_btn = QPushButton("✏ Edit")
            edit_btn.setStyleSheet(
                "QPushButton{background:#3B82F6;color:white;border-radius:5px;"
                "font-size:11px;font-weight:600;border:none;}"
                "QPushButton:hover{background:#2563EB;}")
            edit_btn.clicked.connect(lambda _, idx=i: self._edit_item(idx))
            self.items_table.setCellWidget(i, 5, self._wrap_btn(edit_btn))

            # Remove button
            del_btn = QPushButton("🗑 Del")
            del_btn.setStyleSheet(
                "QPushButton{background:#E74C3C;color:white;border-radius:5px;"
                "font-size:11px;font-weight:600;border:none;}"
                "QPushButton:hover{background:#C0392B;}")
            del_btn.clicked.connect(lambda _, idx=i: self._remove_item(idx))
            self.items_table.setCellWidget(i, 6, self._wrap_btn(del_btn))

            total += it["amount"]

        self.total_lbl.setText(f"Total: ₹ {total:,.2f}")
        self._total = total

    def _wrap_btn(self, btn):
        wrapper = QWidget(); wrapper.setStyleSheet("background:transparent;")
        wl = QHBoxLayout(wrapper); wl.setContentsMargins(4,3,4,3); wl.addWidget(btn)
        return wrapper

    # ── Save ─────────────────────────────────────────────────────────────
    def _save(self):
        if not self.items:
            QMessageBox.warning(self, "Khaali", "Kam se kam ek product add karo."); return
        total = sum(i["amount"] for i in self.items)
        data = {
            "purchase_number": self.pur_num.text(),
            "supplier_id":     self.sup_combo.currentData(),
            "purchase_date":   self.date_edit.date().toString("yyyy-MM-dd"),
            "total_amount":    total, "grand_total": total,
            "paid_amount":     0,    "balance_amount": total,
            "payment_status":  "unpaid", "created_by": self.user["id"],
        }
        self.db.save_purchase(data, self.items, self.user["id"])
        QMessageBox.information(self, "Success", "✅ Purchase save ho gaya!")
        self.accept()


class PurchaseDetailDialog(QDialog):
    def __init__(self, db, purchase_id, purchase_number, purchase_date, supplier, grand_total, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Purchase Detail — {purchase_number}")
        self.setMinimumSize(620, 460)
        layout = QVBoxLayout(self)
        layout.setSpacing(10); layout.setContentsMargins(16,16,16,16)

        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background:#F0F4FF; border-radius:8px; border:1px solid #CBD5E0; }")
        info_lay = QHBoxLayout(info_frame)
        info_lay.setContentsMargins(14,10,14,10)

        def info_block(label, value):
            col = QVBoxLayout(); col.setSpacing(2)
            l = QLabel(label); l.setStyleSheet("color:#6B7280; font-size:10px; font-weight:600;")
            v = QLabel(str(value)); v.setStyleSheet("color:#1A2A4A; font-size:13px; font-weight:700;")
            col.addWidget(l); col.addWidget(v)
            return col

        info_lay.addLayout(info_block("Purchase #", purchase_number))
        info_lay.addLayout(info_block("Date", purchase_date))
        info_lay.addLayout(info_block("Supplier", supplier or "—"))
        info_lay.addLayout(info_block("Grand Total", f"₹{grand_total:,.2f}"))
        layout.addWidget(info_frame)

        lbl = QLabel("Purchased Products")
        lbl.setFont(QFont("Segoe UI", 12, 700)); lbl.setStyleSheet("color:#1A2A4A;")
        layout.addWidget(lbl)

        table = QTableWidget(); table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["#", "Product Name", "Qty", "Rate (₹)", "Amount (₹)"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True); table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setColumnWidth(0, 35); table.setColumnWidth(2, 60)
        table.setColumnWidth(3, 90); table.setColumnWidth(4, 100)

        try:
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            conn.row_factory = sqlite3.Row
            items = conn.execute(
                "SELECT * FROM purchase_items WHERE purchase_id=? ORDER BY id",
                (purchase_id,)).fetchall()
            conn.close()
            items = [dict(r) for r in items]
        except Exception:
            items = []

        table.setRowCount(len(items))
        for i, it in enumerate(items):
            amt = it.get("amount", 0) or 0
            table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            table.setItem(i, 1, QTableWidgetItem(it.get("product_name", "") or ""))
            for col, key in [(2,"quantity"),(3,"rate"),(4,"amount")]:
                val = it.get(key, 0) or 0
                cell = QTableWidgetItem(f"₹{val:,.2f}" if col in (3,4) else str(val))
                cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, col, cell)
        layout.addWidget(table)

        total_row = QHBoxLayout(); total_row.addStretch()
        total_lbl = QLabel(f"Grand Total:  ₹ {grand_total:,.2f}")
        total_lbl.setFont(QFont("Segoe UI", 13, 700))
        total_lbl.setStyleSheet("color:#1A2A4A; padding:6px 14px; background:#EEF2FF; border-radius:6px;")
        total_row.addWidget(total_lbl)
        layout.addLayout(total_row)

        close_btn = QPushButton("✖ Close"); close_btn.setFixedHeight(38)
        close_btn.setStyleSheet("background:#1A2A4A;color:white;border-radius:6px;font-weight:600;font-size:12px;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
