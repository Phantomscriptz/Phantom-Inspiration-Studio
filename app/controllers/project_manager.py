from datetime import datetime
from pathlib import Path
import json


class ProjectManager:

    def __init__(self):

        Path("projects").mkdir(exist_ok=True)

    def create_project(self, name):

        folder = Path("projects") / name

        folder.mkdir(exist_ok=True)

        project = {

            "name": name,

            "created": datetime.now().isoformat(),

            "status": "new",

            "script": "",

            "voice": "",

            "images": [],

            "thumbnail": ""

        }

        with open(folder / "project.phantomproj", "w") as f:

            json.dump(project, f, indent=4)

        return folder