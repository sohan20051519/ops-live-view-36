from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import supabase, redis_client
from .models import UserCreate, UserLogin, Workspace, UserProfile, Project
import uuid
import json

app = FastAPI()

# --- Middleware ---

origins = [
    "http://localhost:3000",  # Next.js frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_scheme = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        user_response = supabase.auth.get_user(token.credentials)
        user = user_response.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


@app.post("/signup")
async def signup(user_data: UserCreate):
    try:
        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                }
            }
        })

        if auth_response.user is None:
             # This can happen if email confirmation is required
            if "confirmation_sent_at" in str(auth_response):
                return {"message": "Confirmation email sent. Please verify your email address."}
            raise HTTPException(status_code=400, detail="User creation failed.")

        new_user = auth_response.user

        # TODO: Implement this as a transactional operation.
        # If any step after user creation fails, the user should be rolled back.

        # Create a workspace for the new user
        workspace_name = f"{user_data.full_name}'s Workspace"
        workspace_data = {"name": workspace_name, "owner_id": str(new_user.id)}

        workspace_response = supabase.table('workspaces').insert(workspace_data).execute()
        if workspace_response.data is None or not workspace_response.data:
            raise HTTPException(status_code=500, detail="Failed to create workspace.")

        new_workspace = workspace_response.data[0]

        # Create a user profile to link user to workspace
        profile_data = {"id": str(new_user.id), "workspace_id": str(new_workspace['id'])}
        profile_response = supabase.table('user_profiles').insert(profile_data).execute()

        if profile_response.data is None or not profile_response.data:
            raise HTTPException(status_code=500, detail="Failed to create user profile.")

        return {"user": new_user, "session": auth_response.session, "workspace": new_workspace}

    except Exception as e:
        # Check for specific Supabase errors, e.g., user already exists
        if "User already registered" in str(e):
            raise HTTPException(status_code=400, detail="User with this email already exists.")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(user_data: UserLogin):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        return auth_response
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid login credentials: {e}")

from typing import List

@app.post("/projects", response_model=Project)
async def create_project(project_data: Project, current_user: dict = Depends(get_current_user)):
    try:
        # Get user's workspace
        profile_response = supabase.table('user_profiles').select('workspace_id').eq('id', str(current_user.id)).single().execute()
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="User profile not found.")

        workspace_id = profile_response.data['workspace_id']

        # Create project in the database
        new_project = {
            "name": project_data.name,
            "repo_url": project_data.repo_url,
            "workspace_id": str(workspace_id),
            "status": "analysis_pending" # Initial status
        }

        project_response = supabase.table('projects').insert(new_project).execute()
        if not project_response.data:
            raise HTTPException(status_code=500, detail="Failed to create project.")

        created_project = project_response.data[0]

        # Push job to Redis queue for background analysis
        job_data = {
            "project_id": created_project['id'],
            "repo_url": created_project['repo_url']
        }
        redis_client.lpush("analysis_queue", json.dumps(job_data))

        return created_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects", response_model=List[Project])
async def get_projects(current_user: dict = Depends(get_current_user)):
    try:
        # Get user's workspace
        profile_response = supabase.table('user_profiles').select('workspace_id').eq('id', str(current_user.id)).single().execute()
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="User profile not found.")

        workspace_id = profile_response.data['workspace_id']

        # Fetch projects for that workspace
        projects_response = supabase.table('projects').select('*').eq('workspace_id', workspace_id).execute()

        if projects_response.data is None:
            return []

        return projects_response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the Devyntra API"}