from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    password = "TestPassword123!"
    print(f"Hashing password: {password}")
    hash = pwd_context.hash(password)
    print(f"Hash: {hash}")
    
    print("Verifying...")
    verify = pwd_context.verify(password, hash)
    print(f"Verify: {verify}")
except Exception as e:
    print(f"Error: {e}")
