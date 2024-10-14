CREATE TABLE IF NOT EXISTS chaturbate (
streamer_name   VARCHAR(20) NOT NULL, 
detail_date     DATETIME DEFAULT NULL,
last_broadcast  TEXT DEFAULT NULL,
pid             INTEGER DEFAULT NULL,
followers       INTEGER DEFAULT NULL,
viewers         INTEGER DEFAULT NULL,
query_time      INTEGER DEFAULT 0,
last_capture    DATETIME DEFAULT NULL,
follow          DATETIME DEFAULT NULL,
block_date      DATETIME DEFAULT NULL,
notes           VARCHAR(25),
created_on      DEFAULT (date('now','localtime')),
model_status    VARCHAR(12),
PRIMARY KEY (streamer_name)
);


CREATE TABLE IF NOT EXISTS num_streamers (
id     INTEGER PRIMARY KEY AUTOINCREMENT,
query  DEFAULT (datetime('now','localtime')),
num_   INTEGER NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_streamer ON chaturbate (streamer_name);
