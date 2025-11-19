import shutil
import zipfile
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

async def download_file(item_id: int, destination_path: str):
    item = await db.item.find_unique(
        where={"id": item_id}
    )
    if not item:
        print("File/Folder not found")
        return
    source = Path(item.path)
    destination = Path(destination_path)
    if not item.isFolder:
        if not source.exists():
            print("Source file not found in storage")
            return
        shutil.copy2(source, destination)
        print(f"Succesfully Downloaded File: {item.name}")
    else:
        zip_file = destination / f"{item.name}.zip"
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            _add_folder_to_zip(source, zipf, base_path=source)
        print(f"Succesfully Donwloaded the folder: {item.name}")

def _add_folder_to_zip(folder_path: Path, zipf: zipfile.ZipFile, base_path: Path):
    for item in folder_path.iterdir():
        if item.is_file():
            rel_path = item.relative_to(base_path)
            zipf.write(item, arcname=rel_path)
        elif item.is_dir():
            _add_folder_to_zip(item, zipf, base_path)

async def rename_item(item_id: int, new_name: str):
    item = await db.item.find_unique(
        where={"id": item_id}
    )
    if not item:
        print("No file/folder found by that name")
        return
    old_path = Path(item.path)
    new_path = old_path.parent / new_name
    old_path.rename(new_path)
    await db.item.update(
        where={"id": item_id},
        data={"name": new_name, "path": str(new_path)}
    )
    if item.isFolder:
        await _update_children_paths(item.id, new_path)
    print(f"Successfully renamed to: {new_name}")

async def copy_item(item_id: int, new_parent_id: int):
    item = await db.item.find_unique(
        where={"id": item_id}
    )
    if not item:
        print("No item found..")
        return
    source = Path(item.path)
    parent = await db.item.find_unique(
        where={"id": new_parent_id}
    )
    if not parent or not parent.isFolder:
        print("Invalid destination folder")
        return
    destination = Path(parent.path)
    new_path = destination / item.name
    if not item.isFolder:
        shutil.copy2(source, new_path)
        await db.item.create(
            data={
                "name": item.name,
                "path": str(new_path),
                "isFolder": False,
                "parentId": new_parent_id,
                "userId": item.userId
            }
        )
        print(f"Sucessfully copied file: {item.name}")
    else:
        shutil.copytree(source, new_path)
        new_folder = await db.item.create(
            data={
                "name": item.name,
                "path": str(new_path),
                "isFolder": True,
                "parentId": new_parent_id,
                "userId": item.userId
            }
        )
        await _copy_folder_children(item.id, new_folder.id, new_path)
        print(f"Successfully copied: {item.name}")

async def _copy_folder_children(old_folder_id: int, new_folder_id: int, new_folder_path: Path):
    children = await db.item.find_many(
        where={"parentId": old_folder_id}
    )
    for child in children:
        child_path = new_folder_path / child.name
        if child.isFolder:
            new_child = await db.item.create(
                data={
                    "name": child.name,
                    "path": str(child_path),
                    "isFolder": True,
                    "parentId": new_folder_id,
                    "userId": child.userId
                }
            )
            await _copy_folder_children(child.id, new_child.id, child_path)
        else:
            await db.item.create(
                data={
                    "name": child.name,
                    "path": str(child_path),
                    "isFolder": False,
                    "size": child.size,
                    "parentId": new_folder_id,
                    "userId": child.userId

                }
            )

async def search_item(query: str, user_id: int):
    items = await db.item.find_many(
        where={"userId": user_id, "name": {"contains": query, "mode": "insensitive"}}
    )
    print("Search Result Successfull")
    return items
