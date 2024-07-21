from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Table, MetaData, select, insert, delete, update, and_

app = FastAPI()

engine = create_engine('sqlite:///test.db')
metadata = MetaData()

users = Table('users', metadata, autoload_with=engine)
messages = Table('messages', metadata, autoload_with=engine)

class UserIn(BaseModel):
    id: int
    password: str

class MessageIn(BaseModel):
    sender_id: int
    recipient_id: int
    content: str

@app.post("/register")
async def register(user: UserIn):
    with engine.connect() as connection:
        result = connection.execute(select(users).where(users.c.id == user.id))
        if result.fetchone() is not None:
            raise HTTPException(status_code=400, detail="User with this ID already exists.")
        connection.execute(insert(users).values(id=user.id, password_hash=generate_password_hash(user.password)))
    return {"id": user.id}

@app.post("/send")
async def send(message: MessageIn, password: str):
    with engine.connect() as connection:
        result = connection.execute(select(users).where(users.c.id == message.sender_id))
        user = result.fetchone()
        if user is None or not check_password_hash(user.password_hash, password):
            raise HTTPException(status_code=400, detail="Invalid ID or password.")
        result = connection.execute(select(users).where(users.c.id == message.recipient_id))
        if result.fetchone() is None:
            raise HTTPException(status_code=400, detail="Recipient does not exist.")
        connection.execute(insert(messages).values(sender_id=message.sender_id, recipient_id=message.recipient_id, content=message.content))
    return {"sender_id": message.sender_id, "recipient_id": message.recipient_id}

@app.get("/inbox/{id}")
async def inbox(id: int, password: str):
    with engine.connect() as connection:
        result = connection.execute(select(users).where(users.c.id == id))
        user = result.fetchone()
        if user is None or not check_password_hash(user.password_hash, password):
            raise HTTPException(status_code=400, detail="Invalid ID or password.")
        result = connection.execute(select(messages).where(messages.c.recipient_id == id).order_by(messages.c.id.desc()))
        return [{"sender_id": row.sender_id, "content": row.content} for row in result]
