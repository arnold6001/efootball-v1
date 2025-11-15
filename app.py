# app.py - eFootball Freaks (Python 3 + Flask + SQLite)
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import itertools

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'efootball-freaks-arnold-2025')
DB_NAME = 'data/efootball.db'

# Ensure data folder
os.makedirs('data', exist_ok=True)

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tournament_players (
            tournament_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS fixtures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            home TEXT,
            away TEXT,
            home_score INTEGER DEFAULT 0,
            away_score INTEGER DEFAULT 0,
            played INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS standings (
            tournament_id INTEGER,
            player TEXT,
            played INTEGER DEFAULT 0,
            won INTEGER DEFAULT 0,
            drawn INTEGER DEFAULT 0,
            lost INTEGER DEFAULT 0,
            gf INTEGER DEFAULT 0,
            ga INTEGER DEFAULT 0,
            gd INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = generate_password_hash(request.form['password'])
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
            conn.commit()
            flash('Registered! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username already taken!', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user'] = {'id': user['id'], 'username': user['username']}
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('login'))
    user_id = session['user']['id']
    conn = get_db()
    tournaments = conn.execute('''
        SELECT t.* FROM tournaments t
        JOIN tournament_players tp ON t.id = tp.tournament_id
        WHERE tp.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=session['user'], tournaments=tournaments)

@app.route('/tournament/create', methods=['POST'])
def create_tournament():
    if not session.get('user'): return redirect(url_for('login'))
    name = request.form['name'].strip()
    created_by = session['user']['username']
    conn = get_db()
    cursor = conn.execute('INSERT INTO tournaments (name, created_by) VALUES (?, ?)', (name, created_by))
    tid = cursor.lastrowid
    conn.execute('INSERT INTO tournament_players (tournament_id, user_id) VALUES (?, ?)', (tid, session['user']['id']))
    conn.commit()
    conn.close()
    flash('Tournament created!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/tournament/<int:tid>')
def view_tournament(tid):
    if not session.get('user'): return redirect(url_for('login'))
    conn = get_db()
    tournament = conn.execute('SELECT * FROM tournaments WHERE id = ?', (tid,)).fetchone()
    if not tournament:
        flash('Tournament not found', 'error')
        return redirect(url_for('dashboard'))
    players = [row['username'] for row in conn.execute('''
        SELECT u.username FROM users u JOIN tournament_players tp ON u.id = tp.user_id
        WHERE tp.tournament_id = ?
    ''', (tid,)).fetchall()]
    fixtures = conn.execute('SELECT * FROM fixtures WHERE tournament_id = ? ORDER BY id', (tid,)).fetchall()
    standings = conn.execute('SELECT * FROM standings WHERE tournament_id = ? ORDER BY points DESC, gd DESC', (tid,)).fetchall()
    conn.close()
    return render_template('tournament.html', tournament=tournament, players=players, fixtures=fixtures, standings=standings, user=session['user'])

@app.route('/tournament/join/<int:tid>', methods=['POST'])
def join_tournament(tid):
    if not session.get('user'): return redirect(url_for('login'))
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO tournament_players (tournament_id, user_id) VALUES (?, ?)', (tid, session['user']['id']))
    conn.commit()
    conn.close()
    flash('Joined tournament!', 'success')
    return redirect(url_for('view_tournament', tid=tid))

@app.route('/tournament/generate/<int:tid>', methods=['POST'])
def generate_fixtures(tid):
    if not session.get('user'): return redirect(url_for('login'))
    conn = get_db()
    players = [row['username'] for row in conn.execute('''
        SELECT u.username FROM users u JOIN tournament_players tp ON u.id = tp.user_id
        WHERE tp.tournament_id = ?
    ''', (tid,)).fetchall()]
    if len(players) < 2:
        flash('Need at least 2 players to generate fixtures', 'error')
        return redirect(url_for('view_tournament', tid=tid))
    conn.execute('DELETE FROM fixtures WHERE tournament_id = ?', (tid,))
    conn.execute('DELETE FROM standings WHERE tournament_id = ?', (tid,))
    for home, away in itertools.combinations(players, 2):
        conn.execute('INSERT INTO fixtures (tournament_id, home, away) VALUES (?, ?, ?)', (tid, home, away))
        conn.execute('INSERT INTO fixtures (tournament_id, home, away) VALUES (?, ?, ?)', (tid, away, home))
    for p in players:
        conn.execute('INSERT INTO standings (tournament_id, player) VALUES (?, ?)', (tid, p))
    conn.commit()
    conn.close()
    flash('Fixtures generated!', 'success')
    return redirect(url_for('view_tournament', tid=tid))

@app.route('/tournament/score/<int:tid>', methods=['POST'])
def update_score(tid):
    if not session.get('user'): return redirect(url_for('login'))
    fixture_id = int(request.form['fixture_id'])
    home_score = int(request.form['home_score'])
    away_score = int(request.form['away_score'])
    conn = get_db()
    fixture = conn.execute('SELECT * FROM fixtures WHERE id = ?', (fixture_id,)).fetchone()
    conn.execute('UPDATE fixtures SET home_score = ?, away_score = ?, played = 1 WHERE id = ?', (home_score, away_score, fixture_id))
    for player, gf, ga in [(fixture['home'], home_score, away_score), (fixture['away'], away_score, home_score)]:
        standing = conn.execute('SELECT * FROM standings WHERE tournament_id = ? AND player = ?', (tid, player)).fetchone()
        played = standing['played'] + 1
        won = standing['won'] + (1 if gf > ga else 0)
        drawn = standing['drawn'] + (1 if gf == ga else 0)
        lost = standing['lost'] + (1 if gf < ga else 0)
        points = won * 3 + drawn
        gd = (standing['gf'] + gf) - (standing['ga'] + ga)
        conn.execute('''UPDATE standings SET played = ?, won = ?, drawn = ?, lost = ?, gf = gf + ?, ga = ga + ?, gd = ?, points = ?
                        WHERE tournament_id = ? AND player = ?''',
                     (played, won, drawn, lost, gf, ga, gd, points, tid, player))
    conn.commit()
    conn.close()
    flash('Score updated!', 'success')
    return redirect(url_for('view_tournament', tid=tid))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)