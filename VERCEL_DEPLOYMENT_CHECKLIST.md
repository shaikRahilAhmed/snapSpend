# Vercel Deployment Checklist - Fix CSV & AI Chat

## ❌ Problem
CSV upload and AI chat work on localhost but not on Vercel deployment.

## 🔍 Root Causes

### 1. Missing Environment Variables
Vercel needs ALL these variables set:

| Variable | Value | Status |
|----------|-------|--------|
| `VITE_SUPABASE_URL` | `https://xxpzxhmekuxhhzyxdsht.supabase.co` | ❓ Check |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | ❓ Check |
| `GEMINI_API_KEY` | `AIzaSyARp70LwbgR4wpVqv4wLImtPgduDwHc62M` | ❓ Check |
| `VITE_API_URL` | (empty) | ❓ Check |

### 2. Frontend Not Using API Helper
The frontend is calling API directly without auth tokens.

### 3. Supabase Database Not Set Up
The `transactions` table might not exist in Supabase.

---

## ✅ Fix Steps

### Step 1: Verify Vercel Environment Variables

1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Verify ALL 4 variables are set
5. Make sure they're applied to **Production**, **Preview**, AND **Development**

**If missing, add them now!**

### Step 2: Set Up Supabase Database

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **SQL Editor**
4. Run this SQL:

```sql
-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  description TEXT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  category VARCHAR(50),
  transaction_type VARCHAR(10) CHECK (transaction_type IN ('DR', 'CR')),
  categorization_method VARCHAR(20) DEFAULT 'rule_based',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own transactions" ON transactions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own transactions" ON transactions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own transactions" ON transactions
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own transactions" ON transactions
  FOR DELETE USING (auth.uid() = user_id);
```

### Step 3: Update Frontend to Use Auth

The frontend needs to send auth tokens. Update these files:

#### Option A: Quick Fix (Without Supabase Auth)

Update `api/app.py` to NOT require auth for testing:

```python
def get_user_from_token(auth_header):
    """Extract user from Authorization header"""
    # For testing without auth, return a dummy user ID
    return "test-user-123"
    
    # Uncomment below for production with auth
    # if not auth_header or not auth_header.startswith('Bearer '):
    #     return None
    # token = auth_header.replace('Bearer ', '')
    # try:
    #     user = supabase.auth.get_user(token)
    #     return user.user.id if user and user.user else None
    # except:
    #     return None
```

#### Option B: Full Fix (With Supabase Auth)

Update `src/pages/TransactionAnalyzer.tsx`:

```typescript
import { supabase } from "@/integrations/supabase/client";

const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;
  
  setLoading(true);
  
  try {
    // Get auth token
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.access_token) {
      toast.error("Please login first");
      return;
    }
    
    const formData = new FormData();
    formData.append("csvFile", file);
    
    const apiUrl = import.meta.env.VITE_API_URL || "";
    const response = await fetch(`${apiUrl}/api/analyze-transactions`, {
      method: "POST",
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      },
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Upload failed');
    }
    
    const result = await response.json();
    setData(result);
    toast.success("CSV uploaded successfully!");
  } catch (error: any) {
    toast.error(error.message || "Upload failed");
  } finally {
    setLoading(false);
  }
};
```

### Step 4: Redeploy to Vercel

```bash
git add .
git commit -m "Fix Vercel deployment with auth"
git push origin main
```

Vercel will auto-deploy in 2-3 minutes.

---

## 🧪 Testing After Deployment

### Test 1: Check Environment Variables
```bash
# Visit your Vercel URL
https://your-app.vercel.app/api/hello

# Should return:
{"message": "Hello from Python Flask server! 🐍"}
```

### Test 2: Check Supabase Connection
1. Login to your app
2. Open browser console (F12)
3. Check for any Supabase errors

### Test 3: Upload CSV
1. Login
2. Go to Transaction Analyzer
3. Upload a CSV file
4. Check browser console for errors
5. Check Vercel function logs

### Test 4: AI Chat
1. After uploading CSV
2. Go to AI Chat
3. Ask a question
4. Should get a response

---

## 🐛 Debugging

### Check Vercel Logs

1. Go to Vercel Dashboard
2. Select your project
3. Click **Functions**
4. Click on `/api/app`
5. View logs for errors

### Common Errors

**Error: "Unauthorized"**
- User not logged in
- Auth token not sent
- Use Option A (dummy user) for testing

**Error: "Supabase connection failed"**
- Environment variables not set
- Check `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`

**Error: "Gemini API error"**
- `GEMINI_API_KEY` not set or invalid
- Check the key in Vercel environment variables

**Error: "Table doesn't exist"**
- Run the SQL in Step 2
- Check Supabase Table Editor

---

## 🎯 Quick Test Without Auth

For quick testing, update `api/app.py`:

```python
def get_user_from_token(auth_header):
    # Return dummy user for testing
    return "test-user-123"
```

Then:
```bash
git add api/app.py
git commit -m "Disable auth for testing"
git push origin main
```

This will let you test CSV upload and AI chat without login.

---

## ✅ Final Checklist

Before testing:
- [ ] All 4 environment variables set in Vercel
- [ ] Supabase `transactions` table created
- [ ] RLS policies created
- [ ] Code pushed to GitHub
- [ ] Vercel deployment succeeded
- [ ] Checked Vercel function logs

After deployment works:
- [ ] CSV upload works
- [ ] AI chat works
- [ ] Data persists after refresh
- [ ] Multiple users have separate data

---

## 💡 Pro Tip

If you want to test quickly without auth:
1. Use Option A (dummy user)
2. Test CSV and AI chat
3. Once working, implement Option B (full auth)

This way you can verify the backend works before adding auth complexity.

---

## 📞 Still Not Working?

Share:
1. Your Vercel URL
2. Browser console errors (F12)
3. Vercel function logs
4. Which step failed

I'll help debug further!
