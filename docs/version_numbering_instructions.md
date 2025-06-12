# BMM Version Numbering Implementation Instructions

## Overview
This guide explains how to implement dynamic version numbering in both BMM applications (read-only and read-write versions) that automatically extracts version numbers from source code comments and displays them as badges in the navigation bar.

## Prerequisites
- Existing BMM application structure with FastAPI
- Jinja2 templates with Bootstrap CSS
- Basic understanding of Python regex and template contexts

## Implementation Steps

### Step 1: Add Version Detection Function

Add this function to both `bmm-ro/main.py` and `bmm-rw/main.py` files, after the imports section:

```python
import re  # Add this to your imports if not already present

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
```

### Step 2: Initialize Version at Startup

Add these lines after your FastAPI app initialization:

```python
# Get version once at startup
APP_VERSION = get_version()

def get_base_context(request: Request) -> dict:
    """Get base template context with version info"""
    return {"request": request, "app_version": APP_VERSION}
```

### Step 3: Update Route Handlers

Replace all existing template context creation with the new helper function. 

**Before:**
```python
return templates.TemplateResponse(
    "home.html", 
    {"request": request, "media_count": media_count, "asset_count": asset_count}
)
```

**After:**
```python
context = get_base_context(request)
context.update({"media_count": media_count, "asset_count": asset_count})
return templates.TemplateResponse("home.html", context)
```

Apply this pattern to ALL route handlers in both applications.

### Step 4: Update Base Templates

#### For bmm-ro/templates-readonly/base.html:

Add this CSS to the `<style>` section:
```css
/* Version badge styling */
.version-badge {
    margin-left: auto;
}
```

Update the navbar section to include the version badge:
```html
<div class="collapse navbar-collapse" id="navbarNav">
    <ul class="navbar-nav">
        <li class="nav-item">
            <a class="nav-link" href="/">Home</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/assets/">Assets</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/media/">Media</a>
        </li>
    </ul>
    <!-- Version badge on the far right -->
    <div class="version-badge">
        <span class="badge bg-secondary">{{ app_version }}</span>
    </div>
</div>
```

#### For bmm-rw/templates/base.html:

Add the same CSS and update the navbar with:
```html
<div class="collapse navbar-collapse" id="navbarNav">
    <ul class="navbar-nav">
        <li class="nav-item">
            <a class="nav-link" href="/">Home</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/assets/">Assets</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/media/">Media</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/tmdb-search/">TMDB Search</a>
        </li>
    </ul>
    <!-- Version badge on the far right -->
    <div class="version-badge">
        <span class="badge bg-primary">{{ app_version }}</span>
    </div>
</div>
```

## Usage Instructions

### Updating Version Numbers

To update the version number:

1. Edit the first line comment in `main.py`
2. Change the version number in the pattern `version X.XX`
3. Restart the application
4. The new version will automatically appear in the navigation

**Example:**
```python
# main.py (Read-Only Version) version 1.12
```

### Version Number Format

The regex pattern `r'version\s+([\d.]+)'` supports:
- `version 1.11` → displays as `v1.11`
- `version 2.0.1` → displays as `v2.0.1`
- `version 1.37` → displays as `v1.37`

### Badge Styling

- **Read-only version**: Uses `bg-secondary` (gray badge)
- **Read-write version**: Uses `bg-primary` (blue badge)

You can customize badge colors by changing the Bootstrap CSS classes:
- `bg-primary` (blue)
- `bg-secondary` (gray)
- `bg-success` (green)
- `bg-danger` (red)
- `bg-warning` (yellow)
- `bg-info` (cyan)

## Troubleshooting

### Version Shows as "v?.??"
- Check that the first line of `main.py` contains the version pattern
- Ensure the file is readable
- Verify the regex pattern matches your comment format

### Badge Not Appearing
- Verify `app_version` is in the template context
- Check that all route handlers use `get_base_context()`
- Ensure the template syntax `{{ app_version }}` is correct

### Styling Issues
- Confirm Bootstrap CSS is loaded
- Check that the `.version-badge` CSS class is defined
- Verify the navbar structure matches the examples

## Benefits

- **Automatic updates**: Version changes in code automatically reflect in UI
- **Single source of truth**: Version defined once in the source file
- **Visual distinction**: Different badge colors help distinguish app versions
- **Professional appearance**: Clean, pill-style badges in navigation
- **Error resilience**: Graceful fallback if version can't be read

## Future Enhancements

Consider these additional features:
- Add build date/time to version display
- Include Git commit hash in version
- Create an "About" modal with detailed version information
- Add version history changelog page
- Implement semantic versioning with major.minor.patch format