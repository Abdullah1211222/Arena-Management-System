import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  email TEXT,
                  role TEXT DEFAULT 'player',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tournament registrations table
    c.execute('''CREATE TABLE IF NOT EXISTS tournament_registrations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  tournament_id INTEGER,
                  status TEXT DEFAULT 'registered',
                  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Tournaments table (for league owners to create)
    c.execute('''CREATE TABLE IF NOT EXISTS tournaments_db
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  game TEXT,
                  max_players INTEGER,
                  status TEXT DEFAULT 'upcoming',
                  sponsor_name TEXT,
                  created_by INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (created_by) REFERENCES users (id))''')
    
    # Advertisements table
    c.execute('''CREATE TABLE IF NOT EXISTS advertisements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  description TEXT,
                  advertiser_id INTEGER,
                  tournament_id INTEGER,
                  budget REAL,
                  status TEXT DEFAULT 'active',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (advertiser_id) REFERENCES users (id))''')
    
    # Insert default users if not exists
    default_users = [
        ('test', 'test', 'test@arena.com', 'player'),
        ('league', 'test', 'league@arena.com', 'league_owner'),
        ('advertiser', 'test', 'advertiser@arena.com', 'advertiser'),
        ('player1', 'password', 'player1@arena.com', 'player'),
        ('player2', 'password', 'player2@arena.com', 'player'),
        ('player3', 'password', 'player3@arena.com', 'player')
    ]
    
    for username, password, email, role in default_users:
        try:
            c.execute("INSERT OR IGNORE INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                     (username, password, email, role))
        except:
            pass
    
    # Insert default tournaments if not exists
    default_tournaments = [
        ('🔥 TEKKEN 8 EVO Championship 2024', 'Tekken 8', 32, 'live', 'Razer Inc.', 2),
        ('🎮 PUBG Mobile Global Championship', 'PUBG Mobile', 100, 'live', 'Red Bull', 2),
        ('🎯 Valorant Champions 2024', 'Valorant', 16, 'live', 'Logitech G', 2),
        ('⚔️ DOTA 2 The International', 'DOTA 2', 18, 'completed', 'PGL', 2),
        ('👑 League of Legends Worlds 2024', 'League of Legends', 24, 'live', 'Mastercard', 2)
    ]
    
    for name, game, max_players, status, sponsor, created_by in default_tournaments:
        try:
            c.execute("INSERT OR IGNORE INTO tournaments_db (name, game, max_players, status, sponsor_name, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                     (name, game, max_players, status, sponsor, created_by))
        except:
            pass
    
    conn.commit()
    conn.close()

init_db()

# CSS Styles
CSS = '''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: white; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
.navbar { background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); padding: 1rem 0; position: fixed; width: 100%; top: 0; z-index: 1000; border-bottom: 1px solid rgba(255,255,255,0.1); }
.nav-container { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 20px; }
.logo { font-size: 1.8rem; font-weight: bold; color: white; text-decoration: none; display: flex; align-items: center; gap: 10px; }
.nav-links { display: flex; gap: 15px; align-items: center; }
.btn { padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; transition: all 0.3s; border: 2px solid transparent; }
.btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4); }
.btn-live { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; animation: pulse 1.5s infinite; }
.btn-highlight { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
.btn-outline { background: transparent; border-color: rgba(255, 255, 255, 0.2); color: white; }
.btn-outline:hover { background: rgba(255, 255, 255, 0.1); }
.btn-success { background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); color: white; }
.btn-warning { background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%); color: white; }
.btn-admin { background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%); color: white; }
@keyframes pulse { 0% {opacity:1} 50% {opacity:0.7} 100% {opacity:1} }
.live-badge { background: #ef4444; color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; display: inline-block; animation: pulse 1.5s infinite; }
.hero { padding: 180px 0 100px; text-align: center; background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%); }
.hero-title { font-size: 4rem; background: linear-gradient(135deg, #667eea 0%, #f093fb 50%, #f5576c 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }
.hero-subtitle { font-size: 1.25rem; color: #cbd5e1; max-width: 600px; margin: 0 auto 40px; }
.tournament-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; margin-top: 30px; }
.tournament-card { background: rgba(255,255,255,0.05); border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); transition: transform 0.3s; }
.tournament-card:hover { transform: translateY(-5px); }
.tournament-header { background: rgba(255,255,255,0.08); padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.tournament-body { padding: 20px; }
.tournament-footer { padding: 20px; background: rgba(255,255,255,0.03); border-top: 1px solid rgba(255,255,255,0.1); }
.video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; margin: 20px 0; background: #000; }
.video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }
.score-board { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 16px; text-align: center; margin: 20px 0; }
.score-display { font-size: 4rem; font-weight: bold; margin: 20px 0; }
.player-name { font-size: 1.5rem; margin-bottom: 10px; }
.card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 30px; margin: 20px 0; border: 1px solid rgba(255,255,255,0.1); }
.section { padding: 100px 0; }
.highlights-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin-top: 30px; }
.highlight-card { background: rgba(255,255,255,0.03); border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }
.highlight-content { padding: 20px; }
.alert { padding: 16px; border-radius: 8px; margin: 20px 0; }
.alert-success { background: rgba(72, 187, 120, 0.1); color: #48bb78; }
.alert-danger { background: rgba(245, 101, 101, 0.1); color: #f56565; }
.form-group { margin-bottom: 20px; }
.form-control { width: 100%; padding: 12px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; font-size: 1rem; }
.live-indicator { display: inline-block; width: 12px; height: 12px; background: #ef4444; border-radius: 50%; margin-right: 8px; animation: pulse 1.5s infinite; }
.stream-container { margin-top: 120px; }
.stream-info { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 30px; }
.bracket-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 30px 0; }
.round { display: flex; flex-direction: column; gap: 20px; }
.match { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); }
.match.winner { background: rgba(72, 187, 120, 0.1); border-color: #48bb78; }
.match-player { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
.match-player:last-child { border-bottom: none; }
.leaderboard { width: 100%; border-collapse: collapse; }
.leaderboard th { background: rgba(255,255,255,0.1); padding: 15px; text-align: left; }
.leaderboard td { padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.leaderboard tr:hover { background: rgba(255,255,255,0.05); }
.upcoming-match { background: rgba(255,255,255,0.03); padding: 20px; border-radius: 12px; margin: 10px 0; border: 1px solid rgba(255,255,255,0.1); }
.match-time { color: #f6d365; font-size: 0.9rem; }
.team-logo { width: 40px; height: 40px; border-radius: 50%; background: rgba(255,255,255,0.1); display: inline-flex; align-items: center; justify-content: center; margin-right: 10px; }
.registration-status { display: inline-flex; align-items: center; gap: 5px; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }
.registered { background: rgba(72, 187, 120, 0.2); color: #48bb78; }
.not-registered { background: rgba(245, 101, 101, 0.2); color: #f56565; }
.ad-card { background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 87, 108, 0.1) 100%); border: 1px solid rgba(245, 158, 11, 0.3); }
.ad-badge { background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; }
.ad-banner { background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%); padding: 15px 25px; border-radius: 10px; margin: 20px 0; text-align: center; }
@media (max-width: 768px) {
    .hero-title { font-size: 2.5rem; }
    .tournament-grid, .highlights-grid { grid-template-columns: 1fr; }
    .score-display { font-size: 2.5rem; }
    .container { padding: 0 15px; }
    .bracket-container { grid-template-columns: 1fr; }
}
'''

# Database functions - Convert rows to dictionaries with safe access
def get_db_connection():
    conn = sqlite3.connect('arena.db')
    conn.row_factory = sqlite3.Row
    return conn

def safe_row_to_dict(row):
    """Safely convert SQLite row to dictionary with default values"""
    if row is None:
        return None
    try:
        return dict(row)
    except:
        return None

def safe_rows_to_dict_list(rows):
    """Safely convert multiple SQLite rows to list of dictionaries"""
    if rows is None:
        return []
    try:
        return [dict(row) for row in rows]
    except:
        return []

def check_user_credentials(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                       (username, password)).fetchone()
    conn.close()
    return safe_row_to_dict(user)

def create_user(username, password, email, role='player'):
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                    (username, password, email, role))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def register_for_tournament(user_id, tournament_id):
    conn = get_db_connection()
    
    # Check user role - only players can register
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    user_dict = safe_row_to_dict(user)
    if not user_dict or user_dict.get('role') != 'player':
        conn.close()
        return False, "Only players can register for tournaments"
    
    # Check if already registered
    existing = conn.execute('SELECT * FROM tournament_registrations WHERE user_id = ? AND tournament_id = ?',
                          (user_id, tournament_id)).fetchone()
    
    if existing:
        conn.close()
        return False, "Already registered"
    
    # Check tournament capacity
    tournament = conn.execute('SELECT * FROM tournaments_db WHERE id = ?', (tournament_id,)).fetchone()
    tournament_dict = safe_row_to_dict(tournament)
    if not tournament_dict:
        conn.close()
        return False, "Tournament not found"
    
    # Get current registrations
    current_reg = conn.execute('SELECT COUNT(*) as count FROM tournament_registrations WHERE tournament_id = ?',
                             (tournament_id,)).fetchone()
    current_count = dict(current_reg).get('count', 0) if current_reg else 0
    
    if current_count >= tournament_dict.get('max_players', 0):
        conn.close()
        return False, "Tournament is full"
    
    # Register user
    conn.execute('INSERT INTO tournament_registrations (user_id, tournament_id) VALUES (?, ?)',
                (user_id, tournament_id))
    conn.commit()
    
    conn.close()
    return True, "Registration successful"

def get_user_tournaments(user_id):
    conn = get_db_connection()
    tournaments = conn.execute('''
        SELECT t.*, tr.registered_at 
        FROM tournaments_db t
        JOIN tournament_registrations tr ON t.id = tr.tournament_id
        WHERE tr.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return safe_rows_to_dict_list(tournaments)

def is_user_registered(user_id, tournament_id):
    conn = get_db_connection()
    registration = conn.execute('SELECT * FROM tournament_registrations WHERE user_id = ? AND tournament_id = ?',
                              (user_id, tournament_id)).fetchone()
    conn.close()
    return registration is not None

def get_tournament_registration_count(tournament_id):
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) as count FROM tournament_registrations WHERE tournament_id = ?',
                        (tournament_id,)).fetchone()
    conn.close()
    if count:
        count_dict = dict(count)
        return count_dict.get('count', 0)
    return 0

def create_tournament(name, game, max_players, sponsor_name, created_by):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO tournaments_db (name, game, max_players, sponsor_name, created_by, status) 
                         VALUES (?, ?, ?, ?, ?, 'upcoming')''',
                      (name, game, max_players, sponsor_name, created_by))
        tournament_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return tournament_id
    except Exception as e:
        print(f"Error creating tournament: {e}")
        return None

def create_advertisement(title, description, advertiser_id, tournament_id, budget):
    try:
        conn = get_db_connection()
        conn.execute('''INSERT INTO advertisements (title, description, advertiser_id, tournament_id, budget) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (title, description, advertiser_id, tournament_id, budget))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating ad: {e}")
        return False

def get_tournament_by_id(tournament_id):
    conn = get_db_connection()
    tournament = conn.execute('SELECT * FROM tournaments_db WHERE id = ?', (tournament_id,)).fetchone()
    conn.close()
    return safe_row_to_dict(tournament)

def get_all_tournaments():
    conn = get_db_connection()
    tournaments = conn.execute('SELECT * FROM tournaments_db ORDER BY status DESC, created_at DESC').fetchall()
    conn.close()
    return safe_rows_to_dict_list(tournaments)

def get_live_tournaments():
    conn = get_db_connection()
    tournaments = conn.execute("SELECT * FROM tournaments_db WHERE status = 'live' ORDER BY created_at DESC").fetchall()
    conn.close()
    return safe_rows_to_dict_list(tournaments)

def get_tournament_ads(tournament_id):
    conn = get_db_connection()
    ads = conn.execute('SELECT * FROM advertisements WHERE tournament_id = ? AND status = "active"', (tournament_id,)).fetchall()
    conn.close()
    return safe_rows_to_dict_list(ads)

def get_user_ads(user_id):
    conn = get_db_connection()
    ads = conn.execute('SELECT * FROM advertisements WHERE advertiser_id = ?', (user_id,)).fetchall()
    conn.close()
    return safe_rows_to_dict_list(ads)

def get_active_ads():
    conn = get_db_connection()
    ads = conn.execute('SELECT * FROM advertisements WHERE status = "active" ORDER BY created_at DESC LIMIT 5').fetchall()
    conn.close()
    return safe_rows_to_dict_list(ads)

# Static data for highlights
HIGHLIGHTS = [
    {
        'id': 1,
        'title': '🔥 INSANE CLUTCH by ArslanAsh!',
        'description': '30-second highlight: Best moment from TEKKEN 8 match',
        'tournament': '🔥 TEKKEN 8 EVO Championship 2024',
        'game': 'Tekken 8',
        'url': 'https://www.youtube.com/embed/uMKE_julLAY?start=120&end=150',
        'views': 12500,
        'duration': '30 sec',
        'full_match_duration': '27 min'
    },
    {
        'id': 2,
        'title': '🎯 TenZ ACE ROUND in Finals!',
        'description': '30-second highlight: Key moment from Valorant match',
        'tournament': '🎯 Valorant Champions 2024',
        'game': 'Valorant',
        'url': 'https://www.youtube.com/embed/jGiOaLglOME?start=90&end=120',
        'views': 8900,
        'duration': '30 sec',
        'full_match_duration': '32 min'
    },
    {
        'id': 3,
        'title': '👑 Faker GODLIKE Play!',
        'description': '30-second highlight: Insane outplay from LoL match',
        'tournament': '👑 League of Legends Worlds 2024',
        'game': 'League of Legends',
        'url': 'https://www.youtube.com/embed/p4QG59y6FGE?start=150&end=180',
        'views': 21500,
        'duration': '30 sec',
        'full_match_duration': '35 min'
    }
]

# Static data for brackets and leaderboards
BRACKETS = {
    1: {  # Tekken 8 bracket
        'rounds': [
            {
                'name': 'Round of 32',
                'matches': [
                    {'player1': 'ArslanAsh', 'player2': 'Knee', 'score1': 3, 'score2': 2, 'winner': 1},
                    {'player1': 'JDCR', 'player2': 'Anakin', 'score1': 3, 'score2': 1, 'winner': 1},
                ]
            },
            {
                'name': 'Round of 16',
                'matches': [
                    {'player1': 'ArslanAsh', 'player2': 'JDCR', 'score1': 3, 'score2': 1, 'winner': 1},
                ]
            },
        ]
    },
    3: {  # Valorant bracket
        'rounds': [
            {
                'name': 'Group Stage',
                'matches': [
                    {'player1': 'Sentinels', 'player2': 'LOUD', 'score1': 13, 'score2': 9, 'winner': 1},
                    {'player1': 'FNATIC', 'player2': 'DRX', 'score1': 13, 'score2': 11, 'winner': 1},
                ]
            },
        ]
    }
}

LEADERBOARDS = {
    1: [  # Tekken 8
        {'rank': 1, 'player': 'ArslanAsh', 'wins': 12, 'losses': 2, 'points': 2450},
        {'rank': 2, 'player': 'Knee', 'wins': 11, 'losses': 3, 'points': 2320},
        {'rank': 3, 'player': 'JDCR', 'wins': 10, 'losses': 4, 'points': 2210},
    ],
    2: [  # PUBG
        {'rank': 1, 'team': 'Soniqs', 'kills': 245, 'points': 350},
        {'rank': 2, 'team': 'Natus Vincere', 'kills': 232, 'points': 340},
        {'rank': 3, 'team': 'Four Angry Men', 'kills': 228, 'points': 335},
    ],
    3: [  # Valorant
        {'rank': 1, 'team': 'Sentinels', 'wins': 15, 'losses': 3, 'points': 45},
        {'rank': 2, 'team': 'FNATIC', 'wins': 14, 'losses': 4, 'points': 42},
        {'rank': 3, 'team': 'LOUD', 'wins': 13, 'losses': 5, 'points': 39},
    ],
}

# YouTube URLs for tournaments
TOURNAMENT_VIDEOS = {
    1: {'stream': 'https://www.youtube.com/embed/uMKE_julLAY', 'highlight': 'https://www.youtube.com/embed/uMKE_julLAY?start=120&end=150'},
    2: {'stream': 'https://www.youtube.com/embed/VeRSj_W3dIQ', 'highlight': 'https://www.youtube.com/embed/VeRSj_W3dIQ?start=180&end=210'},
    3: {'stream': 'https://www.youtube.com/embed/jGiOaLglOME', 'highlight': 'https://www.youtube.com/embed/jGiOaLglOME?start=90&end=120'},
    4: {'stream': 'https://www.youtube.com/embed/qdMTOvYBsPQ', 'highlight': 'https://www.youtube.com/embed/qdMTOvYBsPQ?start=240&end=270'},
    5: {'stream': 'https://www.youtube.com/embed/p4QG59y6FGE', 'highlight': 'https://www.youtube.com/embed/p4QG59y6FGE?start=150&end=180'},
}

# ========== FLASK ROUTES ==========

@app.route('/')
def home():
    """Home page with live tournaments"""
    live_tournaments = get_live_tournaments()
    active_ads = get_active_ads()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ARENA - Watch LIVE Esports Tournaments</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/live_matches" class="btn btn-live">🔥 Live Matches</a>
                    <a href="/match_highlights" class="btn btn-highlight">📹 Highlights</a>
                    <a href="/upcoming" class="btn btn-outline">📅 Upcoming</a>
                    {% if 'user_id' in session %}
                        {% if session.get('role') == 'player' %}
                        <a href="/my_tournaments" class="btn btn-success">🏆 My Tournaments</a>
                        {% endif %}
                        {% if session.get('role') == 'league_owner' %}
                        <a href="/create_tournament" class="btn btn-warning">🎮 Create Tournament</a>
                        {% endif %}
                        {% if session.get('role') == 'advertiser' %}
                        <a href="/create_ad" class="btn btn-admin">📢 Create Ad</a>
                        <a href="/my_ads" class="btn btn-admin">📋 My Ads</a>
                        {% endif %}
                        <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }} ({{ session.get('role', 'guest') }})</span>
                        <a href="/logout" class="btn btn-outline">Logout</a>
                    {% else %}
                        <a href="/login" class="btn btn-outline">Login</a>
                        <a href="/register" class="btn btn-primary">Register</a>
                    {% endif %}
                </div>
            </div>
        </nav>

        <!-- Advertisement Banner -->
        {% if active_ads %}
        <div style="margin-top: 80px; padding: 0 20px;">
            {% for ad in active_ads %}
            <div class="ad-banner">
                <h3>{{ ad.get('title', 'Advertisement') }}</h3>
                <p>{{ ad.get('description', '') }}</p>
                <small>Sponsored Ad | Budget: ${{ ad.get('budget', 0) }}</small>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <section class="hero">
            <div class="container">
                <h1 class="hero-title">Watch LIVE Esports Tournaments</h1>
                <p class="hero-subtitle">Full matches • 30-second compressed highlights • Perfect sound</p>
                <div style="margin-top: 40px;">
                    <a href="/live_matches" class="btn btn-live" style="padding: 15px 30px; font-size: 1.1rem;">🔥 Watch Live Matches</a>
                    <a href="/match_highlights" class="btn btn-highlight" style="padding: 15px 30px; font-size: 1.1rem; margin-left: 15px;">📹 View 30-sec Highlights</a>
                    <a href="/upcoming" class="btn btn-primary" style="padding: 15px 30px; font-size: 1.1rem; margin-left: 15px;">📅 Upcoming Matches</a>
                </div>
            </div>
        </section>

        <section class="section">
            <div class="container">
                <h2 style="text-align: center; margin-bottom: 40px; font-size: 2.5rem;">🔥 LIVE Tournaments Now</h2>
                
                {% if live_tournaments %}
                <div class="tournament-grid">
                    {% for tournament in live_tournaments %}
                    {% set reg_count = get_tournament_registration_count(tournament.get('id', 0)) %}
                    <div class="tournament-card">
                        <div class="tournament-header">
                            <h3 style="margin-bottom: 10px;">{{ tournament.get('name', 'Tournament') }}</h3>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span class="live-badge">LIVE NOW</span>
                                <span style="background: rgba(102, 126, 234, 0.2); color: #667eea; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">{{ tournament.get('game', 'Game') }}</span>
                            </div>
                        </div>
                        <div class="tournament-body">
                            <div style="display: flex; flex-direction: column; gap: 15px;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 1.2rem;">👥</span>
                                    <span>{{ reg_count }}/{{ tournament.get('max_players', 0) }} players registered</span>
                                </div>
                                {% if tournament.get('sponsor_name') %}
                                <div style="background: rgba(255,215,0,0.1); padding: 8px 12px; border-radius: 8px;">
                                    <small>Sponsored by {{ tournament.get('sponsor_name') }}</small>
                                </div>
                                {% endif %}
                                <div style="background: rgba(255, 215, 0, 0.1); padding: 8px 12px; border-radius: 8px;">
                                    <small>🎬 <strong>30-second highlights available</strong></small>
                                </div>
                            </div>
                        </div>
                        <div class="tournament-footer">
                            <a href="/stream/{{ tournament.get('id', 0) }}" class="btn btn-live" style="display: block; width: 100%; text-align: center;">🔥 Watch Full Match</a>
                            <a href="/tournament/{{ tournament.get('id', 0) }}" class="btn btn-primary" style="display: block; width: 100%; text-align: center; margin-top: 10px;">View Tournament</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div style="text-align: center; padding: 60px;">
                    <p style="font-size: 1.2rem; color: #a0aec0;">No live tournaments at the moment.</p>
                </div>
                {% endif %}
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, live_tournaments=live_tournaments, active_ads=active_ads, get_tournament_registration_count=get_tournament_registration_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        user = check_user_credentials(username, password)
        if user:
            session['user_id'] = user.get('id')
            session['username'] = user.get('username', 'User')
            session['role'] = user.get('role', 'player')
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <div style="max-width: 400px; margin: 120px auto; padding: 20px;">
            <div class="card">
                <h2 style="text-align: center; margin-bottom: 30px;">Login to ARENA</h2>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <div class="form-group">
                        <input type="text" name="username" class="form-control" placeholder="Username" required>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" class="form-control" placeholder="Password" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                </form>
                
                <div style="margin-top: 30px; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                    <p style="color: #a0aec0; font-size: 0.9rem; margin-bottom: 10px;">Test Accounts (password: test):</p>
                    <div style="font-size: 0.85rem;">
                        <div>👤 Player: test</div>
                        <div>👑 League Owner: league</div>
                        <div>📢 Advertiser: advertiser</div>
                        <div>🎮 Player1: player1 / password</div>
                        <div>🎮 Player2: player2 / password</div>
                        <div>🎮 Player3: player3 / password</div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <p style="color: #a0aec0;">Don't have an account? <a href="/register" style="color: #667eea;">Register here</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', css=CSS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        role = request.form.get('role', 'player')
        
        if create_user(username, password, email, role):
            flash('Registration successful! Please login.', 'success')
            return redirect('/login')
        else:
            flash('Username already exists!', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <div style="max-width: 400px; margin: 120px auto; padding: 20px;">
            <div class="card">
                <h2 style="text-align: center; margin-bottom: 30px;">Register for ARENA</h2>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <div class="form-group">
                        <input type="text" name="username" class="form-control" placeholder="Username" required>
                    </div>
                    <div class="form-group">
                        <input type="email" name="email" class="form-control" placeholder="Email" required>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" class="form-control" placeholder="Password" required>
                    </div>
                    <div class="form-group">
                        <select name="role" class="form-control" required>
                            <option value="player">Player</option>
                            <option value="league_owner">League Owner</option>
                            <option value="advertiser">Advertiser</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Register</button>
                </form>
                
                <div style="text-align: center; margin-top: 20px;">
                    <p style="color: #a0aec0;">Already have an account? <a href="/login" style="color: #667eea;">Login here</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', css=CSS)

@app.route('/my_tournaments')
def my_tournaments():
    if 'user_id' not in session or session.get('role') != 'player':
        flash('Only players can access tournament registrations!', 'danger')
        return redirect('/')
    
    user_id = session['user_id']
    tournaments = get_user_tournaments(user_id)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Tournaments - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <a href="/live_matches" class="btn btn-live">🔥 Live</a>
                    <a href="/match_highlights" class="btn btn-highlight">📹 Highlights</a>
                    <a href="/upcoming" class="btn btn-outline">📅 Upcoming</a>
                    <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }} ({{ session.get('role', 'guest') }})</span>
                    <a href="/logout" class="btn btn-outline">Logout</a>
                </div>
            </div>
        </nav>

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <h1 style="font-size: 2.8rem; margin-bottom: 10px;">🏆 My Tournaments</h1>
                <p style="color: #a0aec0; font-size: 1.2rem; margin-bottom: 40px;">Tournaments you're registered in</p>
                
                {% if tournaments %}
                <div class="tournament-grid">
                    {% for tournament in tournaments %}
                    {% set reg_count = get_tournament_registration_count(tournament.get('id', 0)) %}
                    <div class="tournament-card">
                        <div class="tournament-header">
                            <h3 style="margin-bottom: 10px;">{{ tournament.get('name', 'Tournament') }}</h3>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                {% if tournament.get('status') == 'live' %}
                                <span class="live-badge">LIVE NOW</span>
                                {% elif tournament.get('status') == 'completed' %}
                                <span style="background: rgba(107, 114, 128, 0.2); color: #9ca3af; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">
                                    COMPLETED
                                </span>
                                {% else %}
                                <span style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">
                                    UPCOMING
                                </span>
                                {% endif %}
                                <span style="background: rgba(102, 126, 234, 0.2); color: #667eea; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">
                                    {{ tournament.get('game', 'Game') }}
                                </span>
                            </div>
                        </div>
                        <div class="tournament-body">
                            <div style="display: flex; flex-direction: column; gap: 15px;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 1.2rem;">👥</span>
                                    <span>{{ reg_count }}/{{ tournament.get('max_players', 0) }} players</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 1.2rem;">📅</span>
                                    <span>Registered: {{ tournament.get('registered_at', '')[:10] if tournament.get('registered_at') else 'N/A' }}</span>
                                </div>
                                <div style="background: rgba(72, 187, 120, 0.2); padding: 8px 12px; border-radius: 8px;">
                                    <small>✅ <strong>You are registered!</strong></small>
                                </div>
                            </div>
                        </div>
                        <div class="tournament-footer">
                            <a href="/tournament/{{ tournament.get('id', 0) }}" class="btn btn-primary" style="display: block; width: 100%; text-align: center;">View Tournament</a>
                            <a href="/stream/{{ tournament.get('id', 0) }}" class="btn btn-live" style="display: block; width: 100%; text-align: center; margin-top: 10px;">
                                {% if tournament.get('status') == 'live' %}
                                🔥 Watch Live
                                {% else %}
                                📺 Watch Stream
                                {% endif %}
                            </a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="card" style="text-align: center; padding: 60px;">
                    <h2>No Tournament Registrations</h2>
                    <p style="color: #a0aec0; margin-top: 20px; font-size: 1.1rem;">You haven't registered for any tournaments yet.</p>
                    <div style="margin-top: 30px;">
                        <a href="/upcoming" class="btn btn-primary">Browse Tournaments</a>
                    </div>
                </div>
                {% endif %}
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, tournaments=tournaments, get_tournament_registration_count=get_tournament_registration_count)

