# 🚀 Simple Deployment - 3 Steps

Deploy your Emergency Response System in **15 minutes**!

---

## 📦 Step 1: Push to GitHub

```bash
# In your project folder
git init
git add .
git commit -m "Ready to deploy"
git branch -M main
git remote add origin https://github.com/SanketPande-max/emergency-backend.git
git push -u origin main
```

**Replace `YOUR_USERNAME` with your GitHub username**

---

## 🔧 Step 2: Deploy Backend (Render)

1. **Go to**: https://render.com → Sign up (free)

2. **Click**: "New +" → "Web Service"

3. **Connect**: Your GitHub account → Select `emergency-backend` repo

4. **Fill in**:
   ```
   Name: emergency-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app --bind 0.0.0.0:$PORT
   Plan: Free
   ```

5. **Add Environment Variables** (click "Advanced"):
   ```
   MONGO_URI=your_mongodb_uri_here
   JWT_SECRET_KEY=CHANGE-THIS-TO-RANDOM-SECURE-KEY-123456789
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=CHANGE-THIS-PASSWORD-123456
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   PORT=10000
   FLASK_DEBUG=False
   FRONTEND_URL=https://your-frontend.vercel.app
   ```
   ⚠️ **Change JWT_SECRET_KEY and ADMIN_PASSWORD!**

6. **Click**: "Create Web Service"

7. **Wait**: 5-10 minutes

8. **Copy Backend URL**: `https://emergency-backend-xxxx.onrender.com`

---

## 🎨 Step 3: Deploy Frontend (Vercel)

1. **Go to**: https://vercel.com → Sign up (free)

2. **Click**: "Add New Project"

3. **Import**: Your GitHub repo → Select `emergency-backend` repo

4. **Configure**:
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   ```

5. **Add Environment Variable**:
   ```
   VITE_API_URL=https://emergency-backend-xxxx.onrender.com
   ```
   (Use your Render backend URL from Step 2)

6. **Click**: "Deploy"

7. **Wait**: 2-5 minutes

8. **Copy Frontend URL**: `https://emergency-frontend.vercel.app`

9. **Go back to Render** → Update `FRONTEND_URL` = Your Vercel URL

---

## ✅ Done!

**Your app is live at**: `https://your-frontend.vercel.app`

**Test it**:
- Open URL on your phone
- Open URL on your laptop
- Works from anywhere!

---

## 🔒 Important Security

**Before going live, change**:
1. `JWT_SECRET_KEY` → Use: https://randomkeygen.com/
2. `ADMIN_PASSWORD` → Use a strong password

---

## 🆘 Need Help?

- **Backend not starting?** → Check Render logs
- **Frontend can't connect?** → Check `VITE_API_URL` matches backend URL
- **CORS errors?** → Update `FRONTEND_URL` in Render

---

## 📱 Share Your App

Once deployed, share the frontend URL with:
- Users (for emergency requests)
- Ambulance drivers
- Admin staff

**It works on all devices, all networks!** 🌍
