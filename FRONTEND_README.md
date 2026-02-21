# Emergency Response System – Frontend

Web frontend for the Emergency Response System with three portals:

1. **User Portal** – Request emergency, share location (allow or pick on map), track assigned ambulance
2. **Ambulance Portal** – Login via OTP, update location, accept assignments, complete requests
3. **Admin Portal** – Dashboard with Google Map view, users, ambulances, requests

## Map & Routing (100% Free, No API Key)

- **Leaflet + OpenStreetMap** for map display
- **OSRM** (router.project-osrm.org) for route calculation
- Click-to-select location, navigation via OpenStreetMap directions

## Run

1. Start the backend:
   ```bash
   python app.py
   ```
   (Backend runs on http://localhost:5000)

2. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   (Frontend runs on http://localhost:5173)

3. Open http://localhost:5173 in a browser.

## Integration

- The Vite dev server proxies `/api` to `http://localhost:5000`, so all API calls go through the backend.
- Auth uses JWT tokens stored in `localStorage` and sent as `Authorization: Bearer <token>`.
- User and Ambulance use phone + OTP (via Twilio). Admin uses username/password from `.env`.
