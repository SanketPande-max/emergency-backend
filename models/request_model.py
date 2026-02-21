from datetime import datetime
from bson import ObjectId
from utils.time_utils import get_ist_now_naive
from utils.distance import haversine_distance

class RequestModel:
    @staticmethod
    def create_request(db, user_id, lat, lng, source='manual'):
        """source: 'manual' (user tapped) or 'auto_detected' (accident detection)"""
        request = {
            'user_id': ObjectId(user_id),
            'location': {'lat': float(lat), 'lng': float(lng)},
            'status': 'pending',
            'assigned_ambulance_id': None,
            'assigned_at': None,
            'selected_hospital': None,
            'source': source,
            'created_at': get_ist_now_naive()
        }
        result = db.requests.insert_one(request)
        return result.inserted_id

    @staticmethod
    def find_by_id(db, request_id):
        return db.requests.find_one({'_id': ObjectId(request_id)})

    @staticmethod
    def assign_ambulance(db, request_id, ambulance_id):
        now = get_ist_now_naive()
        db.requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {
                'assigned_ambulance_id': ObjectId(ambulance_id),
                'status': 'assigned',
                'assigned_at': now
            }}
        )
        return db.requests.find_one({'_id': ObjectId(request_id)})

    @staticmethod
    def complete_request(db, request_id):
        db.requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {'status': 'completed'}}
        )
        return db.requests.find_one({'_id': ObjectId(request_id)})

    @staticmethod
    def mark_as_fake(db, request_id):
        """Mark request as fake and return the request."""
        db.requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {'status': 'fake', 'is_fake': True}}
        )
        return db.requests.find_one({'_id': ObjectId(request_id)})

    @staticmethod
    def select_hospital(db, request_id, hospital):
        db.requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {'selected_hospital': hospital, 'status': 'to_hospital'}}
        )
        return db.requests.find_one({'_id': ObjectId(request_id)})

    @staticmethod
    def get_by_user(db, user_id, statuses=None):
        """Get requests for a user. statuses: e.g. ['pending','assigned'] or None for all."""
        q = {'user_id': ObjectId(user_id)}
        if statuses:
            q['status'] = {'$in': statuses}
        return list(db.requests.find(q).sort('created_at', -1))

    @staticmethod
    def get_active_for_user(db, user_id):
        """Get user's most recent non-completed request (pending, assigned, or to_hospital)."""
        reqs = list(db.requests.find({
            'user_id': ObjectId(user_id),
            'status': {'$in': ['pending', 'assigned', 'to_hospital']}
        }).sort('created_at', -1).limit(1))
        return reqs[0] if reqs else None

    @staticmethod
    def get_by_ambulance(db, ambulance_id):
        return list(db.requests.find({
            'assigned_ambulance_id': ObjectId(ambulance_id)
        }).sort('created_at', -1))

    @staticmethod
    def get_all_requests(db):
        return list(db.requests.find().sort('created_at', -1))

    @staticmethod
    def get_pending_requests(db):
        return list(db.requests.find({'status': 'pending'}).sort('created_at', -1))

    @staticmethod
    def assign_nearest_pending_to_ambulance(db, ambulance):
        """
        When an ambulance becomes active, assign it to the nearest pending request (if any).
        Returns the assigned request document or None if nothing was assigned.
        """
        if not ambulance:
            return None

        amb_loc = (ambulance.get('current_location') or {})
        if amb_loc.get('lat') is None or amb_loc.get('lng') is None:
            return None

        pending_cursor = db.requests.find({'status': 'pending'}).sort('created_at', 1)

        nearest_req = None
        nearest_dist = None

        for req in pending_cursor:
            loc = (req.get('location') or {})
            if loc.get('lat') is None or loc.get('lng') is None:
                continue
            d = haversine_distance(
                float(amb_loc['lat']),
                float(amb_loc['lng']),
                float(loc['lat']),
                float(loc['lng']),
            )
            if nearest_dist is None or d < nearest_dist:
                nearest_dist = d
                nearest_req = req

        if not nearest_req:
            return None

        assigned = RequestModel.assign_ambulance(db, str(nearest_req['_id']), str(ambulance['_id']))
        return assigned


class LocationTrackModel:
    """Track ambulance location during an assigned request (for dashboard map)."""
    @staticmethod
    def add(db, request_id, ambulance_id, lat, lng):
        doc = {
            'request_id': ObjectId(request_id),
            'ambulance_id': ObjectId(ambulance_id),
            'lat': float(lat),
            'lng': float(lng),
            'created_at': get_ist_now_naive()
        }
        db.location_tracks.insert_one(doc)

    @staticmethod
    def get_track_for_request(db, request_id):
        return list(db.location_tracks.find(
            {'request_id': ObjectId(request_id)}
        ).sort('created_at', 1))
