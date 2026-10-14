"""
ITR & CA Export Module - Database Functions
HOE Billing Software ke actual DB structure ke saath compatible
"""

import sqlite3
from datetime import datetime, date
from typing import Optional


def get_db_connection(db_path: str = "billing.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def setup_itr_tables(db_path: str = "billing.db"):
    """ITR module ke liye tables verify karta hai — existing tables safe hain."""
    conn = get_db_connection(db_path)
    conn.close()


# ─────────────────────────────────────────────
# SALES DATA
# invoices table mein customer_name nahi hai —
# customers table se JOIN karna padega
# ─────────────────────────────────────────────

def fetch_sales_data(from_date: str, to_date: str, db_path: str = "billing.db") -> list:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            i.invoice_number                            AS invoice_number,
            i.invoice_date                              AS invoice_date,
            COALESCE(c.customer_name, 'Walk-in')        AS customer_name,
            COALESCE(c.gst_number, '-')                 AS customer_gst,
            COALESCE(i.subtotal, 0)                     AS taxable_amount,
            COALESCE(i.cgst, 0)                         AS cgst_amount,
            COALESCE(i.sgst, 0)                         AS sgst_amount,
            COALESCE(i.igst, 0)                         AS igst_amount,
            COALESCE(i.final_amount, 0)                 AS total_amount,
            COALESCE(i.paid_amount, 0)                  AS paid_amount,
            COALESCE(i.balance_amount, 0)               AS balance_amount,
            COALESCE(i.payment_status, '-')             AS payment_status,
            COALESCE(i.payment_method, '-')             AS payment_method
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        WHERE i.invoice_date BETWEEN ? AND ?
        ORDER BY i.invoice_date ASC
    """, (from_date, to_date))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────
# PURCHASE DATA
# purchases table mein supplier_name nahi —
# suppliers table se JOIN karna padega
# invoice_number bhi nahi hai — purchase_number use karenge
# taxable_amount nahi — total_amount use karenge
# ─────────────────────────────────────────────

def fetch_purchase_data(from_date: str, to_date: str, db_path: str = "billing.db") -> list:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            p.purchase_number                           AS purchase_number,
            p.purchase_date                             AS invoice_date,
            COALESCE(s.supplier_name, '-')              AS supplier_name,
            COALESCE(s.gst_number, '-')                 AS supplier_gst,
            p.purchase_number                           AS invoice_number,
            p.purchase_date                             AS purchase_date,
            COALESCE(p.total_amount, 0)                 AS taxable_amount,
            COALESCE(p.cgst, 0) + COALESCE(p.sgst, 0)  AS gst_amount,
            COALESCE(p.grand_total, 0)                  AS total_amount,
            COALESCE(p.paid_amount, 0)                  AS paid_amount,
            COALESCE(p.balance_amount, 0)               AS balance_amount
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.purchase_date BETWEEN ? AND ?
        ORDER BY p.purchase_date ASC
    """, (from_date, to_date))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────
# EXPENSE DATA
# ─────────────────────────────────────────────

def fetch_expense_data(from_date: str, to_date: str, db_path: str = "billing.db") -> list:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            expense_date   AS "Expense Date",
            category       AS "Category",
            expense_name   AS "Expense Name",
            amount         AS "Amount",
            gst_amount     AS "GST Amount",
            total_amount   AS "Total Amount"
        FROM expenses
        WHERE expense_date BETWEEN ? AND ?
        ORDER BY expense_date ASC
    """, (from_date, to_date))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────
# CUSTOMER LEDGER
# invoices mein customer_name nahi — JOIN karo
# ─────────────────────────────────────────────

def fetch_customer_ledger(from_date: str, to_date: str, db_path: str = "billing.db") -> list:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COALESCE(c.customer_name, 'Walk-in')            AS customer_name,
            COALESCE(c.gst_number, '-')                     AS customer_gst,
            COUNT(i.id)                                     AS total_invoices,
            ROUND(SUM(COALESCE(i.final_amount, 0)), 2)      AS total_sales,
            ROUND(SUM(COALESCE(i.paid_amount, 0)), 2)       AS total_received,
            ROUND(SUM(COALESCE(i.balance_amount, 0)), 2)    AS outstanding_balance
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        WHERE i.invoice_date BETWEEN ? AND ?
        GROUP BY i.customer_id
        ORDER BY total_sales DESC
    """, (from_date, to_date))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────
# SUPPLIER LEDGER
# purchases mein supplier_name nahi — JOIN karo
# ─────────────────────────────────────────────

