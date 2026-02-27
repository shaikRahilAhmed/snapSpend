# Deploy Everything to Vercel (Easiest!)

## ✅ Advantages
- **One Platform**: Frontend + Backend on Vercel
- **Same Domain**: No CORS issues
- **Free Tier**: Generous limits
- **Auto Deploy**: Push to GitHub = instant deploy
- **Fast**: Edge network worldwide

## 📦 What I've Set Up

1. **`api/app.py`** - Simplified Flask backend as Vercel serverless function
2. **`api/requirements.txt`** - Python dependencies
3. **`vercel.json`** - Configuration for both frontend and backend
4. **`.env.production`** - Empty API URL (uses same domain)

---

## 🚀 Deployment Steps

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Setup Vercel deployment"
git push origin main
```

### Step 2: Deploy to Vercel
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Add New..." → "Project"
4. Select your repository
5. Configure:
   - **Framework Preset**: Vite (auto-detected)
   - **Root Directory**: `./`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### Step 3: Add Environment Variable
In Vercel project settings → Environment Variables:
- **Key**: `GEMINI_API_KEY`
- **Value**: `AIzaSyDYWUZQL5vAvb9rrK1FQbB9UWz_ffd9O34`
- **Environment**: Production, Preview, Development

### Step 4: Deploy!
Click "Deploy" and wait 2-3 minutes

---

## 🌐 How It Works

### URL Structure
```
https://your-project.vercel.app/          → Frontend (React)
https://your-project.vercel.app/api/hello → Backend (Python)
```

### API Routes
All backend routes are under `/api/`:
- `GET  /api/hello`
- `POST /api/analyze-transactions`
- `POST /api/ask-question`
- `GET  /api/check-data`

### Frontend API Calls
The frontend automatically uses the same domain:
```typescript
const apiUrl = import.meta.env.VITE_API_URL || "";
// Calls /api/analyze-transactions on same domain
```

---

## 🧪 Testing After Deployment

### Test Backend
```bash
curl https://your-project.vercel.app/api/hello
```

Expected response:
```json
{"message": "Hello from Python Flask server! 🐍"}
```

### Test Frontend
Open `https://your-project.vercel.app` in browser

---

## ⚙️ Configuration Details

### vercel.json
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/app.py"  // Routes /api/* to Python
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"  // Routes everything else to React
    }
  ],
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11"  // Python version
    }
  }
}
```

### .env.production
```env
VITE_API_URL=
# Empty = uses same domain (no CORS issues!)
```

---

## 🔄 Updates & Redeployment

### Automatic
Just push to GitHub:
```bash
git add .
git commit -m "Update feature"
git push origin main
```
Vercel auto-deploys in 1-2 minutes!

### Manual
Vercel Dashboard → Your Project → Deployments → Redeploy

---

## 📊 Vercel Free Tier Limits

| Resource | Limit |
|----------|-------|
| Bandwidth | 100 GB/month |
| Serverless Function Execution | 100 GB-hours/month |
| Serverless Function Duration | 10 seconds max |
| Build Time | 6000 minutes/month |
| Deployments | Unlimited |

**Perfect for your app!** ✅

---

## ⚠️ Important Notes

### Serverless Limitations
- **Stateless**: Each request is independent
- **Cold Starts**: First request may be slow (1-2 seconds)
- **No Persistent Storage**: Data resets between requests
- **10 Second Timeout**: Long operations may fail

### Data Storage
The in-memory storage (`stored_transactions_df`) works but:
- Data persists only during function execution
- Resets on cold start
- Users need to re-upload CSV if function restarts

**Solution for Production**: Add a database (Supabase, MongoDB Atlas, etc.)

---

## 🆚 Vercel vs Render

| Feature | Vercel (All-in-One) | Render (Separate) |
|---------|---------------------|-------------------|
| Setup | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐⭐ Moderate |
| Speed | ⚡ Very Fast | ⚡ Fast |
| Free Tier | 100GB bandwidth | Backend sleeps |
| CORS | ✅ No issues | ⚠️ Need config |
| Persistent Data | ❌ Serverless | ✅ Always-on |
| Cost | $0/month | $0 or $7/month |

**Recommendation**: 
- **Vercel** for quick demo/testing
- **Render** for production with persistent data

---

## 🐛 Troubleshooting

### Backend Not Working
1. Check Vercel Functions logs
2. Verify `GEMINI_API_KEY` is set
3. Check `api/app.py` exists
4. Verify `vercel.json` rewrites

### Frontend Not Loading
1. Check build logs
2. Verify `npm run build` works locally
3. Check browser console for errors

### CORS Errors
Should not happen! Backend is on same domain.

### CSV Upload Fails
1. Check file size (< 4.5MB for Vercel)
2. Check function timeout (< 10 seconds)
3. For large files, use Render instead

---

## 🎯 Next Steps

1. ✅ Deploy to Vercel
2. ✅ Test all features
3. ✅ Share your live URL!
4. 🔄 (Optional) Add database for persistence
5. 📈 (Optional) Upgrade to Pro for more limits

---

## 💡 Pro Tips

### Custom Domain
Vercel Dashboard → Settings → Domains → Add your domain

### Environment Variables
Add different values for:
- Production
- Preview (for testing)
- Development

### Analytics
Vercel Dashboard → Analytics → View traffic

### Logs
Vercel Dashboard → Functions → View logs

---

## 🚀 Deploy Now!

```bash
# 1. Commit changes
git add .
git commit -m "Deploy to Vercel"
git push origin main

# 2. Go to vercel.com and import your repo

# 3. Add GEMINI_API_KEY environment variable

# 4. Deploy!
```

That's it! Your app will be live in 2-3 minutes! 🎉
