from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from exports.prisma import connect_db, disconnect_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_headers=['*'],
    allow_credentials=True,
    allow_methods=['*']
)

@asynccontextmanager
async def on_startup():
    await connect_db() 
    yield
    await disconnect_db()

if __name__ == "__main__":
    main()
