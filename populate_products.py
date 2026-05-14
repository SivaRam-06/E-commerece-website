"""
Populate e-commerce database with real products and images
"""
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

# Real product images from Unsplash
PRODUCTS_WITH_IMAGES = [
    {
        "name": "Premium Wireless Earbuds Pro",
        "slug": "premium-wireless-earbuds-pro",
        "description": "Active noise cancellation, 32-hour battery life, premium sound quality with deep bass.",
        "price": 4999,
        "compare_at_price": 6999,
        "category_id": 1,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop",
        "stock": 150,
        "is_featured": 1,
        "popularity": 98,
    },
    {
        "name": "Smart Watch Ultra",
        "slug": "smart-watch-ultra",
        "description": "AMOLED display, GPS tracking, heart rate monitor, water resistant, 14-day battery.",
        "price": 12999,
        "compare_at_price": 15999,
        "category_id": 1,
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop",
        "stock": 65,
        "is_featured": 1,
        "popularity": 120,
    },
    {
        "name": "Comfortable Cotton T-Shirt",
        "slug": "comfortable-cotton-tshirt",
        "description": "100% organic cotton, breathable fabric, perfect for casual wear, available in multiple colors.",
        "price": 599,
        "compare_at_price": 899,
        "category_id": 2,
        "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&auto=format&fit=crop",
        "stock": 300,
        "is_featured": 1,
        "popularity": 85,
    },
    {
        "name": "Urban Lifestyle Sneakers",
        "slug": "urban-lifestyle-sneakers",
        "description": "Lightweight, comfortable all-day wear, modern design, cushioned sole for support.",
        "price": 3499,
        "compare_at_price": 4999,
        "category_id": 2,
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop",
        "stock": 120,
        "is_featured": 1,
        "popularity": 92,
    },
    {
        "name": "Modern Desk Lamp",
        "slug": "modern-desk-lamp",
        "description": "LED desk lamp with adjustable brightness, USB charging port, minimalist design.",
        "price": 1899,
        "compare_at_price": 2499,
        "category_id": 3,
        "image": "https://images.unsplash.com/photo-1565636192335-14c46fa1120d?w=500&auto=format&fit=crop",
        "stock": 85,
        "is_featured": 0,
        "popularity": 65,
    },
    {
        "name": "Luxury Skincare Serum",
        "slug": "luxury-skincare-serum",
        "description": "Vitamin C infused serum, brightening treatment, reduces fine lines, dermatologist tested.",
        "price": 1299,
        "compare_at_price": 1799,
        "category_id": 4,
        "image": "https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&auto=format&fit=crop",
        "stock": 200,
        "is_featured": 0,
        "popularity": 78,
    },
    {
        "name": "Professional Yoga Mat",
        "slug": "professional-yoga-mat",
        "description": "Non-slip, extra thick 6mm padding, eco-friendly material, includes carrying strap.",
        "price": 1499,
        "compare_at_price": 1999,
        "category_id": 5,
        "image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=500&auto=format&fit=crop",
        "stock": 110,
        "is_featured": 0,
        "popularity": 71,
    },
    {
        "name": "4K Action Camera",
        "slug": "4k-action-camera",
        "description": "Waterproof, 4K video, image stabilization, wide-angle lens, perfect for adventures.",
        "price": 18999,
        "compare_at_price": 22999,
        "category_id": 1,
        "image": "https://images.unsplash.com/photo-1609034227505-5876f6aa4e90?w=500&auto=format&fit=crop",
        "stock": 35,
        "is_featured": 0,
        "popularity": 88,
    },
    {
        "name": "Slim Fit Jeans",
        "slug": "slim-fit-jeans",
        "description": "Premium denim, comfortable stretch fabric, versatile dark wash, perfect fit.",
        "price": 1999,
        "compare_at_price": 2899,
        "category_id": 2,
        "image": "https://images.unsplash.com/photo-1542272604-787c62d465d1?w=500&auto=format&fit=crop",
        "stock": 180,
        "is_featured": 0,
        "popularity": 82,
    },
    {
        "name": "Minimalist Wall Shelf",
        "slug": "minimalist-wall-shelf",
        "description": "Floating wooden shelf, space-saving design, holds up to 15kg, modern aesthetic.",
        "price": 799,
        "compare_at_price": 1199,
        "category_id": 3,
        "image": "https://images.unsplash.com/photo-1595585851963-b0e5c2c2dfa0?w=500&auto=format&fit=crop",
        "stock": 95,
        "is_featured": 0,
        "popularity": 56,
    },
    {
        "name": "Organic Face Cleanser",
        "slug": "organic-face-cleanser",
        "description": "Gentle formula, removes makeup and impurities, suitable for all skin types.",
        "price": 599,
        "compare_at_price": 899,
        "category_id": 4,
        "image": "https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&auto=format&fit=crop",
        "stock": 250,
        "is_featured": 0,
        "popularity": 73,
    },
    {
        "name": "Resistance Band Set",
        "slug": "resistance-band-set",
        "description": "5-piece set with different resistance levels, home gym equipment, portable.",
        "price": 899,
        "compare_at_price": 1299,
        "category_id": 5,
        "image": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=500&auto=format&fit=crop",
        "stock": 140,
        "is_featured": 0,
        "popularity": 67,
    },
]


def populate_products():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    
    # Clear existing products to refresh with real images
    db.execute("DELETE FROM products")
    db.commit()
    
    # Insert new products
    for product in PRODUCTS_WITH_IMAGES:
        db.execute(
            """INSERT INTO products
            (name, slug, description, price, compare_at_price, category_id,
             image, stock, is_featured, popularity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                product["name"],
                product["slug"],
                product["description"],
                product["price"],
                product["compare_at_price"],
                product["category_id"],
                product["image"],
                product["stock"],
                product["is_featured"],
                product["popularity"],
            ),
        )
    
    db.commit()
    db.close()
    print(f"Successfully inserted {len(PRODUCTS_WITH_IMAGES)} products with real images!")


if __name__ == "__main__":
    populate_products()
