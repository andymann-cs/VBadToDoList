import os
from uuid import UUID, uuid4 

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field


MONDODB_CONNECTION_STRING = os.environ["MONGODB_CONNECTION_STRING"]

client = AsyncIOMotorClient(MONDODB_CONNECTION_STRING, 
                            uuidRepresentation="standard")
db = client.todolist
todos = db.todos


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TodoItem(BaseModel):
    id : UUID = Field(default_factory =uuid4, alias="_id")
    content : str
    finished : bool = False

class TodoItemCreate(BaseModel):
    content: str
    finished : bool = True

@app.post("/todos", response_model = TodoItem)
async def create_todo(item: TodoItemCreate):
    new_todo = TodoItem(content = item.content, finished=False)
    await todos.insert_one(new_todo.model_dump(by_alias=True))
    return new_todo


@app.get("/todos", response_model = list[TodoItem])
async def read_todos():
    return await todos.find().to_list(length=None)


@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: UUID):
    delete_result = await todos.delete_one({"_id": todo_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code = 404, detail = "Todo not found")
    return {"message" : "Todo deleted successfully"}

@app.patch("/todos/{todo_id}")
async def toggle_finished(todo_id: UUID):
    todo = await todos.find_one({"_id": todo_id})
    if not todo:
        raise HTTPException(status_code=404, detail="couldnt strikethrough an item because item cant be found")
    new_status = not todo.get("finished", False)
    await todos.update_one({"_id": todo_id},{"$set": {"finished": new_status}})
    return {"_id": todo_id, "finished": new_status}