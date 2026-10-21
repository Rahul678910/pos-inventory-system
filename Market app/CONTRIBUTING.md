# Contributing to Apna Market POS & Inventory System

Thank you for your interest in contributing to this project!

## How to Contribute

1. **Fork the Repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/<your-username>/market-pos-inventory.git
   cd market-pos-inventory
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```
4. **Set up a virtual environment and install dependencies**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```
5. **Make your changes** and test thoroughly:
   - Ensure the database initialization and seeding run without error:
     ```bash
     python -c "import market_app; market_app.init_db(); print('DB OK')"
     ```
   - Verify the GUI launches and screens work:
     ```bash
     python market_app.py
     ```
6. **Commit your changes** following conventional commit messages:
   ```bash
   git commit -m "feat(billing): add thermal receipt printing support"
   ```
7. **Push to your branch**:
   ```bash
   git push origin feature/my-new-feature
   ```
8. **Open a Pull Request** describing what changes were made and why.

## Code Standards
- Keep code clean, readable, and PEP 8 compliant.
- Ensure all SQLite connections are properly committed and closed.
- Handle missing optional libraries (`matplotlib`, `reportlab`) gracefully with fallbacks.
- Document any schema changes in the README and Jupyter notebook.
