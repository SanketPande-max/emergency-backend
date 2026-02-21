# Emergency App (Uber-like) – Backend API Summary

## Twilio

- OTP is sent via **Twilio SMS** (no OTP in API response).
- Configure in `.env`: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` (+19787561135).
- Phone numbers in requests should be E.164 (e.g. +919876543210). The backend normalizes 10-digit Indian numbers with +91.

---

## User flow

1. **POST /user/send-otp**  
   Body: `{ "phone": "9876543210" }`  
   Sends OTP via Twilio; no OTP in response.

2. **POST /user/verify-otp**  
   Body: `{ "phone": "9876543210", "otp": "123456" }`  
   Creates user if new; returns `token`, `user_id`.

3. **POST /user/update-profile** (Auth: Bearer user token)  
   Body: `{ "name", "date_of_birth", "gender", "email" }`  
   All fields optional; saves to DB.

4. **POST /user/update-location** (Auth: Bearer user token)  
   Body: `{ "lat", "lng" }`  
   Saves live location (call after location permission).

5. **POST /user/request-emergency** (Auth: Bearer user token)  
   Body: `{ "lat", "lng" }`  
   Creates request; **auto-assigns** nearest ambulance (nearest **active** if any, else nearest any).  
   Returns `request_id` and full `request` (including `assigned_ambulance` if any).

6. **GET /user/my-request** (Auth: Bearer user token)  
   Returns current active request (pending/assigned) with:
   - Accident location
   - `assigned_ambulance`: driver name, phone, vehicle_number, driving_license, **current_location** (for live tracking)

---

## Ambulance driver flow (same login scheme: phone + OTP)

1. **POST /ambulance/send-otp**  
   Body: `{ "phone": "..." }`  
   Sends OTP via Twilio.

2. **POST /ambulance/verify-otp**  
   Body: `{ "phone", "otp" }`  
   Creates ambulance if new; returns `token`, `ambulance_id`, `status`.

3. **POST /ambulance/update-profile** (Auth: Bearer ambulance token)  
   Body: `{ "name", "age", "date_of_birth", "gender", "vehicle_number", "driving_license" }`  
   All optional.

4. **PUT /ambulance/status** (Auth: Bearer ambulance token)  
   Body: `{ "status": "active" | "inactive" }`  
   Only **active** drivers are preferred for assignment; if none active, nearest (any) is assigned.

5. **POST /ambulance/update-location** (Auth: Bearer ambulance token)  
   Body: `{ "lat", "lng" }`  
   Updates current location; if driver has an active assigned request, location is appended to **track** (for dashboard map).

6. **GET /ambulance/my-requests** (Auth: Bearer ambulance token)  
   Lists all assigned requests with **user_name**, **user_phone**, **accident_location**.

7. **GET /ambulance/assigned-details** (Auth: Bearer ambulance token)  
   Current assignment (if any): **user_name**, **user_phone**, **accident_location**, **directions** (origin = ambulance location, destination = accident) for maps/directions.

8. **PUT /ambulance/complete-request/<request_id>** (Auth: Bearer ambulance token)  
   Marks request completed.

---

## Central dashboard (admin)

1. **POST /admin/login**  
   Body: `{ "username", "password" }`  
   From env (`ADMIN_USERNAME`, `ADMIN_PASSWORD`). Returns admin token.

2. **GET /admin/all-users** (Auth: Bearer admin token)  
   All users.

3. **GET /admin/all-ambulances** (Auth: Bearer admin token)  
   All ambulances (no password; OTP-only).

4. **GET /admin/all-requests** (Auth: Bearer admin token)  
   All requests (list).

5. **GET /admin/dashboard-map** (Auth: Bearer admin token)  
   For map view: each request has:
   - **location** (accident marker)
   - **status**, **created_at**
   - **assigned_ambulance** (id, name, phone, vehicle_number, current_location)
   - **track**: array of `{ lat, lng, created_at }` for the assigned ambulance’s route (so ambulance track is visible on the dashboard).

---

## Assignment logic (Uber-like)

- On **POST /user/request-emergency**:  
  - All ambulances with a **current_location** are considered.  
  - Sorted by distance (Haversine) to accident.  
  - **Nearest active** is assigned; if none is active, **nearest any** is assigned.  
  - Request gets `status: assigned` and `assigned_ambulance_id`.  
- Driver is “notified” by the fact that the request appears in **GET /ambulance/my-requests** and **GET /ambulance/assigned-details** (frontend can poll or use push later).

---

## Database (all saved)

- **users**: phone, name, date_of_birth, gender, email, location, location_updated_at, created_at  
- **ambulances**: phone, name, age, date_of_birth, gender, vehicle_number, driving_license, status, current_location, current_location_updated_at, created_at (no password)  
- **requests**: user_id, location, status (pending/assigned/completed), assigned_ambulance_id, assigned_at, created_at  
- **otps**: phone, otp, role (user|ambulance), expires_at, etc.  
- **location_tracks**: request_id, ambulance_id, lat, lng, created_at (for dashboard ambulance track)

---

## Directions

- **GET /ambulance/assigned-details** returns `directions.origin` (ambulance) and `directions.destination` (accident).  
- Frontend can open Google Maps / Apple Maps with these coordinates for turn-by-turn directions.

---

## Quick test (after `python app.py`)

1. User: send-otp → verify-otp → update-profile → update-location → request-emergency → my-request.  
2. Ambulance: send-otp → verify-otp → update-profile → status=active → update-location; then my-requests, assigned-details, complete-request.  
3. Admin: login → dashboard-map (see accident markers and ambulance track).
