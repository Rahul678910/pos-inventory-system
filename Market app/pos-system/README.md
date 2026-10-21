# 🛒 Apna Market POS - Web POS & Inventory Management System

A lightweight, modern Point of Sale (POS) and Inventory Management web application built with **Python (Flask)**, **SQLite3**, and vanilla **HTML5 / CSS3 / JavaScript**.

Designed for shopkeepers, small retail markets, and store owners who need a clean, responsive web interface accessible from desktop PCs, tablets, or mobile barcode scanners on the local network.

---

## 📂 File Structure

```text
pos-system/
├── app.py                 # All routes, SQLite database handlers & business logic (Flask)
├── schema.sql             # Relational database table definitions
├── requirements.txt       # Python web dependencies
├── .gitignore             # Git ignore configuration
├── README.md              # Project documentation & usage guide
├── templates/
│   ├── base.html          # Responsive navbar, flash messages & layout skeleton
│   ├── dashboard.html     # Real-time sales KPIs, low-stock warnings & recent transactions
│   ├── products.html      # Product catalog list, search filter, and stock alert badges
│   ├── product_form.html  # Unified Add / Edit product form
│   ├── billing.html       # Fast POS billing screen with client-side Cart JavaScript
│   ├── receipt.html       # Clean printable receipt with @media print stylesheet
│   ├── inventory.html     # Stock In / Stock Out adjustments & real-time audit logs
│   ├── customers.html     # Customer registry with search & quick add form
│   ├── customer_detail.html # Individual customer profile & full transaction history
│   └── reports.html       # Revenue, COGS, estimated profit margin & top-selling items
└── static/
    └── style.css          # Modern, responsive CSS with container queries & accessible tables
```

---

## 🚀 Quickstart

### 1. Navigate to the Directory
```bash
cd pos-system
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

### 5. Access in Your Browser
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

> **Note:** The SQLite database (`market.db`) is automatically initialized and seeded with demo retail products and sample sales data on first launch.

---

## 🖥️ Screen Features

| Screen | Route | Description |
| :--- | :--- | :--- |
| **📊 Dashboard** | `/` or `/dashboard` | Today’s revenue, items sold, low-stock alerts with direct restock links, and recent transactions. |
| **🏷️ Products** | `/products` | Searchable catalog, price/cost monitoring, and stock alerts. Includes Add (`/products/new`) and Edit (`/products/<id>/edit`). |
| **🛒 Billing / POS** | `/billing` | Split-screen POS layout. Features instant **Barcode Scanner** lookup (Enter-to-Add), live search, cart item quantity adjustments, customer selection, dynamic **Discount %**, **GST / Tax %**, and checkout. |
| **🧾 Receipt** | `/receipt/<id>` | Clean, itemized receipt formatted for printing on 58mm/80mm thermal printers or standard A4 paper via browser print (`Ctrl + P`). |
| **📦 Inventory** | `/inventory` | Form to log manual Stock In (purchases), Stock Out (damages), or physical audit corrections. Full audit trail of all adjustments. |
| **👥 Customers** | `/customers` | Directory of registered customers with lifetime order counts and total spend. Includes customer order drill-down (`/customers/<id>`). |
| **📈 Reports** | `/reports` | Filter by All Time, Today, Last 7 Days, or Last 30 Days. Calculates Total Revenue, Cost of Goods Sold (COGS), Gross Profit, Profit Margin %, and Top 10 Best-Selling Products. |

---

## ⚡ Barcode Scanner & POS Hardware Support

- **Handheld USB / Wireless Scanners**: Standard scanners operating in HID keyboard mode will type directly into the `⚡ Barcode / SKU Quick Scan` input field and trigger `Enter`, adding products instantly to the cart.
- **Receipt Printers**: The receipt view (`/receipt/<id>`) contains a dedicated `@media print` stylesheet that removes navigation bars and buttons, providing a clean receipt layout.

---

## 📄 License

Distributed under the **MIT License**.
