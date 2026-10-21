::: {align="center"}
# 🛒 Apna Market

### POS & Inventory Management System

**A desktop toolkit for smarter billing, stock control, and retail
reporting.**

Built with **Python · Tkinter · SQLite**

```{=html}
<p>
```
`<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">`{=html}
`<img src="https://img.shields.io/badge/Interface-Tkinter-0B7285?style=for-the-badge" alt="Tkinter">`{=html}
`<img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">`{=html}
`<img src="https://img.shields.io/badge/License-MIT-F5C542?style=for-the-badge" alt="MIT License">`{=html}
```{=html}
</p>
```
[Features](#-features) · [Getting Started](#-getting-started) ·
[Notebook](#-jupyter-notebook-version) ·
[Database](#-database-at-a-glance) · [Project
Structure](#-project-structure) · [Contributing](#-contributing)
:::

------------------------------------------------------------------------

## 📌 About the Project

**Apna Market** is a Python desktop application designed for local
markets, retail shops, and grocery stores. It brings everyday shop
operations---billing, product management, stock tracking, customer
records, and sales reporting---into one local application.

It uses **Tkinter** for the desktop interface and **SQLite** for local
data storage, without requiring a separate database server or web
framework.

You can use either the standalone desktop app (`market_app.py`) or the
interactive Jupyter Notebook (`market_pos_inventory.ipynb`).

## ✨ Features

```{=html}
<table>
```
```{=html}
<tr>
```
```{=html}
<td width="50%" valign="top">
```
### 📊 Dashboard

-   Today's revenue and units sold
-   Low-stock alerts and catalog count
-   Quick-restock workflow
-   Recent sales activity

### 🏷️ Product Catalog

-   Add, edit, and delete products
-   Track SKU/barcode, category, and prices
-   Search products quickly
-   Highlight products running low

### 🛍️ POS & Checkout

-   Barcode scanner or manual SKU entry
-   Shopping cart with quantity controls
-   Customer selection or walk-in sales
-   Discount and GST/tax calculations
-   Cash, UPI/QR, and card payment modes
-   Stock checks to help prevent overselling

```{=html}
</td>
```
```{=html}
<td width="50%" valign="top">
```
### 📦 Inventory Control

-   Record stock-in and stock-out changes
-   Track damaged or expired stock
-   Adjust inventory with a reason
-   Maintain stock-change audit logs
-   Deduct stock after completed sales

### 👥 Customer Records

-   Store customer contact details
-   View historical transactions
-   Review previous orders

### 📈 Reports & Analytics

-   Filter by today, last 7 days, last 30 days, or all time
-   Review revenue, COGS, gross profit, and margin
-   Find the top 10 best-selling products
-   View daily revenue trends with Matplotlib (optional)

### 🧾 Invoices & Roles

-   Generate PDF invoices with ReportLab (optional)
-   Fall back to text receipts
-   Admin/Owner and Cashier access modes
-   Restrict cost prices and profit figures in Cashier mode

```{=html}
</td>
```
```{=html}
</tr>
```
```{=html}
</table>
```
## 🖥️ Interface Preview

The app is organized around a familiar retail workflow:

``` text
┌─────────────────────────────────────────────────────────────────────┐
│  🛒 APNA MARKET                            Role: Admin   [Switch]    │
├─────────────────────────────────────────────────────────────────────┤
│  Dashboard │ Products │ Billing / POS │ Inventory │ Reports         │
├─────────────────────────────────────────────────────────────────────┤
│  Today's Revenue      Units Sold      Low Stock      Total Products  │
│     ₹12,450              84               3                45        │
├─────────────────────────────────────────────────────────────────────┤
│  Low-stock warnings                    Recent sales                 │
│  • Assam Gold Tea (Stock: 4)            • Invoice #1 — ₹403.99       │
│  • Herbal Bath Soap (Stock: 3)           • Walk-in — ₹273.00         │
└─────────────────────────────────────────────────────────────────────┘
```

*Illustrative layout only; figures and entries above are examples.*

## 🚀 Getting Started

### Requirements

-   Python **3.10 or newer**
-   Tkinter and SQLite3 (normally included with standard Python
    distributions)
-   Optional: Matplotlib for revenue charts and ReportLab for PDF
    invoices

### 1. Clone the repository

Replace the example URL with your repository URL:

``` bash
git clone https://github.com/your-username/market-pos-inventory.git
cd market-pos-inventory
```

### 2. Create a virtual environment

**Windows**

``` powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

The app is designed to run with Python's standard libraries. Optional
packages such as `matplotlib` and `reportlab` add charting and PDF
invoice features.

### 4. Launch the desktop app

``` bash
python market_app.py
```

## 📓 Jupyter Notebook Version

To explore the notebook workflow:

``` bash
jupyter notebook market_pos_inventory.ipynb
```

Alternatively, open `market_pos_inventory.ipynb` in VS Code and run its
cells in order. The notebook covers database setup, demo data, invoice
generation, and launching the GUI from the notebook.

## 🔫 Barcode Scanner Support

Most USB and Bluetooth barcode scanners that operate in **HID keyboard
mode** work like a keyboard.

1.  Open the **Billing / POS** tab.
2.  Focus the **Barcode / SKU Scan** input.
3.  Scan a barcode. The scanner enters the code and sends Enter,
    allowing the product to be added to the cart.

## 🗄️ Database at a Glance

The application stores its data locally in `market.db` using SQLite.

``` mermaid
erDiagram
    PRODUCTS ||--o{ SALE_ITEMS : "sold in"
    PRODUCTS ||--o{ INVENTORY_LOGS : "tracks"
    CUSTOMERS ||--o{ SALES : "places"
    SALES ||--|{ SALE_ITEMS : "contains"

    PRODUCTS {
        int id PK
        string sku UK
        string name
        string category
        real cost_price
        real selling_price
        int stock
        int min_stock
    }

    CUSTOMERS {
        int id PK
        string name
        string phone UK
        string email
        string created_at
    }

    SALES {
        int id PK
        string invoice_no UK
        string customer_name
        string customer_phone
        real subtotal
        real discount_pct
        real discount_amt
        real gst_pct
        real gst_amt
        real grand_total
        string payment_method
        string cashier
        string sold_at
    }

    SALE_ITEMS {
        int id PK
        int sale_id FK
        int product_id FK
        string sku
        string product_name
        real cost_price
        real unit_price
        int qty
        real line_total
    }

    INVENTORY_LOGS {
        int id PK
        int product_id FK
        string product_name
        string change_type
        int qty_change
        int previous_stock
        int new_stock
        string reason
        string logged_at
    }
```

## 🧰 Tech Stack

  ------------------------------------------------------------------------------------------
  Technology                                             Purpose
  ------------------------------------------------------ -----------------------------------
  [Python](https://www.python.org/)                      Application logic

  [Tkinter /                                             Desktop interface
  ttk](https://docs.python.org/3/library/tkinter.html)   

  [SQLite](https://www.sqlite.org/)                      Local relational database

  [Matplotlib](https://matplotlib.org/) *(optional)*     Revenue trend charts

  [ReportLab](https://www.reportlab.com/) *(optional)*   PDF invoice generation

  Jupyter Notebook                                       Interactive walkthrough
  ------------------------------------------------------------------------------------------

## 📂 Project Structure

``` text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── invoices/                    # Generated invoices
│   └── .gitkeep
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── market_app.py                # Standalone desktop app
├── market_pos_inventory.ipynb   # Notebook version
└── requirements.txt
```

## 🤝 Contributing

Ideas, bug reports, and improvements are welcome.

1.  Fork the repository.
2.  Create a branch: `git checkout -b feature/your-feature`
3.  Make your changes and commit them:
    `git commit -m "feat: describe your change"`
4.  Push the branch: `git push origin feature/your-feature`
5.  Open a Pull Request.

Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting
changes.

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for
details.

------------------------------------------------------------------------

::: {align="center"}
**Made for local markets, shops, and entrepreneurs.**

`<sub>`{=html}Apna Market · POS & Inventory Management
System`</sub>`{=html}
:::
