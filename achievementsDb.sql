create table achievements_types
(
    id          int auto_increment,
    name        varchar(60)  null,
    description varchar(120) null,
    PRIMARY KEY (id)
);

create table user_achievements
(
    discord_id  bigint not null,
    guild_id    bigint not null,
    achievement int    not null,
    PRIMARY KEY (discord_id, guild_id, achievement)
);

INSERT INTO achievements_types
VALUES (1, 'TopDog', 'You stand upon mountains of moolah and declare yourself a champion.'),
       (2, 'Welcome to the Champions club!', 'Reach top ten in moolah leaderboard. Drip in and win!'),
       (3, 'Beginnings of a humble Topdog', 'Reach top 100 in moolah leaderboard.'),
       (4, 'Bubbly', 'Reach 100hrs in Voice Chat'),
       (5, 'Is it just me or is it hot in here ?', 'Be in voice chat with 10 people'),
       (6, 'Riot!', 'Be in voice chat with 20 people'),
       (7, 'I Owe You An Apology', 'lose Cointoss 5 times in a row'),
       (8, 'The Bookies want your location!', 'win Cointoss 5 times in a row'),
       (9, 'Cursed', 'lose Cointoss 10 times in a row'),
       (10, 'Gambling Addict', 'Play slots more than 100 times'),
       (11, 'Gum On My Shoe', 'Lose 100k moolah on gambling'),
       (12, 'Promoted', 'Get a different discord role')