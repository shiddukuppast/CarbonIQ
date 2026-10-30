from typing import Any, Dict
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import TokenResponse, UserLoginRequest, UserProfileResponse, UserRegisterRequest
from app.utils.dates import utc_iso
from app.utils.ids import generate_id


def build_initials(name: str) -> str:
    parts = name.strip().split()
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


async def register_user(req: UserRegisterRequest, db: Any) -> TokenResponse:
    """
    Registers a new user, provisions a private workspace, and generates an access token.
    Enforces normalized email uniqueness.
    """
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise ConflictException(f"An account with email {req.email} already exists.")

    user_id = generate_id("usr")
    workspace_id = generate_id("ws")
    now = utc_iso()

    account_type = req.account_type.lower().strip() if req.account_type else "college"
    if account_type not in ("individual", "college", "organization"):
        account_type = "individual"

    workspace_name = req.workspace_name.strip() if req.workspace_name else f"{req.full_name}'s Workspace"
    workspace_doc = {
        "id": workspace_id,
        "name": workspace_name,
        "owner_id": user_id,
        "created_at": now,
        "updated_at": now,
    }
    await db.workspaces.insert_one(workspace_doc)

    user_doc = {
        "id": user_id,
        "full_name": req.full_name.strip(),
        "email": req.email,
        "hashed_password": hash_password(req.password),
        "workspace_id": workspace_id,
        "account_type": account_type,
        "created_at": now,
        "updated_at": now,
    }
    await db.users.insert_one(user_doc)

    token = create_access_token({
        "sub": user_id,
        "workspace_id": workspace_id,
        "email": req.email,
        "account_type": account_type,
    })
    profile = UserProfileResponse(
        id=user_id,
        full_name=user_doc["full_name"],
        email=user_doc["email"],
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        account_type=account_type,
        created_at=now,
        initials=build_initials(user_doc["full_name"]),
    )
    return TokenResponse(access_token=token, token_type="bearer", user=profile)


async def login_user(req: UserLoginRequest, db: Any) -> TokenResponse:
    """
    Authenticates user credentials and returns a JWT access token.
    """
    user = await db.users.find_one({"email": req.email})
    if not user:
        raise UnauthorizedException("Invalid email address or password.")

    if not verify_password(req.password, user.get("hashed_password", "")):
        raise UnauthorizedException("Invalid email address or password.")

    workspace = await db.workspaces.find_one({"id": user.get("workspace_id")})
    workspace_name = workspace.get("name", "Workspace") if workspace else "Workspace"
    account_type = user.get("account_type", "college")

    token = create_access_token({
        "sub": user["id"],
        "workspace_id": user.get("workspace_id", ""),
        "email": user["email"],
        "account_type": account_type,
    })

    profile = UserProfileResponse(
        id=user["id"],
        full_name=user.get("full_name", ""),
        email=user["email"],
        workspace_id=user.get("workspace_id", ""),
        workspace_name=workspace_name,
        account_type=account_type,
        created_at=user.get("created_at", utc_iso()),
        initials=build_initials(user.get("full_name", "User")),
    )
    return TokenResponse(access_token=token, token_type="bearer", user=profile)


async def get_user_profile(user: Dict[str, Any], db: Any) -> UserProfileResponse:
    """Retrieves full profile for the authenticated user."""
    workspace = await db.workspaces.find_one({"id": user.get("workspace_id")})
    workspace_name = workspace.get("name", "Workspace") if workspace else "Workspace"

    return UserProfileResponse(
        id=user["id"],
        full_name=user.get("full_name", ""),
        email=user["email"],
        workspace_id=user.get("workspace_id", ""),
        workspace_name=workspace_name,
        account_type=user.get("account_type", "college"),
        created_at=user.get("created_at", utc_iso()),
        initials=build_initials(user.get("full_name", "User")),
    )