@app.route('/create_tournament', methods=['GET', 'POST'])
def create_tournament():
    if 'user_id' not in session or session.get('role') != 'league_owner':
        flash('Access denied! Only league owners can create tournaments.', 'danger')
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        game = request.form.get('game', '')
        max_players = int(request.form.get('max_players', 16))
        sponsor_name = request.form.get('sponsor_name', '')
        
        tournament_id = create_tournament(name, game, max_players, sponsor_name, session['user_id'])
        if tournament_id:
            flash('Tournament created successfully!', 'success')
            return redirect(f'/tournament/{tournament_id}')
        else:
            flash('Failed to create tournament.', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create Tournament - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }} (League Owner)</span>
                    <a href="/logout" class="btn btn-outline">Logout</a>
                </div>
            </div>
        </nav>

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <div class="card">
                    <h1 style="font-size: 2.5rem; margin-bottom: 30px;">🎮 Create New Tournament</h1>
                    
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <form method="POST">
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Tournament Name</label>
                            <input type="text" name="name" class="form-control" placeholder="e.g., TEKKEN 8 Championship 2024" required>
                        </div>
                        
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Game</label>
                            <select name="game" class="form-control" required>
                                <option value="Tekken 8">Tekken 8</option>
                                <option value="Valorant">Valorant</option>
                                <option value="PUBG Mobile">PUBG Mobile</option>
                                <option value="DOTA 2">DOTA 2</option>
                                <option value="League of Legends">League of Legends</option>
                                <option value="Counter-Strike 2">Counter-Strike 2</option>
                                <option value="Fortnite">Fortnite</option>
                                <option value="Rocket League">Rocket League</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Maximum Players/Teams</label>
                            <input type="number" name="max_players" class="form-control" min="2" max="256" value="16" required>
                        </div>
                        
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Sponsor Name (Optional)</label>
                            <input type="text" name="sponsor_name" class="form-control" placeholder="e.g., Razer Inc.">
                        </div>
                        
                        <div style="margin-top: 30px;">
                            <button type="submit" class="btn btn-warning" style="padding: 15px 40px; font-size: 1.1rem; width: 100%;">
                                🎮 Create Tournament
                            </button>
                        </div>
                    </form>
                    
                    <div style="margin-top: 40px; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 12px;">
                        <h3>📋 Tournament Features</h3>
                        <ul style="color: #cbd5e1; margin-top: 15px; padding-left: 20px;">
                            <li>Automatic bracket generation</li>
                            <li>Live stream integration</li>
                            <li>30-second highlight compression</li>
                            <li>Leaderboard tracking</li>
                            <li>Player registration system</li>
                            <li>Sponsor advertising slots</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS)

