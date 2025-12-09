# Deploy Backend to Render - Step by Step Guide

## 🎯 Goal
Deploy your Flask backend to Render so it's publicly accessible. Then update your frontend to use the public URL.

---

## ✅ Pre-Deployment Checklist

✅ Backend code is ready  
✅ `requirements.txt` exists  
✅ `Procfile` created (for Render)  
✅ `runtime.txt` created (Python version)  

---

## 📝 Step 1: Push Code to GitHub

### Option A: If you already have a GitHub repo

1. **Initialize git** (if not already):
   ```bash
   cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19
   git init
   git add .
   git commit -m "Initial commit - CarLog app ready for deployment"
   ```

2. **Create repo on GitHub**:
   - Go to: https://github.com/new
   - Create a new repository (name it: `CarLogApp` or similar)
   - Don't initialize with README

3. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/CarLogApp.git
   git branch -M main
   git push -u origin main
   ```

### Option B: If you don't want to use GitHub

Render can also deploy from a zip file or directly from your local machine. But GitHub is easiest.

---

## 🚀 Step 2: Deploy to Render

1. **Sign up for Render**:
   - Go to: https://render.com
   - Sign up with GitHub (easiest) or email
   - Free tier available!

2. **Create New Web Service**:
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub account (if using GitHub)
   - Select your repository: `CarLogApp`

3. **Configure Your Service**:
   
   **Basic Settings:**
   - **Name**: `carlog-backend` (or any name you like)
   - **Region**: Choose closest to you
   - **Branch**: `main` (or `master`)
   - **Root Directory**: `CarLog/backend` ⚠️ **IMPORTANT**
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

   **Environment Variables** (click "Advanced"):
   - `FLASK_DEBUG`: `false`
   - `PORT`: Leave empty (Render sets this automatically)

4. **Create Web Service**:
   - Click **"Create Web Service"**
   - Render will start building and deploying
   - Takes 5-10 minutes on first deployment

5. **Wait for Deployment**:
   - You'll see build logs
   - When done, you'll get a URL like: `https://carlog-backend-xxxx.onrender.com`

6. **Test Your Backend**:
   - Visit: `https://your-app-name.onrender.com/health`
   - Should return: `{"status": "healthy", "database": "connected"}`

---

## ⚠️ Important Notes for Render

### Database
Render provides a free PostgreSQL database, but your app uses SQLite. Options:

**Option 1: Keep SQLite (Simpler, but data resets on redeploy)**
- SQLite file is stored in Render's filesystem
- Data persists but may reset on some deployments
- Good for demos/testing

**Option 2: Switch to PostgreSQL (Better for production)**
- Render offers free PostgreSQL
- Need to update your database code
- More complex but data persists permanently

**For now, we'll keep SQLite** (easiest for demo).

---

## 🔧 Step 3: Update Frontend Config

Once you have your Render URL:

1. **Edit frontend config**:
   - File: `CarLog/frontend/lib/config/app_config.dart`
   - Change: `static const String apiBaseUrl = 'https://your-app-name.onrender.com';`

2. **Rebuild frontend**:
   ```bash
   cd CarLog/frontend
   flutter build web
   ```

3. **Redeploy to Netlify**:
   - Drag and drop `/build/web` folder to Netlify again

---

## ✅ Step 4: Verify Everything Works

1. **Test backend directly**:
   - Visit: `https://your-app-name.onrender.com/`
   - Should see API info

2. **Test VIN decode**:
   - Visit: `https://your-app-name.onrender.com/api/vehicles/decode-vin/1HGCM82633A004352`
   - Should return vehicle data

3. **Test from phone**:
   - Scan your QR code
   - Try VIN lookup
   - Should work now! 🎉

---

## 🔄 Future Updates

When you update backend code:
1. Push changes to GitHub
2. Render automatically redeploys (if auto-deploy is enabled)
3. Backend updates in 5-10 minutes

When you update frontend code:
1. Update code locally
2. Rebuild: `flutter build web`
3. Redeploy to Netlify

---

## 🆘 Troubleshooting

**Backend won't start:**
- Check build logs in Render dashboard
- Make sure `Root Directory` is set to `CarLog/backend`
- Verify `requirements.txt` is correct

**Frontend can't connect:**
- Check backend URL in `app_config.dart`
- Make sure backend is deployed and running
- Test backend URL directly in browser

**VIN lookup still not working:**
- Check Render logs for errors
- Verify backend endpoint: `/api/vehicles/decode-vin/<vin>`
- Test endpoint directly in browser

---

**Ready to deploy?** Follow the steps above and let me know when you have your Render URL!

