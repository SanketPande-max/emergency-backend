# Emergency Response System – Project Status, Testing & Future Directions

---

## 1. Functionalities Built Till Now

### 1.1 User Flow (Phone Verification Based Login)

| # | Functionality | API Endpoint | Method | Description |
|---|---------------|--------------|--------|-------------|
| 1 | Send OTP | `/user/send-otp` | POST | Generates 6-digit OTP, stores in DB with 5-min expiry. Does not create user yet. |
| 2 | Verify OTP | `/user/verify-otp` | POST | Verifies OTP; creates user if not exists; returns JWT token. |
| 3 | Update Profile | `/user/update-profile` | POST | Updates name, date_of_birth, age, email, emergency_contact, blood_group, location (lat/lng). Requires user JWT. |
| 4 | Request Emergency | `/user/request-emergency` | POST | Saves user location; creates request with status `pending`, no ambulance assigned. Requires user JWT. |

**User collection:** `phone`, `name`, `emergency_contact`, `blood_group`, `location: { lat, lng }`, `created_at` (plus optional fields).

---

### 1.2 Ambulance Panel (Active / Inactive Toggle)

| # | Functionality | API Endpoint | Method | Description |
|---|---------------|--------------|--------|-------------|
| 1 | Register | `/ambulance/register` | POST | Registers ambulance: driver_name, phone, vehicle_number, password. Default status: inactive. |
| 2 | Login | `/ambulance/login` | POST | Returns JWT and ambulance_id. |
| 3 | Toggle Status | `/ambulance/status` | PUT | Set `status`: `"active"` or `"inactive"`. Only active ambulances get assigned. |
| 4 | Update Location | `/ambulance/update-location` | POST | Updates current_location (lat, lng) for nearest-ambulance logic. |
| 5 | My Requests | `/ambulance/my-requests` | GET | Lists all requests assigned to this ambulance. |
| 6 | Complete Request | `/ambulance/complete-request/<request_id>` | PUT | Sets request status to `completed`. Only for requests assigned to this ambulance. |

**Ambulance collection:** `driver_name`, `phone`, `vehicle_number`, `password` (hashed), `status`, `current_location`, `created_at`.

---

### 1.3 Central Admin Dashboard

| # | Functionality | API Endpoint | Method | Description |
|---|---------------|--------------|--------|-------------|
| 1 | Admin Login | `/admin/login` | POST | Username/password (from env); returns JWT. |
| 2 | All Users | `/admin/all-users` | GET | Returns all users. Admin JWT required. |
| 3 | All Ambulances | `/admin/all-ambulances` | GET | Returns all ambulances (no password). Admin JWT required. |
| 4 | All Requests | `/admin/all-requests` | GET | Returns all emergency requests. Admin JWT required. |
| 5 | Assign Request | `/admin/assign/<request_id>` | PUT | Finds nearest **active** ambulance (Haversine), assigns and sets request status to `assigned`. Admin JWT required. |

**Request collection:** `user_id`, `location`, `status` (pending/assigned/completed), `assigned_ambulance_id`, `created_at`.

---

### 1.4 Security & Infrastructure

- **JWT (Flask-JWT-Extended):** Access tokens with 24-hour expiry.
- **Role-based protection:** `user`, `ambulance`, `admin` – users cannot access admin/ambulance routes; ambulance cannot access user routes; admin has full access.
- **Password hashing:** bcrypt for ambulance passwords.
- **OTP:** Stored in DB with expiry; verified once then deleted.
- **CORS:** Enabled for frontend.
- **Single database:** MongoDB (e.g. Atlas) – one DB, collections: `users`, `ambulances`, `requests`, `otps`.
- **Config:** `.env` for MONGO_URI, JWT_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD.
- **Health check:** `GET /` returns API status and database connection state.

---

## 2. Is the Backend Completely Ready?

**Yes.** For the scope you described, the backend is **complete and runnable**:

- User: OTP login, profile, emergency request.
- Ambulance: Register, login, active/inactive toggle, location, my-requests, complete-request.
- Admin: Login, list users/ambulances/requests, assign nearest active ambulance.
- Security: JWT, roles, bcrypt, OTP expiry.
- No mock data; all data in MongoDB.

**Production gaps (to do later):**

- OTP is still returned in API response (replace with real SMS and remove from response).
- Rate limiting, stricter CORS, and deployment (e.g. gunicorn, HTTPS) when you go live.

---

## 3. How to Test the Backend

### Prerequisites

- Backend running: `cd d:\Emergency\emergency_backend` then `python app.py`.
- Tool: **Postman**, **Thunder Client** (VS Code), or **curl**.

Base URL: `http://localhost:5000`

---

### Test 1: Health Check

- **Request:** `GET http://localhost:5000/`
- **Expected:** `200`, body with `"database": "connected"`, `"database_name": "emergodb"`.

---

### Test 2: User Flow (OTP → Profile → Emergency)

**2a. Send OTP**

- `POST http://localhost:5000/user/send-otp`
- Body (JSON): `{ "phone": "9876543210" }`
- **Expected:** `200`, `"message": "OTP sent successfully"`, `"otp": "123456"` (use this OTP in next step).

**2b. Verify OTP**

- `POST http://localhost:5000/user/verify-otp`
- Body: `{ "phone": "9876543210", "otp": "<OTP from 2a>" }`
- **Expected:** `200`, `"token": "<JWT>"`, `"user_id": "..."`. **Copy the token.**

**2c. Update Profile**

- `POST http://localhost:5000/user/update-profile`
- Headers: `Authorization: Bearer <user_token>`
- Body (JSON):  
  `{ "name": "Test User", "email": "test@example.com", "age": 30, "lat": 28.6139, "lng": 77.2090 }`