@app.route('/create_ad', methods=['GET', 'POST'])
def create_ad():
    if 'user_id' not in session or session.get('role') != 'advertiser':
        flash('Access denied! Only advertisers can create ads.', 'danger')
        return redirect('/')
    
    tournaments = get_all_tournaments()
    
    if request.method == 'POST':
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        tournament_id = int(request.form.get('tournament_id', 0))
        budget = float(request.form.get('budget', 1000))
        
        if create_advertisement(title, description, session['user_id'], tournament_id, budget):
            flash('Advertisement created successfully!', 'success')
            return redirect('/my_ads')
        else:
            flash('Failed to create advertisement.', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create Advertisement - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <a href="/my_ads" class="btn btn-admin">📋 My Ads</a>
                    <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }} (Advertiser)</span>
                    <a href="/logout" class="btn btn-outline">Logout</a>
                </div>
            </div>
        </nav>

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <div class="card">
                    <h1 style="font-size: 2.5rem; margin-bottom: 30px;">📢 Create Advertisement</h1>
                    
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <form method="POST">
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Ad Title</label>
                            <input type="text" name="title" class="form-control" placeholder="e.g., Sponsored by Razer" required>
                        </div>
                        
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Ad Description</label>
                            <textarea name="description" class="form-control" rows="3" placeholder="Describe your advertisement..." required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Select Tournament</label>
                            <select name="tournament_id" class="form-control" required>
                                <option value="">Choose a tournament...</option>
                                {% for tournament in tournaments %}
                                <option value="{{ tournament.get('id', 0) }}">{{ tournament.get('name', 'Tournament') }} ({{ tournament.get('game', 'Game') }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label style="display: block; margin-bottom: 8px; color: #cbd5e1;">Ad Budget ($)</label>
                            <input type="number" name="budget" class="form-control" min="100" max="100000" step="100" value="1000" required>
                        </div>
                        
                        <div style="margin-top: 30px;">
                            <button type="submit" class="btn btn-admin" style="padding: 15px 40px; font-size: 1.1rem; width: 100%;">
                                📢 Create Advertisement
                            </button>
                        </div>
                    </form>
                    
                    <div style="margin-top: 40px; padding: 20px; background: rgba(245, 158, 11, 0.1); border-radius: 12px;">
                        <h3>🎯 Advertising Benefits</h3>
                        <ul style="color: #cbd5e1; margin-top: 15px; padding-left: 20px;">
                            <li>Reach thousands of esports fans</li>
                            <li>Display on tournament pages</li>
                            <li>Highlight during live streams</li>
                            <li>Featured in 30-second highlights</li>
                            <li>Target specific game audiences</li>
                            <li>Analytics and performance tracking</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, tournaments=tournaments)

@app.route('/my_ads')
def my_ads():
    if 'user_id' not in session or session.get('role') != 'advertiser':
        flash('Access denied! Only advertisers can view ads.', 'danger')
        return redirect('/')
    
    ads = get_user_ads(session['user_id'])
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Ads - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <a href="/create_ad" class="btn btn-admin">📢 Create Ad</a>
                    <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }} (Advertiser)</span>
                    <a href="/logout" class="btn btn-outline">Logout</a>
                </div>
            </div>
        </nav>

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <h1 style="font-size: 2.8rem; margin-bottom: 10px;">📢 My Advertisements</h1>
                <p style="color: #a0aec0; font-size: 1.2rem; margin-bottom: 40px;">Manage your advertising campaigns</p>
                
                {% if ads %}
                <div class="tournament-grid">
                    {% for ad in ads %}
                    <div class="tournament-card ad-card">
                        <div class="tournament-header">
                            <h3 style="margin-bottom: 10px;">{{ ad.get('title', 'Advertisement') }}</h3>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span class="ad-badge">ADVERTISEMENT</span>
                                <span style="background: rgba(102, 126, 234, 0.2); color: #667eea; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">
                                    Budget: ${{ ad.get('budget', 0) }}
                                </span>
                            </div>
                        </div>
                        <div class="tournament-body">
                            <div style="display: flex; flex-direction: column; gap: 15px;">
                                <p style="color: #cbd5e1;">{{ ad.get('description', '') }}</p>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 1.2rem;">📅</span>
                                    <span>Created: {{ ad.get('created_at', '')[:10] }}</span>
                                </div>
                                <div style="background: rgba(72, 187, 120, 0.2); padding: 8px 12px; border-radius: 8px;">
                                    <small>✅ <strong>Active</strong></small>
                                </div>
                            </div>
                        </div>
                        <div class="tournament-footer">
                            <a href="/tournament/{{ ad.get('tournament_id', 0) }}" class="btn btn-primary" style="display: block; width: 100%; text-align: center;">
                                View Tournament
                            </a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="card" style="text-align: center; padding: 60px;">
                    <h2>No Advertisements Yet</h2>
                    <p style="color: #a0aec0; margin-top: 20px; font-size: 1.1rem;">You haven't created any advertisements yet.</p>
                    <div style="margin-top: 30px;">
                        <a href="/create_ad" class="btn btn-admin">📢 Create Your First Ad</a>
                    </div>
                </div>
                {% endif %}
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, ads=ads)

