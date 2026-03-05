import os, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'bengala_2026_MUDA_ESTA_CHAVE_SECRET'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bengala.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── DATABASE ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, posicao TEXT, numero TEXT,
            idade INTEGER, altura TEXT, pe TEXT,
            nacionalidade TEXT DEFAULT 'Mocambicana',
            bio TEXT, foto TEXT DEFAULT 'logo.png',
            jogos INTEGER DEFAULT 0, golos INTEGER DEFAULT 0,
            assistencias INTEGER DEFAULT 0, minutos INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL, categoria TEXT, data TEXT,
            imagem TEXT DEFAULT 'logo.png', resumo TEXT, conteudo TEXT,
            destaque INTEGER DEFAULT 0, publicado INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL, data TEXT, hora TEXT, local TEXT,
            descricao TEXT, status TEXT DEFAULT 'upcoming',
            tipo TEXT DEFAULT 'evento',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS galeria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL, imagem TEXT NOT NULL,
            descricao TEXT, categoria TEXT, ordem INTEGER DEFAULT 0,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS directoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, cargo TEXT,
            foto TEXT DEFAULT 'logo.png', bio TEXT,
            email TEXT, telefone TEXT,
            ordem INTEGER DEFAULT 0, ativo INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS declaracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT NOT NULL, cargo TEXT,
            foto TEXT DEFAULT 'logo.png',
            conteudo TEXT, contexto TEXT, data TEXT, tag TEXT,
            tipo TEXT DEFAULT 'declaracao',
            publicado INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS site_config (
            chave TEXT PRIMARY KEY, valor TEXT
        );
    """)
    if not db.execute("SELECT id FROM users WHERE username='admin'").fetchone():
        db.execute("INSERT INTO users (username,password) VALUES (?,?)",
                   ('admin', generate_password_hash('bengala2026')))
    defaults = [
        ('site_nome','FC BENGALA'),('site_subtitulo','Construindo comunidade atraves do desporto'),
        ('whatsapp','+258864695548'),('email','benga@geral.co.mz'),
        ('localizacao','Massingirine, Nacala-a-Velha'),('facebook','#'),('instagram','#')
    ]
    for k, v in defaults:
        if not db.execute("SELECT chave FROM site_config WHERE chave=?", (k,)).fetchone():
            db.execute("INSERT INTO site_config VALUES (?,?)", (k, v))
    db.commit()
    db.close()

# ─── AUTH ────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Nao autorizado'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json()
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE username=?", (d.get('username'),)).fetchone()
    db.close()
    if u and check_password_hash(u['password'], d.get('password', '')):
        session['user_id'] = u['id']
        session['username'] = u['username']
        return jsonify({'success': True, 'username': u['username']})
    return jsonify({'error': 'Credenciais invalidas'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/me')
def me():
    if 'user_id' in session:
        return jsonify({'loggedin': True, 'username': session['username']})
    return jsonify({'loggedin': False})

# ─── UPLOAD ──────────────────────────────────────────────────────────────────
@app.route('/api/upload', methods=['POST'])
@login_required
def upload():
    f = request.files.get('file')
    if f and '.' in f.filename and f.filename.rsplit('.', 1)[1].lower() in {'png','jpg','jpeg','gif','webp','pdf'}:
        name = datetime.now().strftime('%Y%m%d_%H%M%S_') + secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_FOLDER, name))
        return jsonify({'success': True, 'filename': name, 'url': '/static/uploads/' + name})
    return jsonify({'error': 'Ficheiro invalido'}), 400

# ─── STATS ───────────────────────────────────────────────────────────────────
@app.route('/api/stats')
@login_required
def stats():
    db = get_db()
    s = {
        'jogadores':   db.execute("SELECT COUNT(*) FROM jogadores WHERE ativo=1").fetchone()[0],
        'noticias':    db.execute("SELECT COUNT(*) FROM noticias WHERE publicado=1").fetchone()[0],
        'eventos':     db.execute("SELECT COUNT(*) FROM eventos").fetchone()[0],
        'galeria':     db.execute("SELECT COUNT(*) FROM galeria").fetchone()[0],
        'declaracoes': db.execute("SELECT COUNT(*) FROM declaracoes WHERE publicado=1").fetchone()[0],
        'directoria':  db.execute("SELECT COUNT(*) FROM directoria WHERE ativo=1").fetchone()[0],
    }
    db.close()
    return jsonify(s)

# ─── CRUD FACTORY ─────────────────────────────────────────────────────────────
def make_crud(table, fields, order):
    def get_all():
        db = get_db()
        rows = db.execute("SELECT * FROM {} ORDER BY {}".format(table, order)).fetchall()
        db.close()
        return jsonify([dict(r) for r in rows])

    def create():
        d = request.get_json()
        db = get_db()
        cols = ','.join(fields)
        ph = ','.join(['?'] * len(fields))
        db.execute("INSERT INTO {} ({}) VALUES ({})".format(table, cols, ph),
                   [d.get(f) for f in fields])
        db.commit()
        id_ = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.close()
        return jsonify({'success': True, 'id': id_})

    def update(id):
        d = request.get_json()
        db = get_db()
        sets = ','.join(["{}=?".format(f) for f in fields])
        db.execute("UPDATE {} SET {} WHERE id=?".format(table, sets),
                   [d.get(f) for f in fields] + [id])
        db.commit()
        db.close()
        return jsonify({'success': True})

    def delete(id):
        db = get_db()
        db.execute("DELETE FROM {} WHERE id=?".format(table), (id,))
        db.commit()
        db.close()
        return jsonify({'success': True})

    app.add_url_rule('/api/'+table,          'get_'+table,  get_all,                    methods=['GET'])
    app.add_url_rule('/api/'+table,          'post_'+table, login_required(create),     methods=['POST'])
    app.add_url_rule('/api/'+table+'/<int:id>','put_'+table,  login_required(update),   methods=['PUT'])
    app.add_url_rule('/api/'+table+'/<int:id>','del_'+table,  login_required(delete),   methods=['DELETE'])

make_crud('jogadores',
    ['nome','posicao','numero','idade','altura','pe','nacionalidade','bio','foto',
     'jogos','golos','assistencias','minutos','ativo'],
    'CAST(numero AS INTEGER)')
make_crud('noticias',
    ['titulo','categoria','data','imagem','resumo','conteudo','destaque','publicado'],
    'criado_em DESC')
make_crud('eventos',
    ['titulo','data','hora','local','descricao','status','tipo'],
    'criado_em DESC')
make_crud('galeria',
    ['titulo','imagem','descricao','categoria','ordem'],
    'ordem, criado_em DESC')
make_crud('directoria',
    ['nome','cargo','foto','bio','email','telefone','ordem','ativo'],
    'ordem')
make_crud('declaracoes',
    ['autor','cargo','foto','conteudo','contexto','data','tag','tipo','publicado'],
    'criado_em DESC')

# ─── CONFIG ───────────────────────────────────────────────────────────────────
@app.route('/api/config', methods=['GET'])
def get_config():
    db = get_db()
    rows = db.execute("SELECT * FROM site_config").fetchall()
    db.close()
    return jsonify({r['chave']: r['valor'] for r in rows})

@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    d = request.get_json()
    db = get_db()
    for k, v in d.items():
        db.execute("INSERT OR REPLACE INTO site_config VALUES (?,?)", (k, v))
    db.commit()
    db.close()
    return jsonify({'success': True})

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    d = request.get_json()
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    if not check_password_hash(u['password'], d.get('current', '')):
        db.close()
        return jsonify({'error': 'Password atual incorreta'}), 400
    db.execute("UPDATE users SET password=? WHERE id=?",
               (generate_password_hash(d.get('new')), session['user_id']))
    db.commit()
    db.close()
    return jsonify({'success': True})

# ─── PUBLIC API ───────────────────────────────────────────────────────────────
for _t, _w, _o in [
    ('jogadores', 'ativo=1',     'CAST(numero AS INTEGER)'),
    ('noticias',  'publicado=1', 'criado_em DESC'),
    ('eventos',   '1=1',         'criado_em DESC'),
    ('galeria',   '1=1',         'ordem, criado_em DESC'),
    ('directoria','ativo=1',     'ordem'),
    ('declaracoes','publicado=1','criado_em DESC'),
]:
    def _make(_t=_t, _w=_w, _o=_o):
        def pub():
            db = get_db()
            rows = db.execute("SELECT * FROM {} WHERE {} ORDER BY {}".format(_t, _w, _o)).fetchall()
            db.close()
            return jsonify([dict(r) for r in rows])
        app.add_url_rule('/api/public/'+_t, 'pub_'+_t, pub)
    _make()

# ─── PAGES ───────────────────────────────────────────────────────────────────
@app.route('/admin')
@app.route('/admin/')
def admin_page():
    return send_from_directory('templates', 'admin.html')

@app.route('/')
def index_page():
    return send_from_directory('.', 'index.html')

# ─── WSGI (PythonAnywhere) ────────────────────────────────────────────────────
init_db()

if __name__ == '__main__':
    app.run(debug=True)
