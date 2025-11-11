import shutil
from pathlib import Path

from exports.prisma import db


# class Executor:
async def fileUpload(file_path: str, user_id: int):
    path = Path(file_path)
    if not path.exists():
        print("Error: File Not Found")
        return
    storage_dir = Path("storage")
    storage_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, storage_dir)
    file_size = path.stat().st_size
    await db.file.create(
        data={
            "file_name": path.name,
            "file_size": file_size,
            "userId": user_id
        }
    )
    print(f"File Of Size {file_size} Uploaded Successfully!")

async def list_files():
    files = await db.file.find_many(
        include={"user": True}
    )
    for file in files:
        print(f"Filename: {file.filename}, Size: {file.size}")


async def download_file(file_name: str):
    source_path = Path("storage") / file_name
    if not source_path.exists():
        print("File not found")
        return
    destination = Path(file_name)
    shutil.copy2(source_path, destination)
    print(f"Downloaded {file_name} Successfully! ")

async def move_file(file_name: str, destination_path: str):
    source_path = Path("storage") / file_name
    if not source_path.exists():
        print("File does not exist..")
        return
    shutil.move(source_path, destination_path)
    print(f"{file_name} has been moved to {destination_path}")

async def delete_file(file_name: str):
    source_path = Path("storage") / file_name
    if not source_path.exists():
        print("File not found")
        return
    source_path.unlink()
    print(f"{file_name} has been deleted")
