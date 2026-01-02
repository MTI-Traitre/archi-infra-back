from flask import Flask, request, jsonify
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
import os

# --- Initialisation de l'application Flask ---
app = Flask(__name__)
CORS(app)
# Configuration de la base de données PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://bubbleteauser:bubbleteapass@localhost:5432/bubbleteadb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modèle de données ---
class BubbleTea(db.Model):
    __tablename__ = 'bubble_teas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'note': self.note,
            'address': self.address
        }

# Configuration Swagger UI
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/doc"
}

swagger_template = {
    "info": {
        "title": "Bubble Tea Tier List API",
        "description": "API CRUD pour gérer les classements de Bubble Tea avec PostgreSQL",
        "version": "2.0.0"
    },
    "host": "127.0.0.1:5000",
    "basePath": "/",
    "schemes": ["http"],
    "tags": [
        {
            "name": "Bubble Teas",
            "description": "Opérations sur les Bubble Teas"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# --- Routes API ---

@app.route('/bubble-teas', methods=['GET'])
def get_all_bubble_teas():
    """
    Liste tous les Bubble Teas triés par note (meilleure en premier)
    ---
    tags:
      - Bubble Teas
    responses:
      200:
        description: Liste de tous les Bubble Teas triés par note décroissante
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: Identifiant unique
              name:
                type: string
                description: Nom du Bubble Tea
              note:
                type: number
                description: Note de 0.0 à 5.0
              address:
                type: string
                description: Adresse du magasin
    """
    teas = BubbleTea.query.order_by(BubbleTea.note.desc()).all()
    return jsonify([tea.to_dict() for tea in teas]), 200


@app.route('/bubble-teas/<int:tea_id>', methods=['GET'])
def get_bubble_tea(tea_id):
    """
    Récupère un Bubble Tea par son ID
    ---
    tags:
      - Bubble Teas
    parameters:
      - name: tea_id
        in: path
        type: integer
        required: true
        description: ID du Bubble Tea
    responses:
      200:
        description: Bubble Tea trouvé
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            note:
              type: number
            address:
              type: string
      404:
        description: Bubble Tea non trouvé
    """
    tea = BubbleTea.query.get(tea_id)
    if not tea:
        return jsonify({'message': 'Bubble Tea non trouvé'}), 404
    return jsonify(tea.to_dict()), 200


@app.route('/bubble-teas', methods=['POST'])
def create_bubble_tea():
    """
    Crée un nouveau Bubble Tea
    ---
    tags:
      - Bubble Teas
    parameters:
      - name: body
        in: body
        required: true
        description: Données du nouveau Bubble Tea
        schema:
          type: object
          required:
            - name
            - note
          properties:
            name:
              type: string
              description: Nom du Bubble Tea
              example: Matcha Latte
            note:
              type: number
              description: Note de 0.0 à 5.0
              example: 4.5
            address:
              type: string
              description: Adresse du magasin (optionnel)
              example: 789 Boulevard du Thé
    responses:
      201:
        description: Bubble Tea créé avec succès
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            note:
              type: number
            address:
              type: string
      400:
        description: Données manquantes ou invalides
    """
    data = request.get_json()
    
    if not data or 'name' not in data or 'note' not in data:
        return jsonify({'message': 'Les champs "name" et "note" sont obligatoires'}), 400

    try:
        new_tea = BubbleTea(
            name=data['name'],
            note=data['note'],
            address=data.get('address')
        )
        db.session.add(new_tea)
        db.session.commit()
        
        return jsonify(new_tea.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur lors de la création: {str(e)}'}), 500


@app.route('/bubble-teas/<int:tea_id>', methods=['PUT'])
def update_bubble_tea(tea_id):
    """
    Met à jour un Bubble Tea existant
    ---
    tags:
      - Bubble Teas
    parameters:
      - name: tea_id
        in: path
        type: integer
        required: true
        description: ID du Bubble Tea à modifier
      - name: body
        in: body
        required: true
        description: Nouvelles données du Bubble Tea
        schema:
          type: object
          required:
            - name
            - note
          properties:
            name:
              type: string
              example: Taro Milk Tea (Updated)
            note:
              type: number
              example: 4.8
            address:
              type: string
              example: 123 Nouvelle Rue
    responses:
      200:
        description: Bubble Tea mis à jour
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            note:
              type: number
            address:
              type: string
      400:
        description: Données manquantes
      404:
        description: Bubble Tea non trouvé
    """
    tea = BubbleTea.query.get(tea_id)
    if not tea:
        return jsonify({'message': 'Bubble Tea non trouvé'}), 404
    
    data = request.get_json()
    
    if not data or 'name' not in data or 'note' not in data:
        return jsonify({'message': 'Les champs "name" et "note" sont requis'}), 400
    
    try:
        tea.name = data['name']
        tea.note = data['note']
        tea.address = data.get('address')
        
        db.session.commit()
        return jsonify(tea.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur lors de la mise à jour: {str(e)}'}), 500


@app.route('/bubble-teas/<int:tea_id>', methods=['DELETE'])
def delete_bubble_tea(tea_id):
    """
    Supprime un Bubble Tea
    ---
    tags:
      - Bubble Teas
    parameters:
      - name: tea_id
        in: path
        type: integer
        required: true
        description: ID du Bubble Tea à supprimer
    responses:
      204:
        description: Bubble Tea supprimé avec succès
      404:
        description: Bubble Tea non trouvé
    """
    tea = BubbleTea.query.get(tea_id)
    if not tea:
        return jsonify({'message': 'Bubble Tea non trouvé'}), 404
    
    try:
        db.session.delete(tea)
        db.session.commit()
        return '', 204
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur lors de la suppression: {str(e)}'}), 500


# Route pour initialiser la base de données avec des données de test
@app.route('/init-db', methods=['POST'])
def init_database():
    """
    Initialise la base de données avec des données de test
    ---
    tags:
      - Database
    responses:
      200:
        description: Base de données initialisée
    """
    try:
        # Créer les tables
        db.create_all()
        
        # Vérifier si la DB est déjà peuplée
        if BubbleTea.query.count() == 0:
            # Ajouter des données de test
            test_teas = [
                BubbleTea(name='Taro Milk Tea', note=5.0, address='123 Rue du Boba'),
                BubbleTea(name='Brown Sugar Boba', note=4.0, address='456 Avenue du Thé'),
                BubbleTea(name='Matcha Latte', note=4.5, address='789 Boulevard du Thé')
            ]
            
            for tea in test_teas:
                db.session.add(tea)
            
            db.session.commit()
            return jsonify({'message': 'Base de données initialisée avec succès'}), 200
        else:
            return jsonify({'message': 'La base de données contient déjà des données'}), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur lors de l\'initialisation: {str(e)}'}), 500


# --- Lancement du serveur ---
if __name__ == '__main__':
    print("=" * 60)
    print("🧋 API Bubble Tea Tier List lancée !")
    print("=" * 60)
    print("📍 API : http://127.0.0.1:5000")
    print("📚 Documentation Swagger UI : http://127.0.0.1:5000/api/doc")
    print("🗄️  Database : PostgreSQL")
    print("=" * 60)
    print("💡 Initialisez la DB : POST http://127.0.0.1:5000/init-db")
    print("=" * 60)
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0')