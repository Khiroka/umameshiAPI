# -*- coding: utf-8 -*-

from flask import Flask
import traceback
import json

import umameshi

app = Flask(__name__)

@app.route("/umameshi", methods=["GET"])
def get_umameshi_data():
    message = umameshi.main()
    return message


if __name__ == "__main__":
    app.run()
