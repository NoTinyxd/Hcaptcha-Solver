import asyncio
import time
import json
import os
import traceback

from flask import Flask, request, jsonify
from solver import solve

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_nopecha_key():
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        return config.get("nopecha_key")
    except Exception:
        return None

NOPECHA_KEY = load_nopecha_key()

@app.route('/solve', methods=['POST'])
def solve_endpoint():
    d = request.get_json()
    if not d:
        return jsonify({"message": "Failed to solve"}), 400

    sitekey = d.get("sitekey")
    rqdata = d.get("rqdata") or None

    if not sitekey:
        return jsonify({"message": "Failed to solve"}), 400

    if not NOPECHA_KEY:
        return jsonify({"message": "nopecha_key missing in config.json"}), 400

    start = time.time()
    try:
        token = asyncio.run(solve(sitekey=sitekey, rqdata=rqdata, nopecha_key=NOPECHA_KEY))
        took = round(time.time() - start, 2)

        if not token:
            return jsonify({"message": "Failed to solve"}), 400

        return jsonify({
            "success": "true",
            "token": token,
            "took": str(took)
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to solve",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)