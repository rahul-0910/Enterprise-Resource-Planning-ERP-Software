"""
HOE Billing Software - Dashboard
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QGridLayout, QScrollArea, QTableWidget,
                              QTableWidgetItem, QPushButton, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import datetime


class StatCard(QFrame):
    def __init__(self, icon, title, value, subtitle="", color="#FF6B35", sensitive=False):
        super().__init__()
        self.setFixedHeight(110)
        self._real_value  = str(value)
        self._sensitive   = sensitive
        self._is_hidden   = sensitive   # default HIDDEN for sensitive cards
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
                border: 1px solid #F3F4F6;
            }
            QFrame:hover {
                border: 1px solid #E5E7EB;
            }
        """)
        
        # Soft shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Top row: Icon, Title, Eye-toggle (sensitive cards only)
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        icon_container = QFrame()
        icon_container.setFixedSize(36, 36)
        icon_container.setStyleSheet(f"background: {color}22; border-radius: 18px; border: none;")
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 16px; background: transparent; border: none;")
        icon_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 500; border: none;")
        
        top_row.addWidget(icon_container)
        top_row.addWidget(title_label)
        top_row.addStretch()

        if sensitive:
            self.eye_btn = QPushButton("👁")
            self.eye_btn.setFixedSize(26, 26)
            self.eye_btn.setCursor(Qt.PointingHandCursor)
            self.eye_btn.setStyleSheet("""
                QPushButton {
                    background: #F3F4F6; border: none; border-radius: 13px;
                    font-size: 12px;
                }
                QPushButton:hover { background: #E5E7EB; }
            """)
            self.eye_btn.clicked.connect(self._toggle_visibility)
            top_row.addWidget(self.eye_btn)
        
        layout.addLayout(top_row)

        # Value
        self.value_label = QLabel()
        self.value_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.value_label.setStyleSheet("color: #111827; border: none;")
        layout.addWidget(self.value_label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color: #9CA3AF; font-size: 11px; border: none;")
            layout.addWidget(sub)

        self._update_value_display()

    def _masked_value(self):
        """Amount ko **** se mask karo, lekin currency symbol rakho"""
        v = self._real_value
        if v.startswith("₹"):
            return "₹ ••••••"
        return "••••"

    def _update_value_display(self):
        if self._sensitive and self._is_hidden:
            self.value_label.setText(self._masked_value())
        else:
            self.value_label.setText(self._real_value)
        if self._sensitive:
            self.eye_btn.setText("👁" if self._is_hidden else "🙈")

    def _toggle_visibility(self):
        self._is_hidden = not self._is_hidden
        self._update_value_display()


class SimpleBarChart(QFrame):
    """Simple bar chart using Qt painting."""
    def __init__(self, data, title=""):
        super().__init__()
        self.data = data
        self.chart_title = title
        self.setMinimumHeight(240)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
                border: 1px solid #F3F4F6;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QBrush, QPen, QLinearGradient
        from PyQt5.QtCore import QRect, QPoint
        super().paintEvent(event)
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        padding = 50
        chart_w = w - padding * 2
        chart_h = h - padding * 2

        if not self.data:
            return

        max_val = max(d.get("total", 0) for d in self.data) or 1
        bar_w = max(10, chart_w // max(len(self.data), 1) - 20)

        # Use primary brand colors
        color_primary = QColor("#FF6B35")

        for i, item in enumerate(reversed(self.data[:6])):
            val = item.get("total", 0)
            bar_h = int((val / max_val) * (chart_h - 20))
            x = padding + i * (chart_w // min(len(self.data), 6))
            y = h - padding - bar_h

            painter.setBrush(QBrush(color_primary))
            painter.setPen(Qt.NoPen)
            # Rounded top
            painter.drawRoundedRect(x, y, bar_w, bar_h, 6, 6)
            # Square bottom
            painter.drawRect(x, y + 6, bar_w, bar_h - 6)

            # Label
            painter.setPen(QPen(QColor("#6B7280")))
            painter.setFont(QFont("Segoe UI", 9))
            label = item.get("month", "")[-7:] if item.get("month") else ""
            painter.drawText(QRect(x - 10, h - padding + 8, bar_w + 20, 16),
                             Qt.AlignCenter, label)

            # Value
            if val > 0:
                painter.setPen(QPen(QColor("#111827")))
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                painter.drawText(QRect(x - 10, y - 20, bar_w + 20, 16),
                                 Qt.AlignCenter, f"₹{val:,.0f}")

        painter.end()


class DashboardWidget(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: #F8F9FB;")

        container = QWidget()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(32, 32, 32, 32)
        self.main_layout.setSpacing(24)

        # Greeting
        greeting_layout = QVBoxLayout()
        greeting_layout.setSpacing(4)
        self.greeting_label = QLabel()
        self.greeting_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.greeting_label.setStyleSheet("color: #111827;")
        self.sub_greeting = QLabel("Stay on top of your business, monitor progress, and track status.")
        self.sub_greeting.setStyleSheet("color: #6B7280; font-size: 13px;")
        greeting_layout.addWidget(self.greeting_label)
        greeting_layout.addWidget(self.sub_greeting)
        self.main_layout.addLayout(greeting_layout)

        # Stats grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(20)
        self.main_layout.addLayout(self.stats_grid)

        # Charts row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(20)

        # Monthly Sales Chart
        chart_col = QVBoxLayout()
        chart_col.setSpacing(12)
        chart_title = QLabel("Total Income")
        chart_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        chart_title.setStyleSheet("color: #111827;")
        chart_col.addWidget(chart_title)
        self.sales_chart = SimpleBarChart([], "Monthly Sales")
        chart_col.addWidget(self.sales_chart)
        charts_row.addLayout(chart_col, 7)

        # Alerts Panel
        alerts_col = QVBoxLayout()
        alerts_col.setSpacing(12)
        alerts_title = QLabel("Alerts & Warnings")
        alerts_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        alerts_title.setStyleSheet("color: #111827;")
        alerts_col.addWidget(alerts_title)
        
        self.alerts_frame = QFrame()
        self.alerts_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
                border: 1px solid #F3F4F6;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        self.alerts_frame.setGraphicsEffect(shadow)
        
        self.alerts_container = QVBoxLayout(self.alerts_frame)
        self.alerts_container.setContentsMargins(16, 16, 16, 16)
        self.alerts_container.setSpacing(12)
        self.alerts_container.addStretch()
        
        alerts_col.addWidget(self.alerts_frame)
        charts_row.addLayout(alerts_col, 3)

        self.main_layout.addLayout(charts_row)

        # Recent invoices table
        recent_title = QLabel("Recent Activities")
        recent_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        recent_title.setStyleSheet("color: #111827; margin-top: 12px;")
        self.main_layout.addWidget(recent_title)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(4)
        self.recent_table.setHorizontalHeaderLabels(["Invoice ID", "Customer", "Date", "Amount"])
        self.recent_table.horizontalHeader().setStretchLastSection(True)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setAlternatingRowColors(False)
        self.recent_table.setFixedHeight(220)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setShowGrid(False)
        self.recent_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #F3F4F6;
                border-radius: 12px;
                color: #4B5563;
                font-size: 13px;
                padding: 4px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #F3F4F6;
                padding: 12px 8px;
            }
            QHeaderView::section {
                background: white;
                color: #6B7280;
                padding: 12px 8px;
                font-weight: 600;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                font-size: 13px;
            }
        """)
        shadow_table = QGraphicsDropShadowEffect()
        shadow_table.setBlurRadius(15)
        shadow_table.setColor(QColor(0, 0, 0, 10))
        shadow_table.setOffset(0, 4)
        self.recent_table.setGraphicsEffect(shadow_table)
        
        self.main_layout.addWidget(self.recent_table)
        self.main_layout.addStretch()

    def refresh(self):
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        self.greeting_label.setText(f"{greeting}, {self.user['full_name']}")

        stats = self.db.get_dashboard_stats()

        # Clear and rebuild stats cards
        while self.stats_grid.count():
            item = self.stats_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Layout: 2 rows, 4 columns
        # 6th element = sensitive (True = eye-toggle, default hidden)
        cards = [
            ("💰", "Today's Sales",     f"₹{stats['today_sales']:,.2f}",            "",            "#FF6B35", True),
            ("📅", "Monthly Sales",     f"₹{stats['monthly_sales']:,.2f}",          "",            "#3B82F6", True),
            ("👥", "Total Customers",   str(stats["total_customers"]),              "",            "#8B5CF6", False),
            ("📦", "Total Products",    str(stats["total_products"]),               "",            "#10B981", False),
            ("🏭", "Suppliers",         str(stats["total_suppliers"]),              "",            "#F59E0B", False),
            ("⚠️", "Outstanding",       f"₹{stats['outstanding_receivable']:,.2f}", "Receivable",  "#EF4444", True),
            ("📊", "Inventory Value",   f"₹{stats['inventory_value']:,.2f}",        "",            "#6366F1", True),
            ("🔴", "Low Stock",         str(stats["low_stock_count"]),              "Products",    "#F97316", False),
        ]
        for i, (icon, title, value, subtitle, color, sensitive) in enumerate(cards):
            card = StatCard(icon, title, value, subtitle, color, sensitive=sensitive)
            self.stats_grid.addWidget(card, i // 4, i % 4)

        # Update chart
        self.sales_chart.data = stats.get("monthly_chart", [])
        self.sales_chart.update()

        # Alerts
        # Clear existing alerts
        while self.alerts_container.count() > 1: # Keep the stretch
            item = self.alerts_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        has_alerts = False
        if stats["low_stock_count"] > 0:
            self._add_alert(f"{stats['low_stock_count']} products low on stock", "#F59E0B", "⚠️")
            has_alerts = True
        if stats["out_of_stock_count"] > 0:
            self._add_alert(f"{stats['out_of_stock_count']} products out of stock", "#EF4444", "🔴")
            has_alerts = True
        if stats["outstanding_receivable"] > 0:
            self._add_alert(f"Outstanding: ₹{stats['outstanding_receivable']:,.2f}", "#3B82F6", "💳")
            has_alerts = True
            
        if not has_alerts:
            lbl = QLabel("No active alerts.")
            lbl.setStyleSheet("color: #9CA3AF; font-size: 13px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.alerts_container.insertWidget(0, lbl)

        # Recent invoices table
        self.recent_table.setRowCount(len(stats["recent_invoices"]))
        for i, inv in enumerate(stats["recent_invoices"]):
            # ID
            id_item = QTableWidgetItem(inv.get("invoice_number", ""))
            id_item.setForeground(QColor("#111827"))
            font = QFont()
            font.setBold(True)
            id_item.setFont(font)
            self.recent_table.setItem(i, 0, id_item)
            
            # Customer
            self.recent_table.setItem(i, 1, QTableWidgetItem(inv.get("customer_name", "Walk-in")))
            
            # Date
            self.recent_table.setItem(i, 2, QTableWidgetItem(str(inv.get("invoice_date", ""))))
            
            # Amount
            amt = QTableWidgetItem(f"₹{inv.get('final_amount', 0):,.2f}")
            amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt.setForeground(QColor("#111827"))
            self.recent_table.setItem(i, 3, amt)

    def _add_alert(self, text, color, icon):
        lbl = QLabel(f"{icon}  {text}")
        lbl.setStyleSheet(f"""
            background: {color}15; color: {color};
            border-radius: 8px; padding: 12px 16px;
            font-size: 13px; font-weight: 600;
        """)
        self.alerts_container.insertWidget(self.alerts_container.count() - 1, lbl)