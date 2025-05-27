# main.py  version 1.42
#
from fastapi import FastAPI, Request, Form, Depends, Query, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine, select, delete, Relationship, col, func
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import httpx
import re
from typing import TYPE_CHECKING
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_version():
    """Extract version number from this file's comment"""
    try:
        with open(__file__, 'r') as f:
            first_line = f.readline()
            # Look for version pattern like "version 1.39"
            match = re.search(r'version\s+([\d.]+)', first_line)
            if match:
                return f"v{match.group(1)}"
    except Exception:
        pass
    return "v?.??"

# Create SQLModel models
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

class AssetCreate(AssetBase):
    pass

class AssetRead(AssetBase):
    id: int
    creation: datetime

class AssetUpdate(SQLModel):
    format: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    subtitle: Optional[str] = None
    title: Optional[str] = None
    imageurl: Optional[str] = None
    image: Optional[str] = None
    dupe: Optional[bool] = None
    imdbid: Optional[str] = None
    tmdbid: Optional[int] = None
    active: Optional[bool] = None
    flag: Optional[bool] = None
    mtype: Optional[int] = None
    isbn: Optional[str] = None

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

class MediaCreate(MediaBase):
    pass

class MediaRead(MediaBase):
    id: int
    creation: datetime

class MediaUpdate(SQLModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    imageurl: Optional[str] = None
    mtype: Optional[int] = None
    notes: Optional[str] = None
    imdbid: Optional[str] = None
    tmdbid: Optional[int] = None
    active: Optional[bool] = None
    flag: Optional[bool] = None
    acquire: Optional[bool] = None

# Constants
DATABASE_URL = "sqlite:///./media_assets.db"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Read from .env file
TMDB_BASE_URL = "https://api.themoviedb.org/3"
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# FastAPI app setup
app = FastAPI(title="Media Assets Manager")

# Templates and static files setup
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get version once at startup
APP_VERSION = get_version()

def get_base_context(request: Request) -> dict:
    """Get base template context with version info"""
    return {"request": request, "app_version": APP_VERSION}

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    media_count = session.exec(select(Media)).all().__len__()
    asset_count = session.exec(select(Asset)).all().__len__()
    context = get_base_context(request)
    context.update({"media_count": media_count, "asset_count": asset_count})
    return templates.TemplateResponse("home.html", context)

# TMDB Search Route - Updated with improved duplicate checking and debugging
@app.get("/tmdb-search/", response_class=HTMLResponse)
async def tmdb_search(
    request: Request,
    query: str = "",
    search_type: str = Query("movie", regex="^(movie|tv)$"),  # Validate search type
    page: int = Query(1, ge=1),
    session: Session = Depends(get_session)
):
    results = []
    total_results = 0
    total_pages = 0
    current_page = page
    existing_tmdb_ids = set()
    
    if query:
        # Determine the API endpoint based on search type
        endpoint = f"/search/{search_type}"
        
        # Call TMDB API
        async with httpx.AsyncClient() as client:
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {TMDB_API_KEY}"
            }
            response = await client.get(
                f"{TMDB_BASE_URL}{endpoint}",
                params={"query": query, "page": page},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                total_results = data.get("total_results", 0)
                total_pages = data.get("total_pages", 0)
                current_page = data.get("page", 1)
                
                # Check for existing media in database
                if results:
                    # Determine media type for database query
                    mtype = 1 if search_type == "movie" else 2
                    
                    # Get all TMDB IDs from the current search results
                    search_tmdb_ids = [item.get("id") for item in results if item.get("id")]
                    
                    print(f"DEBUG: Search type: {search_type}, mtype: {mtype}")
                    print(f"DEBUG: Search TMDB IDs from API: {search_tmdb_ids}")
                    
                    if search_tmdb_ids:
                        # Query database for existing media - get all records to debug
                        all_media_query = select(Media.id, Media.title, Media.tmdbid, Media.mtype).where(
                            Media.mtype == mtype
                        )
                        all_media = session.exec(all_media_query).all()
                        
                        print(f"DEBUG: All media with mtype {mtype}:")
                        for media in all_media:
                            print(f"  ID: {media.id}, Title: {media.title}, TMDB ID: {media.tmdbid}, Type: {media.mtype}")
                        
                        # Now get just the existing TMDB IDs that match our search
                        existing_media_query = select(Media.tmdbid).where(
                            Media.tmdbid.in_(search_tmdb_ids),
                            Media.mtype == mtype,
                            Media.tmdbid.is_not(None)
                        )
                        existing_media_results = session.exec(existing_media_query).all()
                        
                        print(f"DEBUG: Raw existing media results: {existing_media_results}")
                        
                        # Create set of existing TMDB IDs for quick lookup
                        existing_tmdb_ids = set()
                        for tmdb_id in existing_media_results:
                            if tmdb_id is not None:
                                existing_tmdb_ids.add(int(tmdb_id))
                        
                        print(f"DEBUG: Final existing TMDB IDs set: {existing_tmdb_ids}")
                        
                        # Check each result item
                        for item in results[:3]:  # Just first 3 for debugging
                            item_id = int(item.get("id", 0))
                            title = item.get("title") or item.get("name", "Unknown")
                            print(f"DEBUG: Checking item '{title}' with TMDB ID {item_id}: {'EXISTS' if item_id in existing_tmdb_ids else 'NEW'}")
    
    context = get_base_context(request)
    context.update({
        "query": query,
        "search_type": search_type,
        "results": results,
        "total_results": total_results,
        "total_pages": total_pages,
        "current_page": current_page,
        "existing_tmdb_ids": existing_tmdb_ids
    })
    
    return templates.TemplateResponse("tmdb_search.html", context)

# Create Media from TMDB Route
@app.get("/media/create-from-tmdb/{tmdb_id}", response_class=HTMLResponse)
async def create_media_from_tmdb(
    request: Request,
    tmdb_id: int,
    session: Session = Depends(get_session)
):
    # Fetch movie details from TMDB
    async with httpx.AsyncClient() as client:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_KEY}"
        }
        response = await client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Movie not found on TMDB")
        
        movie_data = response.json()
    
    # Create a new Media object with TMDB data
    # Start with "To Acquire" status (no asset associated initially)
    media = Media(
        title=movie_data.get("title"),
        subtitle=movie_data.get("tagline"),
        imageurl=f"https://image.tmdb.org/t/p/w92{movie_data.get('poster_path')}" if movie_data.get("poster_path") else None,
        mtype=1,  # Assuming 1 is for movies
        notes=movie_data.get("overview"),
        imdbid=movie_data.get("imdb_id"),
        tmdbid=tmdb_id,
        active=False,  # Not active until an asset is associated
        flag=False,
        acquire=True   # Set to "To Acquire" by default
    )
    
    session.add(media)
    session.commit()
    session.refresh(media)
    
    return RedirectResponse(url=f"/media/{media.id}", status_code=303)

