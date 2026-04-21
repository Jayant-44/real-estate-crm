from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from models import db, Lead, Property # Import the new models

load_dotenv()

app = Flask(__name__)

# Configure MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Bind the database to the app
db.init_app(app)

# This creates the tables in MySQL before the first request runs
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return jsonify({
        "developer": "Jayant",
        "github_profile": "Jayant-44",
        "project": "Real Estate CRM API",
        "status": "Running smoothly and tables are ready!"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)