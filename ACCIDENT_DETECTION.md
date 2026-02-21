# Accident Detection (Auto-Dispatch) Feature

## Overview

Automatically detects accidents in remote/rural areas using phone sensors (speed, accelerometer, gyroscope) and dispatches ambulances when the user cannot request help manually.

## Flow

1. **Opt-in**: User enables "Auto accident detection" in Profile.
2. **Sensors**: App collects location, speed, accelerometer, gyroscope every 5 seconds.
3. **ML/Rules**: Backend analyzes recent readings. If accident pattern detected:
   - Speed sudden drop + impact (accel) + tilt (gyro) + stopped 15+ sec
4. **Verification**: 2 automated calls via Twilio Voice:
   - Call 1: User answers → false positive, cancel
   - Call 1: No answer → Call 2 after 30s (ring timeout)
   - Call 2: User answers → false positive
   - Call 2: No answer → **Confirmed accident**
5. **Dispatch**: Create emergency request, assign nearest ambulance, notify user via SMS.

## Setup

### 1. Train ML Model (optional; rule-based fallback works without it)

```bash
pip install scikit-learn joblib numpy
python -m ml.accident_train
```

This creates `ml/accident_model.joblib`. Without it, rule-based detection is used.

### 2. Environment Variables

Add to `.env`:

```
TWILIO_VOICE_WEBHOOK_BASE=https://your-api-domain.com
```

- Must be **publicly accessible** (Twilio calls your webhooks)
- Use HTTPS in production
- For local dev: use ngrok or similar to expose localhost

### 3. Twilio Voice

- Uses same Twilio account as SMS
- Phone number must support Voice
- No extra Twilio config needed

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /sensor/submit | Submit sensor reading (JWT, user) |
| POST | /sensor/submit-batch | Submit batch of readings |
| GET | /sensor/status | Get accident alert status |
| GET | /accident-webhook/voice-greeting | TwiML for verification call |
| POST | /accident-webhook/voice-status | Twilio call status callback |

## Collections

- `sensor_readings` – rolling window of sensor data per user
- `accident_alerts` – pending/confirmed/false_positive alerts

## Detection Rules (fallback)

- Speed was > 20 km/h, dropped by ≥ 25 km/h
- Accelerometer spike ≥ 12
- Gyroscope spike ≥ 3
- Stopped at same location ≥ 15 seconds
