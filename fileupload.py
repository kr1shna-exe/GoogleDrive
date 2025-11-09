import argparse
import shutil
from pathlib import Path


# class Executor:
def fileUpload(file_path: str):
    path = Path(file_path)
    if not path.exists():
        print("Error: File Not Found")
        return
    else:
        print("File Already Exists")
    storage_dir = Path("storage")
    storage_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, storage_dir)
    file_size = path.stat().st_size
    print(f"File Of Size {file_size} Uploaded Successfully!")

fileUpload("/Users/jkchinnu/Downloads/Ticket.pdf")