@app.route('/register_tournament/<int:tournament_id>', methods=['POST'])
def register_tournament(tournament_id):
    if 'user_id' not in session:
        flash('Please login first!', 'danger')
        return redirect('/login')
    
    user_id = session['user_id']
    
    # Check if user is a player
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    user_dict = safe_row_to_dict(user)
    conn.close()
    
    if not user_dict or user_dict.get('role') != 'player':
        flash('Only players can register for tournaments!', 'danger')
        return redirect(f'/tournament/{tournament_id}')
    
    success, message = register_for_tournament(user_id, tournament_id)
    
    if success:
        flash('Successfully registered for tournament!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(f'/tournament/{tournament_id}')

@app.route('/tournament/<int:tournament_id>')
def tournament_detail(tournament_id):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        flash('Tournament not found!', 'danger')
        return redirect('/')
    
    # Get registration count
    reg_count = get_tournament_registration_count(tournament_id)
    
    # Check if user is registered
    is_registered = False
    if 'user_id' in session:
        is_registered = is_user_registered(session['user_id'], tournament_id)
    
    # Get bracket and leaderboard
    bracket = BRACKETS.get(tournament_id % 3 + 1)  # Simple mapping
    leaderboard = LEADERBOARDS.get(tournament_id % 3 + 1, [])
    
    # Get ads for this tournament
    ads = get_tournament_ads(tournament_id)
    
    # Get video URLs
    video_info = TOURNAMENT_VIDEOS.get(tournament_id, {'stream': '', 'highlight': ''})
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ tournament.get('name', 'Tournament') }} - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <a href="/live_matches" class="btn btn-live">🔥 Live</a>
                    <a href="/match_highlights" class="btn btn-highlight">📹 Highlights</a>
                    <a href="/upcoming" class="btn btn-outline">📅 Upcoming</a>
                    {% if 'user_id' in session %}
                        {% if session.get('role') == 'player' %}
                        <a href="/my_tournaments" class="btn btn-success">🏆 My Tournaments</a>
                        {% endif %}
                        {% if session.get('role') == 'league_owner' %}
                        <a href="/create_tournament" class="btn btn-warning">🎮 Create</a>
                        {% endif %}
                        {% if session.get('role') == 'advertiser' %}
                        <a href="/create_ad" class="btn btn-admin">📢 Create Ad</a>
                        <a href="/my_ads" class="btn btn-admin">📋 My Ads</a>
                        {% endif %}
                        <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }}</span>
                        <a href="/logout" class="btn btn-outline">Logout</a>
                    {% else %}
                        <a href="/login" class="btn btn-outline">Login</a>
                        <a href="/register" class="btn btn-primary">Register</a>
                    {% endif %}
                </div>
            </div>
        </nav>

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <div class="card">
                    <h1 style="margin-bottom: 10px;">{{ tournament.get('name', 'Tournament') }}</h1>
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                        {% if tournament.get('status') == 'live' %}
                        <span class="live-badge">LIVE NOW</span>
                        {% elif tournament.get('status') == 'completed' %}
                        <span style="background: rgba(107, 114, 128, 0.2); color: #9ca3af; padding: 6px 15px; border-radius: 20px; font-weight: 600;">COMPLETED</span>
                        {% else %}
                        <span style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 6px 15px; border-radius: 20px; font-weight: 600;">UPCOMING</span>
                        {% endif %}
                        <span style="background: rgba(102, 126, 234, 0.2); color: #667eea; padding: 6px 15px; border-radius: 20px; font-weight: 600;">{{ tournament.get('game', 'Game') }}</span>
                        <span style="color: #a0aec0;">👥 {{ reg_count }}/{{ tournament.get('max_players', 0) }} registered</span>
                    </div>
                    
                    {% if tournament.get('sponsor_name') %}
                    <div style="background: rgba(255,215,0,0.1); padding: 12px; border-radius: 8px; margin-bottom: 20px;">
                        <span style="color: #f6d365;">💰 Sponsored by <strong>{{ tournament.get('sponsor_name') }}</strong></span>
                    </div>
                    {% endif %}
                    
                    {% if 'user_id' in session %}
                    <div style="margin-top: 20px;">
                        {% if session.get('role') == 'player' %}
                            {% if is_registered %}
                            <div style="background: rgba(72, 187, 120, 0.2); padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px;">
                                <span style="color: #48bb78;">✅ You are registered for this tournament!</span>
                                <a href="/my_tournaments" class="btn btn-success" style="padding: 8px 16px;">🏆 View My Tournaments</a>
                            </div>
                            {% elif reg_count >= tournament.get('max_players', 0) %}
                            <div style="background: rgba(245, 101, 101, 0.2); padding: 12px; border-radius: 8px;">
                                <span style="color: #f56565;">❌ Tournament is full. Cannot register.</span>
                            </div>
                            {% else %}
                            <form method="POST" action="/register_tournament/{{ tournament.get('id', 0) }}" style="display: inline;">
                                <button type="submit" class="btn btn-success" style="padding: 12px 24px;">
                                    🎮 Register for Tournament
                                </button>
                            </form>
                            <span style="color: #a0aec0; margin-left: 15px;">{{ tournament.get('max_players', 0) - reg_count }} spots remaining</span>
                            {% endif %}
                        {% elif session.get('role') == 'league_owner' %}
                            <div style="background: rgba(245, 158, 11, 0.2); padding: 12px; border-radius: 8px;">
                                <span style="color: #f59e0b;">👑 You are a League Owner (Cannot register for tournaments)</span>
                            </div>
                        {% elif session.get('role') == 'advertiser' %}
                            <div style="background: rgba(154, 92, 234, 0.2); padding: 12px; border-radius: 8px;">
                                <span style="color: #9f7aea;">📢 You are an Advertiser (Cannot register for tournaments)</span>
                            </div>
                        {% endif %}
                    </div>
                    {% else %}
                    <div style="background: rgba(245, 158, 11, 0.2); padding: 12px; border-radius: 8px; margin-top: 20px;">
                        <span style="color: #f59e0b;">⚠️ Please <a href="/login" style="color: #f6d365;">login</a> to register for this tournament</span>
                    </div>
                    {% endif %}
                </div>
                
                <!-- Advertisements Section -->
                {% if ads %}
                <div class="card" style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 87, 108, 0.1) 100%);">
                    <h2 style="margin-bottom: 20px;">📢 Tournament Sponsors</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        {% for ad in ads %}
                        <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px;">
                            <h3 style="color: #f6d365; margin-bottom: 10px;">{{ ad.get('title', 'Advertisement') }}</h3>
                            <p style="color: #cbd5e1; margin-bottom: 15px;">{{ ad.get('description', '') }}</p>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: #a0aec0; font-size: 0.9rem;">Budget: ${{ ad.get('budget', 0) }}</span>
                                <span style="color: #48bb78; font-size: 0.9rem;">✅ Active</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <a href="#stream" class="btn btn-primary" style="text-align: center;">📺 Watch Stream</a>
                    <a href="#bracket" class="btn btn-highlight" style="text-align: center;">📊 View Bracket</a>
                    <a href="#leaderboard" class="btn btn-outline" style="text-align: center;">🏆 Leaderboard</a>
                </div>
                
                <div class="card" id="stream">
                    <h2 style="margin-bottom: 20px;">
                        {% if tournament.get('status') == 'live' %}
                        🔥 Live Stream (Full Match)
                        {% else %}
                        📺 Tournament Stream
                        {% endif %}
                    </h2>
                    {% if video_info.stream %}
                    <div class="video-container">
                        <iframe 
                            src="{{ video_info.stream }}"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                    </div>
                    <p style="text-align: center; margin-top: 20px; color: #a0aec0;">
                        Full match stream
                    </p>
                    {% else %}
                    <p style="text-align: center; padding: 40px; color: #a0aec0;">Stream available soon</p>
                    {% endif %}
                </div>
                
                <div class="card">
                    <h2 style="margin-bottom: 20px;">🎬 30-Second Tournament Highlight</h2>
                    {% if video_info.highlight %}
                    <div class="video-container">
                        <iframe 
                            src="{{ video_info.highlight }}"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                    </div>
                    <p style="text-align: center; margin-top: 20px;">
                        <span class="live-badge">30-SECOND COMPRESSED HIGHLIGHT</span>
                    </p>
                    <p style="text-align: center; color: #a0aec0; margin-top: 10px;">
                        Best moments compressed into 30 seconds
                    </p>
                    {% else %}
                    <p style="text-align: center; padding: 40px; color: #a0aec0;">Highlights available soon</p>
                    {% endif %}
                </div>
                
                {% if bracket %}
                <div class="card" id="bracket">
                    <h2 style="margin-bottom: 20px;">📊 Tournament Bracket</h2>
                    <div class="bracket-container">
                        {% for round in bracket.rounds %}
                        <div class="round">
                            <h4 style="margin-bottom: 15px; color: #f6d365;">{{ round.name }}</h4>
                            {% for match in round.matches %}
                            <div class="match {% if match.winner == 1 %}winner{% endif %}">
                                <div class="match-player">
                                    <span>{{ match.player1 }}</span>
                                    <span>{{ match.score1 if match.score1 is not none else "-" }}</span>
                                </div>
                                <div class="match-player {% if match.winner == 2 %}winner{% endif %}">
                                    <span>{{ match.player2 }}</span>
                                    <span>{{ match.score2 if match.score2 is not none else "-" }}</span>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
                
                {% if leaderboard %}
                <div class="card" id="leaderboard">
                    <h2 style="margin-bottom: 20px;">🏆 Leaderboard</h2>
                    <table class="leaderboard">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                {% if leaderboard[0].get('player') %}
                                <th>Player</th>
                                <th>Wins</th>
                                <th>Losses</th>
                                <th>Points</th>
                                {% else %}
                                <th>Team</th>
                                <th>Kills</th>
                                <th>Points</th>
                                {% endif %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for entry in leaderboard %}
                            <tr>
                                <td>#{{ entry.get('rank', 0) }}</td>
                                {% if entry.get('player') %}
                                <td><strong>{{ entry.get('player', '') }}</strong></td>
                                <td>{{ entry.get('wins', 0) }}</td>
                                <td>{{ entry.get('losses', 0) }}</td>
                                <td>{{ entry.get('points', 0) }}</td>
                                {% else %}
                                <td><strong>{{ entry.get('team', '') }}</strong></td>
                                <td>{{ entry.get('kills', 0) }}</td>
                                <td>{{ entry.get('points', 0) }}</td>
                                {% endif %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, tournament=tournament, reg_count=reg_count, is_registered=is_registered,
         bracket=bracket, leaderboard=leaderboard, ads=ads, video_info=video_info)

