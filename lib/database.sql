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
       (3, 'cointoss', 'Winnings from cointoss bet'),
       (4, 'message_moolah', 'Moolah earned for messages'),
       (5, 'vc_moolah', 'Moolah earned for voice chat'),
       (6, 'slots', 'Winnings and payment for slots'),
       (7, 'cointoss_escrow_refund', 'Balance refunded from escrow when bet does not take place'),
       (8, 'highnoon_escrow', 'Balance kept in escrow for a highnoon bet'),
       (9, 'highnoon', 'Winnings from highnoon bet'),
       (10, 'highnoon_escrow_refund', 'Balance refunded from escrow when bet does not take place');


CREATE TABLE user_achievements
(
    discord_id  bigint not null,
    guild_id    bigint not null,
    achievement int    not null,
    PRIMARY KEY (discord_id, guild_id, achievement)
);

CREATE TABLE achievements_types
(
    id          int auto_increment,
    name        varchar(60),
    description varchar(120),
    PRIMARY KEY (id)
);

INSERT INTO achievements_types
VALUES (1, 'TopDog', 'You stand upon mountains of moolah and declare yourself a champion.'),
       (2, 'Welcome to the Champions club!', 'Reach top ten in moolah leaderboard. Drip in and win!'),
       (3, 'Beginnings of a humble Topdog', 'Reach top 100 in moolah leaderboard.'),
       (4, 'Bubbly', 'Reach 100hrs in Voice Chat'),
       (5, 'Is it just me or is it hot in here ?', 'Be in voice chat with 10 people'),
       (6, 'Riot!', 'Be in voice chat with 20 people'),
       (7, 'I Owe You An Apology', 'lose Cointoss 5 times in a row'),           # TODO
       (8, 'The Bookies want your location!', 'win Cointoss 5 times in a row'), # TODO
       (9, 'Cursed', 'lose Cointoss 10 times in a row'),                        # TODO
       (10, 'Gambling Addict', 'Play slots more than 100 times'),
       (11, 'Gum On My Shoe', 'Lose 100k moolah on gambling'),                  # TODO
       (12, 'Promoted', 'Get a different discord role'),
       (13, 'Feels bad man', 'Lose 100 cointosses'),
       (14, 'On a Roll!', 'Win 100 cointosses')
