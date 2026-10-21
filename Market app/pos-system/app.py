import os
import sqlite3
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify, g
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-pos-system-key-2026'
app.config['DATABASE'] = os.path.join(app.root_path, 'market.db')

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    """Initializes the database schema using schema.sql."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def seed_data():
    """Seeds sample retail data if products table is empty."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        sample_products = [
            ("SKU-1001", "Basmati Rice 1kg", "Grains & Rice", 75.0, 95.0, 30, 8),
            ("SKU-1002", "Refined Sunflower Oil 1L", "Oils", 110.0, 135.0, 20, 6),
            ("SKU-1003", "Whole Wheat Flour 5kg", "Flour & Atta", 185.0, 220.0, 15, 5),
            ("SKU-1004", "Pure White Sugar 1kg", "Sweeteners", 38.0, 48.0, 50, 10),
            ("SKU-1005", "Assam Gold Tea 250g", "Beverages", 95.0, 125.0, 4, 6),   # Low stock
            ("SKU-1006", "Herbal Bathing Soap 125g", "Personal Care", 28.0, 38.0, 3, 8), # Low stock
            ("SKU-1007", "Milk Sandwich Bread 400g", "Bakery", 30.0, 42.0, 12, 5),
            ("SKU-1008", "Dark Chocolate Slab 100g", "Confectionery", 65.0, 85.0, 25, 6),
            ("SKU-1009", "Roasted Ground Coffee 200g", "Beverages", 140.0, 180.0, 18, 5),
            ("SKU-1010", "Dishwash Gel 500ml", "Household", 70.0, 95.0, 2, 5)        # Low stock
        ]
        cur.executemany("""
            INSERT INTO products (sku, name, category, cost_price, selling_price, stock, min_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_products)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("SELECT id, name, stock FROM products")
        for pid, pname, pstock in cur.fetchall():
            cur.execute("""
                INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
                VALUES (?, ?, 'STOCK_IN', ?, 0, ?, 'Initial Inventory Setup', ?)
            """, (pid, pname, pstock, pstock, now_str))

    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] == 0:
        sample_customers = [
            ("Walk-in Customer", "9999999999", "walkin@market.local"),
            ("Ramesh Kumar", "9876543210", "ramesh@example.com"),
            ("Priya Sharma", "9811223344", "priya@example.com"),
            ("Amit Patel", "9988776655", "amit@example.com")
        ]
        cur.executemany("""
            INSERT INTO customers (name, phone, email)
            VALUES (?, ?, ?)
        """, sample_customers)

    cur.execute("SELECT COUNT(*) FROM sales")
    if cur.fetchone()[0] == 0:
        sample_sales_data = [
            ("INV-DEMO-01", 2, "Ramesh Kumar", "9876543210", 315.0, 0.0, 0.0, 5.0, 15.75, 330.75, "UPI / QR Code", (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d 10:30:00")),
            ("INV-DEMO-02", 3, "Priya Sharma", "9811223344", 405.0, 5.0, 20.25, 5.0, 19.24, 403.99, "Cash", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d 14:15:00")),
            ("INV-DEMO-03", 1, "Walk-in Customer", "9999999999", 260.0, 0.0, 0.0, 5.0, 13.0, 273.0, "Cash", datetime.now().strftime("%Y-%m-%d 11:20:00"))
        ]
        for inv, cid, cname, cphone, sub, disc_p, disc_a, gst_p, gst_a, total, pay, dt in sample_sales_data:
            cur.execute("""
                INSERT INTO sales (invoice_no, customer_id, customer_name, customer_phone, subtotal, discount_pct, discount_amt, gst_pct, gst_amt, grand_total, payment_method, sold_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (inv, cid, cname, cphone, sub, disc_p, disc_a, gst_p, gst_a, total, pay, dt))
            sale_id = cur.lastrowid

            cur.execute("""
                INSERT INTO sale_items (sale_id, product_id, sku, product_name, cost_price, unit_price, qty, line_total)
                VALUES (?, 1, 'SKU-1001', 'Basmati Rice 1kg', 75.0, 95.0, 2, 190.0)
            """, (sale_id,))

    db.commit()

# Ensure database exists when server starts
with app.app_context():
    init_db()
    seed_data()

# ==========================================
# 1. DASHBOARD
# ==========================================
@app.route('/')
@app.route('/dashboard')
def dashboard():
    db = get_db()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Today's Revenue
    cur = db.execute("SELECT COALESCE(SUM(grand_total), 0.0) FROM sales WHERE sold_at LIKE ?", (f"{today_str}%",))
    today_revenue = cur.fetchone()[0]

    # Units Sold Today
    cur = db.execute("""
        SELECT COALESCE(SUM(si.qty), 0) 
        FROM sale_items si 
        JOIN sales s ON si.sale_id = s.id 
        WHERE s.sold_at LIKE ?
    """, (f"{today_str}%",))
    today_units = cur.fetchone()[0]

    # Total Products
    cur = db.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    # Low Stock Count
    cur = db.execute("SELECT COUNT(*) FROM products WHERE stock <= min_stock")
    low_stock_count = cur.fetchone()[0]

    # Low Stock Items List
    low_stock_items = db.execute("""
        SELECT * FROM products 
        WHERE stock <= min_stock 
        ORDER BY stock ASC
    """).fetchall()

    # Recent Transactions
    recent_sales = db.execute("""
        SELECT * FROM sales 
        ORDER BY id DESC LIMIT 8
    """).fetchall()

    return render_template(
        'dashboard.html',
        today_revenue=today_revenue,
        today_units=today_units,
        total_products=total_products,
        low_stock_count=low_stock_count,
        low_stock_items=low_stock_items,
        recent_sales=recent_sales
    )

# ==========================================
# 2. PRODUCTS (CRUD)
# ==========================================
@app.route('/products')
def products():
    db = get_db()
    query = request.args.get('q', '').strip()
    if query:
        pattern = f"%{query}%"
        products_list = db.execute("""
            SELECT * FROM products 
            WHERE name LIKE ? OR sku LIKE ? OR category LIKE ? 
            ORDER BY name ASC
        """, (pattern, pattern, pattern)).fetchall()
    else:
        products_list = db.execute("SELECT * FROM products ORDER BY name ASC").fetchall()

    return render_template('products.html', products=products_list, query=query)

@app.route('/products/new', methods=['GET', 'POST'])
def product_new():
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip() or 'General'
        cost_price = float(request.form.get('cost_price', 0.0) or 0.0)
        selling_price = float(request.form.get('selling_price', 0.0) or 0.0)
        stock = int(request.form.get('stock', 0) or 0)
        min_stock = int(request.form.get('min_stock', 5) or 5)

        if not sku or not name or selling_price <= 0:
            flash("SKU, Name, and a valid Selling Price are required.", "danger")
            return render_template('product_form.html', product=None, action="new")

        db = get_db()
        try:
            cur = db.cursor()
            cur.execute("""
                INSERT INTO products (sku, name, category, cost_price, selling_price, stock, min_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sku, name, category, cost_price, selling_price, stock, min_stock))
            pid = cur.lastrowid

            # Log inventory creation
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
                VALUES (?, ?, 'STOCK_IN', ?, 0, ?, 'Product Created', ?)
            """, (pid, name, stock, stock, now_str))

            db.commit()
            flash(f"Product '{name}' added successfully!", "success")
            return redirect(url_for('products'))
        except sqlite3.IntegrityError:
            flash(f"Error: A product with SKU '{sku}' already exists.", "danger")

    return render_template('product_form.html', product=None, action="new")

@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
def product_edit(id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('products'))

    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip() or 'General'
        cost_price = float(request.form.get('cost_price', 0.0) or 0.0)
        selling_price = float(request.form.get('selling_price', 0.0) or 0.0)
        stock = int(request.form.get('stock', 0) or 0)
        min_stock = int(request.form.get('min_stock', 5) or 5)

        try:
            db.execute("""
                UPDATE products 
                SET sku = ?, name = ?, category = ?, cost_price = ?, selling_price = ?, stock = ?, min_stock = ?
                WHERE id = ?
            """, (sku, name, category, cost_price, selling_price, stock, min_stock, id))
            db.commit()
            flash(f"Product '{name}' updated successfully!", "success")
            return redirect(url_for('products'))
        except sqlite3.IntegrityError:
            flash(f"Error: SKU '{sku}' already in use by another product.", "danger")

    return render_template('product_form.html', product=product, action="edit")

@app.route('/products/<int:id>/delete', methods=['POST'])
def product_delete(id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (id,))
    db.commit()
    flash("Product deleted successfully.", "info")
    return redirect(url_for('products'))

# ==========================================
# 3. BILLING / POS
# ==========================================
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    db = get_db()

    # Handle Checkout via POST (JSON API)
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('items'):
            return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

        items = data.get('items')
        cust_name = data.get('customer_name', 'Walk-in Customer')
        cust_phone = data.get('customer_phone', '9999999999')
        payment_method = data.get('payment_method', 'Cash')
        discount_pct = float(data.get('discount_pct', 0.0) or 0.0)
        gst_pct = float(data.get('gst_pct', 5.0) or 0.0)

        # Look up customer id if exists
        cust_row = db.execute("SELECT id FROM customers WHERE phone = ?", (cust_phone,)).fetchone()
        customer_id = cust_row['id'] if cust_row else None

        # Verify stock and calculate subtotal
        subtotal = 0.0
        verified_items = []
        for it in items:
            pid = it['id']
            qty = int(it['qty'])
            p_row = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
            if not p_row:
                return jsonify({'success': False, 'message': f"Product ID {pid} not found."}), 400
            if qty > p_row['stock']:
                return jsonify({'success': False, 'message': f"Insufficient stock for {p_row['name']} (Available: {p_row['stock']})."}), 400

            line_total = p_row['selling_price'] * qty
            subtotal += line_total
            verified_items.append({
                'product_id': pid,
                'sku': p_row['sku'],
                'name': p_row['name'],
                'cost_price': p_row['cost_price'],
                'unit_price': p_row['selling_price'],
                'qty': qty,
                'line_total': line_total,
                'current_stock': p_row['stock']
            })

        # Calculate totals
        discount_amt = (subtotal * discount_pct) / 100.0
        taxable = max(0.0, subtotal - discount_amt)
        gst_amt = (taxable * gst_pct) / 100.0
        grand_total = taxable + gst_amt

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        invoice_no = f"INV-{now.strftime('%y%m%d')}-{now.strftime('%H%M%S')}"

        try:
            cur = db.cursor()
            cur.execute("""
                INSERT INTO sales (invoice_no, customer_id, customer_name, customer_phone, subtotal, discount_pct, discount_amt, gst_pct, gst_amt, grand_total, payment_method, sold_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_no, customer_id, cust_name, cust_phone, subtotal, discount_pct, discount_amt, gst_pct, gst_amt, grand_total, payment_method, now_str))
            sale_id = cur.lastrowid

            for vi in verified_items:
                cur.execute("""
                    INSERT INTO sale_items (sale_id, product_id, sku, product_name, cost_price, unit_price, qty, line_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (sale_id, vi['product_id'], vi['sku'], vi['name'], vi['cost_price'], vi['unit_price'], vi['qty'], vi['line_total']))

                # Deduct stock
                new_stock = vi['current_stock'] - vi['qty']
                cur.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, vi['product_id']))

                # Log inventory movement
                cur.execute("""
                    INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
                    VALUES (?, ?, 'SALE', ?, ?, ?, ?, ?)
                """, (vi['product_id'], vi['name'], -vi['qty'], vi['current_stock'], new_stock, f"Sold on {invoice_no}", now_str))

            db.commit()
            return jsonify({
                'success': True,
                'sale_id': sale_id,
                'invoice_no': invoice_no,
                'redirect_url': url_for('receipt', sale_id=sale_id)
            })
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # GET Request: Load POS Catalog
    products_list = db.execute("SELECT id, sku, name, category, selling_price, stock FROM products WHERE stock > 0 ORDER BY name ASC").fetchall()
    customers_list = db.execute("SELECT id, name, phone FROM customers ORDER BY name ASC").fetchall()

    return render_template('billing.html', products=products_list, customers=customers_list)

