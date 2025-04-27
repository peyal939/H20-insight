CREATE TABLE users (
    user_id INT NOT NULL AUTO_INCREMENT,
    user_name VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    user_type CHAR(1) NOT NULL CHECK (user_type IN ("A", "R", "V")),
    latitude DECIMAL(10, 6) DEFAULT 0.00,
    longitude DECIMAL(10, 6) DEFAULT 0.00,
    first_name VARCHAR(255),
    last_name VARCHAR(255), 
    PRIMARY KEY (user_id)
);

CREATE TABLE locations (
    location_id INT NOT NULL AUTO_INCREMENT,
    user_id INT,
    location_name VARCHAR(255) NOT NULL,
    description VARCHAR(6000),
    latitude DECIMAL(10, 6) DEFAULT 0.00,
    longitude DECIMAL(10, 6) DEFAULT 0.00,
    date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (location_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE data (
    data_id INT NOT NULL AUTO_INCREMENT, 
    location_id INT,
    user_id INT,
    date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ph FLOAT,
    bod FLOAT,
    cod FLOAT,
    temperature FLOAT,
    ammonia FLOAT,
    arsenic FLOAT,
    calcium FLOAT,
    ec FLOAT,
    coliform FLOAT,
    hardness FLOAT,
    lead_pb FLOAT,
    nitrogen FLOAT,
    sodium FLOAT,
    sulfate FLOAT,
    tss FLOAT,
    turbidity FLOAT,
    tds FLOAT,
    PRIMARY KEY (data_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE tickets (
    ticket_id INT NOT NULL AUTO_INCREMENT,
    user_id INT,
    subject VARCHAR (255) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR(6000) NOT NULL,
    status INT DEFAULT 0 CHECK (status IN (0, 1)),
    PRIMARY KEY (ticket_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE messages (
    message_id INT NOT NULL AUTO_INCREMENT,
    user_id INT,
    ticket_id INT,
    text VARCHAR(2000),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);