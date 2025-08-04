from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List
from uuid import uuid4
import uvicorn

app = FastAPI()

# In-memory "database"
db = {}

# --- Models ---
class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    password: str  # In production, use hashed passwords

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    name: str = None
    email: EmailStr = None
    password: str = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.get("/")
def health_check():
    return {"status": "OK"}

@app.get("/users", response_model=List[User])
def get_users():
    return list(db.values())

@app.get("/user/{user_id}", response_model=User)
def get_user(user_id: str):
    user = db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=User, status_code=201)
def create_user(req: CreateUserRequest):
    user_id = str(uuid4())
    user = User(id=user_id, **req.dict())
    db[user_id] = user
    return user

@app.put("/user/{user_id}", response_model=User)
def update_user(user_id: str, req: UpdateUserRequest):
    user = db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_data = req.dict(exclude_unset=True)
    updated_user = user.copy(update=updated_data)
    db[user_id] = updated_user
    return updated_user

@app.delete("/user/{user_id}", status_code=204)
def delete_user(user_id: str):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")
    del db[user_id]
    return JSONResponse(status_code=204, content={})

@app.get("/search")
def search_users(name: str = Query(...)):
    results = [user for user in db.values() if name.lower() in user.name.lower()]
    return results

@app.post("/login")
def login(req: LoginRequest):
    for user in db.values():
        if user.email == req.email and user.password == req.password:
            return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- Run App ---
# uvicorn main:app --reload


# --- Task 2: URL Shortener ---

# File: app/main.py
from flask import Flask, request, jsonify, redirect
from datetime import datetime
import string, random

app = Flask(__name__)

url_store = {}

# Helpers
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route("/")
def health():
    return {"status": "OK"}

@app.route("/api/shorten", methods=["POST"])
def shorten():
    data = request.get_json()
    url = data.get("url")
    if not url or not url.startswith("http"):
        return jsonify({"error": "Invalid URL"}), 400
    code = generate_code()
    while code in url_store:
        code = generate_code()
    url_store[code] = {"url": url, "clicks": 0, "created_at": datetime.utcnow()}
    return jsonify({"short_code": code, "short_url": f"http://localhost:5000/{code}"})

@app.route("/<code>")
def redirect_url(code):
    if code not in url_store:
        return jsonify({"error": "URL not found"}), 404
    url_store[code]["clicks"] += 1
    return redirect(url_store[code]["url"])

@app.route("/api/stats/<code>")
def stats(code):
    if code not in url_store:
        return jsonify({"error": "Short code not found"}), 404
    entry = url_store[code]
    return jsonify({
        "url": entry["url"],
        "clicks": entry["clicks"],
        "created_at": entry["created_at"].isoformat()
    })
