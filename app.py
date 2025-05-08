from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://krishnabk0803:keshika0803@cluster0.5jw6k.mongodb.net/database")
db = client["database"]
movie_collection = db["ucea"]
booking_collection = db["bookings"]

# Convert MongoDB ObjectId to string for JSON serialization
def convert_objectid_to_str(document):
    if "_id" in document and isinstance(document["_id"], ObjectId):
        document["_id"] = str(document["_id"])
    return document

@app.route("/", methods=["GET", "POST"])
def index():
    movies = list(movie_collection.find())
    # Convert all _id fields to string
    for movie in movies:
        convert_objectid_to_str(movie)
    return render_template("index.html", movies=movies)

@app.route("/select_movie", methods=["POST"])
def select_movie():
    movie_name = request.form.get("movie_name")
    movie = movie_collection.find_one({"movie_name": movie_name})
    
    if movie:
        convert_objectid_to_str(movie)
        return render_template("select_location.html", movie=movie)
    else:
        return render_template("index.html", error="Movie not found")

@app.route("/booking", methods=["POST"])
def booking():
    movie_name = request.form.get("movie_name")
    city = request.form.get("city")
    theatre = request.form.get("theatre")
    date = request.form.get("date")
    time = request.form.get("time")
    seats = int(request.form.get("seats"))

    # Fetch movie details from MongoDB
    movie = movie_collection.find_one({"movie_name": movie_name})

    if not movie:
        return render_template("index.html", error="Movie not found")

    show = None
    price_per_seat = 0  # Initialize the price_per_seat variable

    # Ensure that the location and show data are valid
    for loc in movie.get("locations", []):
        if loc.get("city") == city and loc.get("theatre") == theatre:
            for s in loc.get("shows", []):
                if s.get("date") == date and s.get("time") == time:
                    show = s
                    price_per_seat = s.get("price_per_seat", 0)
                    break

    if show and show.get("available_seats", 0) >= seats:
        # Calculate the total price
        total_price = price_per_seat * seats
        # Pass price_per_seat and total_price to the confirmation page
        return render_template("confirm_booking.html", movie_name=movie_name, city=city, theatre=theatre, date=date, time=time, seats=seats, price_per_seat=price_per_seat, total_price=total_price)
    else:
        convert_objectid_to_str(movie)
        error = "Not enough seats available for this show."
        return render_template("select_location.html", movie=movie, error=error)

@app.route("/payment", methods=["POST"])
def payment():
    movie_name = request.form.get("movie_name")
    city = request.form.get("city")
    theatre = request.form.get("theatre")
    date = request.form.get("date")
    time = request.form.get("time")
    seats = int(request.form.get("seats"))
    price_per_seat = int(request.form.get("price_per_seat"))

    movie = movie_collection.find_one({"movie_name": movie_name})

    if not movie:
        return render_template("index.html", error="Movie not found")

    for loc in movie.get("locations", []):
        if loc.get("city") == city and loc.get("theatre") == theatre:
            for s in loc.get("shows", []):
                if s.get("date") == date and s.get("time") == time:
                    if s.get("available_seats", 0) >= seats:
                        s["available_seats"] -= seats  # Update seats
                        break

    # Update the movie document in the database
    movie_collection.update_one(
        {"movie_name": movie_name},
        {"$set": {"locations": movie["locations"]}}
    )

    # Insert the booking record into the database
    booking = {
        "movie_name": movie_name,
        "city": city,
        "theatre": theatre,
        "date": date,
        "time": time,
        "seats": seats,
        "price_per_seat": price_per_seat,  # Store price_per_seat in the booking record
        "payment_status": "Success",
        "created_at": datetime.now()
    }
    booking_collection.insert_one(booking)

    total_price = price_per_seat * seats

    return render_template("payment.html", status="Success", movie_name=movie_name, total_price=total_price)

if __name__ == "__main__":
    app.run(debug=True)
