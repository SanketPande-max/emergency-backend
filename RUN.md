# How to Run the Emergency Response System Backend

## Quick Start Guide

### Step 1: Install Dependencies

First, make sure all required packages are installed:

```bash
cd d:\Emergency\emergency_backend
pip install -r requirements.txt
```

**If you get permission errors, use:**
```bash
pip install --user -r requirements.txt
```

### Step 2: Test Database Connection

Before running the main app, test your MongoDB connection:

```bash
python test_connection.py
```

**Expected Output:**
```
==================================================
Testing MongoDB Connection...
==================================================
Connection URI: <your_mongo_uri>...
✓ Connection successful!
✓ Database: emergodb
✓ Collections found: 0
  (No collections yet - they will be created automatically)
✓ Write/Delete test successful!
==================================================
✓ All tests passed! Database is ready to use.
==================================================
```

### Step 3: Run the Flask Application

Start the Flask server:

```bash
python app.py
```

**Expected Output:**
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Step 4: Verify the API is Running

Open your browser or use curl:

**Browser:**
- Visit: `http://localhost:5000/`

**Command Line (PowerShell):**
```powershell
Invoke-WebRequest -Uri http://localhost:5000/ | Select-Object -ExpandProperty Content
```

**Command Line (curl):**
```bash
curl http://localhost:5000/
```

**Expected Response:**
```json
{
  "status": "ok",
  "message": "Emergency Response System API is running",
  "database": "connected",
  "database_name": "emergodb"
}
```

## Running Both Tests and Server

### Option 1: Run Tests First, Then Server

```bash
# Terminal 1: Test connection
python test_connection.py

# Terminal 2: Run server (after test passes)
python app.py
```

### Option 2: Run Server (It Will Test Connection on Startup)

The Flask app automatically tests the database connection when it starts. Just run:

```bash
python app.py
```

## API Endpoints

Once running, you can test these endpoints:

### Health Check
```
GET http://localhost:5000/
```

### User - Send OTP
```
POST http://localhost:5000/user/send-otp
Body: { "phone": "1234567890" }
```

### User - Verify OTP
```
POST http://localhost:5000/user/verify-otp
Body: { "phone": "1234567890", "otp": "123456" }
```

### Admin - Login
```
POST http://localhost:5000/admin/login
Body: { "username": "admin", "password": "admin123" }
```

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Connection Timeout
**Solution:** 
1. Check your internet connection
2. Verify MongoDB Atlas IP whitelist includes your IP (or 0.0.0.0/0)
3. Check MongoDB Atlas cluster is running

### Issue: Port Already in Use
**Solution:** Change port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### Issue: SSL Handshake Error
**Solution:** 
1. Make sure `dnspython` is installed: `pip install dnspython`
2. Check MongoDB Atlas connection string is correct
3. Verify your IP is whitelisted in MongoDB Atlas

## Stopping the Server

Press `Ctrl + C` in the terminal where the server is running.
