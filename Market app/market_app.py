"""
Simple Market Businessman Desktop App - POS + Inventory Manager
Built with Python, Tkinter, and SQLite
"""

import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime, timedelta

# Try importing optional dependencies
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

REPORTLAB_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

DB_NAME = "market.db"
INVOICE_DIR = "invoices"

def init_db(db_path=DB_NAME):
    """Initialize the SQLite database schema."""
    os.makedirs(INVOICE_DIR, exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Products Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            cost_price REAL NOT NULL DEFAULT 0.0,
            selling_price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            min_stock INTEGER NOT NULL DEFAULT 5
        )
    """)

    # Customers Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Sales Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            customer_name TEXT,
            customer_phone TEXT,
            subtotal REAL NOT NULL,
            discount_pct REAL DEFAULT 0.0,
            discount_amt REAL DEFAULT 0.0,
            gst_pct REAL DEFAULT 0.0,
            gst_amt REAL DEFAULT 0.0,
            grand_total REAL NOT NULL,
            payment_method TEXT DEFAULT 'Cash',
            cashier TEXT DEFAULT 'Admin',
            sold_at TEXT NOT NULL
        )
    """)

    # Sale Items Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            sku TEXT,
            product_name TEXT NOT NULL,
            cost_price REAL NOT NULL,
            unit_price REAL NOT NULL,
            qty INTEGER NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(id)
        )
    """)

    # Inventory Movement Log Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            change_type TEXT NOT NULL,
            qty_change INTEGER NOT NULL,
            previous_stock INTEGER,
            new_stock INTEGER,
            reason TEXT,
            logged_at TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()

def seed_sample_data(db_path=DB_NAME):
    """Seed initial demo data if database is empty."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Check if products already exist
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        sample_products = [
            ("SKU-1001", "Basmati Rice 1kg", "Grains & Rice", 75.0, 95.0, 30, 8),
            ("SKU-1002", "Refined Sunflower Oil 1L", "Oils", 110.0, 135.0, 20, 6),
            ("SKU-1003", "Whole Wheat Flour 5kg", "Flour & Atta", 185.0, 220.0, 15, 5),
            ("SKU-1004", "Pure White Sugar 1kg", "Sweeteners", 38.0, 48.0, 50, 10),
            ("SKU-1005", "Assam Gold Tea 250g", "Beverages", 95.0, 125.0, 4, 6),   # Low stock demo
            ("SKU-1006", "Herbal Bathing Soap 125g", "Personal Care", 28.0, 38.0, 3, 8), # Low stock demo
            ("SKU-1007", "Milk Sandwich Bread 400g", "Bakery", 30.0, 42.0, 12, 5),
            ("SKU-1008", "Dark Chocolate Slab 100g", "Confectionery", 65.0, 85.0, 25, 6),
            ("SKU-1009", "Roasted Ground Coffee 200g", "Beverages", 140.0, 180.0, 18, 5),
            ("SKU-1010", "Dishwash Gel 500ml", "Household", 70.0, 95.0, 2, 5)        # Low stock demo
        ]
        cur.executemany("""
            INSERT INTO products (sku, name, category, cost_price, selling_price, stock, min_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_products)

        # Log initial inventory
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("SELECT id, name, stock FROM products")
        for pid, pname, pstock in cur.fetchall():
            cur.execute("""
                INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
                VALUES (?, ?, 'STOCK_IN', ?, 0, ?, 'Initial Inventory Setup', ?)
            """, (pid, pname, pstock, pstock, now_str))

    # Check if customers exist
    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] == 0:
        sample_customers = [
            ("Walk-in Customer", "9999999999", "walkin@market.local", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Ramesh Kumar", "9876543210", "ramesh@example.com", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Priya Sharma", "9811223344", "priya@example.com", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Amit Patel", "9988776655", "amit@example.com", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]
        cur.executemany("""
            INSERT INTO customers (name, phone, email, created_at)
            VALUES (?, ?, ?, ?)
        """, sample_customers)

    # Seed past sales if no sales exist (to populate dashboard & reports)
    cur.execute("SELECT COUNT(*) FROM sales")
    if cur.fetchone()[0] == 0:
        # Create a few demo sales over the last 3 days
        sample_sales_data = [
            ("INV-1001", "Ramesh Kumar", "9876543210", 315.0, 0.0, 0.0, 5.0, 15.75, 330.75, "UPI", "Admin", (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d 10:30:00")),
            ("INV-1002", "Priya Sharma", "9811223344", 405.0, 5.0, 20.25, 5.0, 19.24, 403.99, "Cash", "Admin", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d 14:15:00")),
            ("INV-1003", "Walk-in Customer", "9999999999", 260.0, 0.0, 0.0, 5.0, 13.0, 273.0, "Cash", "Cashier", datetime.now().strftime("%Y-%m-%d 11:20:00"))
        ]
        for inv, cname, cphone, sub, disc_p, disc_a, gst_p, gst_a, total, pay, cashier, dt in sample_sales_data:
            cur.execute("""
                INSERT INTO sales (invoice_no, customer_name, customer_phone, subtotal, discount_pct, discount_amt, gst_pct, gst_amt, grand_total, payment_method, cashier, sold_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (inv, cname, cphone, sub, disc_p, disc_a, gst_p, gst_a, total, pay, cashier, dt))
            sale_id = cur.lastrowid

            # Add demo item
            cur.execute("""
                INSERT INTO sale_items (sale_id, product_id, sku, product_name, cost_price, unit_price, qty, line_total)
                VALUES (?, 1, 'SKU-1001', 'Basmati Rice 1kg', 75.0, 95.0, 2, 190.0)
            """, (sale_id,))

    con.commit()
    con.close()

def generate_invoice_file(sale_id, db_path=DB_NAME):
    """
    Generate either a PDF invoice (if reportlab is installed) or a structured text receipt.
    Returns the file path generated.
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
    sale = cur.fetchone()
    if not sale:
        con.close()
        return None

    # sales columns: id(0), invoice_no(1), customer_id(2), customer_name(3), customer_phone(4),
    # subtotal(5), discount_pct(6), discount_amt(7), gst_pct(8), gst_amt(9),
    # grand_total(10), payment_method(11), cashier(12), sold_at(13)
    invoice_no = sale[1]
    cust_name = sale[3] or "Walk-in Customer"
    cust_phone = sale[4] or "N/A"
    subtotal = sale[5]
    discount_pct = sale[6]
    discount_amt = sale[7]
    gst_pct = sale[8]
    gst_amt = sale[9]
    grand_total = sale[10]
    payment_method = sale[11]
    cashier = sale[12]
    sold_at = sale[13]

    cur.execute("SELECT sku, product_name, unit_price, qty, line_total FROM sale_items WHERE sale_id = ?", (sale_id,))
    items = cur.fetchall()
    con.close()

    os.makedirs(INVOICE_DIR, exist_ok=True)

    if REPORTLAB_AVAILABLE:
        pdf_path = os.path.join(INVOICE_DIR, f"{invoice_no}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1E3A8A'),
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            'InvoiceSub',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=1
        )

        story.append(Paragraph("<b>APNA MARKET - POS & INVENTORY</b>", title_style))
        story.append(Paragraph("Main Market Road, City Center | GSTIN: 22AAAAA0000A1Z5 | Phone: +91 98765 00000", subtitle_style))
        story.append(Spacer(1, 15))

        # Meta info table
        meta_data = [
            [f"Invoice No: {invoice_no}", f"Date: {sold_at}"],
            [f"Customer: {cust_name} ({cust_phone})", f"Payment Mode: {payment_method}"],
            [f"Billed By: {cashier}", "Status: PAID"]
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#333333')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # Items Table
        table_data = [["SKU", "Item Description", "Unit Price (₹)", "Qty", "Total (₹)"]]
        for sku, name, price, qty, ltotal in items:
            table_data.append([sku, name, f"{price:.2f}", str(qty), f"{ltotal:.2f}"])

        items_table = Table(table_data, colWidths=[90, 230, 80, 50, 90])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 10))

        # Totals Summary
        summary_data = [
            ["Subtotal:", f"₹ {subtotal:.2f}"],
            [f"Discount ({discount_pct:.1f}%):", f"- ₹ {discount_amt:.2f}"],
            [f"GST ({gst_pct:.1f}%):", f"+ ₹ {gst_amt:.2f}"],
            ["Grand Total:", f"₹ {grand_total:.2f}"]
        ]
        summary_table = Table(summary_data, colWidths=[400, 140])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1E3A8A')),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1E3A8A')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        footer_text = "Thank you for your business! Goods once sold cannot be taken back without original bill."
        story.append(Paragraph(footer_text, subtitle_style))

        doc.build(story)
        return pdf_path

    else:
        # Fallback to structured text invoice
        txt_path = os.path.join(INVOICE_DIR, f"{invoice_no}.txt")
        lines = []
        lines.append("=" * 55)
        lines.append("           APNA MARKET - POS & INVENTORY")
        lines.append("   Main Market Road, City Center | Ph: +91 98765 00000")
        lines.append("=" * 55)
        lines.append(f"Invoice No : {invoice_no}")
        lines.append(f"Date & Time: {sold_at}")
        lines.append(f"Customer   : {cust_name} ({cust_phone})")
        lines.append(f"Payment    : {payment_method}  | Billed By: {cashier}")
        lines.append("-" * 55)
        lines.append(f"{'Item':<24}{'Price':>8}{'Qty':>6}{'Total':>10}")
        lines.append("-" * 55)
        for sku, name, price, qty, ltotal in items:
            item_display = (name[:22] + '..') if len(name) > 24 else name
            lines.append(f"{item_display:<24}{price:>8.2f}{qty:>6}{ltotal:>10.2f}")
        lines.append("-" * 55)
        lines.append(f"{'Subtotal:':<38} ₹{subtotal:>10.2f}")
        if discount_amt > 0:
            lines.append(f"{'Discount (' + str(discount_pct) + '%):':<38}-₹{discount_amt:>10.2f}")
        if gst_amt > 0:
            lines.append(f"{'GST (' + str(gst_pct) + '%):':<38}+₹{gst_amt:>10.2f}")
        lines.append("=" * 55)
        lines.append(f"{'GRAND TOTAL:':<38} ₹{grand_total:>10.2f}")
        lines.append("=" * 55)
        lines.append("      Thank you for shopping with us! Visit again!   ")
        lines.append("=" * 55)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return txt_path


class MarketApp(tk.Tk):
    """Full-featured Tkinter POS & Inventory Desktop Application."""
    def __init__(self, db_path=DB_NAME):
        super().__init__()
        self.db_path = db_path
        self.title("Apna Market - POS & Inventory Management System")
        self.geometry("1150x740")
        self.minsize(980, 650)

        # State Variables
        self.user_role = tk.StringVar(value="Admin") # "Admin" or "Cashier"
        self.cart = [] # List of dict: {id, sku, name, cost_price, price, qty, max_stock}
        self.selected_product_id = None
        self.selected_customer_id = None

        # Styling
        self.setup_styles()

        # Build Main UI
        self.build_header()
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Frames for Tabs
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.products_tab = ttk.Frame(self.notebook)
        self.pos_tab = ttk.Frame(self.notebook)
        self.inventory_tab = ttk.Frame(self.notebook)
        self.customers_tab = ttk.Frame(self.notebook)
        self.reports_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab, text=" 📊 Dashboard ")
        self.notebook.add(self.products_tab, text=" 🏷️ Products ")
        self.notebook.add(self.pos_tab, text=" 🛒 Billing / POS ")
        self.notebook.add(self.inventory_tab, text=" 📦 Inventory ")
        self.notebook.add(self.customers_tab, text=" 👥 Customers ")
        self.notebook.add(self.reports_tab, text=" 📈 Reports & Analytics ")

        # Tab Change Binding to refresh views dynamically
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Build each tab
        self.build_dashboard_tab()
        self.build_products_tab()
        self.build_pos_tab()
        self.build_inventory_tab()
        self.build_customers_tab()
        self.build_reports_tab()

        # Initial Load
        self.refresh_all_data()

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Global fonts & colors
        self.primary_color = "#1E3A8A" # Royal Blue
        self.accent_color = "#2563EB"
        self.bg_light = "#F8FAFC"
        self.danger_color = "#DC2626"
        self.success_color = "#16A34A"

        style.configure(".", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E2E8F0")
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        style.map("Treeview", background=[('selected', '#2563EB')], foreground=[('selected', 'white')])

        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground=self.primary_color)
        style.configure("CardVal.TLabel", font=("Segoe UI", 18, "bold"), foreground=self.primary_color)
        style.configure("CardTitle.TLabel", font=("Segoe UI", 9), foreground="#64748B")

        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def build_header(self):
        header = ttk.Frame(self, padding=(12, 10))
        header.pack(fill="x")

        # Title
        title_box = ttk.Frame(header)
        title_box.pack(side="left")
        ttk.Label(title_box, text="🛒 APNA MARKET", style="Header.TLabel").pack(side="left")
        ttk.Label(title_box, text=" | POS & Inventory Management System", font=("Segoe UI", 11), foreground="#475569").pack(side="left", padx=5)

        # User Role & Actions on Right
        role_box = ttk.Frame(header)
        role_box.pack(side="right")

        ttk.Label(role_box, text="Active Role: ", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.role_badge = tk.Label(role_box, text=self.user_role.get(), bg="#22C55E", fg="white", font=("Segoe UI", 9, "bold"), padx=8, pady=2, relief="flat")
        self.role_badge.pack(side="left", padx=(0, 10))

        ttk.Button(role_box, text="Switch Role", command=self.toggle_user_role).pack(side="left", padx=4)

    def toggle_user_role(self):
        current = self.user_role.get()
        new_role = "Cashier" if current == "Admin" else "Admin"
        self.user_role.set(new_role)
        self.role_badge.config(
            text=new_role,
            bg="#3B82F6" if new_role == "Cashier" else "#22C55E"
        )
        self.apply_role_permissions()
        messagebox.showinfo("Role Changed", f"Switched active role to: {new_role}")

    def apply_role_permissions(self):
        """Show/hide admin sensitive features based on role."""
        is_admin = (self.user_role.get() == "Admin")
        # In cashier mode, disable product delete button & cost price visibility
        if hasattr(self, 'btn_prod_delete'):
            self.btn_prod_delete.config(state="normal" if is_admin else "disabled")
        self.refresh_products_table()
        self.refresh_reports()

    def on_tab_changed(self, event):
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 0:
            self.refresh_dashboard()
        elif tab_idx == 1:
            self.refresh_products_table()
        elif tab_idx == 2:
            self.refresh_pos_products()
            self.refresh_pos_customers()
        elif tab_idx == 3:
            self.refresh_inventory_tab()
        elif tab_idx == 4:
            self.refresh_customers_tab()
        elif tab_idx == 5:
            self.refresh_reports()

    # ==========================================
    # 1. DASHBOARD TAB
    # ==========================================
    def build_dashboard_tab(self):
        pad_frame = ttk.Frame(self.dashboard_tab, padding=12)
        pad_frame.pack(fill="both", expand=True)

        # 4 Metric Cards at top
        cards_frame = ttk.Frame(pad_frame)
        cards_frame.pack(fill="x", pady=(0, 15))

        def create_kpi_card(parent, title, default_val):
            card = ttk.LabelFrame(parent, padding=12)
            card.pack(side="left", fill="both", expand=True, padx=5)
            val_lbl = ttk.Label(card, text=default_val, style="CardVal.TLabel")
            val_lbl.pack(anchor="w")
            title_lbl = ttk.Label(card, text=title, style="CardTitle.TLabel")
            title_lbl.pack(anchor="w")
            return val_lbl

        self.kpi_today_sales = create_kpi_card(cards_frame, "Today's Revenue", "₹ 0.00")
        self.kpi_today_units = create_kpi_card(cards_frame, "Units Sold Today", "0")
        self.kpi_low_stock = create_kpi_card(cards_frame, "Low-Stock Alerts", "0")
        self.kpi_total_products = create_kpi_card(cards_frame, "Total Active Products", "0")

        # Lower Split: Left = Low Stock Alerts; Right = Recent Sales
        split_frame = ttk.Frame(pad_frame)
        split_frame.pack(fill="both", expand=True)

        # Left: Low Stock Alerts
        low_stock_box = ttk.LabelFrame(split_frame, text="⚠️ Low-Stock Warnings (Requires Restocking)", padding=10)
        low_stock_box.pack(side="left", fill="both", expand=True, padx=(0, 6))

        columns_low = ("sku", "name", "stock", "min_stock")
        self.tree_low_stock = ttk.Treeview(low_stock_box, columns=columns_low, show="headings", height=8)
        self.tree_low_stock.heading("sku", text="SKU")
        self.tree_low_stock.heading("name", text="Product Name")
        self.tree_low_stock.heading("stock", text="Stock")
        self.tree_low_stock.heading("min_stock", text="Min Alert")
        self.tree_low_stock.column("sku", width=90, anchor="center")
        self.tree_low_stock.column("name", width=180, anchor="w")
        self.tree_low_stock.column("stock", width=60, anchor="center")
        self.tree_low_stock.column("min_stock", width=70, anchor="center")
        self.tree_low_stock.pack(fill="both", expand=True)

        low_actions = ttk.Frame(low_stock_box)
        low_actions.pack(fill="x", pady=(6, 0))
        ttk.Button(low_actions, text="Quick Restock Selected", command=self.quick_restock_dialog).pack(side="left")

        # Right: Recent Sales
        recent_sales_box = ttk.LabelFrame(split_frame, text="🕒 Recent Sales Activity", padding=10)
        recent_sales_box.pack(side="right", fill="both", expand=True, padx=(6, 0))

        columns_sales = ("invoice", "date", "customer", "total")
        self.tree_recent_sales = ttk.Treeview(recent_sales_box, columns=columns_sales, show="headings", height=8)
        self.tree_recent_sales.heading("invoice", text="Invoice #")
        self.tree_recent_sales.heading("date", text="Time")
        self.tree_recent_sales.heading("customer", text="Customer")
        self.tree_recent_sales.heading("total", text="Amount (₹)")
        self.tree_recent_sales.column("invoice", width=80, anchor="center")
        self.tree_recent_sales.column("date", width=120, anchor="center")
        self.tree_recent_sales.column("customer", width=130, anchor="w")
        self.tree_recent_sales.column("total", width=80, anchor="e")
        self.tree_recent_sales.pack(fill="both", expand=True)

    def refresh_dashboard(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        today_str = datetime.now().strftime("%Y-%m-%d")

        # Today's Revenue & Units Sold
        cur.execute("""
            SELECT COALESCE(SUM(grand_total), 0.0) FROM sales 
            WHERE sold_at LIKE ?
        """, (f"{today_str}%",))
        today_rev = cur.fetchone()[0]
        self.kpi_today_sales.config(text=f"₹ {today_rev:,.2f}")

        cur.execute("""
            SELECT COALESCE(SUM(si.qty), 0) FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.sold_at LIKE ?
        """, (f"{today_str}%",))
        today_units = cur.fetchone()[0]
        self.kpi_today_units.config(text=str(today_units))

        # Total Products & Low Stock Count
        cur.execute("SELECT COUNT(*) FROM products")
        total_prods = cur.fetchone()[0]
        self.kpi_total_products.config(text=str(total_prods))

        cur.execute("SELECT COUNT(*) FROM products WHERE stock <= min_stock")
        low_count = cur.fetchone()[0]
        self.kpi_low_stock.config(text=str(low_count))

        # Populate Low Stock Alerts
        self.tree_low_stock.delete(*self.tree_low_stock.get_children())
        cur.execute("""
            SELECT sku, name, stock, min_stock FROM products 
            WHERE stock <= min_stock 
            ORDER BY stock ASC
        """)
        for row in cur.fetchall():
            self.tree_low_stock.insert("", "end", values=row)

        # Populate Recent Sales
        self.tree_recent_sales.delete(*self.tree_recent_sales.get_children())
        cur.execute("""
            SELECT invoice_no, sold_at, customer_name, grand_total 
            FROM sales 
            ORDER BY id DESC LIMIT 10
        """)
        for row in cur.fetchall():
            inv, s_at, c_name, tot = row
            time_part = s_at[5:] if len(s_at) >= 16 else s_at
            self.tree_recent_sales.insert("", "end", values=(inv, time_part, c_name, f"₹ {tot:.2f}"))

        con.close()

    def quick_restock_dialog(self):
        selected = self.tree_low_stock.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select a low-stock product to restock.")
            return

        values = self.tree_low_stock.item(selected[0])["values"]
        sku, name, curr_stock, min_s = values

        qty = simpledialog.askinteger("Quick Restock", f"Product: {name}\nCurrent Stock: {curr_stock}\nEnter quantity to add to inventory:", minvalue=1, maxvalue=1000)
        if qty:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            cur.execute("SELECT id, stock FROM products WHERE sku = ?", (sku,))
            row = cur.fetchone()
            if row:
                pid, old_stock = row
                new_stock = old_stock + qty
                cur.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, pid))
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
                    VALUES (?, ?, 'STOCK_IN', ?, ?, ?, 'Quick Restock via Dashboard', ?)
                """, (pid, name, qty, old_stock, new_stock, now_str))
                con.commit()
            con.close()
            self.refresh_all_data()
            messagebox.showinfo("Success", f"Successfully added {qty} units to {name}. New stock: {curr_stock + qty}")

    # ==========================================
    # 2. PRODUCTS TAB
    # ==========================================
    def build_products_tab(self):
        pad_frame = ttk.Frame(self.products_tab, padding=12)
        pad_frame.pack(fill="both", expand=True)

        # Form Frame
        form_frame = ttk.LabelFrame(pad_frame, text="Product Details (Add / Edit)", padding=10)
        form_frame.pack(fill="x", pady=(0, 10))

        # Row 1
        ttk.Label(form_frame, text="SKU / Barcode:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_prod_sku = ttk.Entry(form_frame, width=16)
        self.entry_prod_sku.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Name:").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.entry_prod_name = ttk.Entry(form_frame, width=24)
        self.entry_prod_name.grid(row=0, column=3, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Category:").grid(row=0, column=4, sticky="w", padx=5, pady=4)
        self.entry_prod_cat = ttk.Combobox(form_frame, width=16, values=["General", "Grains & Rice", "Flour & Atta", "Oils", "Beverages", "Snacks", "Dairy", "Household", "Personal Care"])
        self.entry_prod_cat.set("General")
        self.entry_prod_cat.grid(row=0, column=5, sticky="w", padx=5, pady=4)

        # Row 2
        ttk.Label(form_frame, text="Cost Price (₹):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.entry_prod_cost = ttk.Entry(form_frame, width=16)
        self.entry_prod_cost.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Selling Price (₹):").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.entry_prod_price = ttk.Entry(form_frame, width=24)
        self.entry_prod_price.grid(row=1, column=3, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Stock Qty:").grid(row=1, column=4, sticky="w", padx=5, pady=4)
        self.entry_prod_stock = ttk.Entry(form_frame, width=8)
        self.entry_prod_stock.grid(row=1, column=5, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Min Stock Alert:").grid(row=1, column=6, sticky="w", padx=5, pady=4)
        self.entry_prod_min_stock = ttk.Entry(form_frame, width=8)
        self.entry_prod_min_stock.insert(0, "5")
        self.entry_prod_min_stock.grid(row=1, column=7, sticky="w", padx=5, pady=4)

        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=8, sticky="w", pady=(8, 2))

        ttk.Button(btn_frame, text="➕ Add Product", command=self.add_product).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="✏️ Update Selected", command=self.update_product).pack(side="left", padx=4)
        self.btn_prod_delete = ttk.Button(btn_frame, text="🗑️ Delete Selected", command=self.delete_product)
        self.btn_prod_delete.pack(side="left", padx=4)
        ttk.Button(btn_frame, text="🧹 Clear Form", command=self.clear_product_form).pack(side="left", padx=4)

        # Search Bar
        search_frame = ttk.Frame(pad_frame)
        search_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(search_frame, text="🔍 Search Products:").pack(side="left", padx=(0, 6))
        self.entry_prod_search = ttk.Entry(search_frame, width=30)
        self.entry_prod_search.pack(side="left", padx=(0, 6))
        self.entry_prod_search.bind("<KeyRelease>", lambda e: self.refresh_products_table())
        ttk.Button(search_frame, text="Reset", command=lambda: (self.entry_prod_search.delete(0, tk.END), self.refresh_products_table())).pack(side="left")

        # Treeview
        columns = ("id", "sku", "name", "category", "cost", "price", "stock", "min_stock", "status")
        self.tree_products = ttk.Treeview(pad_frame, columns=columns, show="headings", selectmode="browse")

        self.tree_products.heading("id", text="ID")
        self.tree_products.heading("sku", text="SKU / Barcode")
        self.tree_products.heading("name", text="Product Name")
        self.tree_products.heading("category", text="Category")
        self.tree_products.heading("cost", text="Cost (₹)")
        self.tree_products.heading("price", text="Price (₹)")
        self.tree_products.heading("stock", text="Stock")
        self.tree_products.heading("min_stock", text="Min Stock")
        self.tree_products.heading("status", text="Alert Status")

        self.tree_products.column("id", width=40, anchor="center")
        self.tree_products.column("sku", width=100, anchor="center")
        self.tree_products.column("name", width=220, anchor="w")
        self.tree_products.column("category", width=120, anchor="w")
        self.tree_products.column("cost", width=80, anchor="e")
        self.tree_products.column("price", width=80, anchor="e")
        self.tree_products.column("stock", width=60, anchor="center")
        self.tree_products.column("min_stock", width=70, anchor="center")
        self.tree_products.column("status", width=100, anchor="center")

        # Scrollbar
        sb = ttk.Scrollbar(pad_frame, orient="vertical", command=self.tree_products.yview)
        self.tree_products.configure(yscrollcommand=sb.set)
        self.tree_products.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree_products.bind("<<TreeviewSelect>>", self.on_product_row_select)

    def refresh_products_table(self):
        query_text = self.entry_prod_search.get().strip().lower()
        self.tree_products.delete(*self.tree_products.get_children())

        is_admin = (self.user_role.get() == "Admin")

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, sku, name, category, cost_price, selling_price, stock, min_stock FROM products ORDER BY name ASC")
        rows = cur.fetchall()
        con.close()

        for row in rows:
            pid, sku, name, cat, cost, price, stock, min_s = row
            if query_text:
                if query_text not in name.lower() and query_text not in sku.lower() and query_text not in cat.lower():
                    continue

            status = "⚠️ LOW STOCK" if stock <= min_s else "OK"
            display_cost = f"{cost:.2f}" if is_admin else "***"

            tag = "low_stock" if stock <= min_s else "normal"
            self.tree_products.insert("", "end", values=(
                pid, sku, name, cat, display_cost, f"{price:.2f}", stock, min_s, status
            ), tags=(tag,))

        self.tree_products.tag_configure("low_stock", foreground="#DC2626")
        self.tree_products.tag_configure("normal", foreground="#0F172A")

    def on_product_row_select(self, event):
        selected = self.tree_products.selection()
        if not selected:
            return
        vals = self.tree_products.item(selected[0])["values"]
        # id(0), sku(1), name(2), category(3), cost(4), price(5), stock(6), min_stock(7)
        self.selected_product_id = vals[0]
        self.entry_prod_sku.delete(0, tk.END)
        self.entry_prod_sku.insert(0, vals[1])

        self.entry_prod_name.delete(0, tk.END)
        self.entry_prod_name.insert(0, vals[2])

        self.entry_prod_cat.set(vals[3])

        self.entry_prod_cost.delete(0, tk.END)
        if self.user_role.get() == "Admin":
            self.entry_prod_cost.insert(0, str(vals[4]))
        else:
            self.entry_prod_cost.insert(0, "0.0")

        self.entry_prod_price.delete(0, tk.END)
        self.entry_prod_price.insert(0, str(vals[5]))

        self.entry_prod_stock.delete(0, tk.END)
        self.entry_prod_stock.insert(0, str(vals[6]))

        self.entry_prod_min_stock.delete(0, tk.END)
        self.entry_prod_min_stock.insert(0, str(vals[7]))

    def clear_product_form(self):
        self.selected_product_id = None
        self.entry_prod_sku.delete(0, tk.END)
        self.entry_prod_name.delete(0, tk.END)
        self.entry_prod_cat.set("General")
        self.entry_prod_cost.delete(0, tk.END)
        self.entry_prod_price.delete(0, tk.END)
        self.entry_prod_stock.delete(0, tk.END)
        self.entry_prod_min_stock.delete(0, tk.END)
        self.entry_prod_min_stock.insert(0, "5")

    def add_product(self):
        sku = self.entry_prod_sku.get().strip()
        name = self.entry_prod_name.get().strip()
        cat = self.entry_prod_cat.get().strip() or "General"
        cost_str = self.entry_prod_cost.get().strip()
        price_str = self.entry_prod_price.get().strip()
        stock_str = self.entry_prod_stock.get().strip()
        min_stock_str = self.entry_prod_min_stock.get().strip() or "5"

        if not sku or not name or not price_str or not stock_str:
            messagebox.showerror("Validation Error", "SKU, Name, Price, and Stock are required.")
            return

        try:
            cost = float(cost_str) if cost_str else 0.0
            price = float(price_str)
            stock = int(stock_str)
            min_stock = int(min_stock_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Price and Cost must be numeric; Stock must be integer.")
            return

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO products (sku, name, category, cost_price, selling_price, stock, min_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sku, name, cat, cost, price, stock, min_stock))
            pid = cur.lastrowid

            # Log initial inventory
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
                VALUES (?, ?, 'STOCK_IN', ?, 0, ?, 'Product Created', ?)
            """, (pid, name, stock, stock, now_str))

            con.commit()
            messagebox.showinfo("Success", f"Product '{name}' added successfully!")
            self.clear_product_form()
            self.refresh_all_data()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Product with SKU '{sku}' already exists.")
        finally:
            con.close()

    def update_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("Select Product", "Please select a product from the list to update.")
            return

        sku = self.entry_prod_sku.get().strip()
        name = self.entry_prod_name.get().strip()
        cat = self.entry_prod_cat.get().strip() or "General"
        cost_str = self.entry_prod_cost.get().strip()
        price_str = self.entry_prod_price.get().strip()
        stock_str = self.entry_prod_stock.get().strip()
        min_stock_str = self.entry_prod_min_stock.get().strip() or "5"

        try:
            cost = float(cost_str) if (cost_str and cost_str != "***") else None
            price = float(price_str)
            stock = int(stock_str)
            min_stock = int(min_stock_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid numeric values entered.")
            return

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        try:
            if cost is not None:
                cur.execute("""
                    UPDATE products 
                    SET sku=?, name=?, category=?, cost_price=?, selling_price=?, stock=?, min_stock=?
                    WHERE id=?
                """, (sku, name, cat, cost, price, stock, min_stock, self.selected_product_id))
            else:
                cur.execute("""
                    UPDATE products 
                    SET sku=?, name=?, category=?, selling_price=?, stock=?, min_stock=?
                    WHERE id=?
                """, (sku, name, cat, price, stock, min_stock, self.selected_product_id))

            con.commit()
            messagebox.showinfo("Success", "Product updated successfully!")
            self.refresh_all_data()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"SKU '{sku}' is already in use by another product.")
        finally:
            con.close()

    def delete_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("Select Product", "Please select a product to delete.")
            return

        if self.user_role.get() != "Admin":
            messagebox.showerror("Permission Denied", "Only Admin can delete products.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product? Past sales records will retain item names.")
        if not confirm:
            return

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("DELETE FROM products WHERE id = ?", (self.selected_product_id,))
        con.commit()
        con.close()

        messagebox.showinfo("Deleted", "Product removed.")
        self.clear_product_form()
        self.refresh_all_data()

    # ==========================================
    # 3. BILLING / POS TAB
    # ==========================================
    def build_pos_tab(self):
        pad_frame = ttk.Frame(self.pos_tab, padding=10)
        pad_frame.pack(fill="both", expand=True)

        # Split: Left (Catalog / Quick Scan) | Right (Cart & Checkout)
        split = ttk.Frame(pad_frame)
        split.pack(fill="both", expand=True)

        # --- LEFT PANEL: Product Catalog ---
        left = ttk.LabelFrame(split, text="📦 Product Selection & Quick Scan", padding=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Barcode scan entry
        scan_box = ttk.Frame(left)
        scan_box.pack(fill="x", pady=(0, 6))
        ttk.Label(scan_box, text="⚡ Barcode / SKU Scan:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4))
        self.entry_pos_barcode = ttk.Entry(scan_box, width=18)
        self.entry_pos_barcode.pack(side="left", padx=(0, 6))
        self.entry_pos_barcode.bind("<Return>", lambda e: self.quick_add_by_barcode())
        ttk.Button(scan_box, text="Add Scan", command=self.quick_add_by_barcode).pack(side="left")

        # Search Products
        pos_search_box = ttk.Frame(left)
        pos_search_box.pack(fill="x", pady=(0, 6))
        ttk.Label(pos_search_box, text="Filter Catalog:").pack(side="left", padx=(0, 4))
        self.entry_pos_search = ttk.Entry(pos_search_box)
        self.entry_pos_search.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.entry_pos_search.bind("<KeyRelease>", lambda e: self.refresh_pos_products())

        # Catalog Treeview
        pos_cols = ("id", "sku", "name", "price", "stock")
        self.tree_pos_products = ttk.Treeview(left, columns=pos_cols, show="headings", height=12)
        self.tree_pos_products.heading("id", text="ID")
        self.tree_pos_products.heading("sku", text="SKU")
        self.tree_pos_products.heading("name", text="Product Name")
        self.tree_pos_products.heading("price", text="Price (₹)")
        self.tree_pos_products.heading("stock", text="In Stock")

        self.tree_pos_products.column("id", width=35, anchor="center")
        self.tree_pos_products.column("sku", width=85, anchor="center")
        self.tree_pos_products.column("name", width=190, anchor="w")
        self.tree_pos_products.column("price", width=70, anchor="e")
        self.tree_pos_products.column("stock", width=65, anchor="center")
        self.tree_pos_products.pack(fill="both", expand=True)

        # Quantity and Add button
        qty_box = ttk.Frame(left)
        qty_box.pack(fill="x", pady=(8, 0))
        ttk.Label(qty_box, text="Quantity:").pack(side="left", padx=(0, 4))
        self.spin_pos_qty = ttk.Spinbox(qty_box, from_=1, to=100, width=5)
        self.spin_pos_qty.set(1)
        self.spin_pos_qty.pack(side="left", padx=(0, 8))
        ttk.Button(qty_box, text="🛒 Add To Cart", command=self.add_selected_to_cart).pack(side="left")

        # --- RIGHT PANEL: Cart & Billing Details ---
        right = ttk.LabelFrame(split, text="🛒 Active Cart & Checkout", padding=10)
        right.pack(side="right", fill="both", expand=True, padx=(6, 0))

        # Customer selection bar
        cust_bar = ttk.Frame(right)
        cust_bar.pack(fill="x", pady=(0, 6))
        ttk.Label(cust_bar, text="Customer:").pack(side="left", padx=(0, 4))
        self.combo_pos_customer = ttk.Combobox(cust_bar, width=28)
        self.combo_pos_customer.pack(side="left", padx=(0, 6))

        # Cart Table
        cart_cols = ("sku", "name", "price", "qty", "total")
        self.tree_cart = ttk.Treeview(right, columns=cart_cols, show="headings", height=8)
        self.tree_cart.heading("sku", text="SKU")
        self.tree_cart.heading("name", text="Item")
        self.tree_cart.heading("price", text="Price")
        self.tree_cart.heading("qty", text="Qty")
        self.tree_cart.heading("total", text="Total (₹)")

        self.tree_cart.column("sku", width=75, anchor="center")
        self.tree_cart.column("name", width=150, anchor="w")
        self.tree_cart.column("price", width=65, anchor="e")
        self.tree_cart.column("qty", width=45, anchor="center")
        self.tree_cart.column("total", width=75, anchor="e")
        self.tree_cart.pack(fill="both", expand=True)

        # Cart adjustment buttons
        cart_btns = ttk.Frame(right)
        cart_btns.pack(fill="x", pady=4)
        ttk.Button(cart_btns, text="➕ Qty +1", command=lambda: self.adjust_cart_qty(1)).pack(side="left", padx=2)
        ttk.Button(cart_btns, text="➖ Qty -1", command=lambda: self.adjust_cart_qty(-1)).pack(side="left", padx=2)
        ttk.Button(cart_btns, text="❌ Remove", command=self.remove_cart_item).pack(side="left", padx=2)
        ttk.Button(cart_btns, text="🗑️ Clear Cart", command=self.clear_cart).pack(side="left", padx=2)

        # Checkout / Totals Frame
        totals_frame = ttk.LabelFrame(right, text="Billing Summary", padding=8)
        totals_frame.pack(fill="x", pady=(6, 0))

        # Subtotal
        ttk.Label(totals_frame, text="Subtotal:").grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_subtotal = ttk.Label(totals_frame, text="₹ 0.00", font=("Segoe UI", 10, "bold"))
        self.lbl_subtotal.grid(row=0, column=1, sticky="e", pady=2)

        # Discount %
        ttk.Label(totals_frame, text="Discount (%):").grid(row=1, column=0, sticky="w", pady=2)
        self.spin_discount = ttk.Spinbox(totals_frame, from_=0, to=100, width=6, command=self.render_cart_totals)
        self.spin_discount.set(0)
        self.spin_discount.grid(row=1, column=1, sticky="e", pady=2)
        self.spin_discount.bind("<KeyRelease>", lambda e: self.render_cart_totals())

        # GST %
        ttk.Label(totals_frame, text="GST / Tax (%):").grid(row=2, column=0, sticky="w", pady=2)
        self.combo_gst = ttk.Combobox(totals_frame, values=["0", "5", "12", "18", "28"], width=6)
        self.combo_gst.set("5")
        self.combo_gst.grid(row=2, column=1, sticky="e", pady=2)
        self.combo_gst.bind("<<ComboboxSelected>>", lambda e: self.render_cart_totals())
        self.combo_gst.bind("<KeyRelease>", lambda e: self.render_cart_totals())

        # Payment Method
        ttk.Label(totals_frame, text="Payment Mode:").grid(row=3, column=0, sticky="w", pady=2)
        self.combo_payment = ttk.Combobox(totals_frame, values=["Cash", "UPI / QR Code", "Debit/Credit Card"], width=14)
        self.combo_payment.set("Cash")
        self.combo_payment.grid(row=3, column=1, sticky="e", pady=2)

        # Grand Total
        ttk.Separator(totals_frame, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Label(totals_frame, text="GRAND TOTAL:", font=("Segoe UI", 12, "bold"), foreground=self.primary_color).grid(row=5, column=0, sticky="w")
        self.lbl_grand_total = ttk.Label(totals_frame, text="₹ 0.00", font=("Segoe UI", 14, "bold"), foreground=self.primary_color)
        self.lbl_grand_total.grid(row=5, column=1, sticky="e")

        # Checkout Action Buttons
        ttk.Button(right, text="✅ Complete Sale & Print Bill", command=lambda: self.process_checkout(print_bill=True)).pack(fill="x", pady=(8, 2))
        ttk.Button(right, text="💾 Complete Sale (No Print)", command=lambda: self.process_checkout(print_bill=False)).pack(fill="x", pady=2)

    def refresh_pos_products(self):
        query = self.entry_pos_search.get().strip().lower()
        self.tree_pos_products.delete(*self.tree_pos_products.get_children())

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, sku, name, selling_price, stock FROM products ORDER BY name ASC")
        rows = cur.fetchall()
        con.close()

        for row in rows:
            pid, sku, name, price, stock = row
            if query and query not in name.lower() and query not in sku.lower():
                continue
            self.tree_pos_products.insert("", "end", values=(pid, sku, name, f"{price:.2f}", stock))

    def refresh_pos_customers(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, name, phone FROM customers ORDER BY id ASC")
        rows = cur.fetchall()
        con.close()

        options = [f"{name} ({phone})" for cid, name, phone in rows]
        if not options:
            options = ["Walk-in Customer (9999999999)"]
        self.combo_pos_customer["values"] = options
        if not self.combo_pos_customer.get():
            self.combo_pos_customer.current(0)

    def quick_add_by_barcode(self):
        barcode = self.entry_pos_barcode.get().strip()
        if not barcode:
            return

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, sku, name, cost_price, selling_price, stock FROM products WHERE sku = ?", (barcode,))
        prod = cur.fetchone()
        con.close()

        if not prod:
            messagebox.showerror("Not Found", f"No product found matching SKU/Barcode: {barcode}")
            return

        self.add_item_to_cart_data(prod[0], prod[1], prod[2], prod[3], prod[4], prod[5], 1)
        self.entry_pos_barcode.delete(0, tk.END)

    def add_selected_to_cart(self):
        selected = self.tree_pos_products.selection()
        if not selected:
            messagebox.showwarning("Select Product", "Please select a product from the list.")
            return

        pid = self.tree_pos_products.item(selected[0])["values"][0]
        try:
            qty = int(self.spin_pos_qty.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Please enter a valid positive quantity.")
            return

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, sku, name, cost_price, selling_price, stock FROM products WHERE id = ?", (pid,))
        prod = cur.fetchone()
        con.close()

        if prod:
            self.add_item_to_cart_data(prod[0], prod[1], prod[2], prod[3], prod[4], prod[5], qty)

    def add_item_to_cart_data(self, pid, sku, name, cost_price, price, max_stock, qty):
        # Check existing in cart
        for item in self.cart:
            if item["id"] == pid:
                if item["qty"] + qty > max_stock:
                    messagebox.showwarning("Stock Exceeded", f"Only {max_stock} units available in stock.")
                    return
                item["qty"] += qty
                self.render_cart()
                return

        if qty > max_stock:
            messagebox.showwarning("Stock Exceeded", f"Only {max_stock} units available in stock.")
            return

        self.cart.append({
            "id": pid,
            "sku": sku,
            "name": name,
            "cost_price": cost_price,
            "price": float(price),
            "qty": qty,
            "max_stock": max_stock
        })
        self.render_cart()

    def adjust_cart_qty(self, delta):
        selected = self.tree_cart.selection()
        if not selected:
            return
        idx = self.tree_cart.index(selected[0])
        item = self.cart[idx]

        new_qty = item["qty"] + delta
        if new_qty <= 0:
            self.cart.pop(idx)
        else:
            if new_qty > item["max_stock"]:
                messagebox.showwarning("Stock Limit", f"Cannot exceed available stock of {item['max_stock']}.")
                return
            item["qty"] = new_qty
        self.render_cart()

    def remove_cart_item(self):
        selected = self.tree_cart.selection()
        if not selected:
            return
        idx = self.tree_cart.index(selected[0])
        self.cart.pop(idx)
        self.render_cart()

    def clear_cart(self):
        self.cart.clear()
        self.render_cart()

    def render_cart(self):
        self.tree_cart.delete(*self.tree_cart.get_children())
        for item in self.cart:
            ltotal = item["price"] * item["qty"]
            self.tree_cart.insert("", "end", values=(
                item["sku"], item["name"], f"{item['price']:.2f}", item["qty"], f"{ltotal:.2f}"
            ))
        self.render_cart_totals()

    def render_cart_totals(self):
        subtotal = sum(i["price"] * i["qty"] for i in self.cart)
        self.lbl_subtotal.config(text=f"₹ {subtotal:,.2f}")

        try:
            disc_pct = float(self.spin_discount.get() or 0)
        except ValueError:
            disc_pct = 0.0

        try:
            gst_pct = float(self.combo_gst.get() or 0)
        except ValueError:
            gst_pct = 0.0

        disc_amt = (subtotal * disc_pct) / 100.0
        taxable = max(0.0, subtotal - disc_amt)
        gst_amt = (taxable * gst_pct) / 100.0
        grand_total = taxable + gst_amt

        self.lbl_grand_total.config(text=f"₹ {grand_total:,.2f}")
        return subtotal, disc_pct, disc_amt, gst_pct, gst_amt, grand_total

    def process_checkout(self, print_bill=True):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Cannot checkout an empty cart. Please add products.")
            return

        subtotal, disc_pct, disc_amt, gst_pct, gst_amt, grand_total = self.render_cart_totals()

        # Customer parsing
        cust_str = self.combo_pos_customer.get().strip()
        cust_name = "Walk-in Customer"
        cust_phone = "9999999999"
        if "(" in cust_str and ")" in cust_str:
            cust_name = cust_str.split("(")[0].strip()
            cust_phone = cust_str.split("(")[1].replace(")", "").strip()

        payment_method = self.combo_payment.get()
        cashier = self.user_role.get()
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        invoice_no = f"INV-{now.strftime('%y%m%d')}-{now.strftime('%H%M%S')}"

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        # Verify stock sufficiency in real-time
        for item in self.cart:
            cur.execute("SELECT stock FROM products WHERE id = ?", (item["id"],))
            current_s = cur.fetchone()[0]
            if item["qty"] > current_s:
                con.close()
                messagebox.showerror("Stock Error", f"Insufficient stock for {item['name']}. Current stock: {current_s}")
                return

        # Insert Sale
        cur.execute("""
            INSERT INTO sales (invoice_no, customer_name, customer_phone, subtotal, discount_pct, discount_amt, gst_pct, gst_amt, grand_total, payment_method, cashier, sold_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_no, cust_name, cust_phone, subtotal, disc_pct, disc_amt, gst_pct, gst_amt, grand_total, payment_method, cashier, now_str))
        sale_id = cur.lastrowid

        # Insert Sale Items & Deduct Stock
        for item in self.cart:
            ltotal = item["price"] * item["qty"]
            cur.execute("""
                INSERT INTO sale_items (sale_id, product_id, sku, product_name, cost_price, unit_price, qty, line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sale_id, item["id"], item["sku"], item["name"], item["cost_price"], item["price"], item["qty"], ltotal))

            # Deduct stock
            cur.execute("SELECT stock FROM products WHERE id = ?", (item["id"],))
            old_stock = cur.fetchone()[0]
            new_stock = old_stock - item["qty"]
            cur.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, item["id"]))

            # Log Inventory deduction
            cur.execute("""
                INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
                VALUES (?, ?, 'SALE', ?, ?, ?, ?, ?)
            """, (item["id"], item["name"], -item["qty"], old_stock, new_stock, f"Sold on {invoice_no}", now_str))

        con.commit()
        con.close()

        # Generate Invoice File
        filepath = generate_invoice_file(sale_id, self.db_path)

        # Clear Cart
        self.clear_cart()
        self.refresh_all_data()

        if print_bill and filepath:
            self.show_invoice_modal(filepath)
        else:
            messagebox.showinfo("Sale Complete", f"Sale recorded successfully!\nInvoice No: {invoice_no}\nTotal: ₹{grand_total:,.2f}")

    def show_invoice_modal(self, filepath):
        """Display generated receipt or PDF path notification."""
        win = tk.Toplevel(self)
        win.title("Invoice Receipt")
        win.geometry("540x560")
        win.transient(self)
        win.grab_set()

        ttk.Label(win, text="🧾 Sale Invoice Generated", font=("Segoe UI", 12, "bold"), foreground=self.primary_color).pack(pady=8)

        text_area = tk.Text(win, wrap="word", font=("Consolas", 10))
        text_area.pack(fill="both", expand=True, padx=10, pady=5)

        if filepath.endswith(".txt"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                text_area.insert("1.0", content)
            except Exception as e:
                text_area.insert("1.0", f"Error reading invoice: {e}")
        else:
            text_area.insert("1.0", f"PDF Invoice created successfully at:\n{os.path.abspath(filepath)}\n\n(Install reportlab to generate styled PDFs).")

        text_area.config(state="disabled")

        btn_box = ttk.Frame(win, padding=8)
        btn_box.pack(fill="x")
        ttk.Button(btn_box, text="Open File Location", command=lambda: os.startfile(os.path.dirname(os.path.abspath(filepath))) if sys.platform == "win32" else None).pack(side="left", padx=5)
        ttk.Button(btn_box, text="Close", command=win.destroy).pack(side="right", padx=5)

    # ==========================================
    # 4. INVENTORY TAB
    # ==========================================
    def build_inventory_tab(self):
        pad_frame = ttk.Frame(self.inventory_tab, padding=12)
        pad_frame.pack(fill="both", expand=True)

        # Manual Adjustment Form
        adj_frame = ttk.LabelFrame(pad_frame, text="Manual Stock In / Stock Out", padding=10)
        adj_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(adj_frame, text="Product:").grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.combo_inv_product = ttk.Combobox(adj_frame, width=32)
        self.combo_inv_product.grid(row=0, column=1, padx=5, pady=4, sticky="w")

        ttk.Label(adj_frame, text="Action Type:").grid(row=0, column=2, padx=5, pady=4, sticky="w")
        self.combo_inv_action = ttk.Combobox(adj_frame, values=["STOCK_IN (Restock / Purchase)", "STOCK_OUT (Damaged / Expired)", "STOCK_ADJUST (Audit Correction)"], width=28)
        self.combo_inv_action.set("STOCK_IN (Restock / Purchase)")
        self.combo_inv_action.grid(row=0, column=3, padx=5, pady=4, sticky="w")

        ttk.Label(adj_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=4, sticky="w")
        self.entry_inv_qty = ttk.Entry(adj_frame, width=12)
        self.entry_inv_qty.grid(row=1, column=1, padx=5, pady=4, sticky="w")

        ttk.Label(adj_frame, text="Reason / Note:").grid(row=1, column=2, padx=5, pady=4, sticky="w")
        self.entry_inv_reason = ttk.Entry(adj_frame, width=32)
        self.entry_inv_reason.grid(row=1, column=3, padx=5, pady=4, sticky="w")

        ttk.Button(adj_frame, text="Apply Stock Adjustment", command=self.apply_inventory_adjustment).grid(row=1, column=4, padx=10, pady=4)

        # Inventory Movement History Log
        log_box = ttk.LabelFrame(pad_frame, text="📜 Inventory Audit Logs (Real-time Stock Tracking)", padding=10)
        log_box.pack(fill="both", expand=True)

        columns = ("id", "date", "product", "action", "change", "old", "new", "reason")
        self.tree_inv_logs = ttk.Treeview(log_box, columns=columns, show="headings")

        self.tree_inv_logs.heading("id", text="Log #")
        self.tree_inv_logs.heading("date", text="Date & Time")
        self.tree_inv_logs.heading("product", text="Product")
        self.tree_inv_logs.heading("action", text="Type")
        self.tree_inv_logs.heading("change", text="Change")
        self.tree_inv_logs.heading("old", text="Prev Stock")
        self.tree_inv_logs.heading("new", text="New Stock")
        self.tree_inv_logs.heading("reason", text="Reason")

        self.tree_inv_logs.column("id", width=45, anchor="center")
        self.tree_inv_logs.column("date", width=130, anchor="center")
        self.tree_inv_logs.column("product", width=180, anchor="w")
        self.tree_inv_logs.column("action", width=95, anchor="center")
        self.tree_inv_logs.column("change", width=65, anchor="center")
        self.tree_inv_logs.column("old", width=75, anchor="center")
        self.tree_inv_logs.column("new", width=75, anchor="center")
        self.tree_inv_logs.column("reason", width=220, anchor="w")

        sb = ttk.Scrollbar(log_box, orient="vertical", command=self.tree_inv_logs.yview)
        self.tree_inv_logs.configure(yscrollcommand=sb.set)
        self.tree_inv_logs.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def refresh_inventory_tab(self):
        # Refresh Product options in combobox
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, sku, name, stock FROM products ORDER BY name ASC")
        rows = cur.fetchall()
        options = [f"[{sku}] {name} (Current: {stock})" for pid, sku, name, stock in rows]
        self.combo_inv_product["values"] = options
        if options and not self.combo_inv_product.get():
            self.combo_inv_product.current(0)

        # Refresh logs
        self.tree_inv_logs.delete(*self.tree_inv_logs.get_children())
        cur.execute("""
            SELECT id, logged_at, product_name, change_type, qty_change, previous_stock, new_stock, reason 
            FROM inventory_logs 
            ORDER BY id DESC LIMIT 100
        """)
        for row in cur.fetchall():
            self.tree_inv_logs.insert("", "end", values=row)

        con.close()

    def apply_inventory_adjustment(self):
        selected_prod = self.combo_inv_product.get().strip()
        if not selected_prod:
            messagebox.showwarning("Select Product", "Please select a product.")
            return

        sku = selected_prod.split("]")[0].replace("[", "").strip()
        action_val = self.combo_inv_action.get()
        reason = self.entry_inv_reason.get().strip() or "Manual Adjustment"

        try:
            qty = int(self.entry_inv_qty.get().strip())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Quantity must be a positive integer.")
            return

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, name, stock FROM products WHERE sku = ?", (sku,))
        row = cur.fetchone()
        if not row:
            con.close()
            messagebox.showerror("Error", "Product not found.")
            return

        pid, name, old_stock = row
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if "STOCK_IN" in action_val:
            new_stock = old_stock + qty
            qty_change = qty
            change_type = "STOCK_IN"
        elif "STOCK_OUT" in action_val:
            if qty > old_stock:
                con.close()
                messagebox.showerror("Error", f"Cannot remove {qty} units. Current stock is only {old_stock}.")
                return
            new_stock = old_stock - qty
            qty_change = -qty
            change_type = "STOCK_OUT"
        else: # ADJUST
            new_stock = qty
            qty_change = new_stock - old_stock
            change_type = "ADJUSTMENT"

        cur.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, pid))
        cur.execute("""
            INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, name, change_type, qty_change, old_stock, new_stock, reason, now_str))

        con.commit()
        con.close()

        self.entry_inv_qty.delete(0, tk.END)
        self.entry_inv_reason.delete(0, tk.END)
        self.refresh_all_data()
        messagebox.showinfo("Stock Updated", f"Updated stock for {name}.\nPrevious: {old_stock} -> New: {new_stock}")

    # ==========================================
    # 5. CUSTOMERS TAB
    # ==========================================
    def build_customers_tab(self):
        pad_frame = ttk.Frame(self.customers_tab, padding=12)
        pad_frame.pack(fill="both", expand=True)

        # Split: Left (Customer List & Form) | Right (Customer Purchase History)
        split = ttk.Frame(pad_frame)
        split.pack(fill="both", expand=True)

        left = ttk.Frame(split)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Add Customer Form
        cust_form = ttk.LabelFrame(left, text="Add / Manage Customer", padding=10)
        cust_form.pack(fill="x", pady=(0, 10))

        ttk.Label(cust_form, text="Name:").grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.entry_cust_name = ttk.Entry(cust_form, width=22)
        self.entry_cust_name.grid(row=0, column=1, padx=5, pady=4, sticky="w")

        ttk.Label(cust_form, text="Phone:").grid(row=0, column=2, padx=5, pady=4, sticky="w")
        self.entry_cust_phone = ttk.Entry(cust_form, width=16)
        self.entry_cust_phone.grid(row=0, column=3, padx=5, pady=4, sticky="w")

        ttk.Label(cust_form, text="Email:").grid(row=1, column=0, padx=5, pady=4, sticky="w")
        self.entry_cust_email = ttk.Entry(cust_form, width=22)
        self.entry_cust_email.grid(row=1, column=1, padx=5, pady=4, sticky="w")

        ttk.Button(cust_form, text="Save Customer", command=self.save_customer).grid(row=1, column=3, padx=5, pady=4)

        # Customer List
        list_box = ttk.LabelFrame(left, text="Registered Customers", padding=10)
        list_box.pack(fill="both", expand=True)

        cust_cols = ("id", "name", "phone", "email")
        self.tree_customers = ttk.Treeview(list_box, columns=cust_cols, show="headings")
        self.tree_customers.heading("id", text="ID")
        self.tree_customers.heading("name", text="Customer Name")
        self.tree_customers.heading("phone", text="Phone Number")
        self.tree_customers.heading("email", text="Email")

        self.tree_customers.column("id", width=35, anchor="center")
        self.tree_customers.column("name", width=140, anchor="w")
        self.tree_customers.column("phone", width=110, anchor="center")
        self.tree_customers.column("email", width=160, anchor="w")
        self.tree_customers.pack(fill="both", expand=True)
        self.tree_customers.bind("<<TreeviewSelect>>", self.on_customer_select)

        # Right: Purchase History
        right = ttk.LabelFrame(split, text="📜 Customer Purchase History", padding=10)
        right.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self.lbl_cust_history_title = ttk.Label(right, text="Select a customer to view their transactions", font=("Segoe UI", 10, "italic"))
        self.lbl_cust_history_title.pack(anchor="w", pady=(0, 6))

        hist_cols = ("invoice", "date", "total", "pay_mode")
        self.tree_cust_history = ttk.Treeview(right, columns=hist_cols, show="headings")
        self.tree_cust_history.heading("invoice", text="Invoice #")
        self.tree_cust_history.heading("date", text="Date")
        self.tree_cust_history.heading("total", text="Total (₹)")
        self.tree_cust_history.heading("pay_mode", text="Payment")

        self.tree_cust_history.column("invoice", width=110, anchor="center")
        self.tree_cust_history.column("date", width=140, anchor="center")
        self.tree_cust_history.column("total", width=90, anchor="e")
        self.tree_cust_history.column("pay_mode", width=90, anchor="center")
        self.tree_cust_history.pack(fill="both", expand=True)

    def refresh_customers_tab(self):
        self.tree_customers.delete(*self.tree_customers.get_children())
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, name, phone, email FROM customers ORDER BY name ASC")
        for row in cur.fetchall():
            self.tree_customers.insert("", "end", values=row)
        con.close()

    def save_customer(self):
        name = self.entry_cust_name.get().strip()
        phone = self.entry_cust_phone.get().strip()
        email = self.entry_cust_email.get().strip()

        if not name or not phone:
            messagebox.showerror("Error", "Name and Phone number are required.")
            return

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cur.execute("""
                INSERT INTO customers (name, phone, email, created_at)
                VALUES (?, ?, ?, ?)
            """, (name, phone, email, now_str))
            con.commit()
            messagebox.showinfo("Success", f"Customer '{name}' saved.")
            self.entry_cust_name.delete(0, tk.END)
            self.entry_cust_phone.delete(0, tk.END)
            self.entry_cust_email.delete(0, tk.END)
            self.refresh_customers_tab()
            self.refresh_pos_customers()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Customer with phone {phone} already exists.")
        finally:
            con.close()

    def on_customer_select(self, event):
        selected = self.tree_customers.selection()
        if not selected:
            return
        vals = self.tree_customers.item(selected[0])["values"]
        cid, name, phone, email = vals

        self.lbl_cust_history_title.config(text=f"Showing orders for: {name} ({phone})", font=("Segoe UI", 10, "bold"))
        self.tree_cust_history.delete(*self.tree_cust_history.get_children())

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("""
            SELECT invoice_no, sold_at, grand_total, payment_method 
            FROM sales 
            WHERE customer_phone = ? 
            ORDER BY id DESC
        """, (str(phone),))
        for row in cur.fetchall():
            inv, s_at, tot, pay = row
            self.tree_cust_history.insert("", "end", values=(inv, s_at, f"₹ {tot:.2f}", pay))
        con.close()

    # ==========================================
    # 6. REPORTS & ANALYTICS TAB
    # ==========================================
    def build_reports_tab(self):
        pad_frame = ttk.Frame(self.reports_tab, padding=12)
        pad_frame.pack(fill="both", expand=True)

        # Filters Bar
        filter_bar = ttk.Frame(pad_frame)
        filter_bar.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_bar, text="Filter Period:").pack(side="left", padx=(0, 6))
        self.combo_report_period = ttk.Combobox(filter_bar, values=["All Time", "Today", "Last 7 Days", "Last 30 Days"], width=15)
        self.combo_report_period.set("All Time")
        self.combo_report_period.pack(side="left", padx=(0, 10))
        self.combo_report_period.bind("<<ComboboxSelected>>", lambda e: self.refresh_reports())

        ttk.Button(filter_bar, text="🔄 Refresh Report", command=self.refresh_reports).pack(side="left")

        # Metric summary cards
        metric_bar = ttk.Frame(pad_frame)
        metric_bar.pack(fill="x", pady=(0, 10))

        def create_rep_card(parent, title):
            card = ttk.LabelFrame(parent, padding=8)
            card.pack(side="left", fill="both", expand=True, padx=4)
            val_lbl = ttk.Label(card, text="₹ 0.00", style="CardVal.TLabel")
            val_lbl.pack(anchor="w")
            title_lbl = ttk.Label(card, text=title, style="CardTitle.TLabel")
            title_lbl.pack(anchor="w")
            return val_lbl

        self.rep_total_revenue = create_rep_card(metric_bar, "Total Revenue")
        self.rep_total_cost = create_rep_card(metric_bar, "Estimated Cost of Goods")
        self.rep_gross_profit = create_rep_card(metric_bar, "Estimated Gross Profit")
        self.rep_profit_margin = create_rep_card(metric_bar, "Profit Margin %")

        # Split: Left (Top Selling Items) | Right (Sales Chart or breakdown)
        split = ttk.Frame(pad_frame)
        split.pack(fill="both", expand=True)

        # Left: Top Products
        left = ttk.LabelFrame(split, text="🏆 Top Selling Products", padding=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        top_cols = ("product", "qty_sold", "revenue")
        self.tree_top_products = ttk.Treeview(left, columns=top_cols, show="headings", height=8)
        self.tree_top_products.heading("product", text="Product Name")
        self.tree_top_products.heading("qty_sold", text="Units Sold")
        self.tree_top_products.heading("revenue", text="Total Revenue (₹)")

        self.tree_top_products.column("product", width=180, anchor="w")
        self.tree_top_products.column("qty_sold", width=80, anchor="center")
        self.tree_top_products.column("revenue", width=110, anchor="e")
        self.tree_top_products.pack(fill="both", expand=True)

        # Right: Chart or Daily Sales Summary
        self.rep_chart_frame = ttk.LabelFrame(split, text="📊 Sales & Revenue Trends", padding=10)
        self.rep_chart_frame.pack(side="right", fill="both", expand=True, padx=(6, 0))

    def refresh_reports(self):
        period = self.combo_report_period.get()
        now = datetime.now()

        date_condition = ""
        params = []
        if period == "Today":
            date_condition = "WHERE s.sold_at LIKE ?"
            params.append(f"{now.strftime('%Y-%m-%d')}%")
        elif period == "Last 7 Days":
            since_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            date_condition = "WHERE s.sold_at >= ?"
            params.append(since_date)
        elif period == "Last 30 Days":
            since_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            date_condition = "WHERE s.sold_at >= ?"
            params.append(since_date)

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        # Revenue & Profit Calculation
        cur.execute(f"""
            SELECT 
                COALESCE(SUM(si.line_total), 0.0) AS total_revenue,
                COALESCE(SUM(si.cost_price * si.qty), 0.0) AS total_cost
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            {date_condition}
        """, params)
        rev, cost = cur.fetchone()
        profit = rev - cost
        margin = (profit / rev * 100.0) if rev > 0 else 0.0

        is_admin = (self.user_role.get() == "Admin")

        self.rep_total_revenue.config(text=f"₹ {rev:,.2f}")
        if is_admin:
            self.rep_total_cost.config(text=f"₹ {cost:,.2f}")
            self.rep_gross_profit.config(text=f"₹ {profit:,.2f}", foreground=self.success_color if profit >= 0 else self.danger_color)
            self.rep_profit_margin.config(text=f"{margin:.1f}%")
        else:
            self.rep_total_cost.config(text="*** (Hidden)")
            self.rep_gross_profit.config(text="*** (Hidden)")
            self.rep_profit_margin.config(text="***")

        # Top Products
        self.tree_top_products.delete(*self.tree_top_products.get_children())
        cur.execute(f"""
            SELECT si.product_name, SUM(si.qty) AS total_qty, SUM(si.line_total) AS total_rev
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            {date_condition}
            GROUP BY si.product_id
            ORDER BY total_qty DESC
            LIMIT 10
        """, params)
        for row in cur.fetchall():
            pname, t_qty, t_rev = row
            self.tree_top_products.insert("", "end", values=(pname, t_qty, f"₹ {t_rev:.2f}"))

        # Sales Trend Data
        cur.execute(f"""
            SELECT SUBSTR(s.sold_at, 1, 10) as sale_date, SUM(s.grand_total) as daily_total
            FROM sales s
            {date_condition}
            GROUP BY sale_date
            ORDER BY sale_date ASC
        """, params)
        daily_data = cur.fetchall()
        con.close()

        # Render Chart or fallback table
        for widget in self.rep_chart_frame.winfo_children():
            widget.destroy()

        if MATPLOTLIB_AVAILABLE and daily_data:
            dates = [row[0][5:] for row in daily_data] # MM-DD
            totals = [row[1] for row in daily_data]

            fig = Figure(figsize=(4.8, 3.2), dpi=90)
            ax = fig.add_subplot(111)
            ax.bar(dates, totals, color="#2563EB", width=0.5)
            ax.set_title("Revenue by Day (₹)", fontsize=10, fontweight="bold")
            ax.set_ylabel("Sales (₹)", fontsize=8)
            ax.tick_params(axis='x', labelsize=8, rotation=25)
            ax.tick_params(axis='y', labelsize=8)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.rep_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        elif MATPLOTLIB_AVAILABLE and not daily_data:
            ttk.Label(self.rep_chart_frame, text="No sales records in selected date range.", font=("Segoe UI", 10, "italic")).pack(pady=40)
        else:
            # Fallback when matplotlib is not installed
            msg = "📊 Daily Revenue Summary:\n" + ("-" * 35) + "\n"
            if daily_data:
                for d, amt in daily_data:
                    msg += f" {d}  :  ₹ {amt:>10.2f}\n"
            else:
                msg += " No sales in this timeframe."
            msg += ("-" * 35) + "\n💡 Tip: Run `pip install matplotlib` to display graphical bar charts!"
            
            lbl = tk.Label(self.rep_chart_frame, text=msg, justify="left", font=("Consolas", 9), bg="#F1F5F9", padx=10, pady=10)
            lbl.pack(fill="both", expand=True)

    def refresh_all_data(self):
        """Refreshes all components and tables."""
        self.refresh_dashboard()
        self.refresh_products_table()
        self.refresh_pos_products()
        self.refresh_pos_customers()
        self.refresh_inventory_tab()
        self.refresh_customers_tab()
        self.refresh_reports()


if __name__ == "__main__":
    init_db()
    seed_sample_data()
    app = MarketApp()
    app.mainloop()
