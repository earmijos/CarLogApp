# How to Update Your Deployed App

## 🔄 Current Setup: Manual Deployment (Drag & Drop)

**Changes are NOT automatic** - you need to manually rebuild and redeploy.

---

## 📝 How to Update Your App After Making Changes:

### Step 1: Make Your Code Changes
- Edit your Flutter code in `/CarLog/frontend/lib/`
- Or edit backend code in `/CarLog/backend/`

### Step 2: Rebuild the Web App
```bash
cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend
flutter build web
```

### Step 3: Redeploy to Netlify

**Option A: Drag & Drop Again (Same as before)**
1. Go to https://app.netlify.com
2. Sign in to your account
3. Find your site: `carlogapp`
4. Click on it
5. Go to **"Deploys"** tab
6. Drag and drop the `/build/web` folder again
   - Or drag the entire `build` folder
   - Netlify will overwrite the old deployment

**Option B: Use Netlify CLI (Faster)**
```bash
# Install Netlify CLI (one time)
npm install -g netlify-cli

# Login (one time)
netlify login

# Deploy from build folder
cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build/web
netlify deploy --prod --dir=.
```

**Option C: Link Your Site (One-Time Setup)**
```bash
cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build/web
netlify link
# Follow prompts to link to your carlogapp site
# Then deploy:
netlify deploy --prod --dir=.
```

---

## ⚡ Setting Up Automatic Deployments (Recommended)

For automatic updates, connect your code to Git and Netlify:

### Option 1: GitHub + Netlify (Most Popular)

1. **Push your code to GitHub**:
   ```bash
   cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19
   git init
   git add .
   git commit -m "Initial commit"
   # Create a new repo on GitHub, then:
   git remote add origin https://github.com/yourusername/CarLogApp.git
   git push -u origin main
   ```

2. **Connect GitHub to Netlify**:
   - Go to https://app.netlify.com
   - Click **"Add new site"** → **"Import an existing project"**
   - Choose **"Deploy with GitHub"**
   - Authorize Netlify to access GitHub
   - Select your `CarLogApp` repository

3. **Configure Build Settings**:
   - **Base directory**: `CarLog/frontend`
   - **Build command**: `flutter build web`
   - **Publish directory**: `build/web`
   - Click **"Deploy site"**

4. **How It Works**:
   - Every time you push to GitHub, Netlify automatically:
     - Runs `flutter build web`
     - Deploys the new build
     - Your site updates in 2-3 minutes

### Option 2: GitLab / Bitbucket
Same process, but select GitLab or Bitbucket instead of GitHub.

---

## 🎯 Quick Reference

### Manual Update (Current Method):
```bash
# 1. Make code changes
# 2. Rebuild
cd CarLog/frontend && flutter build web

# 3. Drag & drop /build/web to Netlify
# OR use CLI:
cd build/web && netlify deploy --prod --dir=.
```

### Automatic Update (After Git Setup):
```bash
# 1. Make code changes
# 2. Commit and push
git add .
git commit -m "Your changes"
git push

# 3. Netlify automatically builds and deploys!
```

---

## 📋 Summary

**Right Now (Manual)**:
- ❌ Changes do NOT automatically update
- ✅ You control when to deploy
- ⏱️ Takes 2-5 minutes to update manually

**With Git Setup (Automatic)**:
- ✅ Every git push = automatic deployment
- ✅ Built automatically by Netlify
- ⏱️ Updates in 2-3 minutes after pushing code
- ✅ Build logs and deployment history

---

## 🔧 Important Notes

1. **Backend Changes**: If you change backend code, you need to:
   - Update your backend deployment (if deployed separately)
   - OR restart your local backend if using ngrok

2. **Frontend Config Changes**: If you change `app_config.dart`:
   - Must rebuild: `flutter build web`
   - Must redeploy the new build

3. **Database Changes**: Backend database changes don't affect frontend build, but make sure your backend API matches what the frontend expects.

