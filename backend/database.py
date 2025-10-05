import os
from supabase import create_client, Client
from dotenv import load_dotenv
import redis

load_dotenv()

# Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    raise ValueError("Supabase URL and Key must be set in the environment variables.")

supabase: Client = create_client(url, key)

# Redis
redis_url: str = os.environ.get("REDIS_URL")
if not redis_url:
    raise ValueError("Redis URL must be set in the environment variables.")

redis_client = redis.from_url(redis_url)