import sqlite3

def init_db():
    """Initialize the database with all tables"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'player',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tournaments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            game TEXT DEFAULT 'TicTacToe',
            max_players INTEGER DEFAULT 16,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'announced',
            creator_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users (id)
        )
    ''')
    
    # Applications table
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            tournament_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES users (id),
            FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database tables created!")

def add_sample_data():
    """Add sample data for testing"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Add sample users
    users = [
        ('admin', 'admin123', 'admin@arena.com', 'operator'),
        ('league1', 'league123', 'league@arena.com', 'league_owner'),
        ('player1', 'player123', 'player1@arena.com', 'player'),
        ('player2', 'player123', 'player2@arena.com', 'player'),
        ('spectator1', 'spectator123', 'spectator@arena.com', 'spectator')
    ]
    
    for user in users:
        c.execute('''
            INSERT OR IGNORE INTO users (username, password, email, role)
            VALUES (?, ?, ?, ?)
        ''', user)
    
    # Add sample tournaments for popular games
    tournaments = [
        ('Tekken 8 Championship', 'Tekken 8', 32, '2024-02-01', '2024-02-15', 2, 'announced'),
        ('PUBG Mobile Tournament', 'PUBG Mobile', 100, '2024-02-05', '2024-02-20', 2, 'announced'),
        ('FC 25 eLeague', 'FC 25', 64, '2024-02-10', '2024-02-25', 2, 'announced'),
        ('Valorant Champions', 'Valorant', 16, '2024-02-15', '2024-02-28', 2, 'announced'),
        ('Mobile Legends Cup', 'Mobile Legends', 40, '2024-02-20', '2024-03-05', 2, 'announced'),
        ('Call of Duty Warzone', 'COD Warzone', 50, '2024-02-25', '2024-03-10', 2, 'announced')
    ]
    
    for tournament in tournaments:
        c.execute('''
            INSERT OR IGNORE INTO tournaments 
            (name, game, max_players, start_date, end_date, creator_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', tournament)
    
    conn.commit()
    conn.close()
    print("✓ Sample data added with popular games!")
    
    # Add sample users
    users = [
        ('admin', 'admin123', 'admin@arena.com', 'operator'),
        ('league1', 'league123', 'league@arena.com', 'league_owner'),
        ('player1', 'player123', 'player1@arena.com', 'player'),
        ('player2', 'player123', 'player2@arena.com', 'player'),
        ('spectator1', 'spectator123', 'spectator@arena.com', 'spectator')
    ]
    
    for user in users:
        c.execute('''
            INSERT OR IGNORE INTO users (username, password, email, role)
            VALUES (?, ?, ?, ?)
        ''', user)
    
    # Add sample tournament
    c.execute('''
        INSERT OR IGNORE INTO tournaments 
        (name, game, max_players, start_date, end_date, creator_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('Tic Tac Toe Championship', 'TicTacToe', 16, '2024-01-15', '2024-01-30', 2, 'announced'))
    
    conn.commit()
    conn.close()
    print("✓ Sample data added!")