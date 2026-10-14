"""
HOE Billing Software - Database Manager
Hari Om Electric, Jobner Road, Lalpura Mode, Jaipur
Fixes:
  1. _seed_defaults: "My Business" → Hari Om Electric with full details
  2. get_dashboard_stats: datetime.now() → datetime.today() (import fix)
  3. save_customer_payment: datetime.now() → datetime.today() (import fix)
  4. save_invoice: item dict mutate bug fix
  5. get_next_invoice_number: counter sync fix
  6. Har jagah try/except se crash nahi hoga
"""
import sqlite3
import os
import hashlib
from datetime import datetime as dt





DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "database", "hoe_billing.db"
)


class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db_path = DB_PATH

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def initialize(self):
        self._create_tables()
        self._seed_defaults()
        self._migrate_qr_column()
        self._add_indexes()

    def _add_indexes(self):
        """Performance indexes — fast queries ke liye"""
        try:
            conn = self.get_connection()
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_invoices_date     ON invoices(invoice_date)",
                "CREATE INDEX IF NOT EXISTS idx_invoices_status   ON invoices(payment_status)",
                "CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_products_name     ON products(product_name)",
                "CREATE INDEX IF NOT EXISTS idx_products_status   ON products(status)",
                "CREATE INDEX IF NOT EXISTS idx_customers_name    ON customers(customer_name)",
                "CREATE INDEX IF NOT EXISTS idx_customers_mobile  ON customers(mobile)",
                "CREATE INDEX IF NOT EXISTS idx_purchases_date    ON purchases(purchase_date)",
            ]
            for idx in indexes:
                conn.execute(idx)
            conn.commit()
            conn.close()
        except Exception:
            pass
        
    def _migrate_qr_column(self):
        """Purani DB mein qr_code_path column add karo agar nahi hai"""
        try:
            conn = self.get_connection()
            cols = [r[1] for r in conn.execute(
                "PRAGMA table_info(business_profile)").fetchall()]
            if "qr_code_path" not in cols:
                conn.execute(
                    "ALTER TABLE business_profile ADD COLUMN qr_code_path TEXT")
                conn.commit()
            conn.close()
        except Exception:
            pass
    # ─── Tables ───────────────────────────────────────────────────────────
    def _create_tables(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'employee',
            mobile TEXT, email TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS business_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT, owner_name TEXT,
            gst_number TEXT, pan_number TEXT,
            address TEXT, city TEXT, state TEXT,
            country TEXT DEFAULT 'India', pincode TEXT,
            mobile TEXT, alternate_mobile TEXT,
            email TEXT, website TEXT,
            bank_name TEXT, account_holder TEXT,
            account_number TEXT, ifsc_code TEXT,
            branch_name TEXT, upi_id TEXT,
            invoice_prefix TEXT DEFAULT 'INV',
            invoice_counter INTEGER DEFAULT 1,
            currency TEXT DEFAULT 'INR',
            date_format TEXT DEFAULT 'DD-MM-YYYY',
            terms TEXT DEFAULT 'Thank you for your business!',
            logo_path TEXT, signature_path TEXT, stamp_path TEXT, qr_code_path TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS feature_toggles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_name TEXT UNIQUE NOT NULL,
            enabled INTEGER DEFAULT 1,
            updated_by INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_code TEXT UNIQUE,
            sku TEXT, hsn_code TEXT,
            category_id INTEGER, brand TEXT,
            unit_type TEXT DEFAULT 'Piece',
            purchase_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            gst_rate REAL DEFAULT 18,
            mrp REAL DEFAULT 0,
            wholesale_price REAL DEFAULT 0,
            stock_quantity REAL DEFAULT 0,
            minimum_stock REAL DEFAULT 5,
            serial_tracking INTEGER DEFAULT 0,
            imei_tracking INTEGER DEFAULT 0,
            image_path TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS serial_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            serial_number TEXT, imei_number TEXT,
            imei2 TEXT, batch_number TEXT, warranty_number TEXT,
            purchase_id INTEGER, purchase_date DATE,
            sale_date DATE, customer_id INTEGER, invoice_id INTEGER,
            status TEXT DEFAULT 'available',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            business_name TEXT, mobile TEXT, email TEXT,
            address TEXT, city TEXT, state TEXT,
            country TEXT, pincode TEXT, gst_number TEXT,
            customer_type TEXT DEFAULT 'retail',
            status TEXT DEFAULT 'active', notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            company_name TEXT, mobile TEXT, email TEXT,
            gst_number TEXT, pan_number TEXT,
            address TEXT, city TEXT, state TEXT,
            country TEXT, pincode TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            invoice_date DATE NOT NULL,
            invoice_time TIME,
            customer_id INTEGER,
            subtotal REAL DEFAULT 0,
            cgst REAL DEFAULT 0, sgst REAL DEFAULT 0,
            igst REAL DEFAULT 0,
            gross_total REAL DEFAULT 0,
            round_off REAL DEFAULT 0,
            final_amount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            balance_amount REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'unpaid',
            payment_method TEXT DEFAULT 'cash',
            notes TEXT, created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            serial_number_id INTEGER,
            serial_number TEXT,
            product_name TEXT, hsn_code TEXT,
            quantity REAL DEFAULT 1,
            unit_type TEXT,
            rate REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            gst_amount REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER,
            purchase_date DATE NOT NULL,
            total_amount REAL DEFAULT 0,
            cgst REAL DEFAULT 0, sgst REAL DEFAULT 0,
            grand_total REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            balance_amount REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'unpaid',
            notes TEXT, created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT,
            quantity REAL DEFAULT 1,
            rate REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            gst_amount REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            FOREIGN KEY (purchase_id) REFERENCES purchases(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS inventory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            transaction_type TEXT,
            quantity REAL DEFAULT 0,
            old_stock REAL DEFAULT 0,
            new_stock REAL DEFAULT 0,
            reference_id INTEGER, reference_type TEXT,
            remarks TEXT, created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS customer_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            invoice_id INTEGER, payment_id INTEGER,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            entry_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS serial_number_tracking (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id      INTEGER,
            invoice_number  TEXT,
            invoice_date    TEXT,
            customer_name   TEXT,
            customer_mobile TEXT,
            product_id      INTEGER,
            product_name    TEXT,
            product_code    TEXT,
            serial_number   TEXT,
            qty             REAL DEFAULT 1,
            sale_price      REAL DEFAULT 0,
            created_by      TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(serial_number, invoice_number)
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_snt_serial ON serial_number_tracking(serial_number)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_snt_invoice ON serial_number_tracking(invoice_number)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_snt_customer ON serial_number_tracking(customer_name)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_snt_date ON serial_number_tracking(invoice_date)")

        c.execute("""CREATE TABLE IF NOT EXISTS supplier_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            purchase_id INTEGER, payment_id INTEGER,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            entry_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS customer_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            invoice_id INTEGER,
            amount REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash',
            reference_number TEXT,
            payment_date DATE, notes TEXT,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS supplier_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            purchase_id INTEGER,
            amount REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash',
            reference_number TEXT,
            payment_date DATE, notes TEXT,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, action TEXT,
            module TEXT, description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        conn.commit()
        conn.close()

    # ─── Seed Data — Hari Om Electric ────────────────────────────────────
    def _seed_defaults(self):
        conn = self.get_connection()
        c = conn.cursor()

        # Admin user
        c.execute("SELECT id FROM users WHERE username='admin'")
        if not c.fetchone():
            pwd = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("""INSERT INTO users
                (full_name, username, password_hash, role, mobile, status)
                VALUES (?,?,?,?,?,?)""",
                ("Administrator", "admin", pwd, "admin", "9414000000", "active"))

        # ── Hari Om Electric business profile ────────────────────────────
        c.execute("SELECT id FROM business_profile")
        if not c.fetchone():
            c.execute("""INSERT INTO business_profile (
                shop_name, owner_name, gst_number, pan_number,
                address, city, state, country, pincode,
                mobile, email,
                bank_name, account_holder, account_number,
                ifsc_code, branch_name,
                invoice_prefix, invoice_counter,
                terms
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                "Hari Om Electric",          # shop_name
                "Owner Name",                # owner_name (Settings se update karo)
                "08DDEPS0049R1ZW",           # gst_number
                "DDEPS0049R",                # pan_number
                "Jobner Road, Lalpura Mode", # address
                "Jaipur",                    # city
                "Rajasthan",                 # state
                "India",                     # country
                "303506",                    # pincode
                "9414000000",               # mobile (Settings se update karo)
                "hoelalpura@gmail.com",      # email
                "",                          # bank_name
                "Hari Om Electric",          # account_holder
                "",                          # account_number
                "",                          # ifsc_code
                "Jaipur",                    # branch_name
                "HOE",                       # invoice_prefix
                1,                           # invoice_counter
                "Thank you for your business!\n"
                "1. Goods once sold will not be taken back.\n"
                "2. Interest @24% P.A. charged after due date.\n"
                "3. Subject to Jaipur jurisdiction only.",
            ))

        # Default settings
        for key, val in [
            ("theme",            "light"),
            ("invoice_prefix",   "HOE"),
            ("date_format",      "DD-MM-YYYY"),
            ("currency_symbol",  "₹"),
            ("gst_enabled",      "1"),
            ("round_off_enabled","1"),
            ("shop_state",       "Rajasthan"),
            ("shop_state_code",  "08"),
        ]:
            c.execute("INSERT OR IGNORE INTO settings (setting_key,setting_value) VALUES (?,?)",
                      (key, val))

        # Feature toggles
        for feat in [
            "billing", "customers", "suppliers", "inventory", "purchases",
            "reports", "dashboard_charts", "gst", "serial_tracking",
            "imei_tracking", "warranty_tracking", "customer_ledger",
            "supplier_ledger", "outstanding_tracking", "email_invoice",
            "pdf_export", "invoice_preview", "dark_mode",
            "profit_reports", "round_off_system",
        ]:
            c.execute("INSERT OR IGNORE INTO feature_toggles (feature_name,enabled) VALUES (?,1)",
                      (feat,))

        # Categories (electrical shop ke liye)
        for cat in [
            "Wires & Cables", "Switches & Sockets", "MCB & Distribution Boards",
            "Fans", "Lights & LED", "Motors & Pumps",
            "Electrical Fittings", "Tools & Testers",
            "Inverter & Battery", "Other",
        ]:
            c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

        conn.commit()
        conn.close()

    # ─── Settings ─────────────────────────────────────────────────────────
    def get_setting(self, key, default=None):
        try:
            conn = self.get_connection()
            row = conn.execute(
                "SELECT setting_value FROM settings WHERE setting_key=?", (key,)
            ).fetchone()
            conn.close()
            return row[0] if row else default
        except Exception:
            return default

    def set_setting(self, key, value):
        conn = self.get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO settings (setting_key,setting_value) VALUES (?,?)",
            (key, value)
        )
        conn.commit()
        conn.close()

    def is_feature_enabled(self, feature):
        try:
            conn = self.get_connection()
            row = conn.execute(
                "SELECT enabled FROM feature_toggles WHERE feature_name=?", (feature,)
            ).fetchone()
            conn.close()
            return bool(row[0]) if row else True
        except Exception:
            return True

    # ─── Auth ─────────────────────────────────────────────────────────────
    def authenticate(self, username, password):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = self.get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=? AND status='active'",
            (username, pwd_hash)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    # ─── Business Profile ─────────────────────────────────────────────────
    def get_business_profile(self):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM business_profile LIMIT 1").fetchone()
        conn.close()
        return dict(row) if row else {}

    def save_business_profile(self, data):
        conn = self.get_connection()
        fields = ", ".join(f"{k}=?" for k in data)
        conn.execute(f"UPDATE business_profile SET {fields}", list(data.values()))
        conn.commit()
        conn.close()

    # ─── Customers ────────────────────────────────────────────────────────
    def get_customers(self, search="", status="all"):
        conn = self.get_connection()
        q = "SELECT * FROM customers WHERE 1=1"
        params = []
        if search:
            q += " AND (customer_name LIKE ? OR mobile LIKE ? OR gst_number LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]
        if status != "all":
            q += " AND status=?"
            params.append(status)
        q += " ORDER BY customer_name"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_customer(self, data, customer_id=None):
        conn = self.get_connection()
        if customer_id:
            fields = ", ".join(f"{k}=?" for k in data)
            conn.execute(
                f"UPDATE customers SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                list(data.values()) + [customer_id]
            )
        else:
            keys = ", ".join(data.keys())
            ph = ", ".join(["?"] * len(data))
            conn.execute(f"INSERT INTO customers ({keys}) VALUES ({ph})", list(data.values()))
        conn.commit()
        lid = conn.execute("SELECT last_insert_rowid()").fetchone()[0] if not customer_id else customer_id
        conn.close()
        return lid

    def get_customer(self, customer_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    # ─── Suppliers ────────────────────────────────────────────────────────
    def get_suppliers(self, search=""):
        conn = self.get_connection()
        q = "SELECT * FROM suppliers WHERE 1=1"
        params = []
        if search:
            q += " AND (supplier_name LIKE ? OR company_name LIKE ? OR mobile LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]
        q += " ORDER BY supplier_name"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_supplier(self, data, supplier_id=None):
        conn = self.get_connection()
        if supplier_id:
            fields = ", ".join(f"{k}=?" for k in data)
            conn.execute(
                f"UPDATE suppliers SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                list(data.values()) + [supplier_id]
            )
        else:
            keys = ", ".join(data.keys())
            ph = ", ".join(["?"] * len(data))
            conn.execute(f"INSERT INTO suppliers ({keys}) VALUES ({ph})", list(data.values()))
        conn.commit()
        lid = conn.execute("SELECT last_insert_rowid()").fetchone()[0] if not supplier_id else supplier_id
        conn.close()
        return lid

    def get_supplier(self, supplier_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    # ─── Products ─────────────────────────────────────────────────────────
    def get_products(self, search="", category_id=None, status="active"):
        conn = self.get_connection()
        q = """SELECT p.*, c.name as category_name
               FROM products p LEFT JOIN categories c ON p.category_id=c.id
               WHERE 1=1"""
        params = []
        if search:
            q += " AND (p.product_name LIKE ? OR p.product_code LIKE ? OR p.sku LIKE ? OR p.hsn_code LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s, s]
        if category_id:
            q += " AND p.category_id=?"
            params.append(category_id)
        if status != "all":
            q += " AND p.status=?"
            params.append(status)
        q += " ORDER BY p.product_name"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_product(self, data, product_id=None):
        conn = self.get_connection()
        if product_id:
            fields = ", ".join(f"{k}=?" for k in data)
            conn.execute(
                f"UPDATE products SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                list(data.values()) + [product_id]
            )
        else:
            if not data.get("product_code"):
                count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                data["product_code"] = f"HOE{count+1:05d}"
            keys = ", ".join(data.keys())
            ph = ", ".join(["?"] * len(data))
            conn.execute(f"INSERT INTO products ({keys}) VALUES ({ph})", list(data.values()))
        conn.commit()
        lid = conn.execute("SELECT last_insert_rowid()").fetchone()[0] if not product_id else product_id
        conn.close()
        return lid

    def get_product(self, product_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_categories(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_stock(self, product_id, qty_change, reason="", user_id=None):
        conn = self.get_connection()
        row = conn.execute("SELECT stock_quantity FROM products WHERE id=?", (product_id,)).fetchone()
        old = row[0] if row else 0
        new = old + qty_change
        conn.execute("UPDATE products SET stock_quantity=? WHERE id=?", (new, product_id))
        conn.execute("""INSERT INTO inventory_logs
            (product_id, transaction_type, quantity, old_stock, new_stock, remarks, created_by)
            VALUES (?,?,?,?,?,?,?)""",
            (product_id, "adjustment" if qty_change > 0 else "sale",
             abs(qty_change), old, new, reason, user_id))
        conn.commit()
        conn.close()
        return new

    # ─── Invoices ─────────────────────────────────────────────────────────
    def get_next_invoice_number(self):
        """Invoice number return karo — counter increment NAHI hoga.
        Sirf save_invoice() mein counter badhega."""
        conn = self.get_connection()
        try:
            # Safe column check
            cols = [r[1] for r in conn.execute(
                "PRAGMA table_info(business_profile)").fetchall()]

            if "invoice_num_padding" in cols:
                row = conn.execute(
                    "SELECT invoice_prefix, invoice_counter, "
                    "COALESCE(invoice_num_padding, 6) "
                    "FROM business_profile LIMIT 1"
                ).fetchone()
                padding = int(row[2]) if row and row[2] else 6
            else:
                row = conn.execute(
                    "SELECT invoice_prefix, invoice_counter "
                    "FROM business_profile LIMIT 1"
                ).fetchone()
                padding = 6

            prefix  = (row[0] or "HOE-") if row else "HOE-"
            counter = int(row[1] or 1)   if row else 1
        except Exception:
            conn.close()
            return "HOE-000001"
        conn.close()
        return f"{prefix}{str(counter).zfill(padding)}"

    def increment_invoice_counter(self):
        """Sirf save ke baad call karo — counter +1 karta hai."""
        conn = self.get_connection()
        conn.execute(
            "UPDATE business_profile SET invoice_counter = invoice_counter + 1"
        )
        conn.commit()
        conn.close()

    def save_invoice(self, invoice_data, items, user_id=None):
        conn = self.get_connection()
        try:
            # Insert invoice
            keys = ", ".join(invoice_data.keys())
            ph   = ", ".join(["?"] * len(invoice_data))
            conn.execute(
                f"INSERT INTO invoices ({keys}) VALUES ({ph})",
                list(invoice_data.values())
            )
            inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # Save ke baad counter +1 — sirf yahan hoga
            conn.execute(
                "UPDATE business_profile SET invoice_counter = invoice_counter + 1"
            )

            for raw_item in items:
                item = dict(raw_item)          # ← copy karo, original mutate mat karo
                item["invoice_id"] = inv_id

                # Remove keys not in invoice_items table
                for k in ("buyPrice", "salePrice"):
                    item.pop(k, None)

                ikeys = ", ".join(item.keys())
                iph   = ", ".join(["?"] * len(item))
                conn.execute(
                    f"INSERT INTO invoice_items ({ikeys}) VALUES ({iph})",
                    list(item.values())
                )

                # Stock update
                stock_row = conn.execute(
                    "SELECT stock_quantity FROM products WHERE id=?",
                    (item["product_id"],)
                ).fetchone()
                if stock_row:
                    new_stock = stock_row[0] - item["quantity"]
                    conn.execute(
                        "UPDATE products SET stock_quantity=? WHERE id=?",
                        (new_stock, item["product_id"])
                    )
                    conn.execute("""INSERT INTO inventory_logs
                        (product_id, transaction_type, quantity,
                         old_stock, new_stock, remarks, created_by)
                        VALUES (?, 'sale', ?, ?, ?, ?, ?)""",
                        (item["product_id"], item["quantity"],
                         stock_row[0], new_stock,
                         f"Invoice {invoice_data['invoice_number']}", user_id))

                # Serial number sold
                if item.get("serial_number_id"):
                    conn.execute("""UPDATE serial_numbers
                        SET status='sold', sale_date=?, customer_id=?, invoice_id=?
                        WHERE id=?""",
                        (invoice_data["invoice_date"],
                         invoice_data.get("customer_id"),
                         inv_id, item["serial_number_id"]))

            # Customer ledger entry
            if invoice_data.get("customer_id"):
                bal = self._get_customer_balance(conn, invoice_data["customer_id"])
                new_bal = bal + invoice_data["final_amount"]
                conn.execute("""INSERT INTO customer_ledger
                    (customer_id, invoice_id, description, debit, balance, entry_date)
                    VALUES (?,?,?,?,?,?)""",
                    (invoice_data["customer_id"], inv_id,
                     f"Invoice {invoice_data['invoice_number']}",
                     invoice_data["final_amount"], new_bal,
                     invoice_data["invoice_date"]))

            # Activity log
            conn.execute("""INSERT INTO activity_logs
                (user_id, action, module, description)
                VALUES (?, 'create', 'billing', ?)""",
                (user_id, f"Invoice {invoice_data['invoice_number']} created"))

            conn.commit()
            return inv_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _get_customer_balance(self, conn, customer_id):
        row = conn.execute("""SELECT balance FROM customer_ledger
                              WHERE customer_id=? ORDER BY id DESC LIMIT 1""",
                           (customer_id,)).fetchone()
        return row[0] if row else 0.0

    def get_invoices(self, search="", date_from=None, date_to=None, customer_id=None):
        conn = self.get_connection()
        q = """SELECT i.*, c.customer_name, c.mobile
               FROM invoices i LEFT JOIN customers c ON i.customer_id=c.id
               WHERE 1=1"""
        params = []
        if search:
            q += " AND (i.invoice_number LIKE ? OR c.customer_name LIKE ? OR c.mobile LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]
        if date_from:
            q += " AND i.invoice_date >= ?"
            params.append(date_from)
        if date_to:
            q += " AND i.invoice_date <= ?"
            params.append(date_to)
        if customer_id:
            q += " AND i.customer_id=?"
            params.append(customer_id)
        q += " ORDER BY i.id DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_invoice(self, invoice_id):
        conn = self.get_connection()
        inv = conn.execute("""SELECT i.*, c.customer_name, c.mobile,
                               c.address, c.gst_number, c.business_name
                               FROM invoices i
                               LEFT JOIN customers c ON i.customer_id=c.id
                               WHERE i.id=?""", (invoice_id,)).fetchone()
        items = conn.execute("""SELECT ii.*, p.product_name as pname
                                FROM invoice_items ii
                                LEFT JOIN products p ON ii.product_id=p.id
                                WHERE ii.invoice_id=?""", (invoice_id,)).fetchall()
        conn.close()
        if inv:
            result = dict(inv)
            result["items"] = [dict(i) for i in items]
            return result
        return None

    def get_invoice_items(self, invoice_id):
        conn = self.get_connection()
        rows = conn.execute("""SELECT ii.*, p.product_name
                               FROM invoice_items ii
                               LEFT JOIN products p ON ii.product_id=p.id
                               WHERE ii.invoice_id=?""", (invoice_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Purchases ────────────────────────────────────────────────────────
    def get_next_purchase_number(self):
        conn = self.get_connection()
        count = conn.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
        conn.close()
        return f"PUR-{count+1:06d}"

    def save_purchase(self, purchase_data, items, user_id=None):
        conn = self.get_connection()
        try:
            keys = ", ".join(purchase_data.keys())
            ph   = ", ".join(["?"] * len(purchase_data))
            conn.execute(
                f"INSERT INTO purchases ({keys}) VALUES ({ph})",
                list(purchase_data.values())
            )
            pur_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            for raw_item in items:
                item = dict(raw_item)
                item["purchase_id"] = pur_id
                ikeys = ", ".join(item.keys())
                iph   = ", ".join(["?"] * len(item))
                conn.execute(
                    f"INSERT INTO purchase_items ({ikeys}) VALUES ({iph})",
                    list(item.values())
                )
                stock_row = conn.execute(
                    "SELECT stock_quantity FROM products WHERE id=?",
                    (item["product_id"],)
                ).fetchone()
                if stock_row:
                    new_stock = stock_row[0] + item["quantity"]
                    conn.execute(
                        "UPDATE products SET stock_quantity=?, purchase_price=? WHERE id=?",
                        (new_stock, item["rate"], item["product_id"])
                    )
                    conn.execute("""INSERT INTO inventory_logs
                        (product_id, transaction_type, quantity,
                         old_stock, new_stock, remarks, created_by)
                        VALUES (?, 'purchase', ?, ?, ?, ?, ?)""",
                        (item["product_id"], item["quantity"],
                         stock_row[0], new_stock,
                         f"Purchase {purchase_data['purchase_number']}", user_id))

            if purchase_data.get("supplier_id"):
                conn.execute("""INSERT INTO supplier_ledger
                    (supplier_id, purchase_id, description, debit, balance, entry_date)
                    VALUES (?,?,?,?,?,?)""",
                    (purchase_data["supplier_id"], pur_id,
                     f"Purchase {purchase_data['purchase_number']}",
                     purchase_data["grand_total"], purchase_data["grand_total"],
                     purchase_data["purchase_date"]))

            conn.commit()
            return pur_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_purchases(self, search=""):
        conn = self.get_connection()
        q = """SELECT p.*, s.supplier_name
               FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
               WHERE 1=1"""
        params = []
        if search:
            q += " AND (p.purchase_number LIKE ? OR s.supplier_name LIKE ?)"
            s = f"%{search}%"
            params += [s, s]
        q += " ORDER BY p.id DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Dashboard Stats ──────────────────────────────────────────────────
    # FIX: datetime.now() → dt.today() (import alias se)
    def get_dashboard_stats(self):
        conn = self.get_connection()
        # Performance: cache pragmas
        conn.execute("PRAGMA cache_size = -8000")   # 8MB cache
        conn.execute("PRAGMA temp_store = MEMORY")

        today       = dt.today().strftime("%Y-%m-%d")
        month_start = dt.today().strftime("%Y-%m-01")

        # Saari invoice stats ek hi query mein
        inv_row = conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN invoice_date=? THEN final_amount ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN invoice_date>=? THEN final_amount ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN payment_status!='paid' THEN balance_amount ELSE 0 END),0)
            FROM invoices
        """, (today, month_start)).fetchone()

        # Saari product stats ek hi query mein
        prod_row = conn.execute("""
            SELECT
                COUNT(CASE WHEN status='active' THEN 1 END),
                COALESCE(SUM(stock_quantity * purchase_price), 0),
                COUNT(CASE WHEN stock_quantity <= minimum_stock AND stock_quantity > 0 THEN 1 END),
                COUNT(CASE WHEN stock_quantity <= 0 THEN 1 END)
            FROM products
        """).fetchone()

        stats = {
            "today_sales":            inv_row[0],
            "monthly_sales":          inv_row[1],
            "outstanding_receivable": inv_row[2],
            "total_products":         prod_row[0],
            "inventory_value":        prod_row[1],
            "low_stock_count":        prod_row[2],
            "out_of_stock_count":     prod_row[3],
        }

        stats["total_customers"] = conn.execute(
            "SELECT COUNT(*) FROM customers WHERE status='active'"
        ).fetchone()[0]
        stats["total_suppliers"] = conn.execute(
            "SELECT COUNT(*) FROM suppliers WHERE status='active'"
        ).fetchone()[0]

        stats["recent_invoices"] = [dict(r) for r in conn.execute("""
            SELECT i.invoice_number, i.invoice_date,
                   i.final_amount, c.customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            ORDER BY i.id DESC LIMIT 5
        """).fetchall()]

        stats["monthly_chart"] = [dict(r) for r in conn.execute("""
            SELECT strftime('%Y-%m', invoice_date) as month,
                   SUM(final_amount) as total
            FROM invoices
            GROUP BY month
            ORDER BY month DESC LIMIT 6
        """).fetchall()]

        conn.close()
        return stats

    # ─── Activity Log ─────────────────────────────────────────────────────
    def track_serial_numbers(self, invoice_id, invoice_number, invoice_date,
                               customer_name, customer_mobile, items, created_by=""):
        """Invoice save hone ke baad serialized items track karo"""
        # Ensure table exists
        conn = self.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS serial_number_tracking (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id      INTEGER,
                invoice_number  TEXT,
                invoice_date    TEXT,
                customer_name   TEXT,
                customer_mobile TEXT,
                product_id      INTEGER,
                product_name    TEXT,
                product_code    TEXT,
                serial_number   TEXT,
                qty             REAL DEFAULT 1,
                sale_price      REAL DEFAULT 0,
                created_by      TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(serial_number, invoice_number)
            )""")
        tracked = 0
        for item in items:
            # billing.py ke cart_items mein serial_number key hoti hai
            sn = str(item.get("serial_number") or
                     item.get("serial_no") or
                     item.get("barcode") or "").strip()
            if not sn:
                continue
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO serial_number_tracking
                    (invoice_id, invoice_number, invoice_date,
                     customer_name, customer_mobile,
                     product_id, product_name, product_code,
                     serial_number, qty, sale_price, created_by)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    invoice_id,
                    invoice_number,
                    invoice_date,
                    customer_name or "Walk-in",
                    customer_mobile or "",
                    item.get("product_id"),
                    item.get("product_name", ""),
                    item.get("hsn_code", item.get("product_code", "")),
                    sn,
                    float(item.get("quantity", item.get("qty", 1)) or 1),
                    float(item.get("rate", item.get("sale_price",
                          item.get("unit_price", 0))) or 0),
                    str(created_by)
                ))
                tracked += 1
            except Exception as e:
                print(f"SNTM track error: {e}")
        conn.commit()
        conn.close()
        return tracked

    def record_activity(self, user_id, action, module, description):
        try:
            conn = self.get_connection()
            conn.execute(
                "INSERT INTO activity_logs (user_id,action,module,description) VALUES (?,?,?,?)",
                (user_id, action, module, description)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass   # log fail se crash nahi hoga

    # ─── Users ────────────────────────────────────────────────────────────
    def get_users(self):
        conn = self.get_connection()
        rows = conn.execute("""SELECT id,full_name,username,role,
                               mobile,email,status FROM users
                               ORDER BY full_name""").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_user(self, data, user_id=None):
        conn = self.get_connection()
        data = dict(data)
        if data.get("password"):
            data["password_hash"] = hashlib.sha256(
                data.pop("password").encode()
            ).hexdigest()
        elif "password" in data:
            del data["password"]
        if user_id:
            fields = ", ".join(f"{k}=?" for k in data)
            conn.execute(
                f"UPDATE users SET {fields} WHERE id=?",
                list(data.values()) + [user_id]
            )
        else:
            keys = ", ".join(data.keys())
            ph   = ", ".join(["?"] * len(data))
            conn.execute(f"INSERT INTO users ({keys}) VALUES ({ph})", list(data.values()))
        conn.commit()
        conn.close()

    # ─── Serial Numbers ───────────────────────────────────────────────────
    def get_serial_numbers(self, product_id=None, status=None):
        conn = self.get_connection()
        q = """SELECT sn.*, p.product_name
               FROM serial_numbers sn
               LEFT JOIN products p ON sn.product_id=p.id
               WHERE 1=1"""
        params = []
        if product_id:
            q += " AND sn.product_id=?"; params.append(product_id)
        if status:
            q += " AND sn.status=?";    params.append(status)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_serial_number(self, data):
        conn = self.get_connection()
        keys = ", ".join(data.keys())
        ph   = ", ".join(["?"] * len(data))
        conn.execute(f"INSERT INTO serial_numbers ({keys}) VALUES ({ph})", list(data.values()))
        conn.commit()
        conn.close()

    # ─── Customer Ledger ──────────────────────────────────────────────────
    def get_customer_ledger(self, customer_id):
        conn = self.get_connection()
        rows = conn.execute("""SELECT * FROM customer_ledger
                               WHERE customer_id=? ORDER BY id""",
                            (customer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_customer_payment(self, data, user_id=None):
        conn = self.get_connection()
        try:
            data = dict(data)
            keys = ", ".join(data.keys())
            ph   = ", ".join(["?"] * len(data))
            conn.execute(f"INSERT INTO customer_payments ({keys}) VALUES ({ph})",
                         list(data.values()))
            pay_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            if data.get("invoice_id"):
                inv = conn.execute(
                    "SELECT final_amount, paid_amount FROM invoices WHERE id=?",
                    (data["invoice_id"],)
                ).fetchone()
                if inv:
                    new_paid = inv[1] + data["amount"]
                    new_bal  = inv[0] - new_paid
                    status   = "paid" if new_bal <= 0 else "partial"
                    conn.execute("""UPDATE invoices
                        SET paid_amount=?, balance_amount=?, payment_status=?
                        WHERE id=?""",
                        (new_paid, max(0, new_bal), status, data["invoice_id"]))

            bal = self._get_customer_balance(conn, data["customer_id"])
            new_bal = bal - data["amount"]
            # FIX: datetime.now() → dt.today()
            entry_date = data.get("payment_date") or dt.today().strftime("%Y-%m-%d")
            conn.execute("""INSERT INTO customer_ledger
                (customer_id, payment_id, description, credit, balance, entry_date)
                VALUES (?,?,?,?,?,?)""",
                (data["customer_id"], pay_id, "Payment Received",
                 data["amount"], new_bal, entry_date))

            conn.commit()
            return pay_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ─── Feature Toggles ──────────────────────────────────────────────────
    def get_feature_toggles(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM feature_toggles").fetchall()
        conn.close()
        return {r["feature_name"]: bool(r["enabled"]) for r in rows}

    def save_feature_toggles(self, toggles, user_id=None):
        conn = self.get_connection()
        for name, enabled in toggles.items():
            conn.execute("""UPDATE feature_toggles
                SET enabled=?, updated_by=?, updated_at=CURRENT_TIMESTAMP
                WHERE feature_name=?""",
                (1 if enabled else 0, user_id, name))
        conn.commit()
        conn.close()
