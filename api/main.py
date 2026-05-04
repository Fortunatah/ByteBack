from fastapi import FastAPI, Query, Request
from pydantic import BaseModel
import csv
import os
from typing import List, Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Byte Back Tech API")

# Setup templates directory
# Assumes main.py is in /api and templates is in /api/templates
templates = Jinja2Templates(directory="api/templates")

# --- MODELS ---

class Product(BaseModel):
    part_id: str
    category: str
    model: str
    vram_gb: str
    clock_speed_mhz: str
    health_pct: int
    price_usd: float
    market_equivalent_item: str
    savings_vs_market: str

class Order(BaseModel):
    part_id: str
    guest_email: str
    shipping_address: str

# --- HELPERS ---

def load_products():
    products = []
    # Using os.path.join for better Windows/Linux compatibility
    csv_path = os.path.join('api', 'data', 'products.csv')
    
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Feature 1 & 2 Logic: Value Comparison
            mkt_price = float(row['market_equivalent_price'])
            our_price = float(row['price_usd'])
            savings = mkt_price - our_price
            
            row['savings_vs_market'] = f"${savings:.2f} cheaper than {row['market_equivalent_item']}"
            products.append(row)
    return products

def save_order(order: Order):
    csv_path = os.path.join('api', 'data', 'orders.csv')
    file_exists = os.path.isfile(csv_path)
    
    with open(csv_path, mode='a', newline='') as file:
        fieldnames = ['part_id', 'guest_email', 'shipping_address']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(order.model_dump())

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves the main Byte Back Tech storefront.
    """
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={}
    )

@app.get("/products", response_model=List[Product])
def get_catalog(
    category: Optional[str] = None,
    min_vram: Optional[int] = None,
    max_price: Optional[float] = None,
    min_health: Optional[int] = Query(default=0, ge=0, le=100)
):
    """
    Feature 1 & 2: Combined Product Catalog and Developer Search Engine.
    """
    all_products = load_products()
    filtered_results = []

    for product in all_products:
        if category and product['category'].lower() != category.lower():
            continue
            
        if min_vram is not None:
            try:
                vram_val = int(product['vram_gb'])
                if vram_val < min_vram:
                    continue
            except (ValueError, TypeError):
                continue 

        if max_price and float(product['price_usd']) > max_price:
            continue

        if int(product['health_pct']) < min_health:
            continue

        filtered_results.append(product)

    return filtered_results

@app.post("/checkout")
async def guest_checkout(order: Order):
    """
    Feature 3: Frictionless Guest Checkout.
    Persists order data to orders.csv.
    """
    save_order(order)
    return {"status": "success", "message": f"Order for {order.part_id} recorded!"}