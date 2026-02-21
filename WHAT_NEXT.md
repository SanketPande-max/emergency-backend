# What to Do Next – Emergency Response System

Your backend is running and connected to MongoDB. Here’s a clear path for what to do next.

---

## 1. Test the API (Do This First)

Use **Postman**, **Thunder Client** (VS Code), or **curl** to hit the endpoints.

### Quick test flow

**1. User – Send OTP**
```
POST http://localhost:5000/user/send-otp
Content-Type: application/json

{
  "phone": "9876543210"
}
```
→ Response includes a 6-digit OTP (for testing; remove in production).

**2. User – Verify OTP**
```
POST http://localhost:5000/user/verify-otp
Content-Type: application/json

{
  "phone": "9876543210",
  "otp": "<OTP from step 1>"
}
```
→ Returns `token` and `user_id`. Save the token.

**3. User – Update profile (use token in header)**
```
POST http://localhost:5000/user/update-profile
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "age": 30,
  "lat": 28.6139,
  "lng": 77.2090
}
```

**4. User – Request emergency**
```
POST http://localhost:5000/user/request-emergency
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "lat": 28.6139,
  "lng": 77.2090
}
```
→ Returns `request_id`. Note it for admin assignment.

**5. Ambulance – Register**
```
POST http://localhost:5000/ambulance/register
Content-Type: application/json

{
  "driver_name": "Driver One",
  "phone": "1111111111",
  "vehicle_number": "AMB001",
  "password": "ambulance123"
}
```

**6. Ambulance – Login**
```
POST http://localhost:5000/ambulance/login
Content-Type: application/json

{
  "phone": "1111111111",
  "password": "ambulance123"
}
```
→ Save the ambulance token.

**7. Ambulance – Set status to active**
```
PUT http://localhost:5000/ambulance/status
Authorization: Bearer <ambulance_token>
Content-Type: application/json

{
  "status": "active"
}
```

**8. Ambulance – Update location (so admin can assign)**
```
POST http://localhost:5000/ambulance/update-location
Authorization: Bearer <ambulance_token>
Content-Type: application/json

{
  "lat": 28.6140,
  "lng": 77.2095
}
```

**9. Admin – Login**
```
POST http://localhost:5000/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```
→ Save the admin token.

**10. Admin – Get all requests**
```
GET http://localhost:5000/admin/all-requests
Authorization: Bearer <admin_token>
```

**11. Admin – Assign ambulance to request**
```
PUT http://localhost:5000/admin/assign/<request_id>
Authorization: Bearer <admin_token>
```
→ Uses Haversine to pick nearest **active** ambulance.

**12. Ambulance – Get my requests**
```
GET http://localhost:5000/ambulance/my-requests
Authorization: Bearer <ambulance_token>
```

**13. Ambulance – Complete request**
```
PUT http://localhost:5000/ambulance/complete-request/<request_id>
Authorization: Bearer <ambulance_token>
```

Once this flow works end-to-end, your backend is validated.

---

## 2. Build a Frontend (Web / Mobile)

- **Web:** React, Vue, or Next.js calling your APIs.
- **Mobile:** React Native or Flutter with the same base URL: `http://localhost:5000` (dev) or your deployed URL (production).
- **CORS:** Already enabled in this backend for browser clients.

Use the same endpoints as above; only the UI and how you store/send the JWT (e.g. in headers or secure storage) change.

---

## 3. Production Checklist

Before going live:

| Task | Description |
|------|-------------|
| **SMS for OTP** | Replace “return OTP in response” with Twilio / AWS SNS / MSG91. Remove OTP from API response. |
| **Environment** | Use `.env` for `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `MONGO_URI`. Never commit `.env`. |
| **HTTPS** | Serve the app behind HTTPS (e.g. Nginx + Let’s Encrypt, or your host’s SSL). |
| **CORS** | Restrict `Access-Control-Allow-Origin` to your frontend domain(s) only. |
| **Rate limiting** | Add rate limits on `/user/send-otp` and login endpoints. |
| **MongoDB** | Keep Atlas IP whitelist tight or use VPC peering if possible. |
| **Logging** | Add request/error logging (e.g. Python `logging` or a logging service). |

---

## 4. Deploy the Backend

- **Options:** Railway, Render, Heroku, AWS (EC2/ECS), or a VPS (DigitalOcean, etc.).
- **Steps:**  
  - Set environment variables on the platform.  
  - Point `MONGO_URI` to your Atlas cluster.  
  - Run `pip install -r requirements.txt` and `python app.py` (or use gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`).
- **Frontend:** Use the deployed API URL (e.g. `https://your-api.railway.app`) in your web/mobile app.

---

## 5. Optional Improvements

- **WebSockets / push:** Notify ambulances when a request is assigned; notify users when an ambulance is assigned or completed.
- **Maps:** Show user and ambulance locations on a map (e.g. Leaflet, Mapbox, Google Maps) using the same `lat`/`lng` you already store.
- **Admin dashboard:** Simple React/Vue app for admin: login, list users/ambulances/requests, assign, view status.
- **Backup:** Enable MongoDB Atlas automated backups and, if needed, periodic exports.

---

## Summary

1. **Now:** Test the full flow (user OTP → profile → emergency request → ambulance register/login → status/location → admin assign → ambulance complete) with the steps in section 1.  
2. **Next:** Build a frontend (web or mobile) that uses these APIs.  
3. **Before production:** Follow the production checklist (SMS, env, HTTPS, CORS, rate limit, logging).  
4. **When ready:** Deploy backend and point the frontend to the deployed URL.

If you tell me your preferred stack (e.g. React, React Native, or “admin dashboard only”), I can outline the exact screens and API calls for that next.
