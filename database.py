from sqlitedict import SqliteDict

db = SqliteDict("./BotzHub.sqlite", autocommit=True)


def set_username(user_id, username):
    usernames = db.get("usernames", {})
    usernames[user_id] = username
    db["usernames"] = usernames


def get_username(user_id):
    return db.get("usernames", {}).get(user_id, None)


def set_domain(user_id, domain):
    domains = db.get("domains", {})
    domains[user_id] = domain
    db["domains"] = domains


def get_domain(user_id):
    return db.get("domains", {}).get(user_id, None)


def add_user(user_id):
    users = db.get("users", [])
    if user_id not in users:
        users.append(user_id) if user_id not in users else None
        db["users"] = users


def get_users():
    return db.get("users", [])
