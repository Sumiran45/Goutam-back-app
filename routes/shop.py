from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from schemas.product import Product, ProductCreate, ProductUpdate
from models.product import (
    get_all_products,
    get_product_by_id,
    add_product,
    update_product,
    delete_product,
)
from utils.auth import get_current_user
from utils.activity_logger import ActivityLogger, safe_log_activity

product_router = APIRouter(prefix="/products", tags=["Products"])

@product_router.post("/createProduct", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, user=Depends(get_current_user)):
    """Create new product"""
    try:
        new_product = await add_product(product)
        
        # Log product creation activity
        await safe_log_activity(
            ActivityLogger.log_product_creation,
            user_id=str(user["_id"]),
            user_name=user.get("name", user.get("username", "Unknown")),
            product_id=str(new_product.get("_id", new_product.get("id", "Unknown"))),
            product_name=product.name
        )
        
        return new_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@product_router.get("/getProducts", response_model=List[Product])
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock status")
):
    """Get all products with optional filters"""
    try:
        products = await get_all_products()
                
        if category:
            products = [p for p in products if p.get("category", "").lower() == category.lower()]
        if brand:
            products = [p for p in products if p.get("brand", "").lower() == brand.lower()]
        if in_stock is not None:
            products = [p for p in products if p.get("inStock") == in_stock]
                    
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@product_router.get("/getProduct/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get single product by ID"""
    try:
        product = await get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@product_router.put("/updateProduct/{product_id}", response_model=Product)
async def edit_product(product_id: str, product: ProductUpdate, user=Depends(get_current_user)):
    """Update existing product"""
    try:
        # Get existing product for logging
        existing_product = await get_product_by_id(product_id)
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        updated = await update_product(product_id, product)
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Log product update activity
        await safe_log_activity(
            ActivityLogger.log_product_update,
            user_id=str(user["_id"]),
            user_name=user.get("name", user.get("username", "Unknown")),
            product_id=str(product_id),
            product_name=product.name if product.name else existing_product.get("name", "Unknown Product")
        )
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@product_router.delete("/deleteProduct/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product(product_id: str, user=Depends(get_current_user)):
    """Delete product"""
    try:
        # Get existing product for logging before deletion
        existing_product = await get_product_by_id(product_id)
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Store product name for logging
        product_name = existing_product.get("name", "Unknown Product")
        
        if not await delete_product(product_id):
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Log product deletion activity
        await safe_log_activity(
            ActivityLogger.log_product_deletion,
            user_id=str(user["_id"]),
            user_name=user.get("name", user.get("username", "Unknown")),
            product_id=str(product_id),
            product_name=product_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")