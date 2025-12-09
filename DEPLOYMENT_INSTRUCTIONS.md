# CarLog Web App Deployment Instructions

## ✅ Step 1: Build Complete
The Flutter web build is ready at: `/CarLog/frontend/build/web`

---

## 🌐 Step 2: Host on Netlify (Simplest Method - Drag & Drop)

### Option A: Netlify Drag-and-Drop (Recommended - No account needed for demo)

1. **Go to Netlify Drop**: https://app.netlify.com/drop
   - No account needed for basic hosting
   - Just drag and drop your folder

2. **Drag the build folder**:
   - Navigate to: `/Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build/web`
   - Drag the entire `web` folder onto the Netlify Drop page
   - Or zip it first: `cd build && zip -r web.zip web/` then drag the zip

3. **Get your URL**:
   - Netlify will immediately give you a public URL (e.g., `https://random-name-123.netlify.app`)
   - Copy this URL - you'll need it for the QR code!

4. **Note**: If you need a custom domain later, you can sign up for a free Netlify account.

---

## 🔥 Alternative: Firebase Hosting (Requires Firebase account)

1. **Install Firebase CLI** (if not installed):
   ```bash
   npm install -g firebase-tools
   ```

2. **Login to Firebase**:
   ```bash
   firebase login
   ```

3. **Initialize Firebase** (from project root):
   ```bash
   cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19
   firebase init hosting
   ```
   - Select: "Use an existing project" or "Create a new project"
   - Public directory: `CarLog/frontend/build/web`
   - Single-page app: Yes
   - Overwrite index.html: No

4. **Deploy**:
   ```bash
   firebase deploy --only hosting
   ```

5. **Get your URL**: `https://your-project-id.web.app` or `.firebaseapp.com`

---

## 📄 Alternative: GitHub Pages (Requires GitHub account)

1. **Create a new GitHub repository** (or use existing)

2. **Copy build files**:
   ```bash
   cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build
   cp -r web/* /path/to/github-repo/
   ```

3. **Push to GitHub**:
   ```bash
   cd /path/to/github-repo
   git init
   git add .
   git commit -m "Deploy CarLog web app"
   git branch -M main
   git remote add origin https://github.com/yourusername/yourrepo.git
   git push -u origin main
   ```

4. **Enable GitHub Pages**:
   - Go to repository Settings → Pages
   - Source: Deploy from a branch → main branch
   - Your URL: `https://yourusername.github.io/yourrepo/`

---

## ⚠️ IMPORTANT: Backend Configuration

Your app currently connects to: `http://127.0.0.1:5000`

**For a public demo, you have 2 options:**

### Option 1: Deploy Backend to Cloud
Deploy your Flask backend to:
- **Render**: https://render.com (free tier available)
- **Railway**: https://railway.app (free tier)
- **Heroku**: https://heroku.com (paid after free tier ended)

Then update `app_config.dart` (but you said no code changes, so you may need to rebuild after changing the URL).

### Option 2: Use ngrok (Quick Demo Solution)
Expose your local backend temporarily:

1. **Install ngrok**: https://ngrok.com/download
2. **Start your backend**: `cd backend && python app.py`
3. **Create tunnel**: `ngrok http 5000`
4. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)
5. **Update app_config.dart** to use the ngrok URL
6. **Rebuild**: `flutter build web`
7. **Redeploy** the web folder

---

## 📱 Step 3: Generate QR Code

Once you have your public URL, I'll generate a QR code for you!

Send me your deployed URL and I'll create the QR code.

---

## 🎯 Recommended Quick Path for Demo:

1. **Use Netlify Drop** (2 minutes)
   - Go to https://app.netlify.com/drop
   - Drag `/CarLog/frontend/build/web` folder
   - Get instant URL

2. **Use ngrok for backend** (if demo is today)
   - Install ngrok
   - Run: `ngrok http 5000`
   - Note: Free ngrok URLs change each time, paid plans get permanent URLs

3. **Generate QR code** with your Netlify URL + ngrok backend URL (if using ngrok)

---

**Your build folder is ready at:**
`/Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build/web`

