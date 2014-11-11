import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "chords.config.TestingConfig"

from chords import app
from chords import models
from chords.utils import upload_path
from chords.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the chords API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def testGetEmptySongs(self):
        """Getting songs from an empty database"""
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data, [])


    def testGetSongs(self):
        """ Get songs from a populated database """
        fileA = models.File(id=1, filename="FileA")
        fileB = models.File(id=2, filename="FileB")
        fileC = models.File(id=3, filename="FileC")
        songA = models.Song(id=1, column=1)
        songB = models.Song(id=2, column=3)

        session.add_all([fileA, fileB, fileC, songA, songB])
        session.commit()

        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

        postA = data[0]
        self.assertEqual(songA.id, 1)
        self.assertEqual(songA.column, 1)

        postB = data[1]
        self.assertEqual(songB.id, 2)
        self.assertEqual(songB.column, 3)


    def testGetSong(self):
        """ Getting a single post from a populated database """
        fileA = models.File(id=1, filename="FileA")
        fileB = models.File(id=2, filename="FileB")
        fileC = models.File(id=3, filename="FileC")
        songA = models.Song(id=1, column=1)
        songB = models.Song(id=2, column=3)

        session.add_all([fileA, fileB, fileC, songA, songB])
        session.commit()

        response = self.client.get("/api/songs/{}".format(songB.id), 
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        song = json.loads(response.data)
        self.assertEqual(song["id"], 2)
        self.assertEqual(song["column"], 3)


    def testGetNonExistentPost(self):
        """ Getting a single post which doesn't exist """
        response = self.client.get("/api/songs/1",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Could not find song with id 1")

    def testPostSong(self):
        """ Posting a new song """
        fileA = models.File(id=1, filename="FileA")
        fileB = models.File(id=2, filename="FileB")
        fileC = models.File(id=3, filename="FileC")
        session.add_all([fileA, fileB, fileC])
        session.commit()


        data = {
            "file": {
                "id":3
            }
        }

        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs/1")

        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["column"], 3)

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)

        song = songs[0]
        self.assertEqual(song.id, 1)
        self.assertEqual(song.column, 3)


    def test_get_uploaded_file(self):
        path =  upload_path("test.txt")
        with open(path, "w") as f:
            f.write("File contents")

        response = self.client.get("/uploads/test.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, "File contents")

    
    def test_file_upload(self):
        data = {
            "file": (StringIO("File contents"), "test.txt")
        }

        response = self.client.post("/api/files",
            data=data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")

        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            contents = f.read()
        self.assertEqual(contents, "File contents")
        



