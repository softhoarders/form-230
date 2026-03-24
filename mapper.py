import json
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    coords_path = os.path.join(app.root_path, 'coords.json')
    with open(coords_path) as f:
        coords = json.load(f)
    return render_template('mapper.html', coords=coords)

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    coords_path = os.path.join(app.root_path, 'coords.json')
    with open(coords_path, 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=5002)