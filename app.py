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
    convert_objectid_to_str(movie)
    return render_template("select_location.html", movie=movie)

@app.route("/booking", methods=["POST"])
def booking():
    movie_name = request.form.get("movie_name")
    city = request.form.get("city")
    theatre = request.form.get("theatre")
    date = request.form.get("date")
    time = request.form.get("time")
    seats = int(request.form.get("seats"))

    movie = movie_collection.find_one({"movie_name": movie_name})

    show = None
    for loc in movie["locations"]:
        if loc["city"] == city and loc["theatre"] == theatre:
            for s in loc["shows"]:
                if s["date"] == date and s["time"] == time:
                    show = s
                    break

    if show and show["available_seats"] >= seats:
        # Save to session or pass to next page
        return render_template("confirm_booking.html", movie_name=movie_name, city=city, theatre=theatre, date=date, time=time, seats=seats)
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

    movie = movie_collection.find_one({"movie_name": movie_name})

    for loc in movie["locations"]:
        if loc["city"] == city and loc["theatre"] == theatre:
            for s in loc["shows"]:
                if s["date"] == date and s["time"] == time:
                    if s["available_seats"] >= seats:
                        s["available_seats"] -= seats  # update locally
                        break

    # Update movie document in DB
    movie_collection.update_one(
        {"movie_name": movie_name},
        {"$set": {"locations": movie["locations"]}}
    )

    # Insert booking into DB
    booking = {
        "movie_name": movie_name,
        "city": city,
        "theatre": theatre,
        "date": date,
        "time": time,
        "seats": seats,
        "payment_status": "Success",
        "created_at": datetime.now()
    }
    booking_collection.insert_one(booking)

    return render_template("payment.html", status="Success", movie_name=movie_name)

if __name__ == "__main__":
    app.run(debug=True)
