
from decimal import Decimal

from src.products.models import Product
from src.categories.models import Category
from src.utils.db import LocalSession


PRODUCTS = [
    # APPAREL — category_id 1
    (1, "Classic Cotton T-Shirt", "Soft breathable cotton everyday t-shirt.", "24.99", "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab"),
    (1, "Oversized Graphic T-Shirt", "Relaxed fit graphic printed casual t-shirt.", "29.99", "https://images.unsplash.com/photo-1503341504253-dff4815485f1"),
    (1, "Slim Fit Casual Shirt", "Smart casual slim fit button-down shirt.", "39.99", "https://images.unsplash.com/photo-1598033129183-c4f50c736f10"),
    (1, "Linen Summer Shirt", "Lightweight breathable linen shirt for summer.", "44.99", "https://images.unsplash.com/photo-1603252109303-2751441dd157"),
    (1, "Classic Blue Denim Jeans", "Regular fit blue denim jeans for everyday wear.", "59.99", "https://images.unsplash.com/photo-1542272604-787c3835535d"),
    (1, "Black Slim Fit Jeans", "Modern slim fit black denim jeans.", "64.99", "https://images.unsplash.com/photo-1541099649105-f69ad21f3246"),
    (1, "Men's Casual Hoodie", "Comfortable fleece hoodie with adjustable drawstring.", "49.99", "https://images.unsplash.com/photo-1556821840-3a63f95609a7"),
    (1, "Lightweight Bomber Jacket", "Versatile lightweight bomber jacket.", "79.99", "https://images.unsplash.com/photo-1551028719-00167b16eac5"),
    (1, "Women's Floral Summer Dress", "Elegant floral dress for casual outings.", "54.99", "https://images.unsplash.com/photo-1496747611176-843222e1e57c"),
    (1, "Women's Casual Top", "Comfortable everyday women's casual top.", "27.99", "https://images.unsplash.com/photo-1551163943-3f6a855d1153"),
    (1, "Women's Denim Jacket", "Classic denim jacket with front pockets.", "69.99", "https://images.unsplash.com/photo-1548624149-f7c2c9a6d4b3"),
    (1, "Women's Wide Leg Trousers", "Relaxed tailored trousers for everyday styling.", "48.99", "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1"),
    (1, "Men's Cargo Pants", "Utility cargo pants with multiple pockets.", "52.99", "https://images.unsplash.com/photo-1517438476312-10d79c077509"),
    (1, "Women's Knit Sweater", "Soft knitted sweater for cooler days.", "45.99", "https://images.unsplash.com/photo-1576566588028-4147f3842f27"),
    (1, "Men's Polo T-Shirt", "Classic cotton polo with a comfortable fit.", "32.99", "https://images.unsplash.com/photo-1625910513413-5fcf6f1f4b5e"),
    (1, "Women's Casual Skirt", "Versatile everyday skirt with comfortable fit.", "35.99", "https://images.unsplash.com/photo-1583496661160-fb5886a13d27"),
    (1, "Men's Formal Shirt", "Clean formal shirt suitable for office wear.", "42.99", "https://images.unsplash.com/photo-1596755094514-f87e34085b2c"),
    (1, "Women's Casual Hoodie", "Relaxed soft hoodie for everyday comfort.", "46.99", "https://images.unsplash.com/photo-1556821840-3a63f95609a7"),
    (1, "Men's Chino Trousers", "Smart casual cotton chinos.", "47.99", "https://images.unsplash.com/photo-1473966968600-fa801b869a1a"),
    (1, "Women's Cotton Kurti", "Comfortable printed cotton kurti for daily wear.", "38.99", "https://images.unsplash.com/photo-1583391733956-6c78276477e3"),

    # ACCESSORIES — category_id 2
    (2, "Classic Analog Watch", "Minimal analog wristwatch with elegant dial.", "89.99", "https://images.unsplash.com/photo-1523275335684-37898b6baf30"),
    (2, "Digital Sports Watch", "Digital watch with stopwatch and everyday sports features.", "59.99", "https://images.unsplash.com/photo-1524805444758-089113d48a6d"),
    (2, "Polarized Sunglasses", "UV-protective polarized sunglasses.", "34.99", "https://images.unsplash.com/photo-1511499767150-a48a237f0083"),
    (2, "Leather Wallet", "Compact wallet with multiple card slots.", "29.99", "https://images.unsplash.com/photo-1627123424574-724758594e93"),
    (2, "Classic Leather Belt", "Adjustable everyday leather belt.", "25.99", "https://images.unsplash.com/photo-1624222247344-550fb8f7f6c0"),
    (2, "Canvas Baseball Cap", "Adjustable cotton baseball cap.", "19.99", "https://images.unsplash.com/photo-1588850561407-ed78c282e89b"),
    (2, "Minimalist Backpack", "Everyday backpack with laptop compartment.", "64.99", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62"),
    (2, "Women's Shoulder Handbag", "Stylish shoulder handbag for everyday use.", "74.99", "https://images.unsplash.com/photo-1584917865442-de89df76afd3"),
    (2, "Travel Duffel Bag", "Spacious duffel bag for weekend trips.", "69.99", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62"),
    (2, "Stainless Steel Bracelet", "Minimal stainless steel bracelet.", "22.99", "https://images.unsplash.com/photo-1611591437281-460bfbe1220a"),
    (2, "Classic Hoop Earrings", "Lightweight everyday hoop earrings.", "18.99", "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908"),
    (2, "Travel Crossbody Sling Bag", "Compact crossbody bag for daily essentials.", "39.99", "https://images.unsplash.com/photo-1590874103328-eac38a683ce7"),

    # HOME & LIVING — category_id 3
    (3, "Premium Cotton Bedsheet Set", "Soft cotton bedsheet set for comfortable sleep.", "79.99", "https://images.unsplash.com/photo-1631049307264-da0ec9d70304"),
    (3, "Decorative Cushion Set", "Set of soft decorative cushions for your sofa.", "32.99", "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2"),
    (3, "Modern Table Lamp", "Minimal table lamp for bedroom or workspace.", "49.99", "https://images.unsplash.com/photo-1507473885765-e6ed057f782c"),
    (3, "Reusable Water Bottle", "Insulated stainless steel reusable bottle.", "24.99", "https://images.unsplash.com/photo-1602143407151-7111542de6e8"),
    (3, "Ceramic Coffee Mug Set", "Elegant ceramic mugs for everyday coffee.", "21.99", "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d"),
    (3, "Minimal Wall Clock", "Modern wall clock for living room decoration.", "36.99", "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c"),
    (3, "Storage Organizer Basket", "Multipurpose woven storage basket.", "27.99", "https://images.unsplash.com/photo-1595428774223-ef52624120d2"),
    (3, "Soft Throw Blanket", "Cozy throw blanket for sofa and bedroom.", "42.99", "https://images.unsplash.com/photo-1600369671236-e74521d4b6ad"),

    # FOOTWEAR — category_id 4
    (4, "Weekend Canvas Sneakers", "Lightweight canvas sneakers with a cushioned footbed for weekend exploring.", "72.00", "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77"),
    (4, "Classic White Sneakers", "Versatile white sneakers for everyday casual outfits.", "69.99", "https://images.unsplash.com/photo-1542291026-7eec264c27ff"),
    (4, "Men's Running Shoes", "Lightweight running shoes with cushioned support.", "89.99", "https://images.unsplash.com/photo-1542291026-7eec264c27ff"),
    (4, "Women's Training Shoes", "Comfortable training shoes for gym workouts.", "84.99", "https://images.unsplash.com/photo-1539185441755-769473a23570"),
    (4, "Leather Casual Loafers", "Classic loafers suitable for smart casual outfits.", "94.99", "https://images.unsplash.com/photo-1531310197839-ccf54634509e"),
    (4, "Women's Flat Sandals", "Comfortable flat sandals for everyday use.", "39.99", "https://images.unsplash.com/photo-1562273138-f46be4ebdf33"),
    (4, "Men's Casual Slides", "Lightweight slides for relaxed everyday wear.", "24.99", "https://images.unsplash.com/photo-1603487742131-4160ec999306"),
    (4, "Ankle Boots", "Versatile ankle boots for casual outfits.", "99.99", "https://images.unsplash.com/photo-1543163521-1bf539c55dd2"),
    (4, "Women's White Running Shoes", "Breathable lightweight running shoes.", "79.99", "https://images.unsplash.com/photo-1460353581641-37baddab0fa2"),
    (4, "Men's Formal Leather Shoes", "Classic formal shoes for office and occasions.", "109.99", "https://images.unsplash.com/photo-1614252369475-531eba835eb1"),
]


def seed_products():
    db = LocalSession()

    try:
        categories = {
            category.id: category.name
            for category in db.query(Category).all()
        }

        existing_names = {
            name.lower()
            for (name,) in db.query(Product.name).all()
        }

        inserted = 0
        skipped = 0

        for category_id, name, description, price, image_url in PRODUCTS:
            if category_id not in categories:
                print(f"Skipping {name}: category ID {category_id} not found.")
                skipped += 1
                continue

            if name.lower() in existing_names:
                skipped += 1
                continue

            product = Product(
                category_id=category_id,
                name=name,
                description=description,
                price=Decimal(price),
                stock_quantity=25,
                image_url=f"{image_url}?auto=format&fit=crop&w=1200&q=85",
                is_active=True,
            )

            db.add(product)
            existing_names.add(name.lower())
            inserted += 1

        db.commit()

        print(f"Successfully inserted: {inserted}")
        print(f"Skipped: {skipped}")

        for category_id, category_name in categories.items():
            count = (
                db.query(Product)
                .filter(Product.category_id == category_id)
                .count()
            )
            print(f"{category_name}: {count} products")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()
