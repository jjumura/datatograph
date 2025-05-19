from fastapi import APIRouter

router = APIRouter(tags=["api"])

@router.get("/items")
async def get_items():
    """샘플 아이템 목록을 반환합니다"""
    return [
        {"id": 1, "name": "Item 1", "description": "First item"},
        {"id": 2, "name": "Item 2", "description": "Second item"}
    ]

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    """특정 아이템을 ID로 조회합니다"""
    return {"id": item_id, "name": f"Item {item_id}", "description": f"Description for item {item_id}"} 