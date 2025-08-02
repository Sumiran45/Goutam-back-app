import uuid
from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas.product import Product, ProductCreate, ProductUpdate
from database import db

product_collection = db["products"]

async def get_all_products() -> List[dict]:
    """Get all products from database"""
    try:
        products = []
        async for product in product_collection.find():
            product["_id"] = str(product["_id"])
            products.append(product)
        return products
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

async def get_product_by_id(product_id: str) -> Optional[dict]:
    """Get product by ID"""
    try:
        product = await product_collection.find_one({"id": product_id})
        if product:
            product["_id"] = str(product["_id"])
        return product
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None

async def add_product(product_data: ProductCreate) -> dict:
    """Add new product to database"""
    try:
        product_dict = product_data.dict()
        product_dict["id"] = str(uuid.uuid4())
        product_dict["created_at"] = datetime.utcnow()
        product_dict["updated_at"] = datetime.utcnow()
        
        product_dict["image"] = str(product_dict["image"])
        for vendor in product_dict["vendors"]:
            vendor["link"] = str(vendor["link"])
        
        result = await product_collection.insert_one(product_dict)
        product_dict["_id"] = str(result.inserted_id)
        return product_dict
    except Exception as e:
        print(f"Error adding product: {e}")
        raise

async def update_product(product_id: str, product_data: ProductUpdate) -> Optional[dict]:
    """Update existing product"""
    try:
        existing_product = await get_product_by_id(product_id)
        if not existing_product:
            return None
        
        update_dict = {}
        for field, value in product_data.dict(exclude_unset=True).items():
            if value is not None:
                if field == "image" and value:
                    update_dict[field] = str(value)
                elif field == "vendors" and value:
                    vendors_list = []
                    for vendor in value:
                        vendor_dict = vendor.dict() if hasattr(vendor, 'dict') else vendor
                        vendor_dict["link"] = str(vendor_dict["link"])
                        vendors_list.append(vendor_dict)
                    update_dict[field] = vendors_list
                else:
                    update_dict[field] = value
        
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await product_collection.update_one(
            {"id": product_id},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return await get_product_by_id(product_id)
        return None
    except Exception as e:
        print(f"Error updating product: {e}")
        return None

async def delete_product(product_id: str) -> bool:
    """Delete product from database"""
    try:
        result = await product_collection.delete_one({"id": product_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting product: {e}")
        return False