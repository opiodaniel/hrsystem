import datetime
import pytz
from django.conf import settings
from firebase_admin import firestore
import firebase_admin.exceptions
import sys

# Initialize Firestore client (assuming Firebase is already initialized via settings)
db = firestore.client()

app_id = settings.FIREBASE_WEB_APP_ID
CLIENTS_PATH = f'artifacts/{app_id}/public/data/clients'
DISTRIBUTORS_PATH = f'artifacts/{app_id}/public/data/distributors'

def get_employee_clients(employee_id):
    """
    Fetches the current employee's client leads and calculates the
    current month's top distributor (leaderboard) across all distributors.
    """
    # 1. Initialize result structure
    results = {
        'clients': [],
        'kpi_total_clients': 0,
        'kpi_clients_month': 0,  # Current employee's count this month
        'kpi_top_distributor_name': 'N/A',
        'kpi_top_distributor_count': 0,
    }

    try:
        local_tz = pytz.timezone(settings.TIME_ZONE)
        now_local = datetime.datetime.now(local_tz)

        # 2. Define Date Range for Current Month (in UTC)
        # Start of the current month (e.g., Oct 1, 2025 00:00:00 local time)
        start_of_month_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Find the first day of the next month to define the exclusive upper boundary
        if now_local.month == 12:
            start_of_next_month_local = start_of_month_local.replace(year=now_local.year + 1, month=1)
        else:
            start_of_next_month_local = start_of_month_local.replace(month=now_local.month + 1)

        # Convert local datetimes to UTC to match Firestore server timestamps
        # NOTE: We use .replace(tzinfo=None) as Firestore SDK often expects naive datetime for comparison
        start_of_month_utc = start_of_month_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        end_of_month_utc = start_of_next_month_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        # --- Task A: Fetch current employee's clients and calculate their monthly count ---
        personal_clients = []
        current_employee_monthly_count = 0

        # Query 1: Filtered by current employee's ID
        personal_query = db.collection(CLIENTS_PATH).where('ownerId', '==', employee_id)
        personal_docs = personal_query.stream()

        for doc in personal_docs:
            client_data = doc.to_dict()
            log_timestamp = client_data.get('dateLogged')

            # Formatting and personal monthly count logic
            if log_timestamp:
                # 1. Set the naive Firestore timestamp to UTC
                utc_date = log_timestamp.replace(tzinfo=datetime.timezone.utc)
                # 2. Convert the UTC date to the local timezone for display
                log_date_local = utc_date.astimezone(local_tz)
            else:
                log_date_local = now_local

                # Format the date for the template
            client_data['date_logged_formatted'] = log_date_local.strftime('%b %d, %Y %I:%M %p %Z')

            # Check if this client belongs to the current month (for this employee's KPI)
            if log_date_local.month == now_local.month and log_date_local.year == now_local.year:
                current_employee_monthly_count += 1

            personal_clients.append(client_data)

        results['clients'] = personal_clients
        results['kpi_total_clients'] = len(personal_clients)
        results['kpi_clients_month'] = current_employee_monthly_count

        # --- Task B: Calculate Top Distributor (Leaderboard) for the Current Month ---

        # 1. Fetch Distributors Map (UID -> Name)
        distributor_map = {}
        distributors_snapshot = db.collection(DISTRIBUTORS_PATH).get()
        for doc in distributors_snapshot:
            data = doc.to_dict()
            # Use doc.id (the UID) as the key
            distributor_map[doc.id] = data.get('full_name', f"ID: {doc.id}")

        monthly_counts = {}

        # 2. Query 2: Filtered globally by date range (for leaderboard)
        leaderboard_query = db.collection(CLIENTS_PATH) \
            .where('dateLogged', '>=', start_of_month_utc) \
            .where('dateLogged', '<', end_of_month_utc)

        leaderboard_docs = leaderboard_query.stream()

        # 3. Tally client counts by ownerId
        for doc in leaderboard_docs:
            client_data = doc.to_dict()
            owner_id = client_data.get('ownerId', 'Unknown')

            # Tally counts for valid owner IDs
            if owner_id in distributor_map:
                monthly_counts[owner_id] = monthly_counts.get(owner_id, 0) + 1

        # 4. Determine the top distributor
        if monthly_counts:
            # Get the ownerId (key) with the maximum count (value)
            top_distributor_id = max(monthly_counts, key=monthly_counts.get)
            max_clients = monthly_counts[top_distributor_id]

            # Map the ID back to the name
            results['kpi_top_distributor_name'] = distributor_map.get(top_distributor_id,
                                                                      f"Unknown Distributor ({top_distributor_id[:4]}...)")
            results['kpi_top_distributor_count'] = max_clients

        return results

    except firebase_admin.exceptions.FirebaseError as e:
        print(f"Firebase Client Data Error: {e}", file=sys.stderr)
        results['kpi_top_distributor_name'] = 'Data Error'
        return results

    except Exception as e:
        print(f"General Client Data Error: {e}", file=sys.stderr)
        results['kpi_top_distributor_name'] = 'System Error'
        return results


