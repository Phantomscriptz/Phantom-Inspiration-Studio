import sqlite3
from pathlib import Path


class Database:

    def __init__(self):

        Path("database").mkdir(exist_ok=True)

        self.conn = sqlite3.connect("database/phantom.db")

        self.cursor = self.conn.cursor()

        self.initialize()

    def initialize(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT,

            created TEXT,

            updated TEXT

        )
        """)

        self.conn.commit()