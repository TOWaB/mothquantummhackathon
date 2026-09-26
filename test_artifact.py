#!/usr/bin/env python3
"""Standalone runner for the artifact page. Does not import app.py and does not
touch live state, so it is safe to run while someone else is building.

    python tools/seed_artifact.py state/versions.test.json
    ARTIFACT_VERSIONS=state/versions.test.json python test_artifact.py

Serves out/ as well as static/, which is the thing most likely to be wrong.
"""
import os, pathlib
from flask import Flask, send_from_directory
from artifact import bp

app = Flask(__name__, static_folder="static")
app.register_blueprint(bp)


@app.get("/out/<path:filename>")
def out(filename):
    return send_from_directory(pathlib.Path("out").resolve(), filename)


if __name__ == "__main__":
    print("versions:", os.environ.get("ARTIFACT_VERSIONS", "state/versions.json"))
    app.run(port=5001, debug=True)
