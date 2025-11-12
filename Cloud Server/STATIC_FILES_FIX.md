# Fix for Caddy - Static Files Not Loading

## Problem
Your CSS/JS files aren't loading because Caddy is passing ALL requests to Flask, including static files.

## Solution 1: Update Caddyfile (Recommended)

SSH into your server and edit the Caddyfile:

```bash
sudo nano /etc/caddy/Caddyfile
```

Replace with:

```
46.101.171.129 {
    # Serve static files directly (faster)
    handle /static/* {
        root * /home/YOUR_USERNAME/My-Buddy/Cloud Server
        file_server
    }
    
    # Pass everything else to Flask
    reverse_proxy 127.0.0.1:8000
}
```

**Important:** Replace `YOUR_USERNAME` with your actual username!

Then reload Caddy:
```bash
sudo systemctl reload caddy
```

---

## Solution 2: Let Flask Handle Static Files (Simpler but slower)

If Solution 1 doesn't work, make sure Flask is configured correctly.

Check your main.py has this at the top:

```python
app = Flask(__name__, 
            static_url_path='/static',
            static_folder='static',
            template_folder='templates')
```

---

## Verification

After applying the fix, visit:
- http://46.101.171.129/static/css/style.css (should show CSS code)
- http://46.101.171.129/static/js/app.js (should show JavaScript code)

If you see the file contents, it's working!

---

## Quick Checklist

1. ✓ Static files exist in `~/My-Buddy/Cloud Server/static/`
2. ✓ Templates use `url_for('static', filename='...')`
3. ? Caddy configuration serves static files
4. ? File permissions allow Caddy to read static files

Check permissions:
```bash
chmod -R 755 ~/My-Buddy/Cloud\ Server/static
```

---

## Debug Commands

Check if static files exist:
```bash
ls -la ~/My-Buddy/Cloud\ Server/static/css/
ls -la ~/My-Buddy/Cloud\ Server/static/js/
```

Check Caddy logs:
```bash
sudo journalctl -u caddy -n 50
```

Check Flask logs:
```bash
sudo journalctl -u mybuddy -n 50
```
