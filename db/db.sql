

CREATE TABLE IF NOT EXISTS Data (
   uid SERIAL PRIMARY KEY,
   host varchar(25),
   ts timestamp,
   jdata jsonb
);

CREATE TABLE IF NOT EXISTS Setting (
   uid SERIAL PRIMARY KEY,
   ts timestamp,
   jconf jsonb
)
CREATE TABLE IF NOT EXISTS Events (
   uid SERIAL PRIMARY KEY,
   ts timestamp,
   description VARCHAR(150)
)

CREATE TABLE IF NOT EXISTS User {
   uid SERIAL,
   uname  VARCHAR(25),
   password VARCHAR(255),
   detail jsonb,
   PRIMARY KEY(uid, uname)
}

