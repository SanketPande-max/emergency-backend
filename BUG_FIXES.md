# Bug Fixes Applied

## Fixed Issues

### 1. ✅ Ambulance Status Validation
**Problem:** Ambulance could set status to "active" without completing profile or setting location.

**Fix:** Added validation in `PUT /ambulance/status` endpoint:
- Before setting status to "active", checks:
  - All required profile fields: `name`, `age`, `date_of_birth`, `gender`, `vehicle_number`, `driving_license`
  - Location must be set (`current_location` not null)
- Returns error with missing fields if validation fails
- Status can still be set to "inactive" without validation

**File:** `routes/ambulance_routes.py` (lines 81-115)

---

### 2. ✅ Indian Standard Time (IST)
**Problem:** All timestamps were in UTC.

**Fix:** 
- Created `utils/time_utils.py` with `get_ist_now_naive()` function (IST = UTC + 5:30)
- Replaced all `datetime.utcnow()` calls with `get_ist_now_naive()` in:
  - `models/user_model.py`
  - `models/ambulance_model.py`
  - `models/request_model.py`
  - `models/otp_model.py`
- All timestamps now stored in IST

**Files:** 
- `utils/time_utils.py` (new)
- All model files updated

---

### 3. ✅ Location Update Isolation
**Problem:** Second ambulance was getting previous ambulance's location.

**Fix:**
- Added explicit ambulance existence check in `POST /ambulance/update-location`
- Ensured `update_location()` method uses specific `ambulance_id` from JWT token
- MongoDB query uses `{'_id': ObjectId(ambulance_id)}` to target only that ambulance
- Added validation to ensure ambulance exists before update

**Files:**
- `routes/ambulance_routes.py` (lines 117-135)
- `models/ambulance_model.py` (lines 50-61)

---

### 4. ✅ One Assignment Per Ambulance
**Problem:** Ambulance with active assignment was being assigned to new requests.

**Fix:**
- Added `has_active_assignment()` method in `AmbulanceModel` to check if ambulance has active assigned request
- Updated `get_all_with_location()` to accept `exclude_assigned=True` parameter
- When `exclude_assigned=True`, filters out ambulances with `status='assigned'` requests
- Updated `POST /user/request-emergency` to use `get_all_with_location(db, exclude_assigned=True)`
- Ambulance can only be assigned to one request at a time until it's completed

**Files:**
- `models/ambulance_model.py` (lines 63-84)
- `routes/user_routes.py` (line 132)

---

## Summary

All 4 bugs have been fixed:
1. ✅ Status validation prevents setting active without profile/location
2. ✅ All timestamps now in IST (UTC+5:30)
3. ✅ Location updates are properly isolated per ambulance
4. ✅ Ambulances can only have one active assignment at a time

The backend now correctly enforces:
- Profile completion before activation
- IST timezone for all operations
- Proper data isolation per ambulance
- One-to-one assignment (ambulance ↔ request) until completion
