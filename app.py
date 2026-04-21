from flask import Flask, jsonify, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
import requests
import urllib.parse
from dotenv import load_dotenv
from models import db, Lead, Property, Agent, Client 

load_dotenv()

app = Flask(__name__)

# --- Database Configuration ---
db_password = os.getenv('DB_PASSWORD')
encoded_password = urllib.parse.quote_plus(db_password) if db_password else ""
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{encoded_password}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- File Upload Configuration ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()

# FRONTEND / DASHBOARD ROUTES

@app.route('/')
def home():
    try:
        stats = {
            "leads": Lead.query.count(),
            "properties": Property.query.count(),
            "agents": Agent.query.count(),
            "clients": Client.query.count()
        }
        return render_template('index.html', developer="Jayant", github_profile="Jayant-44", stats=stats)
    except Exception as e:
        return render_template('index.html', developer="Jayant", github_profile="Jayant-44", stats={"leads": 0, "properties": 0, "agents": 0, "clients": 0})

@app.route('/dashboard/leads')
def dashboard_leads():
    try:
        all_leads = Lead.query.order_by(Lead.created_at.desc()).all()
        leads_data = [lead.to_dict() for lead in all_leads]
        return render_template('leads.html', leads=leads_data, developer="Jayant")
    except Exception as e:
        return str(e)
    
@app.route('/dashboard/add-lead')
def add_lead_page():
    return render_template('add_lead.html')

@app.route('/dashboard/properties')
def dashboard_properties():
    try:
        all_properties = Property.query.order_by(Property.created_at.desc()).all()
        properties_data = [prop.to_dict() for prop in all_properties]
        return render_template('properties.html', properties=properties_data)
    except Exception as e:
        return str(e)

@app.route('/dashboard/add-property')
def add_property_page():
    return render_template('add_property.html')

@app.route('/dashboard/admin')
def admin_panel():
    try:
        # Fetch all table data
        properties_data = [p.to_dict() for p in Property.query.order_by(Property.created_at.desc()).all()]
        leads_data = [l.to_dict() for l in Lead.query.order_by(Lead.created_at.desc()).all()]
        agents_data = [a.to_dict() for a in Agent.query.all()]
        clients_data = [c.to_dict() for c in Client.query.all()]
        
        return render_template('admin.html', 
                             properties=properties_data,
                             leads=leads_data,
                             agents=agents_data,
                             clients=clients_data)
    except Exception as e:
        return str(e)

# API ROUTES: PROPERTIES

@app.route('/api/properties', methods=['POST'])
def create_property():
    try:
        data = request.form if request.form else request.get_json()
        
        # Handle Image Upload
        filename = 'default.jpg'
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_property = Property(
            title=data.get('title'), location=data.get('location'), price=data.get('price'),
            size_sqft=data.get('size_sqft'), amenities=data.get('amenities'), image=filename
        )
        db.session.add(new_property)
        db.session.commit()
        
        # Prevent AJAX requests from redirecting
        if request.form and request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return redirect('/dashboard/properties')
        return jsonify({"success": True, "data": new_property.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/properties/<int:id>', methods=['PUT'])
def update_property(id):
    try:
        prop = Property.query.get(id)
        if not prop: return jsonify({"success": False, "error": "Not found"}), 404
        
        data = request.form if request.form else request.get_json()
        prop.title = data.get('title', prop.title)
        prop.location = data.get('location', prop.location)
        prop.price = data.get('price', prop.price)
        prop.size_sqft = data.get('size_sqft', prop.size_sqft)
        prop.amenities = data.get('amenities', prop.amenities)
        
        # Handle new image replacing old one
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                prop.image = filename
                
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/properties/<int:id>', methods=['DELETE'])
def delete_property(id):
    prop = Property.query.get(id)
    if prop:
        db.session.delete(prop)
        db.session.commit()
    return jsonify({"success": True})

# API ROUTES: LEADS

@app.route('/api/leads', methods=['POST'])
def create_lead():
    try:
        data = request.form if request.form else request.get_json()
        new_lead = Lead(
            name=data.get('name'), phone=data.get('phone'), email=data.get('email'),
            budget=data.get('budget'), preferences=data.get('preferences')
        )
        db.session.add(new_lead)
        db.session.commit()

        # Webhook Trigger
        try:
            n8n_url = os.getenv('N8N_WEBHOOK_URL')
            if n8n_url:
                requests.post(n8n_url, json={
                    "event": "new_lead", "lead_name": new_lead.name, "lead_email": new_lead.email,
                    "budget": str(new_lead.budget), "preferences": new_lead.preferences, "agent_assigned": "Jayant"
                }, timeout=2)
        except Exception: pass

        if request.form and request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return redirect('/dashboard/leads')
        return jsonify({"success": True, "data": new_lead.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/leads/<int:id>', methods=['PUT'])
def update_lead(id):
    try:
        lead = Lead.query.get(id)
        if not lead: return jsonify({"success": False}), 404
        data = request.form if request.form else request.get_json()
        
        lead.name = data.get('name', lead.name)
        lead.phone = data.get('phone', lead.phone)
        lead.email = data.get('email', lead.email)
        lead.budget = data.get('budget', lead.budget)
        lead.preferences = data.get('preferences', lead.preferences)
        
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/leads/<int:id>', methods=['DELETE'])
def delete_lead(id):
    lead = Lead.query.get(id)
    if lead:
        db.session.delete(lead)
        db.session.commit()
    return jsonify({"success": True})

# API ROUTES: AGENTS

@app.route('/api/agents', methods=['POST'])
def create_agent():
    try:
        data = request.form if request.form else request.get_json()
        new_agent = Agent(name=data.get('name'), email=data.get('email'), role=data.get('role', 'Agent'))
        db.session.add(new_agent)
        db.session.commit()
        return jsonify({"success": True, "data": new_agent.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/agents/<int:id>', methods=['PUT'])
def update_agent(id):
    try:
        agent = Agent.query.get(id)
        if not agent: return jsonify({"success": False}), 404
        data = request.form if request.form else request.get_json()
        agent.name = data.get('name', agent.name)
        agent.email = data.get('email', agent.email)
        agent.role = data.get('role', agent.role)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<int:id>', methods=['DELETE'])
def delete_agent(id):
    agent = Agent.query.get(id)
    if agent:
        db.session.delete(agent)
        db.session.commit()
    return jsonify({"success": True})

# API ROUTES: CLIENTS

@app.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.form if request.form else request.get_json()
        new_client = Client(name=data.get('name'), phone=data.get('phone'), email=data.get('email'), client_type=data.get('client_type'))
        db.session.add(new_client)
        db.session.commit()
        return jsonify({"success": True, "data": new_client.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/clients/<int:id>', methods=['PUT'])
def update_client(id):
    try:
        client = Client.query.get(id)
        if not client: return jsonify({"success": False}), 404
        data = request.form if request.form else request.get_json()
        client.name = data.get('name', client.name)
        client.phone = data.get('phone', client.phone)
        client.email = data.get('email', client.email)
        client.client_type = data.get('client_type', client.client_type)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Client.query.get(id)
    if client:
        db.session.delete(client)
        db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)