CREATE TABLE IF NOT EXISTS chaturbate (
streamer_name   VARCHAR(20) NOT NULL, 
last_broadcast  DEFAULT (datetime('now','localtime')),
follow          DATETIME DEFAULT NULL,
pid             INTEGER DEFAULT NULL,
followers       INTEGER DEFAULT NULL,
viewers         INTEGER DEFAULT NULL,
most_viewers    INTEGER DEFAULT 0,
last_capture    DATETIME DEFAULT NULL,
block_date      DATETIME DEFAULT NULL,
notes           VARCHAR(25),
recorded        INTEGER DEFAULT NULL,
review          INTEGER DEFAULT NULL,
keep_           INTEGER DEFAULT NULL,
storage         VARCHAR(12),
created_on      DEFAULT (date('now','localtime')),
detail_date     DATETIME DEFAULT NULL,
PRIMARY KEY (streamer_name)
);


CREATE TABLE IF NOT EXISTS num_streamers (
id     INTEGER PRIMARY KEY AUTOINCREMENT,
query  DEFAULT (datetime('now','localtime')),
num_   INTEGER NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_streamer ON chaturbate (streamer_name);
