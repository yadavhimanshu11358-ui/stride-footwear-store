# STRIDE — Footwear E-Commerce Store (Django)




A full-stack Django e-commerce footwear storefront for shoes, sneakers, casuals, slippers & chappals, sandals, and formal shoes.

## Key Features
- **Catalog, Search & Multi-Filters:** Category filtering, live search dropdown, sorting, budget bands, rating filter, discount filter, and pagination.
- **Size-Wise Stock & Cart/Wishlist:** UK size selection (`UK 6` to `UK 10`) with stock tracking, local wishlist drawer, cart drawer, promo codes (`STRIDE10`, `FIRST150`), and 1-click **Buy Now**.
- **Customer Account, Orders & Invoices:** Account registration/login, saved delivery address, order lookup/history, order cancellation (with stock restore), 7-day size exchange requests, and printable order invoices.
- **Checkout & Admin Management:** Cash on Delivery (COD) and Razorpay online payment integration, customer reviews, contact inquiries, and Django Admin management.

---

## Requirements to Run This Project
1. **Python 3.10+** installed on your system.
2. **pip** & **virtualenv** (recommended).
3. **Required Python Packages:**
   - `django`
   - `razorpay`
   - `pillow` (required for `ImageField` / product image uploads)

Create a `requirements.txt` file in the project root if you don't have one yet:

```text
Django>=5.0
razorpay>=1.4.0
Pillow>=10.0.0
```

---

## Local Setup & Run Steps

### 1. Clone the Repository & Move into Project Folder
```bash
git clone [https://github.com/yadavhimanshu11358-ui/stride-footwear-store.git](https://github.com/yadavhimanshu11358-ui/stride-footwear-store.git)
cd stride-footwear-store
```

### 2. Create & Activate Virtual Environment (Recommended)
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment / Settings
- Configure `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, email settings, and Razorpay keys (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) in your Django settings / environment variables.
- For testing online payments, use Razorpay test keys; for local testing without keys, **Cash on Delivery (COD)** works out of the box.

### 5. Apply Migrations, Seed Products & Start Server
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_products
python manage.py createsuperuser
python manage.py runserver
```

Open **`http://127.0.0.1:8000/`** in your browser for the storefront, and **`http://127.0.0.1:8000/admin/`** for the admin panel.

---

## Pushing `README.md` to GitHub
```bash
git add README.md requirements.txt
git commit -m "Add README.md and project setup instructions"
git push
```
