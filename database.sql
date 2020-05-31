-- unique user entry for each guild user is in
CREATE TABLE users
(
    discord_id      bigint NOT NULL,
    guild_id        bigint,
    balance         bigint,
    lifetime_moolah bigint,
    PRIMARY KEY (discord_id, guild_id)
);

CREATE TABLE transactions
(
    id        int    NOT NULL AUTO_INCREMENT,
    type      int,
    amount    bigint NOT NULL,
    recipient bigint NOT NULL,
    sender    bigint NOT NULL,
    guild_id  bigint NOT NULL,
    timestamp int,
    PRIMARY KEY (id)
);

CREATE TABLE transaction_types
(
    id          int NOT NULL AUTO_INCREMENT,
    name        varchar(30),
    description varchar(150),
    PRIMARY KEY (id)
);

INSERT INTO transaction_types
VALUES (1, 'user_to_user', 'A transaction between two users'),
       (2, 'cointoss_escrow', 'Balance kept in escrow for a cointoss bet'),
       (3, 'cointoss', 'Winnings or losses from cointoss bet'),
       (4, 'message_moolah', 'Moolah earned for messages'),
       (5, 'vc_moolah', 'Moolah earned for voice chat'),
       (6, 'slots', 'Winnings and payment for slots');
