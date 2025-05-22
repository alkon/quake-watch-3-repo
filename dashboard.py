from flask import Blueprint, render_template, jsonify, request, send_file, current_app
from utils import generate_graph, get_top_earthquakes, get_last_earthquake, COUNTRIES
from datetime import datetime, timedelta
from utils import COUNTRIES, get_last_earthquakes
import requests

# Init the Dashboard's Blueprint
dashboard_blueprint = Blueprint('dashboard', __name__)

class EarthquakeDashboard:
    @staticmethod
    @dashboard_blueprint.route('/')
    def main_page():
        return render_template('main_page.html')

    @staticmethod
    @dashboard_blueprint.route('/ping')
    def ping():
        return 'pong', 200

    @staticmethod
    @dashboard_blueprint.route('/health')
    def health():
        return jsonify(status='ok', message='Application is healthy'), 200

    @staticmethod
    @dashboard_blueprint.route('/status')
    def status():
        status_info = {
            'service': 'Flask Application',
            'status': 'running',
            'uptime': '72 hours'
        }
        return jsonify(status_info), 200

    @staticmethod
    @dashboard_blueprint.route('/info')
    def info():
        app_info = {
            'name': 'Sample Flask App',
            'version': '1.0',
            'author': 'Your Name',
            'description': 'A sample Flask application demonstrating multiple routes'
        }
        return jsonify(app_info), 200

    @staticmethod
    @dashboard_blueprint.route('/telaviv-earthquakes')
    def telaviv_earthquakes():
        return EarthquakeDashboard.get_earthquake_data_by_location_name("Tel Aviv, Israel")

    @dashboard_blueprint.route('/earthquakes/<location_name>')
    def earthquakes_by_location(location_name):
        """
        Returns earthquake data for a location from the COUNTRIES config via GET.
        """
        return EarthquakeDashboard.get_earthquake_data_by_location_name(location_name)

    from flask import request

    @dashboard_blueprint.route('/today-extreme-earthquakes/<float:minmag>')
    def today_extreme_earthquakes(minmag):
        """
        Fetch extreme earthquakes (magnitude >= minmag) for the last day and log them if found.
        """
        earthquakes_resp = get_last_earthquakes(1, minmag)
        dashboard_logger = current_app.dashboard_logger

        dashboard_logger.info(f"Endpoint '/today-extreme-earthquakes/{minmag}' accessed by {request.remote_addr}")

        # --- ADD THESE LINES TEMPORARILY ---
        dashboard_logger.info(f"Raw earthquakes_resp: {earthquakes_resp}")
        events = earthquakes_resp.get('events', [])
        if events:
            for event in events:
                dashboard_logger.info(f"Raw event data: {event}")
        # --- END OF TEMPORARY LINES ---

        if events:
            message = f"Found {len(events)} extreme earthquakes (magnitude >= {minmag})"
            dashboard_logger.info(f"{message}:")

            for event in events:
                dashboard_logger.info(
                    f"- Magnitude: {event.get('magnitude')}, Location: {event.get('location')}, Time: {event.get('time')}")
        else:
            message = f"No extreme earthquakes found today (magnitude >= {minmag})."
            dashboard_logger.info(f"{message}:")

        earthquakes_resp['message'] = message
        return jsonify(earthquakes_resp)

