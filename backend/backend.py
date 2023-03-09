import os
import logging
from flask import Flask, request, jsonify
from dds_utils import ServerConfig
import json
import yaml
from .server import Server

app = Flask(__name__)
server = None

from munch import *


@app.route("/")
@app.route("/index")
def index():
    # TODO: Add debugging information to the page if needed
    return "Much to do!"


@app.route("/init", methods=["POST"])
def initialize_server():
    args = yaml.load(request.data, Loader=yaml.SafeLoader)
    vid_name = request.headers["vid_name"]
    global server
    if not server:
        logging.basicConfig(
            format="%(name)s -- %(levelname)s -- %(lineno)s -- %(message)s",
            level="INFO")
        server = Server(args, args["nframes"])
        os.makedirs("server_temp-%s" %(vid_name), exist_ok=True)
        os.makedirs("server_temp-%s-cropped" %(vid_name), exist_ok=True)
        return "New Init"
    else:
        server.reset_state(int(args["nframes"]), vid_name)
        return "Reset"


@app.route("/low", methods=["POST"])
def low_query():
    file_data = request.files["media"]
    vid_name = request.headers["vid_name"]
    # results = server.perform_low_query(file_data)
    results = server.perform_low_query_experiment(file_data, vid_name)

    return jsonify(results)


@app.route("/high", methods=["POST"])
def high_query():
    file_data = request.files["media"]
    vid_name = request.headers["vid_name"]
    # results = server.perform_high_query(file_data)
    results = server.perform_high_query_experiment(file_data, vid_name)

    return jsonify(results)
