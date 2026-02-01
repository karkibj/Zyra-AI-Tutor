"""
Authentication Routes
Login, Signup, Google OAuth (with state validation disabled for development)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from authlib.integrations.starlette_client import OAuth
from authlib.common.security import generate_token

from app.core.config import settings
from app.db import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Setup OAuth (Google) - Disable state validation for development
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
    },
    authorize_state=None,  # Disable state validation
)


# ============================================================================
# LOCAL AUTHENTICATION (Email/Password)
# ============================================================================

@router.post("/signup", response_model=Token)
async def signup(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with email and password"""
    result = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_in.password)
    
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role,
        provider="local"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(
        subject=new_user.id,
        role=new_user.role
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(new_user)
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalars().first()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token = create_access_token(
        subject=user.id,
        role=user.role
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.post("/token")
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """OAuth2 compatible token login for Swagger UI"""
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalars().first()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token = create_access_token(
        subject=user.id,
        role=user.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================================
# GOOGLE OAUTH (State validation disabled for development)
# ============================================================================

@router.get("/google/login")
async def login_google(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    print(f"🔐 Initiating Google OAuth (no state validation)...")
    print(f"   Redirect URI: {redirect_uri}")
    
    # Manually build authorization URL without state
    authorization_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid email profile"
    )
    
    return RedirectResponse(url=authorization_url, status_code=302)


@router.get("/google/callback")
async def auth_google_callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google OAuth callback"""
    print(f"📥 Google callback received with code")
    
    try:
        # Exchange code for token manually
        import httpx
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                }
            )
            
            if token_response.status_code != 200:
                print(f"❌ Token exchange failed: {token_response.text}")
                return RedirectResponse(
                    url="http://localhost:3000/login?error=token_exchange_failed",
                    status_code=302
                )
            
            token_data = token_response.json()
            access_token_google = token_data.get("access_token")
            
            # Get user info
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token_google}"}
            )
            
            if userinfo_response.status_code != 200:
                print(f"❌ User info fetch failed: {userinfo_response.text}")
                return RedirectResponse(
                    url="http://localhost:3000/login?error=userinfo_failed",
                    status_code=302
                )
            
            user_info = userinfo_response.json()
            
    except Exception as e:
        print(f"❌ Google OAuth error: {str(e)}")
        return RedirectResponse(
            url="http://localhost:3000/login?error=google_auth_failed",
            status_code=302
        )
    
    print(f"✅ Google user info: {user_info.get('email')}")
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == user_info['email'])
    )
    user = result.scalars().first()
    
    if not user:
        # Auto-signup with Google
        print(f"📝 Creating new user: {user_info.get('email')}")
        user = User(
            email=user_info['email'],
            full_name=user_info.get('name'),
            picture=user_info.get('picture'),
            provider="google",
            role="student",
            hashed_password=None
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ User created: {user.id}")
    else:
        print(f"✅ Existing user found: {user.id}")
    
    # Generate our JWT access token
    access_token = create_access_token(
        subject=user.id,
        role=user.role
    )
    
    print(f"✅ JWT token generated, redirecting to frontend...")
    
    # Redirect to frontend with token
    return RedirectResponse(
        url=f"http://localhost:5173/auth/google/callback?access_token={access_token}",
        status_code=302
    )


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current logged-in user information"""
    return UserOut.model_validate(current_user)