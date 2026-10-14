from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QHBoxLayout, QComboBox, QDoubleSpinBox, QLineEdit, QDateEdit)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QFont

class PaymentDialog(QDialog):
    def __init__(self, db, entity_id, entity_type, parent=None):
        super().__init__(parent)
        self.db = db; self.entity_id = entity_id; self.entity_type = entity_type
        self.setWindowTitle("Record Payment"); self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Payment Details", font=QFont("Segoe UI",13,700)))
        form = QFormLayout(); form.setSpacing(10)
        self.amount = QDoubleSpinBox(); self.amount.setRange(0.01,9999999); self.amount.setPrefix("₹ "); self.amount.setFixedHeight(36)
        self.mode = QComboBox(); self.mode.setFixedHeight(36); self.mode.addItems(["Cash","UPI","Bank Transfer","Card","Cheque"])
        self.ref = QLineEdit(); self.ref.setFixedHeight(36); self.ref.setPlaceholderText("Optional")
        self.date = QDateEdit(QDate.currentDate()); self.date.setCalendarPopup(True); self.date.setFixedHeight(36)
        form.addRow("Amount:", self.amount); form.addRow("Payment Mode:", self.mode)
        form.addRow("Reference #:", self.ref); form.addRow("Date:", self.date); layout.addLayout(form)
        row = QHBoxLayout()
        s = QPushButton("💾 Save"); s.setFixedHeight(40); s.setObjectName("btn_success"); s.clicked.connect(self.accept)
        c = QPushButton("Cancel"); c.setFixedHeight(40); c.setObjectName("btn_secondary"); c.clicked.connect(self.reject)
        row.addWidget(s); row.addWidget(c); layout.addLayout(row)
    def get_data(self):
        return {"customer_id": self.entity_id, "amount": self.amount.value(),
                "payment_method": self.mode.currentText(), "reference_number": self.ref.text(),
                "payment_date": self.date.date().toString("yyyy-MM-dd")}
