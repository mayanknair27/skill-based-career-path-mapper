"""
FastAPI backend for the Skill-Based Career Path Mapper.
Wraps existing Python logic modules and serves them as REST endpoints.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from logic.db import (
    create_user, authenticate_user, reset_password,
    get_user_profile, save_user_profile,
    get_summary_stats, get_recent_activity,
    db_complete_milestone
)
from logic.engine import (
    process_career_data, get_network_data,
    get_all_careers, get_career_by_title, compare_careers
)

app = FastAPI(title="Career Mapper API", version="1.0.0")

# Allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class ResetPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str

class CareerProcessRequest(BaseModel):
    goal: str
    skills: str
    experience_level: str
    username: str = "anon"
    agent_state: Optional[Dict[str, Any]] = None

class SaveProfileRequest(BaseModel):
    username: str
    profile_data: Dict[str, Any]

class MilestoneCompleteRequest(BaseModel):
    username: str
    career_key: str
    milestone_id: str

class CompareRequest(BaseModel):
    title_a: str
    title_b: str
    skills: str


# --- Auth Endpoints ---

@app.post("/api/auth/login")
def login(req: LoginRequest):
    success, message = authenticate_user(req.username, req.password)
    if not success:
        raise HTTPException(status_code=401, detail=message)
    profile = get_user_profile(req.username)
    return {"status": "success", "message": message, "username": req.username, "profile": profile}

@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    success, message = create_user(req.username, req.email, req.password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message}

@app.post("/api/auth/reset-password")
def reset_pwd(req: ResetPasswordRequest):
    success, message = reset_password(req.username, req.email, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message}


# --- Career Endpoints ---

@app.post("/api/career/process")
def process_career(req: CareerProcessRequest):
    return process_career_data(
        req.goal, req.skills, req.experience_level,
        req.username, req.agent_state
    )

@app.get("/api/career/network")
def network_endpoint(skills: str = "", exp: str = "Beginner"):
    return {"careers": get_network_data(skills, exp)}

@app.get("/api/career/all")
def all_careers():
    return {"careers": get_all_careers()}

@app.get("/api/career/{title}")
def career_detail(title: str):
    data = get_career_by_title(title)
    if not data:
        raise HTTPException(status_code=404, detail="Career not found")
    return data

@app.post("/api/career/compare")
def compare(req: CompareRequest):
    result = compare_careers(req.title_a, req.title_b, req.skills)
    if not result:
        raise HTTPException(status_code=404, detail="One or both careers not found")
    return result


# --- User Profile Endpoints ---

@app.get("/api/user/profile")
def get_profile(username: str):
    return get_user_profile(username)

@app.post("/api/user/profile")
def save_profile(req: SaveProfileRequest):
    save_user_profile(req.username, req.profile_data)
    return {"status": "success"}

@app.post("/api/user/milestone/complete")
def complete_milestone(req: MilestoneCompleteRequest):
    success = db_complete_milestone(req.username, req.career_key, req.milestone_id)
    if not success:
        raise HTTPException(status_code=400, detail="User not found or database error.")
    return {"status": "success"}


# --- Admin Endpoints ---

@app.get("/api/admin/stats")
def admin_stats():
    return get_summary_stats()

@app.get("/api/admin/activity")
def admin_activity(limit: int = 20):
    return get_recent_activity(limit)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
