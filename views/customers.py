"""
HOE Billing Software - Customers Module
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QLineEdit, QComboBox,
                              QTableWidget, QTableWidgetItem, QDialog,
                              QFormLayout, QMessageBox, QHeaderView,
                              QAbstractItemView, QTextEdit, QGroupBox,
                              QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class CustomerDialog(QDialog):
    def __init__(self, db, customer=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.customer = customer
        self.setWindowTitle("Edit Customer" if customer else "New Customer")
        self.setMinimumWidth(500)
        self._setup_ui()
        if customer:
            self._fill_data(customer)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Customer Information")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #1A2A4A;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.name = QLineEdit(); self.name.setFixedHeight(36)
        self.name.setPlaceholderText("Customer name *")

        self.business = QLineEdit(); self.business.setFixedHeight(36)
        self.mobile = QLineEdit(); self.mobile.setFixedHeight(36)
        self.email = QLineEdit(); self.email.setFixedHeight(36)
        self.gst = QLineEdit(); self.gst.setFixedHeight(36)
        self.gst.setPlaceholderText("Optional - for B2B invoices")

        self.address = QTextEdit()
        self.address.setFixedHeight(60)

        self.city = QLineEdit(); self.city.setFixedHeight(36)
        self.state = QLineEdit(); self.state.setFixedHeight(36)
        self.pincode = QLineEdit(); self.pincode.setFixedHeight(36)

        self.customer_type = QComboBox(); self.customer_type.setFixedHeight(36)
        self.customer_type.addItems(["retail", "business", "wholesale", "dealer", "distributor", "corporate"])

        self.status = QComboBox(); self.status.setFixedHeight(36)
        self.status.addItems(["active", "inactive", "blocked", "vip"])

        form.addRow("Name *:", self.name)
        form.addRow("Business Name:", self.business)
        form.addRow("Mobile:", self.mobile)
        form.addRow("Email:", self.email)
        form.addRow("GST Number:", self.gst)
        form.addRow("Address:", self.address)
        form.addRow("City:", self.city)
        form.addRow("State:", self.state)
        form.addRow("Pincode:", self.pincode)
        form.addRow("Customer Type:", self.customer_type)
        form.addRow("Status:", self.status)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setFixedHeight(40)
        save_btn.setObjectName("btn_success")
        save_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _fill_data(self, c):
        self.name.setText(c.get("customer_name", ""))
        self.business.setText(c.get("business_name", ""))
        self.mobile.setText(c.get("mobile", ""))
        self.email.setText(c.get("email", ""))
        self.gst.setText(c.get("gst_number", ""))
        self.address.setPlainText(c.get("address", ""))
        self.city.setText(c.get("city", ""))
        self.state.setText(c.get("state", ""))
        self.pincode.setText(c.get("pincode", ""))
        self.customer_type.setCurrentText(c.get("customer_type", "retail"))
        self.status.setCurrentText(c.get("status", "active"))

    def get_data(self):
        return {
            "customer_name": self.name.text().strip(),
            "business_name": self.business.text().strip(),
            "mobile": self.mobile.text().strip(),
            "email": self.email.text().strip(),
            "gst_number": self.gst.text().strip(),
            "address": self.address.toPlainText().strip(),
            "city": self.city.text().strip(),
            "state": self.state.text().strip(),
            "pincode": self.pincode.text().strip(),
            "customer_type": self.customer_type.currentText(),
            "status": self.status.currentText(),
        }


class CustomersWidget(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Customer Management")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #1A2A4A;")

        add_btn = QPushButton("+ New Customer")
        add_btn.setFixedHeight(38)
        add_btn.setObjectName("btn_success")
        add_btn.clicked.connect(self._add_customer)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(add_btn)
        layout.addLayout(header_row)

        # Search
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by name, mobile, GST...")
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self._load_customers)

        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(38)
        self.status_filter.addItems(["all", "active", "inactive", "blocked", "vip"])
        self.status_filter.currentIndexChanged.connect(self._load_customers)

        search_row.addWidget(self.search_input, 3)
        search_row.addWidget(self.status_filter)
        layout.addLayout(search_row)

        # Table
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(7)
        self.customers_table.setHorizontalHeaderLabels([
            "Name", "Business", "Mobile", "GST Number", "City", "Type", "Status"
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.customers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.doubleClicked.connect(self._edit_customer)
        layout.addWidget(self.customers_table)

        # Actions
        action_row = QHBoxLayout()
        for label, fn, obj_name in [
            ("✏️ Edit", self._edit_customer, "btn_edit"),
            ("📄 View Ledger", self._view_ledger, "btn_info"),
            ("💰 Add Payment", self._add_payment, "btn_success"),
            ("🗑 Delete", self._delete_customer, "btn_danger"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            if obj_name:
                btn.setObjectName(obj_name)
            btn.clicked.connect(fn)
            action_row.addWidget(btn)
        action_row.addStretch()
        layout.addLayout(action_row)
        
        self.setStyleSheet("""
        QPushButton {
            padding: 8px 15px;
            border-radius: 6px;
            font-weight: bold;
            color: white;
        }

        /* Edit Button */
        QPushButton#btn_edit {
            background-color: #f39c12;
        }
        QPushButton#btn_edit:hover {
            background-color: #e67e22;
        }

        /* View Ledger Button */
        QPushButton#btn_info {
            background-color: #3498db;
        }
        QPushButton#btn_info:hover {
            background-color: #2980b9;
        }

        /* Add Payment Button */
        QPushButton#btn_success {
            background-color: #27ae60;
        }
        QPushButton#btn_success:hover {
            background-color: #219150;
        }

        /* Delete Button */
        QPushButton#btn_danger {
            background-color: #e74c3c;
        }
        QPushButton#btn_danger:hover {
            background-color: #c0392b;
        }
        """)
                
        
        
        
        
        
        
    def refresh(self):
        self._load_customers()

    def _load_customers(self):
        search = self.search_input.text()
        status = self.status_filter.currentText()
        customers = self.db.get_customers(search=search, status=status)
        self.customers_table.setRowCount(len(customers))
        for i, c in enumerate(customers):
            row_data = [
                c["customer_name"], c.get("business_name", ""), c.get("mobile", ""),
                c.get("gst_number", ""), c.get("city", ""),
                c.get("customer_type", "").title(), c.get("status", "").upper()
            ]
            for j, text in enumerate(row_data):
                item = QTableWidgetItem(str(text) if text else "")
                item.setData(Qt.UserRole, c["id"])
                if j == 6:
                    colors = {"ACTIVE": "#27AE60", "INACTIVE": "#718096",
                              "BLOCKED": "#E74C3C", "VIP": "#F39C12"}
                    item.setForeground(QColor(colors.get(text, "#666")))
                self.customers_table.setItem(i, j, item)

    def _get_selected_id(self):
        row = self.customers_table.currentRow()
        if row >= 0:
            item = self.customers_table.item(row, 0)
            return item.data(Qt.UserRole) if item else None
        return None

    def _add_customer(self):
        dlg = CustomerDialog(self.db, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if not data["customer_name"]:
                QMessageBox.warning(self, "Error", "Customer name is required.")
                return
            self.db.save_customer(data)
            self._load_customers()
            QMessageBox.information(self, "Success", "✅ Customer added!")

    def _edit_customer(self):
        cid = self._get_selected_id()
        if not cid:
            QMessageBox.warning(self, "Select", "Please select a customer.")
            return
        c = self.db.get_customer(cid)
        if c:
            dlg = CustomerDialog(self.db, c, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.get_data()
                self.db.save_customer(data, customer_id=cid)
                self._load_customers()

    def _view_ledger(self):
        cid = self._get_selected_id()
        if not cid:
            return
        from views.ledgers import CustomerLedgerDialog
        dlg = CustomerLedgerDialog(self.db, cid, self)
        dlg.exec_()

    def _add_payment(self):
        cid = self._get_selected_id()
        if not cid:
            QMessageBox.warning(self, "Select", "Please select a customer.")
            return
        from views.payment_dialog import PaymentDialog
        dlg = PaymentDialog(self.db, cid, "customer", self)
        if dlg.exec_() == QDialog.Accepted:
            self.db.save_customer_payment(dlg.get_data(), self.user["id"])
            QMessageBox.information(self, "Payment", "✅ Payment recorded!")

    def _delete_customer(self):
        if self.user["role"] != "admin":
            QMessageBox.warning(self, "Permission", "Only admin can delete customers.")
            return
        cid = self._get_selected_id()
        if not cid:
            return
        reply = QMessageBox.question(self, "Delete", "Delete this customer?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = self.db.get_connection()
            conn.execute("UPDATE customers SET status='inactive' WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self._load_customers()
