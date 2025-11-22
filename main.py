import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="HoloCommerce API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

class Cart(BaseModel):
    session_id: str
    items: List[CartItem]


@app.on_event("startup")
def seed_products():
    if db is None:
        return
    # Seed only if no products exist
    if db["product"].count_documents({}) == 0:
        demo_products = [
            {
                "title": "Aether Chrono X1",
                "description": "Premium titanium watch with sapphire crystal, neon lume, and quantum-precision movement.",
                "price": 1299.0,
                "category": "Watches",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1518544801976-3e188ae4fab1?q=80&w=1600&auto=format&fit=crop",
                "gallery": [
                    "https://images.unsplash.com/photo-1524805444758-089113d48a6f?q=80&w=1600&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1516826957135-700dedea698c?q=80&w=1600&auto=format&fit=crop"
                ],
                "colors": ["titanium", "onyx"],
                "materials": ["titanium", "sapphire"],
                "rating": 4.9,
                "featured": True,
                "model_url": None,
                "tags": ["chrono", "luxury", "neon"]
            },
            {
                "title": "Nebula Wallet Pro",
                "description": "Slim carbon-fiber wallet with RFID shield and magnetic quick-access.",
                "price": 189.0,
                "category": "Wallets",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1610701592028-0b4f6a9817d4?q=80&w=1600&auto=format&fit=crop",
                "gallery": [],
                "colors": ["carbon", "silver"],
                "materials": ["carbon fiber", "aluminum"],
                "rating": 4.7,
                "featured": True,
                "model_url": None,
                "tags": ["rfid", "slim"]
            },
            {
                "title": "Flux Rings Set",
                "description": "Stackable rings with iridescent finish and subtle lumen edge.",
                "price": 129.0,
                "category": "Jewelry",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?q=80&w=1600&auto=format&fit=crop",
                "gallery": [],
                "colors": ["violet", "steel"],
                "materials": ["steel"],
                "rating": 4.6,
                "featured": False,
                "model_url": None,
                "tags": ["rings", "iridescent"]
            },
            {
                "title": "Spectra AR Shades",
                "description": "Next-gen eyewear with polarized optics and AR-ready frame.",
                "price": 349.0,
                "category": "Eyewear",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=1600&auto=format&fit=crop",
                "gallery": [],
                "colors": ["black", "smoke"],
                "materials": ["polycarbonate"],
                "rating": 4.5,
                "featured": True,
                "model_url": None,
                "tags": ["ar", "polarized"]
            },
            {
                "title": "Pulse Band S",
                "description": "Holographic wearable with health telemetry and soft neon glow.",
                "price": 499.0,
                "category": "Wearables",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1526401485004-2fda9f4fced4?q=80&w=1600&auto=format&fit=crop",
                "gallery": [],
                "colors": ["teal", "violet"],
                "materials": ["silicone", "aluminum"],
                "rating": 4.4,
                "featured": False,
                "model_url": None,
                "tags": ["health", "wearable"]
            },
            {
                "title": "Ion Dock +",
                "description": "Minimal magnetic charger with soft white halo illumination.",
                "price": 89.0,
                "category": "Tech",
                "in_stock": True,
                "image": "https://images.unsplash.com/photo-1517495306984-937b1812c8a7?q=80&w=1600&auto=format&fit=crop",
                "gallery": [],
                "colors": ["white", "graphite"],
                "materials": ["aluminum"],
                "rating": 4.3,
                "featured": False,
                "model_url": None,
                "tags": ["charger", "dock"]
            }
        ]
        for p in demo_products:
            create_document("product", p)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# Products API
@app.get("/api/products")
def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    featured: Optional[bool] = None,
    sort: Optional[str] = Query(default=None, description="price_asc|price_desc|rating_desc"),
    limit: int = Query(default=50, ge=1, le=200),
):
    if db is None:
        return {"items": [], "total": 0}
    filt = {}
    if q:
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    if category:
        filt["category"] = category
    price_cond = {}
    if min_price is not None:
        price_cond["$gte"] = min_price
    if max_price is not None:
        price_cond["$lte"] = max_price
    if price_cond:
        filt["price"] = price_cond
    if featured is not None:
        filt["featured"] = featured

    cursor = db["product"].find(filt)
    if sort == "price_asc":
        cursor = cursor.sort("price", 1)
    elif sort == "price_desc":
        cursor = cursor.sort("price", -1)
    elif sort == "rating_desc":
        cursor = cursor.sort("rating", -1)

    items = []
    for doc in cursor.limit(limit):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return {"items": items, "total": len(items)}


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/api/categories")
def get_categories():
    if db is None:
        return ["Watches", "Wearables", "Tech", "Wallets", "Jewelry", "Eyewear"]
    cats = db["product"].distinct("category")
    return cats


# Cart API (session-based)
@app.get("/api/cart/{session_id}")
def get_cart(session_id: str):
    if db is None:
        return {"session_id": session_id, "items": []}
    cart = db["cart"].find_one({"session_id": session_id})
    if not cart:
        return {"session_id": session_id, "items": []}
    cart["id"] = str(cart.pop("_id"))
    return cart


@app.post("/api/cart")
def upsert_cart(cart: Cart):
    if db is None:
        return cart.model_dump()
    payload = cart.model_dump()
    existing = db["cart"].find_one({"session_id": payload["session_id"]})
    if existing:
        db["cart"].update_one({"_id": existing["_id"]}, {"$set": {"items": payload["items"]}})
        existing["items"] = payload["items"]
        existing["id"] = str(existing.pop("_id"))
        return existing
    else:
        new_id = create_document("cart", payload)
        payload["id"] = new_id
        return payload


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
