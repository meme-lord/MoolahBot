CREATE TABLE users (
    id int,
    balance int,
    lifetime_moolah int,
    server_join_time int,
    PRIMARY KEY (id)
);

CREATE TABLE transactions (
    id int NOT NULL AUTO_INCREMENT,
    type int,
    recipient int,
    amount int,
    sender int,
    timestamp int,
    PRIMARY KEY (id),
    FOREIGN KEY (recipient) REFERENCES users(id),
    FOREIGN KEY (sender) REFERENCES users(id)
);

CREATE TABLE transaction_types (
    id int NOT NULL AUTO_INCREMENT,
    name varchar(30),
    description varchar(150),
    PRIMARY KEY (id)
);
