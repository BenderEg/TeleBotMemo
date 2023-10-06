CREATE SCHEMA IF NOT EXISTS memo;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS memo.users (
    id int PRIMARY KEY,
    creation_date DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS memo.bank (
    id uuid DEFAULT uuid_generate_v4(),
    user_id int NOT NULL,
    object TEXT NOT NULL,
    meaning TEXT NOT NULL,
    creation_date DATE NOT NULL DEFAULT CURRENT_DATE,
    next_date DATE NOT NULL DEFAULT CURRENT_DATE+1,
    interval float NOT NULL DEFAULT 1,
    n smallint NOT NULL DEFAULT 1,
    e_factor float NOT NULL DEFAULT 2.5,
    modified DATE NOT NULL DEFAULT CURRENT_DATE,
    category TEXT NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_user_id
	FOREIGN KEY (user_id)
		REFERENCES memo.users (id)
		ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS memo.categories (
    id uuid DEFAULT uuid_generate_v4(),
    user_id int NOT NULL,
    name TEXT NOT NULL,
    creation_date DATE NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    CONSTRAINT fk_user_id
	FOREIGN KEY (user_id)
		REFERENCES memo.users (id)
		ON DELETE CASCADE
);

ALTER ROLE sam SET search_path TO memo,public;
CREATE UNIQUE INDEX user_id_object_idx ON memo.bank (user_id, object);
CREATE UNIQUE INDEX user_id_category_idx ON memo.categories (user_id, name);