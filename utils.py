import io
from datetime import datetime, timedelta
# import matplotlib.pyplot as plt
import requests
from collections import defaultdict

# Country configuration
COUNTRIES = {
    "Tel Aviv, Israel": {"lat": 32.0853, "lon": 34.7818, "radius": 100},
    "United States (California)": {"lat": 36.7783, "lon": -119.4179, "radius": 300},
    "Japan": {"lat": 36.2048, "lon": 138.2529, "radius": 300},
    "Indonesia": {"lat": -0.7893, "lon": 113.9213, "radius": 300},
    "Chile": {"lat": -35.6751, "lon": -71.5430, "radius": 300}
}

def generate_graph(days, lat, lon, radius, title_suffix=""):
    start_time_dt = datetime.utcnow() - timedelta(days=days)
    start_time = start_time_dt.strftime('%Y-%m-%d')
    params = {
        'format': 'geojson',
        'latitude': lat,
        'longitude': lon,
        'maxradiuskm': radius,
        'starttime': start_time
    }
    usgs_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    response = requests.get(usgs_url, params=params)

    # plt.figure(figsize=(10, 5))
    # if response.status_code != 200:
    #     plt.text(0.5, 0.5, "Error fetching data", horizontalalignment='center',
    #              verticalalignment='center', fontsize=14)
    #     plt.axis('off')
    # else:
    #     data = response.json()
    #     counts_by_day = defaultdict(int)
    #     for feature in data.get('features', []):
    #         timestamp = feature.get('properties', {}).get('time')
    #         if timestamp:
    #             event_date = datetime.utcfromtimestamp(timestamp / 1000).date()
    #             counts_by_day[event_date] += 1
    #     days_list = sorted(counts_by_day.keys())
    #     counts = [counts_by_day[day] for day in days_list]
    #
    #     if days_list:
    #         plt.bar(days_list, counts)
    #         plt.xlabel('Date')
    #         plt.ylabel('Number of Earthquakes')
    #         plt.title(f'Earthquakes in Last {days} Days {title_suffix}')
    #         plt.xticks(rotation=45)
    #         plt.tight_layout()
    #     else:
    #         plt.text(0.5, 0.5, "No earthquake data available", horizontalalignment='center',
    #                  verticalalignment='center', fontsize=14)
    #         plt.axis('off')
    #
    # img = io.BytesIO()
    # plt.savefig(img, format='png')
    # plt.close()
    img.seek(0)
    return img

def get_top_earthquakes(limit=5):
    return get_last_earthquakes(30, 1, 5)

def get_last_earthquake(days=30, minmag=1):
    return get_last_earthquakes(days, minmag, 1);

def timestamp_to_str(ts):
    return datetime.utcfromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')

def get_last_earthquakes(days=30, minmag=1, limit=3):
    """
    Fetch the most recent earthquake events based on the given days, minimum magnitude, and limit.

    :param days: Number of days to look back for earthquake data (default is 30)
    :param minmag: Minimum magnitude of the earthquake (default is 1)
    :param limit: The maximum number of earthquake events to return (default is 3)
    :return: A list of the most recent earthquake events (if any), or a message indicating no data found
    """
    # Calculate the start time for the query (UTC datetime, offset by 'days')
    start_time = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')

    # Define query parameters for the USGS API
    params = {
        'format': 'geojson',
        'starttime': start_time,
        'minmagnitude': minmag
    }

    # Define the URL for the USGS API
    usgs_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    try:
        # Make the request to the USGS API
        response = requests.get(usgs_url, params=params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the response JSON
            data = response.json()
            events = data.get('features', [])

            # Check if there are any events
            if events:
                # Sort events by time in descending order and return the most recent ones
                events = sorted(events, key=lambda f: f.get('properties', {}).get('time', 0), reverse=True)

                found_message = f"Found {len(events)} items"
                return {
                    'message': found_message,
                    'events': events[:limit]  # Return the top 'limit' events
                }
            else:
                # No events found within the given timeframe and magnitude
                return {'message': 'No earthquakes found within the specified time and magnitude range.'}
        else:
            # Handle unsuccessful response
            return {'error': f"Failed to fetch data: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        # Handle request exceptions
        return {'error': f"Request failed: {str(e)}"}
