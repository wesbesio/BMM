# Media Assets Manager (BMM) - Build Instructions

## 📋 Overview

This repository contains two FastAPI applications for managing media collections:

- **bmm-rw**: Full-featured Media Assets Manager with CRUD operations (port 8000)
- **bmm-ro**: Read-only Media Assets Viewer (port 8001)

Both applications share the same SQLite database and provide different interfaces for managing movies, TV shows, and their associated physical/digital assets.

## 🎯 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **pip**: Latest version
- **Git**: For repository management
- **Internet**: Required for TMDB API integration (RW version)

### Required Knowledge
- **HTMX Fundamentals**: Required for RW application maintenance
- **📚 MANDATORY READING**: [HTMX Quirks & Best Practices](https://htmx.org/quirks/)
  - Essential for understanding dynamic UI components
  - Covers common pitfalls and implementation patterns
  - Required before modifying any HTMX-related code

## 📝 Development Standards

### File Header Convention
**All code files must include proper headers as the first lines:**

**HTML/Template files:**
```html
<!-- File: path/to/file.html -->
<!-- Revision: X.X - Description of changes/purpose -->
```

**Python files:**
```python
# File: path/to/file.py
# Revision: X.X - Description of changes/purpose
```

**Example implementations:**
```html
<!-- File: bmm-rw/templates/base.html -->
<!-- Revision: 1.0 - Base template with HTMX integration and Bootstrap styling -->
```

```python
# File: bmm-rw/main.py
# Revision: 1.42 - Main FastAPI application with TMDB search and CRUD operations
```

## 🚀 Quick Start

### 1. Repository Setup
```bash
# Clone the repository
git clone [your-repo-url]
cd [repo-directory]

# Verify directory structure
ls -la
# Should show: bmm-ro/ and bmm-rw/ directories
```

### 2. Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Verify activation
which python  # Should point to venv/bin/python
```

### 3. Install Dependencies

**For RW Application (Full Features):**
```bash
cd bmm-rw
pip install -r requirements.txt
```

**For RO Application (Read-Only):**
```bash
cd bmm-ro
pip install -r requirements.txt
```

**Install both if running simultaneously:**
```bash
# Install RW dependencies first
cd bmm-rw && pip install -r requirements.txt
cd ../bmm-ro && pip install -r requirements.txt
cd ..
```

## ⚙️ Configuration

### 1. Environment Variables Setup

**Create `.env` file in bmm-rw directory:**
```bash
cd bmm-rw
cp .env.example .env  # If available, or create new file
```

**Required `.env` contents:**
```bash
# bmm-rw/.env
SECRET_KEY=b'O6CU\xfa\xe1\x82R\x97\x9f\x1e\xa9\xd3\xad\xec\xd1#\xf5$s\xf9\xbc[\x0b'
ACCESS_TOKEN_EXPIRE_MINUTES=30
TMDB_API_KEY=your_tmdb_api_key_here
```

### 2. TMDB API Key Setup

**Get TMDB API Key:**
1. Visit [The Movie Database (TMDB)](https://www.themoviedb.org/)
2. Create a free account
3. Go to Settings → API
4. Request an API key
5. Copy the API key to your `.env` file

**Verify API key format:**
```bash
# Should be a long alphanumeric string
TMDB_API_KEY=1234567890abcdef1234567890abcdef
```

### 3. Database Setup

**The SQLite database is automatically created when either application starts:**
```bash
# Database file will be created as:
./media_assets.db
```

**Database will include these tables:**
- `media` - Movies and TV shows
- `assets` - Physical/digital copies
- `media_asset_link` - Many-to-many relationships

## 🏃‍♂️ Running the Applications

### Option 1: Run RW Application Only (Full Features)
```bash
cd bmm-rw
python main.py

# Or using uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Access at:** http://localhost:8000

### Option 2: Run RO Application Only (Read-Only)
```bash
cd bmm-ro
python main.py

# Or using uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Access at:** http://localhost:8001

### Option 3: Run Both Applications Simultaneously

**Terminal 1 (RW Application):**
```bash
cd bmm-rw
python main.py
```

**Terminal 2 (RO Application):**
```bash
cd bmm-ro
python main.py
```

**Access URLs:**
- **Full Manager:** http://localhost:8000
- **Read-Only Viewer:** http://localhost:8001

## 🎨 Application Features

### BMM-RW (Full Manager) - Port 8000
- ✅ Full CRUD operations for media and assets
- ✅ TMDB search integration
- ✅ HTMX-powered dynamic UI
- ✅ Create media from TMDB results
- ✅ Asset-media relationship management
- ✅ Search and filtering
- ✅ Pagination

### BMM-RO (Read-Only Viewer) - Port 8001
- ✅ View-only interface
- ✅ Search and filtering
- ✅ Pagination
- ✅ Media and asset browsing
- ✅ Clean, simplified UI
- ❌ No create/edit/delete operations
- ❌ No TMDB integration

## 🗂️ Project Structure

```
project-root/
├── bmm-rw/                          # Full-featured application
│   ├── main.py                      # FastAPI app with CRUD operations
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables
│   ├── templates/                   # Jinja2 templates
│   │   ├── base.html               # Base template with HTMX
│   │   ├── tmdb_search.html        # TMDB search interface
│   │   ├── media_list.html         # Media listing with filters
│   │   ├── asset_list.html         # Asset listing
│   │   └── partials/               # HTMX partial templates
│   └── static/                     # CSS/JS assets
├── bmm-ro/                          # Read-only application
│   ├── main.py                      # Read-only FastAPI app
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables
│   ├── templates-readonly/          # Read-only templates
│   └── static/                     # CSS/JS assets
└── media_assets.db                  # Shared SQLite database
```

## 🛠️ Development Workflow

### Adding File Headers to Existing Files

**For Python files:**
```python
# File: bmm-rw/main.py
# Revision: 1.43 - Added new TMDB TV search functionality

# main.py  version 1.42
# (existing content continues...)
```

**For HTML templates:**
```html
<!-- File: bmm-rw/templates/base.html -->
<!-- Revision: 1.1 - Updated navigation and added version badge -->

<!-- templates/base.html -->
<!DOCTYPE html>
<!-- (existing content continues...) -->
```

### Before Making Changes
1. **Review HTMX documentation**: https://htmx.org/quirks/
2. **Update file headers** with new revision numbers
3. **Test both applications** after changes
4. **Verify database compatibility** between RW and RO versions

## 🧪 Testing the Setup

### 1. Verify Applications Start
```bash
# Check RW application
curl http://localhost:8000/
# Should return HTML homepage

# Check RO application  
curl http://localhost:8001/
# Should return HTML homepage
```

### 2. Test Database Creation
```bash
# After starting either application, verify database exists
ls -la media_assets.db
# Should show the SQLite database file
```

### 3. Test TMDB Integration (RW only)
1. Navigate to http://localhost:8000/tmdb-search/
2. Search for a movie or TV show
3. Verify results appear with poster images
4. Test creating media from TMDB result

## 🚨 Troubleshooting

### Common Issues

**1. TMDB API Key Issues**
```bash
# Error: TMDB API calls failing
# Solution: Verify API key in .env file
cat bmm-rw/.env | grep TMDB_API_KEY
```

**2. Database Locked Error**
```bash
# Error: Database is locked
# Solution: Close all connections and restart
pkill -f "python main.py"
# Then restart applications
```

**3. Port Already in Use**
```bash
# Error: Port 8000 or 8001 in use
# Solution: Find and kill process
lsof -i :8000
kill -9 [PID]
```

**4. Missing Dependencies**
```bash
# Error: Module not found
# Solution: Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

**5. HTMX Not Loading**
- Check browser console for JavaScript errors
- Verify HTMX CDN is accessible
- Review [HTMX Quirks documentation](https://htmx.org/quirks/)

### Database Issues

**Reset Database:**
```bash
# Stop all applications first
rm media_assets.db
# Restart either application to recreate
```

**Backup Database:**
```bash
cp media_assets.db media_assets_backup_$(date +%Y%m%d).db
```

## 🔧 Advanced Configuration

### Custom Ports
**Modify port in main.py files:**
```python
# bmm-rw/main.py (line ~890)
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port here

# bmm-ro/main.py (line ~200)  
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change port here
```

### Development Mode with Auto-Reload
```bash
cd bmm-rw
uvicorn main:app --reload --host 0.0.0.0 --port 8000

cd bmm-ro
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLModel Documentation**: https://sqlmodel.tiangolo.com/
- **HTMX Documentation**: https://htmx.org/
- **HTMX Quirks (REQUIRED)**: https://htmx.org/quirks/
- **Bootstrap Documentation**: https://getbootstrap.com/docs/5.3/
- **TMDB API Documentation**: https://developers.themoviedb.org/3

## ✅ Success Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed for required applications
- [ ] `.env` file created with valid TMDB API key
- [ ] Applications start without errors
- [ ] Database file created automatically
- [ ] Web interfaces accessible at correct ports
- [ ] TMDB search functionality working (RW only)
- [ ] File headers added to any new/modified files
- [ ] HTMX quirks documentation reviewed

---

**🎉 You're ready to manage your media collection with BMM!**