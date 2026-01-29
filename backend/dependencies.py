from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
import os
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# We need these to verify against Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") # Anon key is fine for getUser

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not SUPABASE_URL or not SUPABASE_KEY:
        # Fallback for local testing if env vars missing, or error out
        # For now, let's error to prompt configuration
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Authorization configuration missing (SUPABASE_URL/KEY)"
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_KEY
            }
        )
        
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_data = response.json()
    return user_data # Contains 'id', 'email', etc.
