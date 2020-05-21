-- unique user entry for each guild user is in
CREATE TABLE users (
    id int NOT NULL AUTO_INCREMENT,
    discord_id bigint NOT NULL,
    guild_id bigint,
    balance bigint,
    lifetime_moolah bigint,
    user_initialise_time int,
    PRIMARY KEY (id)
);

CREATE TABLE transactions (
    id int NOT NULL AUTO_INCREMENT,
    type int,
    recipient bigint,
    amount bigint,
    sender bigint,
    guild_id bigint,
    timestamp int,
    PRIMARY KEY (id)
);

CREATE TABLE transaction_types (
    id int NOT NULL AUTO_INCREMENT,
    name varchar(30),
    description varchar(150),
    PRIMARY KEY (id)
);
