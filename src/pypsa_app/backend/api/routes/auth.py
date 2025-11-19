"""Authentication routes for GitHub OAuth"""

import logging
import secrets
from datetime import datetime

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from pypsa_app.backend.api.deps import get_current_user, get_db
from pypsa_app.backend.auth.session import get_session_store
from pypsa_app.backend.models import User
from pypsa_app.backend.schemas.auth import UserResponse
from pypsa_app.backend.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

oauth = OAuth()
oauth.register(
    name="github",
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


@router.get("/login")
async def login(request: Request):
    """Redirect to GitHub OAuth login"""
    if not settings.enable_auth:
        raise HTTPException(status_code=400, detail="Authentication is disabled")

    # Generate state and store it in session
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    callback_url = f"{settings.base_url}/api/v1/auth/callback"

    return await oauth.github.authorize_redirect(request, callback_url, state=state)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback"""
    if not settings.enable_auth:
        raise HTTPException(status_code=400, detail="Authentication is disabled")

    try:
        # Verify state for CSRF protection
        state = request.query_params.get("state")
        stored_state = request.session.get("oauth_state")

        if not state or state != stored_state:
            logger.warning("OAuth state mismatch - possible CSRF attack")
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Exchange code for token
        token = await oauth.github.authorize_access_token(request)

        # Get user info from GitHub
        resp = await oauth.github.get("user", token=token)
        github_user = resp.json()

        # Get user email (if available)
        email_resp = await oauth.github.get("user/emails", token=token)
        emails = email_resp.json()
        primary_email = next((e["email"] for e in emails if e["primary"]), None)

        # Update or create user
        user = db.query(User).filter(User.github_id == github_user["id"]).first()

        if user:
            user.username = github_user["login"]
            user.email = primary_email
            user.avatar_url = github_user.get("avatar_url")
            user.update_last_login()
            logger.info(f"User logged in: {user.username}")
        else:
            user = User(
                github_id=github_user["id"],
                username=github_user["login"],
                email=primary_email,
                avatar_url=github_user.get("avatar_url"),
                last_login=datetime.utcnow(),
            )
            db.add(user)
            logger.info(f"New user registered: {user.username}")

        db.commit()
        db.refresh(user)

        # Create session
        session_store = get_session_store()
        session_id = session_store.create_session(user.id)

        # Set session cookie
        response = RedirectResponse(url=settings.base_url)
        response.set_cookie(
            key=settings.session_cookie_name,
            value=session_id,
            httponly=True,
            secure=not settings.base_url.startswith(
                "http://localhost"
            ),  # Secure in production
            samesite="lax",
            max_age=settings.session_ttl,
        )

        # Clear oauth state
        request.session.pop("oauth_state", None)

        return response

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/logout")
async def logout(request: Request):
    """Logout and delete session"""
    if not settings.enable_auth:
        raise HTTPException(status_code=400, detail="Authentication is disabled")

    session_id = request.cookies.get(settings.session_cookie_name)

    if session_id:
        session_store = get_session_store()
        session_store.delete_session(session_id)

    # Clear session cookie
    response = RedirectResponse(url=f"{settings.base_url}/login", status_code=303)
    response.delete_cookie(key=settings.session_cookie_name)

    return response


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    if not settings.enable_auth:
        raise HTTPException(status_code=400, detail="Authentication is disabled")

    return user