@app.route('/match_highlights')
def match_highlights():
    """Show all match highlights - 30-second compressed versions"""
    active_ads = get_active_ads()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎬 30-Second Match Highlights - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <a href="/live_matches" class="btn btn-live">🔥 Live</a>
                    <a href="/upcoming" class="btn btn-outline">📅 Upcoming</a>
                    {% if 'user_id' in session %}
                        {% if session.get('role') == 'player' %}
                        <a href="/my_tournaments" class="btn btn-success">🏆 My Tournaments</a>
                        {% endif %}
                        {% if session.get('role') == 'league_owner' %}
                        <a href="/create_tournament" class="btn btn-warning">🎮 Create</a>
                        {% endif %}
                        {% if session.get('role') == 'advertiser' %}
                        <a href="/create_ad" class="btn btn-admin">📢 Create Ad</a>
                        <a href="/my_ads" class="btn btn-admin">📋 My Ads</a>
                        {% endif %}
                        <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }}</span>
                        <a href="/logout" class="btn btn-outline">Logout</a>
                    {% else %}
                        <a href="/login" class="btn btn-outline">Login</a>
                        <a href="/register" class="btn btn-primary">Register</a>
                    {% endif %}
                </div>
            </div>
        </nav>

        <!-- Advertisement Banner -->
        {% if active_ads %}
        <div style="margin-top: 80px; padding: 0 20px;">
            {% for ad in active_ads %}
            <div class="ad-banner">
                <h3>{{ ad.get('title', 'Advertisement') }}</h3>
                <p>{{ ad.get('description', '') }}</p>
                <small>Sponsored Ad | Budget: ${{ ad.get('budget', 0) }}</small>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <h1 style="font-size: 2.8rem; margin-bottom: 10px;">🎬 30-SECOND COMPRESSED HIGHLIGHTS</h1>
                <p style="color: #a0aec0; font-size: 1.2rem; margin-bottom: 40px;">
                    Best moments from matches, compressed into perfect 30-second highlights!
                </p>
                
                <div class="highlights-grid">
                    {% for highlight in highlights %}
                    <div class="highlight-card">
                        <div class="video-container">
                            <iframe 
                                src="{{ highlight.url }}"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowfullscreen>
                            </iframe>
                        </div>
                        <div class="highlight-content">
                            <h3 style="margin-bottom: 10px;">{{ highlight.title }}</h3>
                            <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">{{ highlight.description }}</p>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
                                <div>
                                    <div style="font-size: 0.9rem; color: #667eea;">{{ highlight.tournament }}</div>
                                    <div style="font-size: 0.85rem; color: #a0aec0;">{{ highlight.game }}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.9rem; color: #f6d365;">⏱️ {{ highlight.duration }} highlight</div>
                                    <div style="font-size: 0.85rem; color: #a0aec0;">📺 {{ highlight.full_match_duration }} full match</div>
                                </div>
                            </div>
                            <div style="margin-top: 15px; padding: 10px; background: rgba(245, 158, 11, 0.1); border-radius: 8px;">
                                <small style="color: #f59e0b;">
                                    🔥 Compressed from {{ highlight.full_match_duration }} to {{ highlight.duration }}
                                </small>
                            </div>
                            <button onclick="playHighlight('{{ highlight.url }}')" class="btn btn-primary" style="width: 100%; margin-top: 20px; padding: 12px;">
                                🎬 Play 30-Second Highlight
                            </button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </section>
        
        <script>
        function playHighlight(url) {
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0,0,0,0.9)';
            modal.style.zIndex = '9999';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            
            const iframe = document.createElement('iframe');
            iframe.src = url + "&autoplay=1";
            iframe.style.width = '80%';
            iframe.style.height = '80%';
            iframe.style.border = 'none';
            iframe.style.borderRadius = '12px';
            iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
            iframe.allowfullscreen = true;
            
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '✕';
            closeBtn.style.position = 'absolute';
            closeBtn.style.top = '20px';
            closeBtn.style.right = '20px';
            closeBtn.style.background = '#ef4444';
            closeBtn.style.color = 'white';
            closeBtn.style.border = 'none';
            closeBtn.style.borderRadius = '50%';
            closeBtn.style.width = '50px';
            closeBtn.style.height = '50px';
            closeBtn.style.fontSize = '1.5rem';
            closeBtn.style.cursor = 'pointer';
            closeBtn.onclick = function() {
                document.body.removeChild(modal);
            };
            
            modal.appendChild(iframe);
            modal.appendChild(closeBtn);
            document.body.appendChild(modal);
        }
        </script>
    </body>
    </html>
    ''', css=CSS, highlights=HIGHLIGHTS, active_ads=active_ads)

@app.route('/stream/<int:tournament_id>')
def stream_view(tournament_id):
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        flash('Tournament not found!', 'danger')
        return redirect('/')
    
    video_info = TOURNAMENT_VIDEOS.get(tournament_id, {'stream': '', 'highlight': ''})
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Stream - {{ tournament.get('name', 'Tournament') }}</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/tournament/{{ tournament.get('id', 0) }}" class="btn btn-outline">Back to Tournament</a>
                    <a href="/match_highlights" class="btn btn-highlight">📹 30-sec Highlights</a>
                    {% if 'user_id' in session %}
                        {% if session.get('role') == 'player' %}
                        <a href="/my_tournaments" class="btn btn-success">🏆 My Tournaments</a>
                        {% endif %}
                    {% endif %}
                </div>
            </div>
        </nav>

        <section class="stream-container">
            <div class="container">
                <div class="stream-info">
                    <h1>🔥 {{ tournament.get('name', 'Tournament') }}</h1>
                    <p style="color: #cbd5e1; margin-top: 10px;">
                        {{ tournament.get('game', 'Game') }} • 
                        <span style="color: #ef4444; font-weight: bold;">FULL MATCH STREAM</span>
                    </p>
                </div>
                
                <div class="card">
                    <div class="video-container">
                        <iframe
                            src="{{ video_info.stream }}"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🎬 30-Second Compressed Highlights</h2>
                    <div class="video-container">
                        <iframe
                            src="{{ video_info.highlight }}"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                    </div>
                </div>
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, tournament=tournament, video_info=video_info)

@app.route('/live_matches')
def live_matches():
    """Show all live matches"""
    live_tournaments = get_live_tournaments()
    active_ads = get_active_ads()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔥 Live Matches - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <a href="/match_highlights" class="btn btn-highlight">📹 Highlights</a>
                    <a href="/upcoming" class="btn btn-outline">📅 Upcoming</a>
                    {% if 'user_id' in session %}
                        {% if session.get('role') == 'player' %}
                        <a href="/my_tournaments" class="btn btn-success">🏆 My Tournaments</a>
                        {% endif %}
                        {% if session.get('role') == 'league_owner' %}
                        <a href="/create_tournament" class="btn btn-warning">🎮 Create</a>
                        {% endif %}
                        {% if session.get('role') == 'advertiser' %}
                        <a href="/create_ad" class="btn btn-admin">📢 Create Ad</a>
                        <a href="/my_ads" class="btn btn-admin">📋 My Ads</a>
                        {% endif %}
                        <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }}</span>
                        <a href="/logout" class="btn btn-outline">Logout</a>
                    {% else %}
                        <a href="/login" class="btn btn-outline">Login</a>
                        <a href="/register" class="btn btn-primary">Register</a>
                    {% endif %}
                </div>
            </div>
        </nav>

        <!-- Advertisement Banner -->
        {% if active_ads %}
        <div style="margin-top: 80px; padding: 0 20px;">
            {% for ad in active_ads %}
            <div class="ad-banner">
                <h3>{{ ad.get('title', 'Advertisement') }}</h3>
                <p>{{ ad.get('description', '') }}</p>
                <small>Sponsored Ad | Budget: ${{ ad.get('budget', 0) }}</small>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <h1 style="font-size: 2.8rem; margin-bottom: 10px;">🔥 LIVE MATCHES</h1>
                
                {% if live_tournaments %}
                <div class="tournament-grid">
                    {% for tournament in live_tournaments %}
                    {% set reg_count = get_tournament_registration_count(tournament.get('id', 0)) %}
                    <div class="tournament-card">
                        <div class="tournament-header">
                            <h3>{{ tournament.get('name', 'Tournament') }}</h3>
                            <div class="live-badge">LIVE NOW</div>
                        </div>
                        <div class="tournament-body">
                            <div style="text-align: center; margin: 20px 0;">
                                <div style="font-size: 1.5rem; font-weight: 600;">{{ tournament.get('game', 'Game') }}</div>
                                <div style="color: #a0aec0; margin-top: 5px;">{{ reg_count }} players registered</div>
                            </div>
                            <div style="margin-top: 15px; padding: 10px; background: rgba(245, 158, 11, 0.1); border-radius: 8px;">
                                <small style="color: #f59e0b;">
                                    ⚡ <strong>30-second highlights available!</strong>
                                </small>
                            </div>
                        </div>
                        <div class="tournament-footer">
                            <a href="/stream/{{ tournament.get('id', 0) }}" class="btn btn-live" style="display: block; width: 100%; text-align: center;">
                                📺 Watch Live
                            </a>
                            <a href="/tournament/{{ tournament.get('id', 0) }}" class="btn btn-primary" style="display: block; width: 100%; text-align: center; margin-top: 10px;">
                                View Tournament
                            </a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="card" style="text-align: center; padding: 60px;">
                    <h2>No Live Matches Currently</h2>
                    <p style="color: #a0aec0; margin-top: 20px; font-size: 1.1rem;">Check back soon for live matches!</p>
                </div>
                {% endif %}
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, live_tournaments=live_tournaments, active_ads=active_ads, get_tournament_registration_count=get_tournament_registration_count)

@app.route('/upcoming')
def upcoming_matches():
    """Show upcoming matches"""
    tournaments = get_all_tournaments()
    upcoming_tournaments = [t for t in tournaments if t.get('status') == 'upcoming']
    active_ads = get_active_ads()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📅 Upcoming Matches - ARENA</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">🎮 ARENA</a>
                <div class="nav-links">
                    <a href="/" class="btn btn-outline">Home</a>
                    <a href="/live_matches" class="btn btn-live">🔥 Live</a>
                    <a href="/match_highlights" class="btn btn-highlight">📹 Highlights</a>
                    {% if 'user_id' in session %}
                        {% if session.get('role') == 'player' %}
                        <a href="/my_tournaments" class="btn btn-success">🏆 My Tournaments</a>
                        {% endif %}
                        {% if session.get('role') == 'league_owner' %}
                        <a href="/create_tournament" class="btn btn-warning">🎮 Create</a>
                        {% endif %}
                        {% if session.get('role') == 'advertiser' %}
                        <a href="/create_ad" class="btn btn-admin">📢 Create Ad</a>
                        <a href="/my_ads" class="btn btn-admin">📋 My Ads</a>
                        {% endif %}
                        <span style="color: white; margin: 0 10px;">{{ session.get('username', 'User') }}</span>
                        <a href="/logout" class="btn btn-outline">Logout</a>
                    {% else %}
                        <a href="/login" class="btn btn-outline">Login</a>
                        <a href="/register" class="btn btn-primary">Register</a>
                    {% endif %}
                </div>
            </div>
        </nav>

        <!-- Advertisement Banner -->
        {% if active_ads %}
        <div style="margin-top: 80px; padding: 0 20px;">
            {% for ad in active_ads %}
            <div class="ad-banner">
                <h3>{{ ad.get('title', 'Advertisement') }}</h3>
                <p>{{ ad.get('description', '') }}</p>
                <small>Sponsored Ad | Budget: ${{ ad.get('budget', 0) }}</small>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <section class="section" style="margin-top: 80px;">
            <div class="container">
                <h1 style="font-size: 2.8rem; margin-bottom: 10px;">📅 UPCOMING TOURNAMENTS</h1>
                <p style="color: #a0aec0; font-size: 1.2rem; margin-bottom: 40px;">Register for upcoming tournaments</p>
                
                {% if upcoming_tournaments %}
                <div class="tournament-grid">
                    {% for tournament in upcoming_tournaments %}
                    {% set reg_count = get_tournament_registration_count(tournament.get('id', 0)) %}
                    <div class="tournament-card">
                        <div class="tournament-header">
                            <h3 style="margin-bottom: 10px;">{{ tournament.get('name', 'Tournament') }}</h3>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">UPCOMING</span>
                                <span style="background: rgba(102, 126, 234, 0.2); color: #667eea; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">{{ tournament.get('game', 'Game') }}</span>
                            </div>
                        </div>
                        <div class="tournament-body">
                            <div style="display: flex; flex-direction: column; gap: 15px;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 1.2rem;">👥</span>
                                    <span>{{ reg_count }}/{{ tournament.get('max_players', 0) }} players registered</span>
                                </div>
                                {% if tournament.get('sponsor_name') %}
                                <div style="background: rgba(255,215,0,0.1); padding: 8px 12px; border-radius: 8px;">
                                    <small>Sponsored by {{ tournament.get('sponsor_name') }}</small>
                                </div>
                                {% endif %}
                            </div>
                        </div>
                        <div class="tournament-footer">
                            <a href="/tournament/{{ tournament.get('id', 0) }}" class="btn btn-primary" style="display: block; width: 100%; text-align: center;">View & Register</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div style="text-align: center; padding: 60px;">
                    <p style="font-size: 1.2rem; color: #a0aec0;">No upcoming tournaments scheduled.</p>
                </div>
                {% endif %}
            </div>
        </section>
    </body>
    </html>
    ''', css=CSS, upcoming_tournaments=upcoming_tournaments, active_ads=active_ads, get_tournament_registration_count=get_tournament_registration_count)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect('/')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎮 ARENA ESPORTS PLATFORM - FINAL VERSION READY!")
    print("="*60)
    print("✅ FIXED: All KeyError issues resolved")
    print("✅ FIXED: Safe dictionary access with .get() method")
    print("✅ FIXED: Session access with .get() method")
    print("✅ FIXED: Safe database row conversion")
    print("✅ FIXED: Role permissions working perfectly")
    print("✅ NEW: Ad banners on all pages")
    print("✅ NEW: Only players can register for tournaments")
    print("✅ NEW: League owners cannot register")
    print("✅ NEW: Advertisers cannot register")
    print("✅ Server: http://localhost:5000")
    print("="*60)
    print("\nROLE PERMISSIONS:")
    print("1. Player: Register for tournaments, watch matches")
    print("2. League Owner: Create tournaments, manage brackets")
    print("3. Advertiser: Create ads, sponsor tournaments (CANNOT register)")
    print("="*60)
    print("\nTEST ACCOUNTS (password: test):")
    print("1. test - Player (can register for tournaments)")
    print("2. league - League Owner (can create tournaments)")
    print("3. advertiser - Advertiser (can create ads)")
    print("4. player1 - Player (can register for tournaments)")
    print("="*60)
    print("\nDEMO FLOW:")
    print("1. Login as 'league' - Create a tournament")
    print("2. Login as 'advertiser' - Create an ad")
    print("3. Login as 'player1' - Register for tournaments")
    print("4. Watch live matches and 30-second highlights")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)