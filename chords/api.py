import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from analysis import analyse
import models
import decorators
import analysis
from chords import app
from database import session
from utils import upload_path

#JSON Schema describing the structure of a song
song_schema = {
    "properties": {
        "file" : {
        	"id" : "integer"
        }
    },
    "required": ["file", "id"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
	""" Get a list of songs"""
	songs = session.query(models.Song).all()

	"""Convert the songs to JSON and return a response"""
	data = json.dumps([song.as_dictionary() for song in songs])
	return Response(data, 200, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def song_get(id):
    """ Single song endpoint """
    # Get the song from the database
    song = session.query(models.Song).get(id)

    # Check whether the song exists
    # If not return a 404 with a helpful message
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Return the song as JSON
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")


@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
    """ Add a new song """
    data = request.json

    # Check that the JSON supplied is valid
    # If not we return a 422 Unprocessable Entity
    try:
        validate(data, song_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")


    # Add the post to the database
    song = models.Song(id=data["id"], file=data["column"])
    session.add(song)
    session.commit()

    # Return a 201 Created, containing the post as JSON and with the
    # Location header set to the location of the post
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("song_get", id=song.id)}
    return Response(data, 201, headers=headers,
    	mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(upload_path(), filename)


@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")

    filename = secure_filename(file.filename)
    db_file = models.File(filename=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))

    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")


## ASSIGNMENT 3
#In your chords/api.py file, add a GET endpoint for /api/songs/<id>/analysis. The endpoint should:

#Check whether a song with the correct ID exists
#Get the filename of the song from the database
#Call the analyse function, passing in the path of the uploaded file
#Return the results of the analysis as a JSON object

@app.route("/api/songs/<int:id>/analysis", methods=["GET"])
@decorators.accept("application/json")
def song_analysis_get(id):
    """ Get the analysis for a single song endpoint """
    # Get the song from the database
    song = session.query(models.Song).get(id)

    # Check whether the song exists
    # If not return a 404 with a helpful message
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Get the filename
    files = session.query(models.File).all()
    file1id = files[song.column-1].id
    #file1name = session.query(models.File).get(filename)
    #songname = file[song.column].filename
    songname = files[file1id-1].filename
    analysis = analyse(songname)
    data = json.dumps(analysis)




    return Response(data, 200, mimetype="application/json")




