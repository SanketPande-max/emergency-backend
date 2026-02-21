"""
Indian Standard Time (IST) utilities.
IST = UTC + 5:30
"""
from datetime import datetime, timedelta, timezone

def get_ist_now():
    """Get current time in IST (UTC+5:30)."""
    ist_offset = timedelta(hours=5, minutes=30)
    ist_tz = timezone(ist_offset)
    return datetime.now(ist_tz)

def get_ist_now_naive():
    """Get current IST time as naive datetime (for MongoDB storage)."""
    ist_offset = timedelta(hours=5, minutes=30)
    utc_now = datetime.utcnow()
    return utc_now + ist_offset
