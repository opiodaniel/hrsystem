import datetime
import pytz
from django.conf import settings
from firebase_admin import firestore
import firebase_admin.exceptions
import sys
import operator

# Initialize Firestore client (assuming Firebase is already initialized via settings)
db = firestore.client()

app_id = settings.FIREBASE_WEB_APP_ID
CLIENTS_PATH = f'artifacts/{app_id}/public/data/clients'
DISTRIBUTORS_PATH = f'artifacts/{app_id}/public/data/distributors'


def get_monthly_leaderboard(top_n=3):
    """
    Calculates the top distributors globally based on the number of clients
    logged in the current month.

    Args:
        top_n (int): The number of top distributors to return.

    Returns:
        list: A sorted list of dictionaries [{'name': '...', 'count': 10}, ...]
    """
    leaderboard_list = []

    try:
        local_tz = pytz.timezone(settings.TIME_ZONE)
        now_local = datetime.datetime.now(local_tz)

        # 1. Define Date Range for Current Month (in UTC)
        start_of_month_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Find the first day of the next month to define the exclusive upper boundary
        if now_local.month == 12:
            start_of_next_month_local = start_of_month_local.replace(year=now_local.year + 1, month=1)
        else:
            start_of_next_month_local = start_of_month_local.replace(month=now_local.month + 1)

        # Convert local datetimes to UTC to match Firestore server timestamps
        start_of_month_utc = start_of_month_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        end_of_month_utc = start_of_next_month_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        # 2. Fetch Distributors Map (UID -> Name)
        distributor_map = {}
        distributors_snapshot = db.collection(DISTRIBUTORS_PATH).get()
        for doc in distributors_snapshot:
            data = doc.to_dict()
            distributor_map[doc.id] = data.get('full_name', f"ID: {doc.id}")

        monthly_counts = {}

        # 3. Query Clients globally by date range
        leaderboard_query = db.collection(CLIENTS_PATH) \
            .where('dateLogged', '>=', start_of_month_utc) \
            .where('dateLogged', '<', end_of_month_utc)

        leaderboard_docs = leaderboard_query.stream()

        # 4. Tally client counts by ownerId
        for doc in leaderboard_docs:
            client_data = doc.to_dict()
            owner_id = client_data.get('ownerId', 'Unknown')

            # Tally counts only for distributors we have names for
            if owner_id in distributor_map:
                monthly_counts[owner_id] = monthly_counts.get(owner_id, 0) + 1

        # 5. Sort and Determine the top N distributors
        if monthly_counts:
            # Convert the dictionary to a list of (ownerId, count) tuples, sorted descending by count
            sorted_counts = sorted(monthly_counts.items(), key=operator.itemgetter(1), reverse=True)

            # Take the top N entries
            top_performers = sorted_counts[:top_n]

            # Format the final list
            for owner_id, count in top_performers:
                leaderboard_list.append({
                    'name': distributor_map.get(owner_id, f"Unknown ID ({owner_id[:4]}...)"),
                    'count': count
                })

        return leaderboard_list

    except firebase_admin.exceptions.FirebaseError as e:
        print(f"Firebase Leaderboard Error: {e}", file=sys.stderr)
        return []

    except Exception as e:
        print(f"General Leaderboard Error: {e}", file=sys.stderr)
        return []



