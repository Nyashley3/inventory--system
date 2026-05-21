# Inventory System (Lightweight)

This is a minimal, mobile-optimized inventory management system built with Flask and SQLite.

Features:
- Login/signup with role-based access (cashier, supervisor, manager)
- Product CRUD and per-branch stock tracking with low-stock alerts
- Barcode scanning via device camera (uses Quagga2 in browser)
- Multi-branch support and centralized sales reporting (daily/weekly/monthly)

Quick start (Windows):

1. Create a virtualenv and install dependencies:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r "inventory System/inventory_app/requirements.txt"
```

2. Run the app (development):

```powershell
python "inventory System/inventory_app/app.py"
```

3. Initialize DB and bootstrap admin:

Run the helper script from the inventory_app folder:

```powershell
cd "inventory_app"
.\init-admin.ps1
```

Or run it directly with a one-line command:

```powershell
cd "inventory_app"
.\init-admin.ps1 --admin-username admin --admin-password "MyStrongPass!23"
```

The helper will create or update the default branch and admin account.

Password requirements:
- At least 10 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one symbol such as `!@#$%^&*()`

4. Visit http://localhost:5000 and login. Use the scanner on mobile or desktop with a camera.

Database schema summary (see `app.py` comments):
- `User(id, username, password_hash, role, branch_id)`
- `Branch(id, name, address)`
- `Product(id, name, barcode, price, description)`
- `ProductStock(id, product_id, branch_id, quantity, threshold)`
- `Sale(id, branch_id, user_id, total, created_at)`
- `SaleItem(id, sale_id, product_id, quantity, price)`

API endpoints (JSON) — main ones:
- `POST /api/signup` {username,password,role,branch_id}
- `POST /api/login` {username,password} -> {access_token}
- `GET /api/branches`
- `POST /api/branches` (manager)
- `GET /api/products` optional `?branch_id=..` or `?barcode=...`
- `POST /api/products` (supervisor/manager)
- `POST /api/stocks` (supervisor/manager) {product_id,branch_id,quantity,threshold}
- `POST /api/sales` (cashier+) {branch_id, items:[{product_id,quantity}]}
- `GET /api/reports/sales?range=daily|weekly|monthly&branch_id=..` (supervisor/manager)
- `GET /api/alerts`

Notes & next steps:
- Replace `JWT_SECRET_KEY` with a secure value for production.
- Consider HTTPS and stricter CORS/CSRF for web deployments.
- For larger deployments, switch to PostgreSQL or MySQL and add migrations (Flask-Migrate).

One-click launch options
-----------------------

Use the provided helper scripts from the `inventory_app` folder to shorten startup:

PowerShell (recommended):

```powershell
cd "inventory_app"
.\run.ps1
```

Windows (double-click or CMD):

```cmd
cd "inventory_app"
start.bat
```

VS Code: open the workspace and press F5 or run the `Run Inventory App` configuration from the Run panel.