- **Expected:** `200`, profile updated.

**2d. Request Emergency**

- `POST http://localhost:5000/user/request-emergency`
- Headers: `Authorization: Bearer <user_token>`
- Body: `{ "lat": 28.6139, "lng": 77.2090 }`
- **Expected:** `201`, `"request_id": "<id>"`. **Copy request_id for admin assign.**

---

### Test 3: Ambulance Flow

**3a. Register**

- `POST http://localhost:5000/ambulance/register`
- Body:  
  `{ "driver_name": "Driver One", "phone": "1111111111", "vehicle_number": "AMB001", "password": "pass123" }`
- **Expected:** `201`, `"ambulance_id": "..."`.

**3b. Login**

- `POST http://localhost:5000/ambulance/login`
- Body: `{ "phone": "1111111111", "password": "pass123" }`
- **Expected:** `200`, `"token": "<JWT>"`. **Copy ambulance token.**

**3c. Set Active**

- `PUT http://localhost:5000/ambulance/status`
- Headers: `Authorization: Bearer <ambulance_token>`
- Body: `{ "status": "active" }`
- **Expected:** `200`, `"status": "active"`.

**3d. Update Location** (needed for admin assign)

- `POST http://localhost:5000/ambulance/update-location`
- Headers: `Authorization: Bearer <ambulance_token>`
- Body: `{ "lat": 28.614, "lng": 77.209 }`
- **Expected:** `200`.

**3e. My Requests (after assign)**

- `GET http://localhost:5000/ambulance/my-requests`
- Headers: `Authorization: Bearer <ambulance_token>`
- **Expected:** `200`, list of assigned requests.

**3f. Complete Request**

- `PUT http://localhost:5000/ambulance/complete-request/<request_id>`
- Headers: `Authorization: Bearer <ambulance_token>`
- **Expected:** `200`, request status `completed`.

---

### Test 4: Admin Flow

**4a. Admin Login**

- `POST http://localhost:5000/admin/login`
- Body: `{ "username": "admin", "password": "admin123" }`
- **Expected:** `200`, `"token": "<JWT>"`. **Copy admin token.**

**4b. All Users**

- `GET http://localhost:5000/admin/all-users`
- Headers: `Authorization: Bearer <admin_token>`
- **Expected:** `200`, list of users.

**4c. All Ambulances**

- `GET http://localhost:5000/admin/all-ambulances`
- Headers: `Authorization: Bearer <admin_token>`
- **Expected:** `200`, list of ambulances.

**4d. All Requests**

- `GET http://localhost:5000/admin/all-requests`
- Headers: `Authorization: Bearer <admin_token>`
- **Expected:** `200`, list of requests (including the one from Test 2d).

**4e. Assign Request**

- `PUT http://localhost:5000/admin/assign/<request_id>`
- Headers: `Authorization: Bearer <admin_token>`
- **Expected:** `200`, request `status: "assigned"`, `assigned_ambulance_id` set, nearest active ambulance chosen.

---

### Full E2E Test Order

1. User: send-otp → verify-otp → update-profile → request-emergency (note `request_id`).
2. Ambulance: register → login → status = active → update-location.
3. Admin: login → all-requests → assign `<request_id>`.
4. Ambulance: my-requests (see the request) → complete-request `<request_id>`.
5. Admin: all-requests (see status `completed`).

---

## 4. Future Directions to Complete the Project

### 4.1 Must-Have for Production

- **SMS OTP:** Integrate Twilio / MSG91 / AWS SNS; send OTP via SMS; **do not** return OTP in API response.
- **Environment:** Keep all secrets in `.env`; use different config for production.
- **HTTPS & CORS:** Deploy behind HTTPS; restrict CORS to your frontend domain(s).
- **Rate limiting:** On `/user/send-otp`, `/admin/login`, `/ambulance/login` to prevent abuse.
- **Deployment:** Use gunicorn (or similar), reverse proxy (e.g. Nginx), and a process manager (e.g. systemd/supervisor).

### 4.2 Frontend (Web / Mobile)

- **User app:** Screens for phone input, OTP, profile, “Request emergency” with location, request status.
- **Ambulance app:** Login, active/inactive toggle, map/location, list of assigned requests, “Complete” button.
- **Admin dashboard:** Login, tables for users/ambulances/requests, “Assign” button, filters (e.g. pending only).

### 4.3 Optional Enhancements

- **Real-time:** WebSockets or push notifications when a request is assigned (ambulance) or when an ambulance is assigned/completed (user).
- **Maps:** Show user and ambulance locations on a map (Leaflet/Mapbox/Google Maps) using existing lat/lng.
- **Admin:** Multiple admin users in DB with roles; audit log for assign/complete actions.
- **Analytics:** Dashboard with counts (requests per day, average response time, completed vs pending).
- **Ambulance availability:** Schedule/shifts; only show ambulances that are both “active” and on duty.

---

## 5. Summary

| Area | Status |
|------|--------|
| User (OTP, profile, emergency request) | Done |
| Ambulance (register, login, status, location, my-requests, complete) | Done |
| Admin (login, list users/ambulances/requests, assign nearest ambulance) | Done |
| Security (JWT, roles, bcrypt, OTP expiry) | Done |
| Database (single MongoDB, no mock data) | Done |
| **Backend readiness for your spec** | **Complete** |
| Production (SMS, HTTPS, rate limit, deploy) | Future |
| Frontend (web + ambulance + admin) | Future |
| Real-time / maps / analytics | Future |

Use the test flow in **Section 3** to validate the backend end-to-end. Use **Section 4** to plan production and next features.