# API endpoint for client search & barcode lookup
@app.route('/api/products')
def api_products():
    db = get_db()
    products_list = db.execute("SELECT id, sku, name, selling_price, stock FROM products ORDER BY name ASC").fetchall()
    return jsonify([dict(row) for row in products_list])

# ==========================================
# 4. RECEIPT
# ==========================================
@app.route('/receipt/<int:sale_id>')
def receipt(sale_id):
    db = get_db()
    sale = db.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
    if not sale:
        flash("Receipt / Sale not found.", "warning")
        return redirect(url_for('dashboard'))

    items = db.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
    return render_template('receipt.html', sale=sale, items=items)

# ==========================================
# 5. INVENTORY & AUDIT LOGS
# ==========================================
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    db = get_db()

    if request.method == 'POST':
        product_id = int(request.form.get('product_id'))
        action_type = request.form.get('action_type') # STOCK_IN, STOCK_OUT, ADJUSTMENT
        qty = int(request.form.get('qty', 0))
        reason = request.form.get('reason', '').strip() or 'Manual Adjustment'

        if qty <= 0:
            flash("Quantity must be a positive number.", "danger")
            return redirect(url_for('inventory'))

        prod = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not prod:
            flash("Product not found.", "danger")
            return redirect(url_for('inventory'))

        old_stock = prod['stock']
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if action_type == 'STOCK_IN':
            new_stock = old_stock + qty
            qty_change = qty
        elif action_type == 'STOCK_OUT':
            if qty > old_stock:
                flash(f"Cannot remove {qty} units. Current stock is only {old_stock}.", "danger")
                return redirect(url_for('inventory'))
            new_stock = old_stock - qty
            qty_change = -qty
        else: # ADJUSTMENT
            new_stock = qty
            qty_change = new_stock - old_stock

        db.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        db.execute("""
            INSERT INTO inventory_logs (product_id, product_name, change_type, qty_change, previous_stock, new_stock, reason, logged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, prod['name'], action_type, qty_change, old_stock, new_stock, reason, now_str))
        db.commit()

        flash(f"Stock for '{prod['name']}' updated. (Old: {old_stock} → New: {new_stock})", "success")
        return redirect(url_for('inventory'))

    products_list = db.execute("SELECT id, sku, name, stock FROM products ORDER BY name ASC").fetchall()
    logs = db.execute("""
        SELECT * FROM inventory_logs 
        ORDER BY id DESC LIMIT 100
    """).fetchall()

    return render_template('inventory.html', products=products_list, logs=logs)

# ==========================================
# 6. CUSTOMERS
# ==========================================
@app.route('/customers', methods=['GET', 'POST'])
def customers():
    db = get_db()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        if not name or not phone:
            flash("Customer Name and Phone are required.", "danger")
            return redirect(url_for('customers'))

        try:
            db.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
            db.commit()
            flash(f"Customer '{name}' registered successfully!", "success")
        except sqlite3.IntegrityError:
            flash(f"Customer with phone number '{phone}' already exists.", "danger")

        return redirect(url_for('customers'))

    query = request.args.get('q', '').strip()
    if query:
        pattern = f"%{query}%"
        customers_list = db.execute("""
            SELECT c.*, COUNT(s.id) as total_orders, COALESCE(SUM(s.grand_total), 0) as total_spent
            FROM customers c
            LEFT JOIN sales s ON c.phone = s.customer_phone
            WHERE c.name LIKE ? OR c.phone LIKE ?
            GROUP BY c.id
            ORDER BY c.name ASC
        """, (pattern, pattern)).fetchall()
    else:
        customers_list = db.execute("""
            SELECT c.*, COUNT(s.id) as total_orders, COALESCE(SUM(s.grand_total), 0) as total_spent
            FROM customers c
            LEFT JOIN sales s ON c.phone = s.customer_phone
            GROUP BY c.id
            ORDER BY c.name ASC
        """).fetchall()

    return render_template('customers.html', customers=customers_list, query=query)

@app.route('/customers/<int:id>')
def customer_detail(id):
    db = get_db()
    customer = db.execute("SELECT * FROM customers WHERE id = ?", (id,)).fetchone()
    if not customer:
        flash("Customer not found.", "warning")
        return redirect(url_for('customers'))

    history = db.execute("""
        SELECT * FROM sales 
        WHERE customer_phone = ? 
        ORDER BY id DESC
    """, (customer['phone'],)).fetchall()

    return render_template('customer_detail.html', customer=customer, history=history)

# ==========================================
# 7. REPORTS & ANALYTICS
# ==========================================
@app.route('/reports')
def reports():
    db = get_db()
    period = request.args.get('period', 'all')
    now = datetime.now()

    where_clause = ""
    params = []
    if period == 'today':
        where_clause = "WHERE s.sold_at LIKE ?"
        params.append(f"{now.strftime('%Y-%m-%d')}%")
    elif period == '7days':
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        where_clause = "WHERE s.sold_at >= ?"
        params.append(since)
    elif period == '30days':
        since = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        where_clause = "WHERE s.sold_at >= ?"
        params.append(since)

    # Financial totals
    rev_row = db.execute(f"""
        SELECT 
            COALESCE(SUM(si.line_total), 0.0) as total_revenue,
            COALESCE(SUM(si.cost_price * si.qty), 0.0) as total_cost
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        {where_clause}
    """, params).fetchone()

    total_revenue = rev_row['total_revenue']
    total_cost = rev_row['total_cost']
    gross_profit = total_revenue - total_cost
    profit_margin = (gross_profit / total_revenue * 100.0) if total_revenue > 0 else 0.0

    # Top selling items
    top_products = db.execute(f"""
        SELECT 
            si.product_name, 
            SUM(si.qty) as total_qty, 
            SUM(si.line_total) as total_rev
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        {where_clause}
        GROUP BY si.product_id
        ORDER BY total_qty DESC
        LIMIT 10
    """, params).fetchall()

    # Daily breakdown
    daily_sales = db.execute(f"""
        SELECT 
            SUBSTR(s.sold_at, 1, 10) as sale_date, 
            COUNT(s.id) as orders_count, 
            SUM(s.grand_total) as daily_revenue
        FROM sales s
        {where_clause}
        GROUP BY sale_date
        ORDER BY sale_date DESC
    """, params).fetchall()

    return render_template(
        'reports.html',
        period=period,
        total_revenue=total_revenue,
        total_cost=total_cost,
        gross_profit=gross_profit,
        profit_margin=profit_margin,
        top_products=top_products,
        daily_sales=daily_sales
    )

if __name__ == '__main__':
    # Run development server
    app.run(debug=True, host='127.0.0.1', port=5000)
