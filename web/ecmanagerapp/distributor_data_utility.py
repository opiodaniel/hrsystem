import datetime
import pytz
from django.conf import settings
from firebase_admin import auth, initialize_app  # Assuming 'auth' is imported globally


def get_distributor_data():
    """
    Fetches all distributor records from Firebase Auth, calculates their local
    last login time, and returns the data as a list of dictionaries.
    """
    distributors = []

    # Define the local timezone object based on Django settings (e.g., Africa/Kampala)
    local_tz = pytz.timezone(settings.TIME_ZONE)

    # Iterate through all user records from Firebase Auth
    for user_record in auth.list_users().iterate_all():

        # 1. Initialize last_login_time to "Never"
        last_login_time = "Never"

        # Access the last sign-in timestamp from user_metadata (in milliseconds)
        last_sign_in_ms = user_record.user_metadata.last_sign_in_timestamp

        # 2. Check if the user has ever signed in (timestamp is not None)
        if last_sign_in_ms:
            # Firebase timestamps are in milliseconds; convert to seconds
            last_sign_in_seconds = last_sign_in_ms / 1000.0

            # Convert UTC timestamp to a timezone-aware datetime object (UTC is standard)
            utc_dt = datetime.datetime.fromtimestamp(last_sign_in_seconds, tz=datetime.timezone.utc)

            # Convert the UTC datetime to the local timezone
            local_dt = utc_dt.astimezone(local_tz)

            # 3. Format the Python datetime object into the desired clean string
            last_login_time = local_dt.strftime('%b %d, %Y %I:%M %p %Z')

        distributors.append({
            "uid": user_record.uid,
            "email": user_record.email,
            "full_name": user_record.display_name or user_record.email,
            "last_login": last_login_time,
        })

    return distributors
