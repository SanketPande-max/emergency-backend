# Deployment Guide - Emergency Response System

Deploy your backend and frontend to make it accessible from any device on any network.

## 🚀 Quick Deploy Options

### Option 1: Render (Backend) + Vercel (Frontend) - **RECOMMENDED** (Free)

### Option 2: Railway (Backend) + Netlify (Frontend) - **ALTERNATIVE** (Free tier)

---

## 📦 Backend Deployment (Render - Free)

### Step 1: Prepare Backend

1. **Create GitHub Repository** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/emergency-backend.git
   git push -u origin main
   ```

2. **Files already created**:
   - ✅ `Procfile` - Tells Render how to run the app
   - ✅ `requirements.txt` - Python dependencies (includes gunicorn)
   - ✅ `runtime.txt` - Python version

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `emergency-backend` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free

5. **Environment Variables** (in Render dashboard):
   ```
   MONGO_URI=your_mongodb_uri_here
   JWT_SECRET_KEY=your-very-secure-random-key-here-change-this
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-admin-password
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   PORT=10000
   FLASK_DEBUG=False
   FRONTEND_URL=https://your-frontend-url.vercel.app
   ```

6. Click **"Create Web Service"**
7. Wait for deployment (5-10 minutes)
8. **Copy your backend URL**: `https://emergency-backend.onrender.com` (or similar)

---

## 🎨 Frontend Deployment (Vercel - Free)

### Step 1: Prepare Frontend

1. **Update Frontend API URL**:
   - Create `frontend/.env.production`:
   ```
   VITE_API_URL=https://your-backend-url.onrender.com
   ```

2. **Update Vite Config** (already done - proxy only for dev)

### Step 2: Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click **"Add New Project"**
3. Import your GitHub repository (select the `frontend` folder or entire repo)
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` (if deploying from root repo)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

5. **Environment Variables**:
   ```
   VITE_API_URL=https://your-backend-url.onrender.com
   ```

6. Click **"Deploy"**
7. Wait for deployment (2-5 minutes)
8. **Copy your frontend URL**: `https://emergency-frontend.vercel.app` (or similar)

### Step 3: Update Backend CORS

1. Go back to Render dashboard
2. Update environment variable:
   ```
   FRONTEND_URL=https://your-frontend-url.vercel.app
   ```
3. Redeploy (or it auto-redeploys)

---

## 🔄 Alternative: Railway (Backend) + Netlify (Frontend)

### Railway Backend:

1. Go to [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub**
3. Select your repo
4. Railway auto-detects Python
5. Add environment variables (same as Render)
6. Deploy

### Netlify Frontend:

1. Go to [netlify.com](https://netlify.com)
2. **Add new site** → **Import from Git**
3. Select repo, set:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
4. Add environment variable: `VITE_API_URL=https://your-backend.railway.app`
5. Deploy

---

## ✅ Post-Deployment Checklist

- [ ] Backend is accessible: `https://your-backend.onrender.com/` (should show health check)
- [ ] Frontend is accessible: `https://your-frontend.vercel.app`
- [ ] Frontend can call backend API (check browser console)
- [ ] Test user login (OTP)
- [ ] Test ambulance login (OTP)
- [ ] Test admin login
- [ ] Update `FRONTEND_URL` in backend env vars

---

## 🔒 Security Notes

1. **Change JWT_SECRET_KEY** to a random secure string
2. **Change ADMIN_PASSWORD** to a strong password
3. **Never commit `.env` files** to Git
4. **Use HTTPS** (Render/Vercel provide this automatically)

---

## 📱 Access from Any Device

Once deployed:
- **Desktop**: Open `https://your-frontend.vercel.app` in browser
- **Mobile**: Open same URL in mobile browser
- **Any Network**: Works on WiFi, mobile data, etc.

---

## 🐛 Troubleshooting

**Backend not starting?**
- Check Render logs
- Verify all environment variables are set
- Check MongoDB connection string

**Frontend can't connect to backend?**
- Verify `VITE_API_URL` is correct
- Check CORS settings in backend
- Check browser console for errors

**CORS errors?**
- Update `FRONTEND_URL` in backend env vars
- Restart backend service

---

## 📞 Support

If deployment fails, check:
1. Render/Vercel logs
2. Environment variables are correct
3. Build commands are correct
4. Dependencies are in requirements.txt/package.json