###########################################################################
# Helper methods to retrieve earthquake data
###########################################################################
    @staticmethod
    def get_earthquake_data_by_location_name(location_name: str):
        """
        Generic method to return earthquake data for a given location name from COUNTRIES config.
        """
        config = COUNTRIES.get(location_name)
        if config:
            latitude = config.get("lat")
            longitude = config.get("lon")
            radius = config.get("radius")
            return EarthquakeDashboard._fetch_earthquake_data(latitude, longitude, max_radius_km=radius)
        else:
            current_app.logger.error(f"{location_name} configuration not found in COUNTRIES")
            return jsonify(error=f"{location_name} configuration not found"), 500

    @staticmethod
    def _fetch_earthquake_data(latitude, longitude, days=30, max_radius_km=100):
        """
        Fetches and processes earthquake data from the USGS API.

        Args:
            latitude (float): The latitude of the center point.
            longitude (float): The longitude of the center point.
            days (int): The number of past days to retrieve data for (default is 30).
            max_radius_km (int): The maximum radius in kilometers to search within (default is 100).

        Returns:
            tuple: A tuple containing a dictionary with earthquake data and the HTTP status code.
                   Returns an error dictionary and status code on failure.
        """
        response = EarthquakeDashboard._fetch_usgs_data(latitude, longitude, days, max_radius_km)
        return EarthquakeDashboard._process_earthquake_response(response)

    @staticmethod
    def _process_earthquake_response(response):
        """
        Processes the JSON response from the USGS API.
        """
        if response.status_code == 200:
            data = response.json()
            processed_events = []
            for feature in data.get('features', []):
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                coordinates = geometry.get('coordinates', [])
                event_data = {
                    'magnitude': properties.get('mag'),
                    'place': properties.get('place'),
                    'time': properties.get('time'),
                    'coordinates': {
                        'longitude': coordinates[0] if len(coordinates) > 0 else None,
                        'latitude': coordinates[1] if len(coordinates) > 1 else None,
                        'depth': coordinates[2] if len(coordinates) > 2 else None,
                    },
                    'type': properties.get('type')
                }
                processed_events.append(event_data)
            result = {
                'count': len(processed_events),
                'events': processed_events
            }
            return jsonify(result), response.status_code
        else:
            current_app.logger.error("Error fetching data from USGS API")
            return jsonify(error="Error fetching data from USGS API"), response.status_code

    @staticmethod
    def _fetch_usgs_data(latitude, longitude, days=30, max_radius_km=100):
        """
        Fetches raw earthquake data from the USGS API.
        """
        start_time = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
        params = {
            'format': 'geojson',
            'latitude': latitude,
            'longitude': longitude,
            'maxradiuskm': max_radius_km,
            'starttime': start_time
        }
        usgs_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        try:
            response = requests.get(usgs_url, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error fetching data from USGS API: {e}")
            return None

############################# Graph presentation methods ######################
    @staticmethod
    @dashboard_blueprint.route('/graph-earthquakes.png')
    def graph_earthquakes_image():
        if 'True':
            return jsonify(message="Graph endpoint temporary disabled"), 501
        days = int(request.args.get('days', 30))
        loc_name = request.args.get('location', "Tel Aviv, Israel")
        location = COUNTRIES.get(loc_name, COUNTRIES["Tel Aviv, Israel"])
        img = generate_graph(days, location["lat"], location["lon"], location["radius"])
        return send_file(img, mimetype='image/png')

    @staticmethod
    @dashboard_blueprint.route('/graph-earthquakes-5years.png')
    def graph_earthquakes_5years_image():
        if 'True':
            return jsonify(message="Graph endpoint temporary disabled"), 501
        days = 5 * 365  # Approximate days in 5 years
        loc_name = request.args.get('location', "Tel Aviv, Israel")
        location = COUNTRIES.get(loc_name, COUNTRIES["Tel Aviv, Israel"])
        img = generate_graph(days, location["lat"], location["lon"], location["radius"], title_suffix="(5 Years)")
        return send_file(img, mimetype='image/png')

    @staticmethod
    @dashboard_blueprint.route('/graph-earthquakes')
    def graph_earthquakes_page():
        if 'True':
            return jsonify(message="Graph endpoint temporary disabled"), 501
        days = int(request.args.get('days', 30))
        loc_name = request.args.get('location', "Tel Aviv, Israel")
        top_events = get_top_earthquakes(limit=5)
        last_event = get_last_earthquake()

        return render_template('graph_dashboard.html',
                               days=days,
                               current_location=loc_name,
                               countries=list(COUNTRIES.keys()),
                               top_events=top_events,
                               last_event=last_event)