def fetch_supplier_ledger(from_date: str, to_date: str, db_path: str = "billing.db") -> list:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COALESCE(s.supplier_name, '-')                      AS supplier_name,
            COALESCE(s.gst_number, '-')                         AS supplier_gst,
            COUNT(p.id)                                         AS total_bills,
            ROUND(SUM(COALESCE(p.grand_total, 0)), 2)           AS total_purchase,
            ROUND(SUM(COALESCE(p.paid_amount, 0)), 2)           AS total_paid,
            ROUND(SUM(COALESCE(p.balance_amount, 0)), 2)        AS outstanding_balance
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.purchase_date BETWEEN ? AND ?
        GROUP BY p.supplier_id
        ORDER BY total_purchase DESC
    """, (from_date, to_date))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────
# GST SUMMARY
# invoices mein subtotal = taxable amount
# purchases mein total_amount = taxable amount
# ─────────────────────────────────────────────

def fetch_gst_summary(from_date: str, to_date: str, db_path: str = "billing.db") -> dict:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ROUND(COALESCE(SUM(subtotal), 0), 2)    AS taxable_sales,
            ROUND(COALESCE(SUM(cgst), 0), 2)        AS total_cgst,
            ROUND(COALESCE(SUM(sgst), 0), 2)        AS total_sgst,
            ROUND(COALESCE(SUM(igst), 0), 2)        AS total_igst
        FROM invoices
        WHERE invoice_date BETWEEN ? AND ?
    """, (from_date, to_date))
    sales_gst = dict(cursor.fetchone())

    cursor.execute("""
        SELECT
            ROUND(COALESCE(SUM(total_amount), 0), 2)                        AS taxable_purchases,
            ROUND(COALESCE(SUM(COALESCE(cgst,0)+COALESCE(sgst,0)),0), 2)    AS input_gst
        FROM purchases
        WHERE purchase_date BETWEEN ? AND ?
    """, (from_date, to_date))
    purchase_gst = dict(cursor.fetchone())

    conn.close()

    output_gst = ((sales_gst.get("total_cgst") or 0) +
                  (sales_gst.get("total_sgst") or 0) +
                  (sales_gst.get("total_igst") or 0))
    input_gst  = purchase_gst.get("input_gst") or 0

    return {
        "Total Taxable Sales":      round(sales_gst.get("taxable_sales") or 0, 2),
        "Total CGST":               round(sales_gst.get("total_cgst") or 0, 2),
        "Total SGST":               round(sales_gst.get("total_sgst") or 0, 2),
        "Total IGST":               round(sales_gst.get("total_igst") or 0, 2),
        "Total Output GST":         round(output_gst, 2),
        "Total Taxable Purchases":  round(purchase_gst.get("taxable_purchases") or 0, 2),
        "Total Input GST":          round(input_gst, 2),
        "GST Payable (Net)":        round(output_gst - input_gst, 2),
    }


# ─────────────────────────────────────────────
# PROFIT & LOSS SUMMARY
# ─────────────────────────────────────────────

def fetch_profit_loss_summary(from_date: str, to_date: str, db_path: str = "billing.db") -> dict:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(SUM(final_amount),0) FROM invoices WHERE invoice_date BETWEEN ? AND ?",
        (from_date, to_date))
    total_sales = round(cursor.fetchone()[0], 2)

    cursor.execute(
        "SELECT COALESCE(SUM(COALESCE(grand_total,0)),0) FROM purchases WHERE purchase_date BETWEEN ? AND ?",
        (from_date, to_date))
    total_purchases = round(cursor.fetchone()[0], 2)

    # expenses table optional hai — exist na kare toh 0
    try:
        cursor.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM expenses WHERE expense_date BETWEEN ? AND ?",
            (from_date, to_date))
        total_expenses = round(cursor.fetchone()[0], 2)
    except Exception:
        total_expenses = 0.0

    conn.close()

    gross_profit = round(total_sales - total_purchases, 2)
    net_profit   = round(gross_profit - total_expenses, 2)

    return {
        "Total Sales":      total_sales,
        "Total Purchases":  total_purchases,
        "Gross Profit":     gross_profit,
        "Total Expenses":   total_expenses,
        "Net Profit":       net_profit,
    }


# ─────────────────────────────────────────────
# COMPANY INFO
# business_profile table se fetch karo
# ─────────────────────────────────────────────

def fetch_company_info(db_path: str = "billing.db") -> dict:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    # pehle business_profile try karo (actual HOE DB)
    try:
        cursor.execute("SELECT * FROM business_profile LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            r = dict(row)
            return {
                "company_name": r.get("shop_name") or r.get("company_name") or "Hari Om Electric",
                "gst_number":   r.get("gst_number", ""),
                "address":      r.get("address", ""),
                "phone":        r.get("mobile", ""),
                "email":        r.get("email", ""),
            }
    except Exception:
        pass
    # fallback — company_info table
    try:
        cursor.execute("SELECT * FROM company_info LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception:
        pass
    conn.close()
    return {"company_name": "Hari Om Electric", "gst_number": "", "address": "", "phone": "", "email": ""}