from datetime import datetime
from bson import ObjectId
from utils.time_utils import get_ist_now_naive

class AmbulanceModel:
    @staticmethod
    def create_ambulance(db, phone, name=None, age=None, date_of_birth=None, gender=None,
                        vehicle_number=None, driving_license=None, ambulance_type=None):
        """Create ambulance (OTP-only login; no password)."""
        ambulance = {
            'phone': phone,
            'name': name,
            'age': age,
            'date_of_birth': date_of_birth,
            'gender': gender,
            'vehicle_number': vehicle_number,
            'driving_license': driving_license,
            'ambulance_type': ambulance_type or 'any',  # any, basic_life, advance_life, icu_life
            'status': 'inactive',
            'current_location': None,
            'current_location_updated_at': None,
            'profile_completed': False,  # Track if profile is completed
            'created_at': get_ist_now_naive()
        }
        result = db.ambulances.insert_one(ambulance)
        return result.inserted_id

    @staticmethod
    def find_by_phone(db, phone):
        return db.ambulances.find_one({'phone': phone})

    @staticmethod
    def find_by_id(db, ambulance_id):
        return db.ambulances.find_one({'_id': ObjectId(ambulance_id)})

    @staticmethod
    def update_profile(db, ambulance_id, update_data):
        # Check if profile is being completed (has name, age, date_of_birth, gender, vehicle_number, driving_license)
        required_fields = ['name', 'age', 'date_of_birth', 'gender', 'vehicle_number', 'driving_license']
        if all(key in update_data and update_data.get(key) for key in required_fields):
            update_data['profile_completed'] = True
        db.ambulances.update_one(
            {'_id': ObjectId(ambulance_id)},
            {'$set': update_data}
        )
        return db.ambulances.find_one({'_id': ObjectId(ambulance_id)})

    @staticmethod
    def update_status(db, ambulance_id, status):
        db.ambulances.update_one(
            {'_id': ObjectId(ambulance_id)},
            {'$set': {'status': status}}
        )
        return db.ambulances.find_one({'_id': ObjectId(ambulance_id)})

    @staticmethod
    def update_location(db, ambulance_id, lat, lng):
        """Update location for specific ambulance_id only."""
        now = get_ist_now_naive()
        db.ambulances.update_one(
            {'_id': ObjectId(ambulance_id)},
            {'$set': {
                'current_location': {'lat': float(lat), 'lng': float(lng)},
                'current_location_updated_at': now
            }}
        )
        return db.ambulances.find_one({'_id': ObjectId(ambulance_id)})
    
    @staticmethod
    def has_active_assignment(db, ambulance_id):
        """Check if ambulance has an active assigned request (status='assigned')."""
        count = db.requests.count_documents({
            'assigned_ambulance_id': ObjectId(ambulance_id),
            'status': 'assigned'
        })
        return count > 0

    @staticmethod
    def get_all_with_location(db, exclude_assigned=True):
        """All ambulances with location.
        If exclude_assigned=True, only ACTIVE ambulances without an active assignment are returned.
        """
        query = {'current_location': {'$ne': None}}
        if exclude_assigned:
            # Only consider ambulances that are currently ACTIVE for assignment
            query['status'] = 'active'
        ambulances = list(db.ambulances.find(query))
        if exclude_assigned:
            # Filter out ambulances with active assigned requests
            filtered = []
            for amb in ambulances:
                if not AmbulanceModel.has_active_assignment(db, str(amb['_id'])):
                    filtered.append(amb)
            return filtered
        return ambulances

    @staticmethod
    def get_active_ambulances(db):
        return list(db.ambulances.find({'status': 'active', 'current_location': {'$ne': None}}))
