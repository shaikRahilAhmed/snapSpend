# Fix Vercel Build Error

## Problem
Vercel says "Missing script: build" even though package.json has the build script.

## Solution

### Option 1: Configure in Vercel Dashboard (Recommended)

1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **General**
4. Scroll to **Build & Development Settings**
5. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `./` (leave empty or set to root)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

6. Click **Save**
7. Go to **Deployments** → Click **Redeploy**

### Option 2: Delete and Re-import Project

If Option 1 doesn't work:

1. Go to Vercel Dashboard
2. Select your project
3. Go to **Settings** → **General**
4. Scroll to bottom → Click **Delete Project**
5. Confirm deletion
6. Go back to dashboard → Click **Add New...** → **Project**
7. Import your GitHub repo again
8. Vercel will auto-detect Vite
9. Add environment variables
10. Deploy

### Option 3: Use vercel.json Override

Update `vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/app"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Then:
```bash
git add vercel.json
git commit -m "Add explicit build command"
git push origin main
```

## Why This Happens

Vercel might be:
1. Using cached configuration
2. Looking in wrong directory
3. Not detecting Vite framework

## Quick Test

Try deploying manually:
```bash
npm install -g vercel
vercel --prod
```

This will deploy from your local machine and show any errors.

## Still Not Working?

Share your Vercel project URL and I'll check the settings directly.
