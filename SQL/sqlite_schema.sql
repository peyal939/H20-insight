-- SQLite schema for H2O-Insight
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('A', 'R', 'V')),
    latitude REAL DEFAULT 0.00,
    longitude REAL DEFAULT 0.00,
    first_name TEXT,
    last_name TEXT,
    is_confirmed BOOLEAN DEFAULT FALSE,
    email_verification_token TEXT DEFAULT NULL
);

CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    location_name TEXT NOT NULL,
    description TEXT,
    latitude REAL DEFAULT 0.00,
    longitude REAL DEFAULT 0.00,
    date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE data (
    data_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    location_id INTEGER,
    user_id INTEGER,
    date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ph REAL,
    bod REAL,
    cod REAL,
    temperature REAL,
    ammonia REAL,
    arsenic REAL,
    calcium REAL,
    ec REAL,
    coliform REAL,
    hardness REAL,
    lead_pb REAL,
    nitrogen REAL,
    sodium REAL,
    sulfate REAL,
    tss REAL,
    turbidity REAL,
    tds REAL,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subject TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    status INTEGER DEFAULT 0 CHECK (status IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ticket_id INTEGER,
    text TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);

-- Authentication tables
CREATE TABLE password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE oauth_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    provider_user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (provider, provider_user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE totp_secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    secret TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_enabled BOOLEAN DEFAULT FALSE,
    UNIQUE (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
); 