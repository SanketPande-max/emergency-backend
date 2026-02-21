# ✅ Deployment Checklist

Follow these steps to deploy your Emergency Response System.

---

## 📝 Pre-Deployment

- [ ] Code is working locally
- [ ] All features tested
- [ ] `.env` file is in `.gitignore`
- [ ] No sensitive data in code

---

## 🔧 Step 1: Backend (Render)

### A. Push to GitHub
```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/emergency-backend.git
git push -u origin main
```

### B. Deploy on Render
- [ ] Go to https://render.com → Sign up/Login
- [ ] New + → Web Service
- [ ] Connect GitHub repo
- [ ] Settings:
  - Name: `emergency-backend`
  - Environment: `Python 3`
  - Build: `pip install -r requirements.txt`
  - Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
  - Plan: **Free**

### C. Environment Variables (Render)
- [ ] `MONGO_URI` = Your MongoDB connection string
- [ ] `JWT_SECRET_KEY` = **CHANGE THIS** (use randomkeygen.com)
- [ ] `ADMIN_USERNAME` = admin (or change)
- [ ] `ADMIN_PASSWORD` = **CHANGE THIS** (strong password)
- [ ] `TWILIO_ACCOUNT_SID` = Your Twilio SID
- [ ] `TWILIO_AUTH_TOKEN` = Your Twilio token
- [ ] `TWILIO_PHONE_NUMBER` = Your Twilio number
- [ ] `PORT` = 10000
- [ ] `FLASK_DEBUG` = False
- [ ] `FRONTEND_URL` = (leave empty for now, update after frontend deploy)

### D. Deploy
- [ ] Click "Create Web Service"
- [ ] Wait 5-10 minutes
- [ ] Copy backend URL: `https://xxxx.onrender.com`
- [ ] Test: Open URL in browser (should show health check JSON)

---

## 🎨 Step 2: Frontend (Vercel)

### A. Deploy on Vercel
- [ ] Go to https://vercel.com → Sign up/Login
- [ ] Add New Project
- [ ] Import GitHub repo
- [ ] Settings:
  - Framework: **Vite**
  - Root Directory: `frontend`
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - Install: `npm install`

### B. Environment Variables (Vercel)
- [ ] `VITE_API_URL` = Your Render backend URL (from Step 1)

### C. Deploy
- [ ] Click "Deploy"
- [ ] Wait 2-5 minutes
- [ ] Copy frontend URL: `https://xxxx.vercel.app`
- [ ] Test: Open URL in browser

---

## 🔗 Step 3: Connect Frontend & Backend

- [ ] Go back to Render dashboard
- [ ] Update `FRONTEND_URL` = Your Vercel frontend URL
- [ ] Save (backend will auto-redeploy)
- [ ] Wait 2-3 minutes

---

## ✅ Step 4: Test Everything

- [ ] Open frontend URL on **desktop**
- [ ] Open frontend URL on **mobile phone**
- [ ] Test User Portal: Login with phone + OTP
- [ ] Test Ambulance Portal: Login with phone + OTP  
- [ ] Test Admin Portal: Login with username/password
- [ ] Test emergency request flow
- [ ] Test hospital selection
- [ ] Test map features

---

## 🔒 Security

- [ ] Changed `JWT_SECRET_KEY` to secure random string
- [ ] Changed `ADMIN_PASSWORD` to strong password
- [ ] Verified `.env` is NOT in Git
- [ ] Backend uses HTTPS (Render provides)
- [ ] Frontend uses HTTPS (Vercel provides)

---

## 📱 Share Your App

Your app is now live! Share the frontend URL:
- **Users**: `https://your-frontend.vercel.app`
- **Ambulance Drivers**: Same URL
- **Admin**: Same URL → Admin Portal

---

## 🆘 If Something Fails

1. **Check Logs**:
   - Render: Dashboard → Service → Logs
   - Vercel: Dashboard → Project → Deployments → Logs

2. **Common Issues**:
   - Backend not starting → Check environment variables
   - Frontend can't connect → Check `VITE_API_URL`
   - CORS errors → Update `FRONTEND_URL` in backend

3. **Test Locally First**:
   ```bash
   # Backend
   python app.py
   
   # Frontend (new terminal)
   cd frontend
   npm run dev
   ```

---

## 🎉 Done!

Your Emergency Response System is now accessible from anywhere in the world!