# Create Media from TMDB TV Route - New route for TV shows
@app.get("/media/create-from-tmdb-tv/{tmdb_id}", response_class=HTMLResponse)
async def create_media_from_tmdb_tv(
    request: Request,
    tmdb_id: int,
    session: Session = Depends(get_session)
):
    # Fetch TV show details from TMDB
    async with httpx.AsyncClient() as client:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_KEY}"
        }
        response = await client.get(
            f"{TMDB_BASE_URL}/tv/{tmdb_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="TV show not found on TMDB")
        
        tv_data = response.json()
    
    # Create a new Media object with TMDB TV data
    # Start with "To Acquire" status (no asset associated initially)
    media = Media(
        title=tv_data.get("name"),  # TV shows use "name" instead of "title"
        subtitle=tv_data.get("tagline"),
        imageurl=f"https://image.tmdb.org/t/p/w92{tv_data.get('poster_path')}" if tv_data.get("poster_path") else None,
        mtype=2,  # 2 is for TV shows
        notes=tv_data.get("overview"),
        imdbid=None,  # TV endpoint doesn't return IMDB ID directly
        tmdbid=tmdb_id,
        active=False,  # Not active until an asset is associated
        flag=False,
        acquire=True   # Set to "To Acquire" by default
    )
    
    session.add(media)
    session.commit()
    session.refresh(media)
    
    return RedirectResponse(url=f"/media/{media.id}", status_code=303)

# Asset Routes
@app.get("/assets/", response_class=HTMLResponse)
async def list_assets(
    request: Request, 
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str = None,
    hx_request: Optional[str] = Header(None)
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
    
    # If it's an HTMX request, return just the table partial
    if hx_request:
        return templates.TemplateResponse("partials/asset_table.html", context)
    
    # Otherwise return the full page
    return templates.TemplateResponse("asset_list.html", context)

@app.get("/assets/new", response_class=HTMLResponse)
async def new_asset_form(request: Request, session: Session = Depends(get_session)):
    # Get media list sorted alphabetically by title
    media_list = session.exec(select(Media).order_by(Media.title)).all()
    context = get_base_context(request)
    context.update({"media_list": media_list})
    return templates.TemplateResponse("asset_form.html", context)

@app.post("/assets/new", response_class=HTMLResponse)
async def create_asset(
    request: Request,
    title: str = Form(None),
    subtitle: str = Form(None),
    format: str = Form(None),
    location: str = Form(None),
    notes: str = Form(None),
    imageurl: str = Form(None),
    image: str = Form(None),
    dupe: bool = Form(False),
    imdbid: str = Form(None),
    tmdbid: int = Form(None),
    active: bool = Form(True),
    flag: bool = Form(False),
    mtype: int = Form(None),
    isbn: str = Form(None),
    media_ids: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    # Process the imageurl to add TMDB base URL if not already present
    if imageurl and not imageurl.startswith('http'):
        # Make sure the image path starts with a slash if needed
        if not imageurl.startswith('/'):
            imageurl = f"/{imageurl}"
        imageurl = f"https://image.tmdb.org/t/p/w92{imageurl}"
        
    asset = Asset(
        title=title,
        subtitle=subtitle,
        format=format,
        location=location,
        notes=notes,
        imageurl=imageurl,
        image=image,
        dupe=dupe,
        imdbid=imdbid,
        tmdbid=tmdbid,
        active=active,
        flag=flag,
        mtype=mtype,
        isbn=isbn
    )
    
    session.add(asset)
    session.commit()
    session.refresh(asset)
    
    # Add relationship to the selected media if specified
    if media_ids and media_ids.strip():
        try:
            media_id = int(media_ids)
            media = session.get(Media, media_id)
            if media:
                link = MediaAssetLink(media_id=media.id, asset_id=asset.id)
                session.add(link)
                session.commit()
        except (ValueError, TypeError):
            # Log or handle error, but continue without adding the relationship
            pass
    
    return RedirectResponse(url="/assets/", status_code=303)

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

@app.get("/assets/{asset_id}/edit", response_class=HTMLResponse)
async def edit_asset_form(
    request: Request,
    asset_id: int,
    session: Session = Depends(get_session)
):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get media list sorted alphabetically by title
    media_list = session.exec(select(Media).order_by(Media.title)).all()
    asset_media_ids = [media.id for media in asset.media]
    
    context = get_base_context(request)
    context.update({
        "asset": asset, 
        "media_list": media_list, 
        "asset_media_ids": asset_media_ids
    })
    
    return templates.TemplateResponse("asset_edit.html", context)

@app.post("/assets/{asset_id}/edit", response_class=HTMLResponse)
async def update_asset(
    request: Request,
    asset_id: int,
    title: str = Form(None),
    subtitle: str = Form(None),
    format: str = Form(None),
    location: str = Form(None),
    notes: str = Form(None),
    imageurl: str = Form(None),
    image: str = Form(None),
    dupe: bool = Form(False),
    imdbid: str = Form(None),
    tmdbid: int = Form(None),
    active: bool = Form(True),
    flag: bool = Form(False),
    mtype: int = Form(None),
    isbn: str = Form(None),
    media_ids: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Process the imageurl to add TMDB base URL if not already present
    if imageurl and not imageurl.startswith('http'):
        # Make sure the image path starts with a slash if needed
        if not imageurl.startswith('/'):
            imageurl = f"/{imageurl}"
        imageurl = f"https://image.tmdb.org/t/p/w92{imageurl}"
    
    # Update asset fields
    asset_data = {
        "title": title,
        "subtitle": subtitle,
        "format": format,
        "location": location,
        "notes": notes,
        "imageurl": imageurl,
        "image": image,
        "dupe": dupe,
        "imdbid": imdbid,
        "tmdbid": tmdbid,
        "active": active,
        "flag": flag,
        "mtype": mtype,
        "isbn": isbn
    }
    
    for key, value in asset_data.items():
        setattr(asset, key, value)
    
    # Update media relationships
    # First, remove all existing links
    session.exec(
        delete(MediaAssetLink).where(MediaAssetLink.asset_id == asset_id)
    )
    
    # Add the new link if a media is selected
    if media_ids and media_ids.strip():
        try:
            media_id = int(media_ids)
            link = MediaAssetLink(media_id=media_id, asset_id=asset_id)
            session.add(link)
        except (ValueError, TypeError):
            # Log or handle error, but continue without adding the relationship
            pass
    
    session.commit()
    
    return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

@app.post("/assets/{asset_id}/delete", response_class=HTMLResponse)
async def delete_asset(
    request: Request,
    asset_id: int,
    session: Session = Depends(get_session)
):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Delete all links first
    session.exec(
        delete(MediaAssetLink).where(MediaAssetLink.asset_id == asset_id)
    )
    
    # Then delete the asset
    session.delete(asset)
    session.commit()
    
    return RedirectResponse(url="/assets/", status_code=303)

# Media Routes
@app.get("/media/", response_class=HTMLResponse)
async def list_media(
    request: Request, 
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str = None,
    status: str = None,
    hx_request: Optional[str] = Header(None)
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
    
    # Get total count for pagination (with filters applied if necessary)
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
    
    # If it's an HTMX request, return just the table partial
    if hx_request:
        return templates.TemplateResponse("partials/media_table.html", context)
    
    # Otherwise return the full page
    return templates.TemplateResponse("media_list.html", context)

@app.get("/media/new", response_class=HTMLResponse)
async def new_media_form(request: Request, session: Session = Depends(get_session)):
    # Get assets sorted alphabetically by title
    assets = session.exec(select(Asset).order_by(Asset.title)).all()
    context = get_base_context(request)
    context.update({"assets": assets})
    return templates.TemplateResponse("media_form.html", context)

@app.post("/media/new", response_class=HTMLResponse)
async def create_media(
    request: Request,
    title: str = Form(None),
    subtitle: str = Form(None),
    imageurl: str = Form(None),
    mtype: int = Form(None),
    notes: str = Form(None),
    imdbid: str = Form(None),
    tmdbid: int = Form(None),
    active: bool = Form(False),
    flag: bool = Form(False),
    acquire: bool = Form(True),
    asset_ids: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    # Process the imageurl to add TMDB base URL if not already present
    if imageurl and not imageurl.startswith('http'):
        # Make sure the image path starts with a slash if needed
        if not imageurl.startswith('/'):
            imageurl = f"/{imageurl}"
        imageurl = f"https://image.tmdb.org/t/p/w92{imageurl}"
    
    # Check if an asset is being associated
    has_asset = asset_ids and asset_ids.strip()
    
    # If an asset is associated, set active to True and acquire to False
    if has_asset:
        active = True
        acquire = False
        
    media = Media(
        title=title,
        subtitle=subtitle,
        imageurl=imageurl,
        mtype=mtype,
        notes=notes,
        imdbid=imdbid,
        tmdbid=tmdbid,
        active=active,
        flag=flag,
        acquire=acquire
    )
    
    session.add(media)
    session.commit()
    session.refresh(media)
    
    # Add relationship to the selected asset if specified
    if has_asset:
        try:
            asset_id = int(asset_ids)
            asset = session.get(Asset, asset_id)
            if asset:
                link = MediaAssetLink(media_id=media.id, asset_id=asset.id)
                session.add(link)
                session.commit()
        except (ValueError, TypeError):
            # Log or handle error, but continue without adding the relationship
            pass
    
    return RedirectResponse(url="/media/", status_code=303)

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

@app.get("/media/{media_id}/edit", response_class=HTMLResponse)
async def edit_media_form(
    request: Request,
    media_id: int,
    session: Session = Depends(get_session)
):
    media = session.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Get assets sorted alphabetically by title
    assets = session.exec(select(Asset).order_by(Asset.title)).all()
    media_asset_ids = [asset.id for asset in media.assets]
    
    context = get_base_context(request)
    context.update({
        "media": media, 
        "assets": assets, 
        "media_asset_ids": media_asset_ids
    })
    
    return templates.TemplateResponse("media_edit.html", context)

@app.post("/media/{media_id}/edit", response_class=HTMLResponse)
async def update_media(
    request: Request,
    media_id: int,
    title: str = Form(None),
    subtitle: str = Form(None),
    imageurl: str = Form(None),
    mtype: int = Form(None),
    notes: str = Form(None),
    imdbid: str = Form(None),
    tmdbid: int = Form(None),
    active: Optional[bool] = Form(None),
    flag: Optional[bool] = Form(None),
    acquire: Optional[bool] = Form(None),
    asset_ids: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    media = session.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Process the imageurl to add TMDB base URL if not already present
    if imageurl and not imageurl.startswith('http'):
        # Make sure the image path starts with a slash if needed
        if not imageurl.startswith('/'):
            imageurl = f"/{imageurl}"
        imageurl = f"https://image.tmdb.org/t/p/w92{imageurl}"
    
    # Check if an asset is being associated
    has_asset = asset_ids and asset_ids.strip()
    
    # Checkboxes need special handling - they're only included in the form if checked
    # Form.active etc will be None if the checkbox isn't checked
    active_value = bool(active)
    flag_value = bool(flag)
    acquire_value = bool(acquire)
    
    # If an asset is associated, automatically set active to True and acquire to False
    if has_asset:
        active_value = True
        acquire_value = False
    
    # Update media fields
    media_data = {
        "title": title,
        "subtitle": subtitle,
        "imageurl": imageurl,
        "mtype": mtype,
        "notes": notes,
        "imdbid": imdbid,
        "tmdbid": tmdbid,
        "active": active_value,
        "flag": flag_value,
        "acquire": acquire_value
    }
    
    for key, value in media_data.items():
        setattr(media, key, value)
    
    # Update asset relationship
    # First, remove all existing links
    session.exec(
        delete(MediaAssetLink).where(MediaAssetLink.media_id == media_id)
    )
    
    # Add the new link if an asset is selected
    if has_asset:
        try:
            asset_id = int(asset_ids)
            link = MediaAssetLink(media_id=media_id, asset_id=asset_id)
            session.add(link)
        except (ValueError, TypeError):
            # Log or handle error, but continue without adding the relationship
            pass
    else:
        # If no asset is associated, revert to "To Acquire" status
        media.active = False
        media.acquire = True
    
    session.commit()
    
    return RedirectResponse(url=f"/media/{media_id}", status_code=303)

@app.post("/media/{media_id}/delete", response_class=HTMLResponse)
async def delete_media(
    request: Request,
    media_id: int,
    session: Session = Depends(get_session)
):
    media = session.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Delete all links first
    session.exec(
        delete(MediaAssetLink).where(MediaAssetLink.media_id == media_id)
    )
    
    # Then delete the media
    session.delete(media)
    session.commit()
    
    return RedirectResponse(url="/media/", status_code=303)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)