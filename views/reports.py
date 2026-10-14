from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox, QDateEdit, QFrame, QTabWidget)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

class ReportsWidget(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db; self.user = user
        layout = QVBoxLayout(self); layout.setContentsMargins(16,16,16,16); layout.setSpacing(12)
        t = QLabel("Reports"); t.setFont(QFont("Segoe UI",16,700)); t.setStyleSheet("color:#1A2A4A;"); layout.addWidget(t)
        tabs = QTabWidget(); layout.addWidget(tabs)
        for title, widget in [("Sales Report", self._build_sales()), ("Inventory Report", self._build_inventory()),
                               ("Customer Report", self._build_customers())]:
            tabs.addTab(widget, title)
    def refresh(self): pass
    def _build_sales(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)
        fr = QHBoxLayout()
        self.from_date = QDateEdit(QDate.currentDate().addDays(-30)); self.from_date.setCalendarPopup(True); self.from_date.setFixedHeight(36)
        self.to_date = QDateEdit(QDate.currentDate()); self.to_date.setCalendarPopup(True); self.to_date.setFixedHeight(36)
        load_btn = QPushButton("📊 Load Report"); load_btn.setFixedHeight(36); load_btn.clicked.connect(self._load_sales); load_btn.setStyleSheet("background-color:#2980B9;color:white;")
        fr.addWidget(QLabel("From:")); fr.addWidget(self.from_date)
        fr.addWidget(QLabel("To:")); fr.addWidget(self.to_date); fr.addWidget(load_btn); fr.addStretch()
        layout.addLayout(fr)
        self.sales_table = QTableWidget(); self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels(["Invoice #","Customer","Date","Subtotal","GST","Total"])
        self.sales_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sales_table.setAlternatingRowColors(True); self.sales_table.verticalHeader().setVisible(False)
        layout.addWidget(self.sales_table)
        self.sales_summary = QLabel(); self.sales_summary.setStyleSheet("font-weight:600;color:#1A2A4A;font-size:13px;")
        layout.addWidget(self.sales_summary)
        self._load_sales(); return w
    def _load_sales(self):
        fd = self.from_date.date().toString("yyyy-MM-dd"); td = self.to_date.date().toString("yyyy-MM-dd")
        invoices = self.db.get_invoices(date_from=fd, date_to=td)
        self.sales_table.setRowCount(len(invoices))
        total = 0
        for i, inv in enumerate(invoices):
            self.sales_table.setItem(i,0,QTableWidgetItem(inv["invoice_number"]))
            self.sales_table.setItem(i,1,QTableWidgetItem(inv.get("customer_name","Walk-in") or "Walk-in"))
            self.sales_table.setItem(i,2,QTableWidgetItem(str(inv["invoice_date"])))
            for j, key in [(3,"subtotal"),(4,"cgst"),(5,"final_amount")]:
                it = QTableWidgetItem(f"₹{inv.get(key,0):,.2f}"); it.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                self.sales_table.setItem(i,j,it)
            total += inv.get("final_amount",0)
        self.sales_summary.setText(f"Total Sales: ₹{total:,.2f}  |  Invoices: {len(invoices)}")
    def _build_inventory(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(12,12,12,12)
        table = QTableWidget(); table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Product","Stock","Purchase Price","Selling Price","Inventory Value"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True); table.verticalHeader().setVisible(False)
        products = self.db.get_products(status="all")
        table.setRowCount(len(products))
        for i, p in enumerate(products):
            table.setItem(i,0,QTableWidgetItem(p["product_name"]))
            table.setItem(i,1,QTableWidgetItem(str(p["stock_quantity"])))
            for j, key in [(2,"purchase_price"),(3,"selling_price")]:
                it = QTableWidgetItem(f"₹{p.get(key,0):,.2f}"); it.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter); table.setItem(i,j,it)
            val = p["stock_quantity"]*p["purchase_price"]
            vi = QTableWidgetItem(f"₹{val:,.2f}"); vi.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter); table.setItem(i,4,vi)
        layout.addWidget(table); return w
    def _build_customers(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(12,12,12,12)
        table = QTableWidget(); table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Customer","Mobile","Total Invoices","Outstanding"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True); table.verticalHeader().setVisible(False)
        customers = self.db.get_customers()
        table.setRowCount(len(customers))
        for i, c in enumerate(customers):
            table.setItem(i,0,QTableWidgetItem(c["customer_name"]))
            table.setItem(i,1,QTableWidgetItem(c.get("mobile","") or ""))
            invs = self.db.get_invoices(customer_id=c["id"])
            table.setItem(i,2,QTableWidgetItem(str(len(invs))))
            outstanding = sum(inv.get("balance_amount",0) for inv in invs)
            oi = QTableWidgetItem(f"₹{outstanding:,.2f}"); oi.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter); table.setItem(i,3,oi)
        layout.addWidget(table); return w
