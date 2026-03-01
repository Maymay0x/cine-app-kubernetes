from flask import Flask, jsonify, request, abort, session
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_session import Session

app = Flask(__name__, instance_relative_config=True)

mysql = MySQL(app)
bcrypt = Bcrypt(app)

app.config.from_pyfile('config.py')
login_manager = LoginManager()
login_manager.init_app(app)

app.config.from_pyfile('config_sessions.py')
Session(app)

# ==================== MODELE CLIENT ====================
class Client(UserMixin):
    def __init__(self, id, email, password, is_admin=False):
        self.id = id
        self.email = email
        self.password = password
        self.is_admin = is_admin

    @classmethod
    def get_client(cls, id=None, email=None):
        cur = mysql.connection.cursor()
        if email:
            cur.execute("SELECT * FROM clients WHERE email = %s", [email])
        elif id:
            cur.execute("SELECT * FROM clients WHERE id = %s", [id])
        result = cur.fetchone()
        cur.close()
        return cls(*result) if result else None

@login_manager.user_loader
def load_user(user_id):
    return Client.get_client(id=user_id)

# ==================== ROUTES AUTH ====================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        abort(400)
    client = Client.get_client(email=data.get('email'))
    if client and bcrypt.check_password_hash(client.password, data.get('password')):
        login_user(client, remember=True)
        session.permanent = True
        return jsonify({'success': True, 'message': 'Connexion réussie.', 'is_admin': client.is_admin})
    return jsonify({'success': False, 'message': 'Mauvais identifiants.'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        abort(400)
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM clients WHERE email = %s", (data['email'],))
    if cur.fetchone():
        cur.close()
        return jsonify({'success': False, 'message': 'Email déjà utilisé.'}), 400
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    cur.execute("INSERT INTO clients (email, password) VALUES (%s, %s)", (data['email'], hashed_password))
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True, 'message': 'Inscription réussie.'})

@app.route('/api/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Déconnecté.'})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({'success': current_user.is_authenticated})

@app.route('/api/profil', methods=['POST'])
@login_required
def profil():
    data = request.get_json()
    if not data:
        abort(400)
    cur = mysql.connection.cursor()
    if 'email' in data:
        cur.execute("SELECT * FROM clients WHERE email = %s", (data['email'],))
        if cur.fetchone():
            cur.close()
            return jsonify({'success': False, 'message': 'Email déjà utilisé.'}), 400
        cur.execute("UPDATE clients SET email = %s WHERE id = %s", (data['email'], current_user.id))
    if 'password' in data:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        cur.execute("UPDATE clients SET password = %s WHERE id = %s", (hashed_password, current_user.id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True, 'message': 'Profil mis à jour.'})

# ==================== MODELE FILM ====================
class Film:
    def __init__(self, id, titre, duree, genre, description, affiche_url):
        self.id = id
        self.titre = titre
        self.duree = duree
        self.genre = genre
        self.description = description
        self.affiche_url = affiche_url

    @staticmethod
    def get_all_films():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM films ORDER BY id DESC")
        result = cur.fetchall()
        cur.close()
        return [Film(*row) for row in result]

# ==================== MODELE SEANCE ====================
class Seance:
    def __init__(self, id, film_id, film_titre, salle_num, places_total, places_restantes, horaire):
        self.id = id
        self.film_id = film_id
        self.film_titre = film_titre
        self.salle_num = salle_num
        self.places_total = places_total
        self.places_restantes = places_restantes
        self.horaire = horaire

    @staticmethod
    def get_all_seances():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT s.id, s.film_id, f.titre, s.salle_num, s.places_total, s.places_restantes, s.horaire
            FROM seances s
            JOIN films f ON f.id = s.film_id
            ORDER BY s.horaire ASC
        """)
        result = cur.fetchall()
        cur.close()
        return [Seance(*row) for row in result]
    
    @staticmethod
    def get_seance_by_id(seance_id):
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT s.id, s.film_id, f.titre, s.salle_num, s.places_total, s.places_restantes, s.horaire
            FROM seances s
            JOIN films f ON f.id = s.film_id
            WHERE s.id = %s
        """, (seance_id,))
        row = cur.fetchone()
        cur.close()
        return Seance(*row) if row else None

def _parse_datetime(dt_str: str) -> str:
    return (dt_str or '').replace('T', ' ')

# ==================== ROUTES FILMS ====================
@app.route('/api/films', methods=['GET'])
@login_required
def get_films():
    films = Film.get_all_films()
    return jsonify([
        {
            'id': f.id,
            'titre': f.titre,
            'duree': f.duree,
            'genre': f.genre,
            'description': f.description,
            'affiche_url': f.affiche_url,
        }
        for f in films
    ])

