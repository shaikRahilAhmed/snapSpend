# Vercel Environment Variables Setup

## ✅ Required Environment Variables

Add these in Vercel Dashboard → Settings → Environment Variables:

### 1. Supabase Configuration

| Variable Name | Value | Where to Find |
|---------------|-------|---------------|
| `VITE_SUPABASE_URL` | `https://xxpzxhmekuxhhzyxdsht.supabase.co` | Supabase Dashboard → Settings → API |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4cHp4aG1la3V4aGh6eXhkc2h0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIxOTA2NjIsImV4cCI6MjA4Nzc2NjY2Mn0.sbXluBvZASjw6Nq8hOROAM_S1VwubIEDOcQx8O8PnFc` | Supabase Dashboard → Settings → API → anon public |

### 2. Gemini AI Configuration

| Variable Name | Value |
|---------------|-------|
| `GEMINI_API_KEY` | `AIzaSyARp70LwbgR4wpVqv4wLImtPgduDwHc62M` |

### 3. API URL (Optional)

| Variable Name | Value |
|---------------|-------|
| `VITE_API_URL` | Leave empty or don't add |

---

## 📝 Step-by-Step Instructions

### Step 1: Go to Vercel Dashboard

1. Visit https://vercel.com/dashboard
2. Select your `snapSpend` project
3. Click **Settings** (top navigation)
4. Click **Environment Variables** (left sidebar)

### Step 2: Add Each Variable

For each variable above:

1. Click **Add New**
2. **Key**: Enter the variable name (e.g., `VITE_SUPABASE_URL`)
3. **Value**: Paste the value
4. **Environments**: Select ALL three:
   - ✅ Production
   - ✅ Preview
   - ✅ Development
5. Click **Save**

### Step 3: Redeploy

After adding all variables:

1. Go to **Deployments** tab
2. Click the three dots (...) on the latest deployment
3. Click **Redeploy**
4. Wait 2-3 minutes

---

## 🔐 Why Authentication Will Work

### Current Setup (Localhost)
```
Frontend → Supabase Auth → Get Token → Send to Backend
```

### After Vercel Deployment
```
Frontend (Vercel) → Supabase Auth → Get Token → Send to Backend (Vercel)
```

The flow is identical! The environment variables tell your app:
- Where Supabase is (`VITE_SUPABASE_URL`)
- How to authenticate (`VITE_SUPABASE_PUBLISHABLE_KEY`)
- Where the AI service is (`GEMINI_API_KEY`)

---

## 🧪 Testing Authentication After Deployment

### Test 1: Sign Up
1. Go to your Vercel URL: `https://your-app.vercel.app`
2. Click "Sign Up"
3. Enter email and password
4. Should create account ✅

### Test 2: Login
1. Click "Login"
2. Enter credentials
3. Should redirect to dashboard ✅

### Test 3: Upload CSV
1. After login, go to Transaction Analyzer
2. Upload a CSV file
3. Should save to Supabase with your user_id ✅

### Test 4: AI Chat
1. Go to AI Chat
2. Ask a question
3. Should get personalized response based on your data ✅

### Test 5: User Isolation
1. Logout
2. Create a new account (different email)
3. Upload different CSV
4. Should see only new user's data ✅
5. Login with first account again
6. Should see only first user's data ✅

---

## 🐛 Troubleshooting

### "Supabase URL not found"
- Check if `VITE_SUPABASE_URL` is added
- Make sure it's applied to Production environment
- Redeploy after adding

### "Invalid API key"
- Check if `VITE_SUPABASE_PUBLISHABLE_KEY` is correct
- Copy the full key (it's very long)
- Make sure no extra spaces

### "Authentication failed"
- Check Supabase Dashboard → Authentication → Settings
- Make sure "Enable Email Signup" is ON
- Check "Site URL" includes your Vercel domain

### "CSV upload fails"
- Make sure you ran the SQL setup in Supabase
- Check if `transactions` table exists
- Verify RLS policies are enabled

---

## 🎯 Quick Checklist

Before testing:
- [ ] Added `VITE_SUPABASE_URL`
- [ ] Added `VITE_SUPABASE_PUBLISHABLE_KEY`
- [ ] Added `GEMINI_API_KEY`
- [ ] Applied to Production, Preview, Development
- [ ] Redeployed the project
- [ ] Ran SQL setup in Supabase
- [ ] Verified `transactions` table exists

After deployment:
- [ ] Can sign up
- [ ] Can login
- [ ] Can upload CSV
- [ ] CSV data saves to Supabase
- [ ] AI chat works
- [ ] Different users see different data

---

## 💡 Pro Tips

### 1. Check Environment Variables
After deployment, verify they're loaded:
```
https://your-app.vercel.app/api/hello
```
Should return: `{"message": "Hello from Python Flask server! 🐍"}`

### 2. Check Supabase Connection
Open browser console (F12) and check for errors.
Should see no Supabase connection errors.

### 3. Test with Multiple Accounts
Create 2-3 test accounts to verify user isolation works.

### 4. Monitor Vercel Logs
Go to Vercel Dashboard → Functions → View Logs
Check for any errors during CSV upload or AI chat.

---

## 🚀 Your Environment Variables

Copy these exactly:

```env
VITE_SUPABASE_URL=https://xxpzxhmekuxhhzyxdsht.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4cHp4aG1la3V4aGh6eXhkc2h0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIxOTA2NjIsImV4cCI6MjA4Nzc2NjY2Mn0.sbXluBvZASjw6Nq8hOROAM_S1VwubIEDOcQx8O8PnFc
GEMINI_API_KEY=AIzaSyARp70LwbgR4wpVqv4wLImtPgduDwHc62M
```

---

## ✅ Expected Result

After adding these variables and redeploying:

1. ✅ Users can sign up and login
2. ✅ Each user's CSV data is stored separately in Supabase
3. ✅ AI chat provides personalized responses
4. ✅ Data persists across sessions
5. ✅ Multiple users can use the app simultaneously
6. ✅ Each user only sees their own data

Authentication will work perfectly! 🎉
