# Emergency Response System

A complete emergency response platform with three portals: User, Ambulance, and Admin.

## 🚀 Quick Start (Local)

### Backend
```bash
python app.py
```
Runs on http://localhost:5000

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on http://localhost:5173

---

## 🌐 Deploy to Production

**Make your app accessible from anywhere!**

See deployment guides:
- **Quick Guide**: [SIMPLE_DEPLOY.md](./SIMPLE_DEPLOY.md) - 15 minutes
- **Detailed Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete instructions
- **Checklist**: [DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md) - Step-by-step checklist

### Recommended Platforms (Both Free):
- **Backend**: Render.com
- **Frontend**: Vercel.com

---

## 📱 Features

### User Portal
- Phone + OTP login
- Request emergency
- Live ambulance tracking
- Hospital selection flow

### Ambulance Portal
- Phone + OTP login
- Accept assignments
- Live location sharing
- Navigate to user/hospital
- Mark completed

### Admin Portal
- Username/password login
- Live map dashboard
- View all requests, users, ambulances
- Track ambulance routes

---

## 🗺️ Map Features

- **Free maps** (Leaflet + OpenStreetMap)
- **Free routing** (OSRM)
- Click-to-select location
- Real-time tracking
- Route visualization (Google Maps style blue)
- Expandable maps

---

## 🔧 Tech Stack

**Backend**:
- Flask
- MongoDB (Atlas)
- JWT Authentication
- Twilio SMS (OTP)

**Frontend**:
- React + Vite
- React Router
- Leaflet Maps
- Axios

---

## 📚 Documentation

- [API Summary](./API_SUMMARY.md) - Backend API endpoints
- [Frontend README](./FRONTEND_README.md) - Frontend setup
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment

---

## 🔒 Security

- JWT tokens for authentication
- CORS protection
- Environment variables for secrets
- HTTPS in production (automatic)

---

## 📞 Support

For deployment help, see:
- [SIMPLE_DEPLOY.md](./SIMPLE_DEPLOY.md) - Quick deployment
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed guide