@app.route('/api/seances', methods=['GET'])
@login_required
def get_seances():
    seances = Seance.get_all_seances()
    return jsonify([
        {
            'id': s.id,
            'film_id': s.film_id,
            'film_titre': s.film_titre,
            'salle_num': s.salle_num,
            'places_total': s.places_total,
            'places_restantes': s.places_restantes,
            'horaire': str(s.horaire),
        }
        for s in seances
    ])

@app.route('/api/seances/<int:film_id>', methods=['GET'])
@login_required
def get_seances_by_film(film_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT s.id, s.film_id, f.titre, s.salle_num, s.places_total, s.places_restantes, s.horaire
        FROM seances s
        JOIN films f ON f.id = s.film_id
        WHERE s.film_id = %s
        ORDER BY s.horaire ASC
    """, (film_id,))
    rows = cur.fetchall()
    cur.close()
    return jsonify([
        {
            'id': row[0],
            'film_id': row[1],
            'film_titre': row[2],
            'salle_num': row[3],
            'places_total': row[4],
            'places_restantes': row[5],
            'horaire': str(row[6]),
        }
        for row in rows
    ])

# ==================== ROUTES TICKETS ====================
@app.route('/api/tickets', methods=['GET'])
@login_required
def get_tickets():
    cur = mysql.connection.cursor()
    if current_user.is_admin:
        cur.execute("""
            SELECT t.id, t.seance_id, f.titre, t.client_id, c.email, t.nb_places, t.date_reservation, t.statut
            FROM tickets t
            JOIN seances s ON s.id = t.seance_id
            JOIN films f ON f.id = s.film_id
            JOIN clients c ON c.id = t.client_id
            ORDER BY t.date_reservation DESC
        """)
    else:
        cur.execute("""
            SELECT t.id, t.seance_id, f.titre, t.client_id, c.email, t.nb_places, t.date_reservation, t.statut
            FROM tickets t
            JOIN seances s ON s.id = t.seance_id
            JOIN films f ON f.id = s.film_id
            JOIN clients c ON c.id = t.client_id
            WHERE t.client_id = %s
            ORDER BY t.date_reservation DESC
        """, (current_user.id,))
    rows = cur.fetchall()
    cur.close()
    return jsonify([
        {
            'id': row[0],
            'seance_id': row[1],
            'film_titre': row[2],
            'client_id': row[3],
            'client_email': row[4],
            'nb_places': row[5],
            'date_reservation': str(row[6]),
            'statut': row[7],
        }
        for row in rows
    ])

@app.route('/api/tickets', methods=['POST'])
@login_required
def create_ticket():
    data = request.get_json()
    if not data:
        abort(400)
    
    try:
        seance_id = int(data.get('seance_id'))
        nb_places = int(data.get('nb_places', 1))
        if nb_places < 1 or nb_places > 10:
            return jsonify({'success': False, 'message': 'Nombre de places invalide (1-10).'}), 400
    except Exception:
        return jsonify({'success': False, 'message': 'Données invalides.'}), 400
    
    cur = mysql.connection.cursor()
    
    # Vérifier que la séance existe et a assez de places
    cur.execute("SELECT places_restantes FROM seances WHERE id = %s", (seance_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        return jsonify({'success': False, 'message': 'Séance introuvable.'}), 404
    
    places_restantes = row[0]
    if places_restantes < nb_places:
        cur.close()
        return jsonify({'success': False, 'message': f'Plus que {places_restantes} place(s) disponible(s).'}), 409
    
    # Créer la réservation
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cur.execute(
        "INSERT INTO tickets (seance_id, client_id, nb_places, date_reservation, statut) VALUES (%s, %s, %s, %s, 'CONFIRME')",
        (seance_id, current_user.id, nb_places, now)
    )
    
    # Mettre à jour les places restantes
    cur.execute(
        "UPDATE seances SET places_restantes = places_restantes - %s WHERE id = %s",
        (nb_places, seance_id)
    )
    
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True, 'message': f'{nb_places} place(s) réservée(s) avec succès.'})

@app.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
@login_required
def cancel_ticket(ticket_id):
    cur = mysql.connection.cursor()
    
    # Récupérer les infos du ticket
    cur.execute("SELECT client_id, seance_id, nb_places FROM tickets WHERE id = %s", (ticket_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        return jsonify({'success': False, 'message': 'Ticket introuvable.'}), 404
    
    client_id, seance_id, nb_places = row
    
    if (not current_user.is_admin) and client_id != current_user.id:
        cur.close()
        abort(403)
    
    # Annuler le ticket
    cur.execute("UPDATE tickets SET statut = 'ANNULE' WHERE id = %s", (ticket_id,))
    
    # Remettre les places disponibles
    cur.execute(
        "UPDATE seances SET places_restantes = places_restantes + %s WHERE id = %s",
        (nb_places, seance_id)
    )
    
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True, 'message': 'Réservation annulée.'})

# ==================== ROUTES ADMIN ====================
@app.route('/api/films', methods=['POST'])
@login_required
def add_film():
    if not current_user.is_admin:
        abort(403)
    data = request.get_json()
    if not data:
        abort(400)
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO films (titre, duree, genre, description, affiche_url) VALUES (%s, %s, %s, %s, %s)",
        (data['titre'], data['duree'], data['genre'], data.get('description', ''), data.get('affiche_url', ''))
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True, 'message': 'Film ajouté.'})

@app.route('/api/seances', methods=['POST'])
@login_required
def add_seance():
    if not current_user.is_admin:
        abort(403)
    data = request.get_json()
    if not data:
        abort(400)
    
    horaire = _parse_datetime(data.get('horaire'))
    if not horaire:
        return jsonify({'success': False, 'message': 'Horaire requis.'}), 400
    
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO seances (film_id, salle_num, places_total, places_restantes, horaire) VALUES (%s, %s, %s, %s, %s)",
        (data['film_id'], data['salle_num'], data['places_total'], data['places_total'], horaire)
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True, 'message': 'Séance ajoutée.'})

@app.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    if not current_user.is_admin:
        abort(403)
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, email, is_admin FROM clients")
    result = cur.fetchall()
    cur.close()
    return jsonify([{'id': row[0], 'email': row[1], 'is_admin': bool(row[2])} for row in result])

# ==================== INIT DATABASE ====================
def initialize_database():
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Table clients
        cur.execute("SHOW TABLES LIKE 'clients'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE clients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            admin_email = 'admin'
            admin_password = bcrypt.generate_password_hash('admin').decode('utf-8')
            cur.execute("INSERT INTO clients (email, password, is_admin) VALUES (%s, %s, 1)", (admin_email, admin_password))
        
        # Table films
        cur.execute("SHOW TABLES LIKE 'films'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE films (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    titre VARCHAR(255) NOT NULL,
                    duree INT NOT NULL,
                    genre VARCHAR(100) NOT NULL,
                    description TEXT,
                    affiche_url VARCHAR(500)
                )
            """)
            # Films de démo
            cur.execute("""
                INSERT INTO films (titre, duree, genre, description, affiche_url) VALUES
                ('Dune 2', 166, 'Science-fiction', 'Suite de l''épopée sur Arrakis', 'https://sf2.cnetfrance.fr/wp-content/uploads/cnet/2024/02/dune-2-actrice-mystere.jpg'),
                ('Barbie', 114, 'Comédie', 'Dans le monde parfait de Barbie', 'https://u-mercari-images.mercdn.net/photos/m15618219739_1.jpg?width=768&quality=75&_=1756253068'),
                ('Oppenheimer', 180, 'Drame historique', 'L''histoire du père de la bombe atomique', 'https://fr.web.img5.acsta.net/pictures/23/05/26/16/52/2793170.jpg')
            """)
        
        # Table seances
        cur.execute("SHOW TABLES LIKE 'seances'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE seances (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    film_id INT NOT NULL,
                    salle_num INT NOT NULL,
                    places_total INT NOT NULL,
                    places_restantes INT NOT NULL,
                    horaire DATETIME NOT NULL,
                    FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE CASCADE
                )
            """)
            # Séances de démo
            from datetime import datetime, timedelta
            now = datetime.now()
            cur.execute("""
                INSERT INTO seances (film_id, salle_num, places_total, places_restantes, horaire) VALUES
                (1, 5, 120, 120, %s),
                (1, 5, 120, 98, %s),
                (2, 3, 85, 85, %s),
                (3, 8, 200, 145, %s)
            """, (
                (now + timedelta(days=1, hours=14)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=1, hours=18)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=2, hours=20)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=3, hours=21)).strftime('%Y-%m-%d %H:%M:%S'),
            ))
        
        # Table tickets
        cur.execute("SHOW TABLES LIKE 'tickets'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    seance_id INT NOT NULL,
                    client_id INT NOT NULL,
                    nb_places INT NOT NULL,
                    date_reservation DATETIME NOT NULL,
                    statut VARCHAR(20) NOT NULL DEFAULT 'CONFIRME',
                    FOREIGN KEY (seance_id) REFERENCES seances(id) ON DELETE CASCADE,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
        
        mysql.connection.commit()
        cur.close()

if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=5000, debug=True)