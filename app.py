# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET', 'efootball-arnold-2025')
DB_PATH = 'data/efootball.db'

# Ensure data folder
os.makedirs('data', exist_ok=True)

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password TEXT
        );
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_by TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS tournament_players (
            tournament_id INTEGER,
            user_id INTEGER
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

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = hash_password(request.form['password'])
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, password))
            conn.commit()
            user_id = c.lastrowid
            session['user'] = {'id': user_id, 'username': username}
            return redirect('/dashboard')
        except sqlite3.IntegrityError:
            flash("Username already taken!")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = {'id': user[0], 'username': user[1]}
            return redirect('/dashboard')
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT t.id, t.name, COUNT(tp.user_id) as players
        FROM tournaments t
        JOIN tournament_players tp ON t.id = tp.tournament_id
        WHERE tp.user_id = ?
        GROUP BY t.id
    """, (session['user']['id'],))
    tournaments = c.fetchall()
    conn.close()
    return render_template('dashboard.html', tournaments=tournaments, user=session['user'])

@app.route('/tournament/create', methods=['POST'])
def create_tournament():
    if 'user' not in session:
        return redirect('/login')
    name = request.form['name']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tournaments (name, created_by, created_at) VALUES (?, ?, ?)",
              (name, session['user']['username'], datetime.now().strftime('%Y-%m-%d')))
    tid = c.lastrowid
    c.execute("INSERT INTO tournament_players (tournament_id, user_id) VALUES (?, ?)", (tid, session['user']['id']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/tournament/<int:tid>')
def tournament(tid):
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tournaments WHERE id=?", (tid,))
    tournament = c.fetchone()
    if not tournament:
        return "Not found", 404

    # Check if user is in tournament
    c.execute("SELECT 1 FROM tournament_players WHERE tournament_id=? AND user_id=?", (tid, session['user']['id']))
    if not c.fetchone():
        c.execute("INSERT INTO tournament_players (tournament_id, user_id) VALUES (?, ?)", (tid, session['user']['id']))
        conn.commit()

    c.execute("SELECT username FROM users u JOIN tournament_players tp ON u.id=tp.user_id WHERE tp.tournament_id=?", (tid,))
    players = [row[0] for row in c.fetchall()]

    c.execute("SELECT * FROM fixtures WHERE tournament_id=? ORDER BY id", (tid,))
    fixtures = c.fetchall()

    c.execute("SELECT * FROM standings WHERE tournament_id=? ORDER BY points DESC, gd DESC", (tid,))
    standings = c.fetchall()

    conn.close()
    return render_template('tournament.html', 
                         tournament=tournament, 
                         players=players, 
                         fixtures=fixtures, 
                         standings=standings,
                         user=session['user'])

@app.route('/tournament/generate/<int:tid>')
def generate_fixtures(tid):
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM users u JOIN tournament_players tp ON u.id=tp.user_id WHERE tp.tournament_id=?", (tid,))
    players = [row[0] for row in c.fetchall()]
    if len(players) < 2:
        return redirect(f'/tournament/{tid}')

    # Clear old
    c.execute("DELETE FROM fixtures WHERE tournament_id=?", (tid,))
    c.execute("DELETE FROM standings WHERE tournament_id=?", (tid,))

    # Generate round-robin
    import itertools
    for home, away in itertools.combinations(players, 2):
        c.execute("INSERT INTO fixtures (tournament_id, home, away) VALUES (?, ?, ?)", (tid, home, away))
        c.execute("INSERT INTO fixtures (tournament_id, home, away) VALUES (?, ?, ?)", (tid, away, home))
    
    for player in players:
        c.execute("INSERT INTO standings (tournament_id, player) VALUES (?, ?)", (tid, player))

    conn.commit()
    conn.close()
    return redirect(f'/tournament/{tid}')

@app.route('/tournament/score/<int:tid>', methods=['POST'])
def update_score(tid):
    if 'user' not in session:
        return redirect('/login')
    fixture_id = int(request.form['fixture_id'])
    home_score = int(request.form['home_score'])
    away_score = int(request.form['away_score'])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE fixtures SET home_score=?, away_score=?, played=1 WHERE id=?", (home_score, away_score, fixture_id))
    
    c.execute("SELECT home, away FROM fixtures WHERE id=?", (fixture_id,))
    home, away = c.fetchone()

    # Update standings
    def update_player(player, gf, ga):
        c.execute("SELECT * FROM standings WHERE tournament_id=? AND player=?", (tid, player))
        s = c.fetchone()
        played = s[2] + 1
        won = s[3] + (1 if gf > ga else 0)
        drawn = s[4] + (1 if gf == ga else 0)
        lost = s[5] + (1 if gf < ga else 0)
        points = won * 3 + drawn
        gd = (s[6] + gf) - (s[7] + ga)
        c.execute("""UPDATE standings SET played=?, won=?, drawn=?, lost=?, 
                     gf=gf+?, ga=ga+?, gd=?, points=? 
                     WHERE tournament_id=? AND player=?""",
                  (played, won, drawn, lost, gf, ga, gd, points, tid, player))

    update_player(home, home_score, away_score)
    update_player(away, away_score, home_score)
    
    conn.commit()
    conn.close()
    return redirect(f'/tournament/{tid}')

if __name__ == '__main__':
    app.run(debug=False)