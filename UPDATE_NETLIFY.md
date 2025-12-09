# How to Update Netlify After Testing

## ✅ Testing Complete?

Once you've tested locally and confirmed VIN lookup works, follow these steps:

---

## 🚀 Update Netlify (Choose One Method)

### Method 1: Drag & Drop (Easiest)

1. **Open Netlify Dashboard**
   - Go to: https://app.netlify.com
   - Sign in with your account

2. **Find Your Site**
   - Click on **"Sites"** in the top menu
   - Find and click on: **`carlogapp`**

3. **Deploy New Build**
   - Go to the **"Deploys"** tab
   - **Drag and drop** this folder onto the page:
     ```
     /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build/web
     ```
   - OR drag the entire `build` folder

4. **Wait for Deployment**
   - Netlify will show "Deploy in progress..."
   - Takes about 30-60 seconds
   - When it says "Published", you're done!

5. **Test Your Live App**
   - Go to: https://carlogapp.netlify.app/
   - Test VIN lookup - it should work now!

---

### Method 2: Netlify CLI (Faster, If Installed)

```bash
# Navigate to build folder
cd /Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build/web

# Deploy to production
netlify deploy --prod --dir=.
```

If not logged in, run first:
```bash
netlify login
```

---

## ✅ After Deployment

- Your QR code **stays the same** (points to same URL)
- The app at `https://carlogapp.netlify.app/` will have the updated code
- VIN lookups should work for all users scanning the QR code

---

## 📝 Quick Reference

**Build folder location:**
`/Users/ericarmijos/SoftwareEngineering/CarLogApp10.19/CarLog/frontend/build/web`

**Your Netlify site:**
`https://carlogapp.netlify.app/`

**Your QR code:**
Already points to the above URL - no changes needed!

