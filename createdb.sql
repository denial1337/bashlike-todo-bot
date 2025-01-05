create table dir(
    id integer primary key AUTOINCREMENT,
    name varchar(255),
    user_id integer,
    meta_dir_id integer,
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(meta_dir_id) REFERENCES dir(id)
);


create table task(
    id integer primary key AUTOINCREMENT,
    serial_number integer,
    content varchar(255),
    is_done boolean,
    dir_id integer,
    user_id integer,
    FOREIGN KEY(user_id) REFERENCES user(id)
    FOREIGN KEY(dir_id) REFERENCES dir(id)
);


create table user(
    id integer primary key,
    username varchar(255),
    active_dir_id integer,
    root_dir_id integer,
    FOREIGN KEY(active_dir_id) REFERENCES dir(id),
    FOREIGN KEY(root_dir_id) REFERENCES dir(id)
);