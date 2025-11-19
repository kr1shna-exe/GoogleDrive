from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from Executor import (copy_item, create_folder, delete_item, download_file,
                      get_contents, move_file, rename_item, search_item,
                      upload_file)
from lib.middleware import authenticateUser

router = APIRouter()

@router.post("/files/upload")
async def fileUpload(file: UploadFile = File(...), folder_id: Optional[int] = None, user = Depends(authenticateUser)):
    try:
        temp_path = Path(f"/storage/{file.filename}")
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        await upload_file(user.id, str(temp_path), folder_id)
        temp_path.unlink()
        return {
            "message": "File Uploaded Successfully",
            "filename": file.filename
        }
    except Exception as e:
        print(f"Error while uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/folders")
async def new_folder(folder_name: str, parent_id: Optional[int] = None, user = Depends(authenticateUser)):
    try:
        folder = await create_folder(user.id, folder_name, parent_id)
        return {
            "message": "New Folder Created",
            "folder": folder
        }
    except Exception as e:
        print(f"Error while creating folder: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/items")
async def get_items(folder_id: Optional[int] = None, user = Depends(authenticateUser)):
    try:
        items = await get_contents(user.id, folder_id)
        return {
            "message": "Fetched All Items",
            "items": items
        }
    except Exception as e:
        print(f"Error while fetching all the items: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/item/search")
async def find_item(query: str, user = Depends(authenticateUser)):
    try:
        item = await search_item(query, user.id)
        return {
            "message": "Search Results",
            "item": item
        }
    except Exception as e:
        print(f"Error while searching for item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/items/{item_id}/move")
async def move_item(item_id: int, user = Depends(authenticateUser) , new_folder_id: Optional[int] = None):
    try:
        await move_file(item_id, new_folder_id)
        return {
            "message": "Item Successfully Moved",
        }
    except Exception as e:
        print(f"Error while moving the item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/items/{item_id}")
async def del_item(item_id: int, user = Depends(authenticateUser)):
    try:
        await delete_item(item_id)
        return {
            "message": "Deleted Item Successfully"
        }
    except Exception as e:
        print(f"Error while deleting the item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/items/{item_id}/download")
async def download_item(item_id: int, user = Depends(authenticateUser)):
    try:
        destination_path = Path("/storage")
        await download_file(item_id, str(destination_path))
        return {
            "message": "Downloaded Item Successfully"
        }
    except Exception as e:
        print(f"Error while downloading the item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/items/{item_id}/rename")
async def rename_items(item_id: int, new_name: str, user = Depends(authenticateUser)):
    try:
        await rename_item(item_id, new_name)
        return {
            "message": "Item Renamed Successfully"
        }
    except Exception as e:
        print(f"Error while renaming the item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/items/{item_id}/copy")
async def copy_items(item_id: int, new_parent_id: int, user = Depends(authenticateUser)):
    try:
        await copy_item(item_id, new_parent_id)
        return {
            "message": "Item Copy Successfull"
        }
    except Exception as e:
        print(f"Error while copying the item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
