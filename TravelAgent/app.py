from flask import Flask, render_template, request
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = Flask(__name__)

ORS_API_KEY = os.getenv("ORS_API_KEY")


def geocode_location(location):
    """
    Convert a place name into longitude and latitude.
    """

    url = "https://api.heigit.org/pelias/v1/search"

    headers = {
        "Authorization": ORS_API_KEY
    }

    params = {
        "text": location,
        "size": 1
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        return None, response.text

    data = response.json()

    if not data.get("features"):
        return None, "Location not found."

    coordinates = data["features"][0]["geometry"]["coordinates"]

    longitude = coordinates[0]
    latitude = coordinates[1]

    return [longitude, latitude], None


def get_route_distance(origin, destination):
    """
    Find route distance and travel time.
    """

    # Convert locations to coordinates
    origin_coords, error = geocode_location(origin)

    if error:
        return None, None, error

    destination_coords, error = geocode_location(destination)

    if error:
        return None, None, error

    # Current openrouteservice Directions API
    url = "https://api.heigit.org/openrouteservice/v2/directions/driving-car"

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "coordinates": [
            origin_coords,
            destination_coords
        ]
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    if response.status_code != 200:
        return None, None, response.text

    result = response.json()

    try:
        summary = result["routes"][0]["summary"]

        distance_km = summary["distance"] / 1000

        duration_minutes = round(
            summary["duration"] / 60
        )

        return distance_km, duration_minutes, None

    except (KeyError, IndexError):
        return None, None, "Route information was not found."


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/plan", methods=["POST"])
def plan_trip():

    current_location = request.form["current_location"]
    destination = request.form["destination"]
    vehicle = request.form["vehicle"]

    petrol_price = float(request.form["petrol_price"])
    mileage = float(request.form["mileage"])

    # Automatically calculate route
    distance, duration, error = get_route_distance(
        current_location,
        destination
    )

    if error:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Travel Agent - Error</title>
        </head>

        <body>

            <h2>Unable to calculate route</h2>

            <p>{error}</p>

            <br>

            <a href="/">Go Back</a>

        </body>
        </html>
        """

    # Calculate fuel required
    fuel_required = distance / mileage

    # Calculate fuel cost
    fuel_cost = fuel_required * petrol_price

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>Travel Agent - Trip Result</title>

    </head>

    <body>

        <h1>🚗 Trip Details</h1>

        <p>
            <strong>From:</strong>
            {current_location}
        </p>

        <p>
            <strong>To:</strong>
            {destination}
        </p>

        <p>
            <strong>Vehicle:</strong>
            {vehicle}
        </p>

        <hr>

        <h2>🗺️ Route Information</h2>

        <p>
            <strong>Distance:</strong>
            {distance:.1f} km
        </p>

        <p>
            <strong>Estimated Travel Time:</strong>
            {duration} minutes
        </p>

        <hr>

        <h2>⛽ Fuel Information</h2>

        <p>
            <strong>Mileage:</strong>
            {mileage:.1f} km/litre
        </p>

        <p>
            <strong>Petrol Price:</strong>
            ₹{petrol_price:.2f}/litre
        </p>

        <p>
            <strong>Fuel Required:</strong>
            {fuel_required:.2f} litres
        </p>

        <h2>
            Estimated Fuel Cost:
            ₹{fuel_cost:.2f}
        </h2>

        <br>

        <a href="/">Plan Another Trip</a>

    </body>

    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)