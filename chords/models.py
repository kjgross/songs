import os.path

from flask import url_for
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import relationship

from chords import app
from database import Base, engine


class Song(Base):
	"""
	song has 1:1 relationship with file
	"""
	__tablename__ = "songs"

	#database fields
	id = Column(Integer, Sequence('post_id_sequence'), primary_key=True)
	column = Column(Integer, ForeignKey('files.id'))

	def as_dictionary(self):
		song = {
			"id": self.id,
			"file": self.column
		}
		return song	


class File(Base):
	"""
	file has a 1:1 relationship with song
	"""
	__tablename__ = "files"

	#database fields
	id = Column(Integer, Sequence('post_id_sequence'), primary_key=True)
	filename = Column(String(128))
	song = relationship('Song', backref='songs')

	def as_dictionary(self):
		return {
			"id": self.id,
			"filename": self.filename,
			"path": url_for("uploaded_file", filename=self.filename)
    }




