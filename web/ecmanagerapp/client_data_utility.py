import datetime
import pytz
from django.conf import settings
from firebase_admin import firestore
import firebase_admin.exceptions
import sys

# Initialize Firestore client (assuming Firebase is already initialized via settings)
db = firestore.client()


def get_client_dashboard_data():
    """
    Fetches all client data from Firestore, joins with distributor names,
    calculates monthly and total KPIs, and returns a dictionary of results.
    """

    # Define Firestore paths using the secured app ID structure
    # NOTE: settings.FIREBASE_WEB_APP_ID must be configured correctly in settings.py
    # If using Canvas, replace settings.FIREBASE_WEB_APP_ID with the actual global variable access if needed,
    # but for a standard Django project, using settings is correct.
    try:
        app_id = settings.FIREBASE_WEB_APP_ID
    except AttributeError:
        # Fallback if the setting is missing (for local testing flexibility)
        app_id = 'default-app-id'

    CLIENTS_PATH = f'artifacts/{app_id}/public/data/clients'
    DISTRIBUTORS_PATH = f'artifacts/{app_id}/public/data/distributors'

    # 1. Initialize result structure
    results = {
        'clients': [],
        'kpi_total_clients': 0,
        'kpi_clients_month': 0,
        'kpi_top_distributor': 'N/A',
    }

    try:
        # 2. Fetch Distributors (UID -> Name Map for Joining)
        distributor_map = {}
        distributors_snapshot = db.collection(DISTRIBUTORS_PATH).get()
        for doc in distributors_snapshot:
            data = doc.to_dict()
            distributor_map[doc.id] = data.get('full_name', 'N/A')

        # 3. Fetch All Clients and Initialize Counters
        clients_snapshot = db.collection(CLIENTS_PATH).get()
        clients_data = []

        # Define local timezone and the current time
        # NOTE: Using datetime.timezone.utc for compatibility
        local_tz = pytz.timezone(settings.TIME_ZONE)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_local = now_utc.astimezone(local_tz)

        current_month_clients_count = 0
        monthly_counts = {}

        for doc in clients_snapshot:
            client = doc.to_dict()
            client['id'] = doc.id

            owner_id = client.get('ownerId', 'Unknown')
            client['distributor_name'] = distributor_map.get(owner_id, owner_id)

            # Date Handling and Formatting
            log_timestamp = client.get('dateLogged')
            log_date = now_local  # Default date

            if log_timestamp:
                # 1. Set the naive Firestore timestamp to UTC
                utc_date = log_timestamp.replace(tzinfo=datetime.timezone.utc)
                # 2. Convert the UTC date to the local timezone
                log_date = utc_date.astimezone(local_tz)

            client['date_logged_formatted'] = log_date.strftime('%b %d, %Y %I:%M %p %Z')

            # KPI Calculation (Monthly Counts and Leaderboard Tally)
            if log_date.month == now_local.month and log_date.year == now_local.year:
                current_month_clients_count += 1
                monthly_counts[owner_id] = monthly_counts.get(owner_id, 0) + 1

            clients_data.append(client)

        # 4. Calculate Top Distributor KPI
        top_distributor_id = max(monthly_counts, key=monthly_counts.get, default=None)

        if top_distributor_id:
            max_clients = monthly_counts[top_distributor_id]
            name = distributor_map.get(top_distributor_id, 'Unknown')
            # Use safe formatting for the template
            top_distributor_kpi = name
            clients_entered = max_clients

        # 5. Compile Final Results
        results['clients'] = clients_data
        results['kpi_total_clients'] = len(clients_data)
        results['kpi_clients_month'] = current_month_clients_count
        results['clients_entered'] = clients_entered
        results['kpi_top_distributor'] = top_distributor_kpi

        return results

    except firebase_admin.exceptions.FirebaseError as e:
        print(f"Firebase Client Data Error: {e}", file=sys.stderr)
        # Return base results with an error indicator
        results['kpi_top_distributor'] = 'Data Error'
        return results

    except Exception as e:
        print(f"General Client Data Error: {e}", file=sys.stderr)
        results['kpi_top_distributor'] = 'System Error'
        return results
