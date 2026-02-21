# 🚀 Quick Deployment Guide

Deploy your Emergency Response System in **15 minutes**!

## Prerequisites
- GitHub account
- Render account (free): https://render.com
- Vercel account (free): https://vercel.com

---

## Step 1: Push to GitHub (5 min)

```bash
cd emergency_backend
git init
git add .
git commit -m "Ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/emergency-backend.git
git push -u origin main
```

---

## Step 2: Deploy Backend on Render (5 min)

1. **Go to**: https://dashboard.render.com
2. **Click**: "New +" → "Web Service"
3. **Connect**: Your GitHub repo
4. **Settings**:
   - Name: `emergency-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - Plan: **Free**

5. **Environment Variables** (click "Advanced" → "Add Environment Variable"):
   ```
   MONGO_URI=your_mongodb_uri_here
   JWT_SECRET_KEY=change-this-to-random-secure-key-12345
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=change-this-password-12345
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   PORT=10000
   FLASK_DEBUG=False
   FRONTEND_URL=https://your-frontend.vercel.app
   ```
   ⚠️ **Change JWT_SECRET_KEY and ADMIN_PASSWORD to secure values!**

6. **Click**: "Create Web Service"
7. **Wait**: 5-10 minutes for first deployment
8. **Copy Backend URL**: `https://emergency-backend-xxxx.onrender.com`

---

## Step 3: Deploy Frontend on Vercel (5 min)

1. **Go to**: https://vercel.com
2. **Click**: "Add New Project"
3. **Import**: Your GitHub repo
4. **Settings**:
   - Framework Preset: **Vite**
   - Root Directory: `frontend` (if repo has frontend folder)
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

5. **Environment Variables**:
   ```
   VITE_API_URL=https://emergency-backend-xxxx.onrender.com
   ```
   (Use the backend URL from Step 2)

6. **Click**: "Deploy"
7. **Wait**: 2-5 minutes
8. **Copy Frontend URL**: `https://emergency-frontend.vercel.app`

---

## Step 4: Update Backend CORS (1 min)

1. **Go back to**: Render dashboard
2. **Find**: `FRONTEND_URL` environment variable
3. **Update**: Set to your Vercel frontend URL
4. **Save**: Backend will auto-redeploy

---

## ✅ Done!

Your app is now live at:
- **Frontend**: `https://your-frontend.vercel.app`
- **Backend**: `https://your-backend.onrender.com`

**Test it:**
1. Open frontend URL on your phone/computer
2. Try user login (OTP)
3. Try ambulance login (OTP)
4. Try admin login

---

## 🔧 Troubleshooting

**Backend not working?**
- Check Render logs: Dashboard → Your Service → Logs
- Verify MongoDB connection string
- Check all environment variables are set

**Frontend can't connect?**
- Verify `VITE_API_URL` in Vercel matches backend URL
- Check browser console (F12) for errors
- Ensure backend CORS allows frontend URL

**CORS errors?**
- Update `FRONTEND_URL` in Render to match Vercel URL exactly
- Include `https://` and no trailing slash

---

## 📱 Access from Anywhere

Once deployed, share these URLs:
- **Users**: `https://your-frontend.vercel.app`
- **Ambulance Drivers**: Same URL
- **Admin**: Same URL → Admin Portal

Works on:
- ✅ Mobile phones (Android/iOS)
- ✅ Tablets
- ✅ Laptops/Desktops
- ✅ Any network (WiFi, mobile data, etc.)

---

## 🔒 Security Checklist

- [ ] Changed `JWT_SECRET_KEY` to random secure string
- [ ] Changed `ADMIN_PASSWORD` to strong password
- [ ] `.env` file is in `.gitignore` (not committed)
- [ ] Backend uses HTTPS (Render provides this)
- [ ] Frontend uses HTTPS (Vercel provides this)

---

## 💰 Cost

**FREE** on both platforms:
- Render: Free tier (spins down after 15 min inactivity, wakes on request)
- Vercel: Free tier (unlimited requests)

**Upgrade** if you need:
- Always-on backend (Render: $7/month)
- More bandwidth (usually not needed)
