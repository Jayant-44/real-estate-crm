from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the database instance
db = SQLAlchemy()

# --- EXISTING MODELS ---

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Numeric(15, 2))
    preferences = db.Column(db.Text)
    status = db.Column(db.String(20), default='New')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "phone": self.phone,
            "email": self.email, "budget": str(self.budget) if self.budget else None,
            "preferences": self.preferences, "status": self.status
        }

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(15, 2), nullable=False)
    size_sqft = db.Column(db.Integer)
    amenities = db.Column(db.Text)
    status = db.Column(db.String(50), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String(255), default='default.jpg')

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "location": self.location,
            "price": str(self.price), "size_sqft": self.size_sqft,
            "amenities": self.amenities, "status": self.status
        }

# --- NEW MODELS ---

class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), default='Agent') # Admin, Manager, Agent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, 
            "email": self.email, "role": self.role
        }

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    client_type = db.Column(db.String(50), nullable=False) # Buyer or Seller
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "phone": self.phone,
            "email": self.email, "client_type": self.client_type
        }