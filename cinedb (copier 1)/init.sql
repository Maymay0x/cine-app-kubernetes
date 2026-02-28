CREATE DATABASE IF NOT EXISTS cinebook;
USE cinebook;

CREATE TABLE clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE films (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titre VARCHAR(255) NOT NULL,
    duree INT NOT NULL,
    genre VARCHAR(100) NOT NULL,
    description TEXT,
    affiche_url VARCHAR(500)
);

CREATE TABLE seances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    film_id INT NOT NULL,
    salle_num INT NOT NULL,
    places_total INT NOT NULL,
    places_restantes INT NOT NULL,
    horaire DATETIME NOT NULL,
    FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE CASCADE
);

CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seance_id INT NOT NULL,
    client_id INT NOT NULL,
    nb_places INT NOT NULL,
    date_reservation DATETIME NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'CONFIRME',
    FOREIGN KEY (seance_id) REFERENCES seances(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);