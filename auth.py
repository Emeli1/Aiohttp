import bcrypt


def hash_password(password: str):
    password = password.encode()
    password = bcrypt.hashpw(password, bcrypt.gensalt())
    password = password.decode()
    return password

def check_password(password:str, hashed: str) -> bool:
    password = password.encode()
    hashed = hashed.encode()
    return bcrypt.checkpw(password, hashed)
