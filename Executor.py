import shutil
from pathlib import Path
from typing import Optional

from exports.prisma import db


# class Executor:
async def create_folder(user_id: int, folder_name: str, parent_id: Optional[int] = None):
    if parent_id:
        parent = await db.item.find_unique(where={"id": parent_id})
        if not parent or not parent.isFolder:
            print("Parent not found...")
            return
        folder_path = Path(parent.path) / folder_name
    else:
        folder_path = Path("My Drive")/ f"user_{user_id}" / folder_name
    folder_path.mkdir(parents=True,exist_ok=True)
    folder = await db.item.create(
        data={
            "name": folder_name,
            "path": str(folder_path),
            "isFolder": True,
            "parentId": parent_id,
            "userId": user_id
        }
    )
    print(f"Folder {folder_name} created at: {folder_path}")
    return folder

async def get_contents(user_id: int, folder_id: Optional[int] = None):
    items = await db.item.find_many(
        where={
            "userId": user_id,
            "parentId": folder_id
        },
        order={"isFolder": "desc"}
    )
    if not items:
        print("Empty Folder")
        return
    for item in items:
        if item.isFolder:
            print(f"Folder: {item.name}")
        else:
            print(f"File: {item.name}, size: {item.size}")


async def upload_file(user_id: int, file_path: str, folder_id: Optional[int] = None):
    source = Path(file_path)
    if not source.exists():
        print("No such file present..")
        return
    if folder_id:
        folder = await db.item.find_unique(
            where={"id": folder_id}
        )
        if not folder or not folder.isFolder:
            print("Folder not found")
            return
        destination = Path(folder.path) / source.name
    else:
        destination = Path("My Drive")/ f"user_{user_id}" 
        destination.mkdir(parents=True, exist_ok=True)
        destination = destination / source.name
    shutil.copy2(source, destination)
    file_size = source.stat().st_size
    await db.item.create(
        data={
            "name": source.name,
            "path": str(destination),
            "isFolder": False,
            "size": file_size,
            "parentId": folder_id,
            "userId": user_id
        }
    )
    print(f"Successfully uploaded file: {source.name}")


async def move_file(item_id: int, new_folder_id: Optional[int] = None):
    item = await db.item.find_unique(
        where={"id": item_id}
    )
    if not item:
        print("No item found..")
        return
    if new_folder_id:
        folder = await db.item.find_unique(
            where={"id": new_folder_id}
        )
        if not folder or not folder.isFolder:
            print("It is not a folder..")
            return
        new_path = Path(folder.path) / item.name
    else:
        new_path = Path("My Drive") / f"user_{item.user_id}"
        new_path.mkdir(parents=True,exist_ok=True)
        new_path = new_path / item.name
    old_path = Path(item.path)
    shutil.move(str(old_path), str(new_path))
    await db.item.update(
        where={"id": item_id},
        data={
            "path": str(new_path),
            "parentId": new_folder_id
        }
    )
    if item.isFolder:
        await _update_children_paths(item_id, new_path)

async def _update_children_paths(folder_id: int, new_folder_path: Path):
    children = await db.item.find_many(
        where={"parentId": folder_id}
    )
    for child in children:
        old_child_path = Path(child.path)
        new_child_path = new_folder_path / old_child_path.name
        await db.item.update(
            where={"id": child.id},
            data={"path": str(new_child_path)}
        )
        if child.isFolder:
            await _update_children_paths(child.id, new_child_path)

async def delete_item(item_id: int):
    item = await db.item.find_unique(
        where={"id": item_id}
    )
    if not item:
        print("No folder or file found..")
        return
    if item.isFolder:
        children = await db.item.find_many(
            where={"parentId": item_id}
        )
        for child in children:
            await delete_item(child.id)
        path = Path(item.path)
        if path.exists():
            shutil.rmtree(path)
    else:
        path = Path(item.path)
        if path.exists():
            path.unlink()
    await db.item.delete(
        where={"id": item_id}
    )
    print(f"Deleted {item.name} Successfully!")
