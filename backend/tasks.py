from .celery_app import celery_app
from .database import supabase
import json
import subprocess
import os
import shutil
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- AI and Dagger Integration ---

def get_project_language(repo_path: str) -> str:
    """Analyzes the repository to determine the primary programming language."""
    # This is a simplified analysis. A real implementation would be more robust.
    # For now, we'll check for common dependency files.
    if os.path.exists(os.path.join(repo_path, 'package.json')):
        return "JavaScript"
    if os.path.exists(os.path.join(repo_path, 'requirements.txt')):
        return "Python"
    if os.path.exists(os.path.join(repo_path, 'pom.xml')):
        return "Java"
    if os.path.exists(os.path.join(repo_path, 'go.mod')):
        return "Go"
    return "Unknown"

def generate_dockerfile_with_ai(language: str) -> str:
    """Generates a Dockerfile using the Gemini AI based on the detected language."""
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ.get("GEMINI_API_KEY"))

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a world-class DevOps engineer specializing in containerization. Your task is to generate a production-ready, multi-stage Dockerfile for the given programming language. The Dockerfile should be optimized for security, small image size, and performance. Do not include any explanations, just the raw Dockerfile content."),
        ("user", "Generate a Dockerfile for a {language} application.")
    ])

    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser

    dockerfile_content = chain.invoke({"language": language})
    return dockerfile_content

# --- Celery Task Definition ---

@celery_app.task(name='tasks.analyze_repository')
def analyze_repository(job_data_str: str):
    """
    Celery task to clone a repository, analyze it, generate a Dockerfile,
    and update the database.
    """
    try:
        job_data = json.loads(job_data_str)
        project_id = job_data['project_id']
        repo_url = job_data['repo_url']

        # 1. Clone the repository to a temporary directory
        temp_dir = f"/tmp/devyntra_project_{project_id}"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)

        # 2. Analyze the project to detect the language
        language = get_project_language(temp_dir)
        supabase.table('projects').update({'language': language}).eq('id', project_id).execute()

        # 3. Generate a Dockerfile using AI
        if language != "Unknown":
            dockerfile_content = generate_dockerfile_with_ai(language)
            dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)

            # For now, we'll just store a reference to the path.
            # In a real system, we'd commit this back to the repo or a storage bucket.
            supabase.table('projects').update({'dockerfile_path': 'Dockerfile'}).eq('id', project_id).execute()

        # 4. Clean up the temporary directory
        shutil.rmtree(temp_dir)

        # 5. Update the project status to 'analysis_complete' or similar
        supabase.table('projects').update({'status': 'ready_to_deploy'}).eq('id', project_id).execute()

        return f"Successfully analyzed project {project_id}."

    except Exception as e:
        # Log the error and update project status to 'failed'
        project_id = job_data.get('project_id')
        if project_id:
            supabase.table('projects').update({'status': 'analysis_failed', 'status_message': str(e)}).eq('id', project_id).execute()

        # Re-raise the exception so Celery knows the task failed
        raise e