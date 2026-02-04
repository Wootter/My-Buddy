# Frontend Files - Local Development

This folder contains only the frontend assets for visual/design work.

## Contents

- **templates/** - HTML files
- **static/** - CSS, JavaScript, and images

## Quick Start for Local Preview

You can view these files using:

1. **Python Simple HTTP Server:**
   ```bash
   python -m http.server 8080
   ```
   Then open: http://localhost:8080

2. **VS Code Live Server Extension:**
   - Install "Live Server" extension
   - Right-click on an HTML file → "Open with Live Server"

3. **Any local web server of your choice**

## Notes

- These are static frontend files only
- No backend/Python required
- Edit CSS, HTML, and JS directly
- Templates use Flask/Jinja2 syntax - some dynamic parts won't work without the backend
