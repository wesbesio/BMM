# main.py (Read-Only Version) version 1.12
#  
from fastapi import FastAPI, Request, Depends, Query, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship, col, func
from typing import Optional, List
from datetime import datetime
import os
import re
from typing import TYPE_CHECKING

def get_version():
    """Extract version number from this file's comment"""
    try:
        with open(__file__, 'r') as f:
            first_line = f.readline()
            # Look for version pattern like "version 1.11"
            match = re.search(r'version\s+([\d.]+)', first_line)
            if match:
                return f"v{match.group(1)}"
    except Exception:
        pass
    return "v?.??"

# Create SQLModel models - same as the original application
class MediaAssetLink(SQLModel, table=True):
    """Association table for Media-Asset relationship"""
    __tablename__ = "media_asset_link"
    
    media_id: Optional[int] = Field(default=None, foreign_key="media.id", primary_key=True)
    asset_id: Optional[int] = Field(default=None, foreign_key="assets.id", primary_key=True)

class AssetBase(SQLModel):
    format: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    subtitle: Optional[str] = None
    title: Optional[str] = None
    imageurl: Optional[str] = None
    image: Optional[str] = None
    dupe: Optional[bool] = False
    imdbid: Optional[str] = None
    tmdbid: Optional[int] = None
    active: bool = True
    flag: bool = False
    mtype: Optional[int] = None
    isbn: Optional[str] = None

class Asset(AssetBase, table=True):
    __tablename__ = "assets"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    creation: datetime = Field(default_factory=datetime.now)
    
    # Relationship to Media
    media: List["Media"] = Relationship(back_populates="assets", link_model=MediaAssetLink)

class MediaBase(SQLModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    imageurl: Optional[str] = None
    mtype: Optional[int] = None
    notes: Optional[str] = None
    imdbid: Optional[str] = None
    tmdbid: Optional[int] = None
    active: bool = False
    flag: bool = False
    acquire: bool = True

class Media(MediaBase, table=True):
    __tablename__ = "media"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    creation: datetime = Field(default_factory=datetime.now)
    
    # Relationship to Asset
    assets: List["Asset"] = Relationship(back_populates="media", link_model=MediaAssetLink)

# Database setup - using the same database as the main application
DATABASE_URL = "sqlite:///./media_assets.db"
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

# FastAPI app setup
app = FastAPI(title="Media Assets Viewer")

# Templates and static files setup
templates = Jinja2Templates(directory="templates-readonly")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get version once at startup
APP_VERSION = get_version()

def get_base_context(request: Request) -> dict:
    """Get base template context with version info"""
    return {"request": request, "app_version": APP_VERSION}

# Routes - Read-only version
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    media_count = session.exec(select(Media)).all().__len__()
    asset_count = session.exec(select(Asset)).all().__len__()
    context = get_base_context(request)
    context.update({"media_count": media_count, "asset_count": asset_count})
    return templates.TemplateResponse("home.html", context)

# Asset Routes - Read-only
@app.get("/assets/", response_class=HTMLResponse)
async def list_assets(
    request: Request, 
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str = None
):
    # Calculate offset based on page and per_page
    offset = (page - 1) * per_page
    
    # Base query
    query = select(Asset)
    count_query = select(func.count()).select_from(Asset)
    
    # Apply search filter if provided
    if search:
        query = query.where(col(Asset.title).contains(search))
        count_query = count_query.where(col(Asset.title).contains(search))
    
    # Get total count for pagination
    total_count = session.exec(count_query).one()
    
    # Calculate total pages
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get assets with pagination
    assets = session.exec(query.offset(offset).limit(per_page)).all()
    
    # Context for the template
    context = get_base_context(request)
    context.update({
        "assets": assets,
        "search": search or "", 
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": total_pages
        }
    })
    
    return templates.TemplateResponse("asset_list.html", context)

@app.get("/assets/{asset_id}", response_class=HTMLResponse)
async def get_asset(
    request: Request,
    asset_id: int,
    session: Session = Depends(get_session)
):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get the previous and next asset IDs for navigation
    prev_asset = session.exec(
        select(Asset).where(Asset.id < asset_id).order_by(Asset.id.desc()).limit(1)
    ).first()
    
    next_asset = session.exec(
        select(Asset).where(Asset.id > asset_id).order_by(Asset.id).limit(1)
    ).first()
    
    prev_id = prev_asset.id if prev_asset else None
    next_id = next_asset.id if next_asset else None
    
    context = get_base_context(request)
    context.update({
        "asset": asset,
        "prev_id": prev_id,
        "next_id": next_id
    })
    
    return templates.TemplateResponse("asset_detail.html", context)

# Media Routes - Read-only
@app.get("/media/", response_class=HTMLResponse)
async def list_media(
    request: Request, 
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str = None,
    status: str = None
):
    # Calculate offset based on page and per_page
    offset = (page - 1) * per_page
    
    # Base query
    query = select(Media)
    count_query = select(func.count()).select_from(Media)
    
    # Apply search filter if provided
    if search:
        query = query.where(col(Media.title).contains(search))
        count_query = count_query.where(col(Media.title).contains(search))
    
    # Apply status filter if provided
    if status:
        if status == "active":
            query = query.where(Media.active == True)
            count_query = count_query.where(Media.active == True)
        elif status == "inactive":
            query = query.where(Media.active == False)
            count_query = count_query.where(Media.active == False)
        elif status == "flagged":
            query = query.where(Media.flag == True)
            count_query = count_query.where(Media.flag == True)
        elif status == "acquire":
            query = query.where(Media.acquire == True)
            count_query = count_query.where(Media.acquire == True)
    
    # Get total count for pagination
    total_count = session.exec(count_query).one()
    
    # Calculate total pages
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get media items with pagination
    media_items = session.exec(query.offset(offset).limit(per_page)).all()
    
    # Context for the template
    context = get_base_context(request)
    context.update({
        "media_items": media_items, 
        "search": search or "",
        "status": status or "",
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": total_pages
        }
    })
    
    return templates.TemplateResponse("media_list.html", context)

@app.get("/media/{media_id}", response_class=HTMLResponse)
async def get_media(
    request: Request,
    media_id: int,
    session: Session = Depends(get_session)
):
    media = session.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Get the previous and next media IDs for navigation
    prev_media = session.exec(
        select(Media).where(Media.id < media_id).order_by(Media.id.desc()).limit(1)
    ).first()
    
    next_media = session.exec(
        select(Media).where(Media.id > media_id).order_by(Media.id).limit(1)
    ).first()
    
    prev_id = prev_media.id if prev_media else None
    next_id = next_media.id if next_media else None
    
    context = get_base_context(request)
    context.update({
        "media": media,
        "prev_id": prev_id,
        "next_id": next_id
    })
    
    return templates.TemplateResponse("media_detail.html", context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Using a different port from the main app