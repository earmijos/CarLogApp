# Making Your Backend Publicly Accessible

## The Problem
Your app currently points to `http://127.0.0.1:5000` which only works on your local computer. When users scan the QR code, their phones can't reach your local backend.

## Solution Options

---

## Option 1: Use ngrok (Quick Demo - 5 minutes)

**Best for**: Quick demos, testing

### Steps:

1. **Install ngrok**
   - Download from: https://ngrok.com/download
   - Or install via Homebrew: `brew install ngrok`

2. **Start your backend** (if not running)
   ```bash
   cd CarLog/backend
   source venv/bin/activate
   python app.py
   ```

3. **Start ngrok tunnel**
   ```bash
   ngrok http 5000
   ```
   
4. **Copy the HTTPS URL**
   - Look for: `Forwarding    https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:5000`
   - Copy that HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

5. **Update frontend config**
   - Edit: `CarLog/frontend/lib/config/app_config.dart`
   - Change: `static const String apiBaseUrl = 'https://your-ngrok-url.ngrok-free.app';`

6. **Rebuild and redeploy**
   ```bash
   cd CarLog/frontend
   flutter build web
   # Then deploy to Netlify
   ```

**Note**: Free ngrok URLs change each time you restart ngrok. Paid plans give permanent URLs.

---

## Option 2: Deploy Backend to Render (Free - Permanent Solution)

**Best for**: Production, permanent solution

### Steps:

1. **Sign up for Render**: https://render.com (free tier available)

2. **Create a new Web Service**
   - Connect your GitHub repo, OR
   - Deploy from a Dockerfile/manually

3. **Configure Render**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Environment**: Python 3
   - **Root Directory**: `CarLog/backend`

4. **Set Environment Variables** (if needed)
   - `PORT=5000` (or whatever Render assigns)
   - `FLASK_DEBUG=false`

5. **Deploy**
   - Render will give you a URL like: `https://your-app.onrender.com`

6. **Update frontend config**
   - Edit: `CarLog/frontend/lib/config/app_config.dart`
   - Change: `static const String apiBaseUrl = 'https://your-app.onrender.com';`

7. **Rebuild and redeploy frontend**
   ```bash
   cd CarLog/frontend
   flutter build web
   # Then deploy to Netlify
   ```

---

## Option 3: Deploy Backend to Railway (Free - Alternative)

Similar process to Render. Visit: https://railway.app

---

## Quick Steps Summary (ngrok method):

1. Install ngrok: `brew install ngrok` or download from ngrok.com
2. Make sure backend is running: `python app.py` (in backend folder)
3. In a new terminal: `ngrok http 5000`
4. Copy the HTTPS URL ngrok gives you
5. Update `app_config.dart` with that URL
6. Rebuild: `flutter build web`
7. Redeploy to Netlify
8. Test QR code on your phone!

---

**Which method do you want to use?** I recommend ngrok for quick testing, or Render for a permanent solution.

