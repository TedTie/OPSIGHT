from passlib.context import CryptContext

# 切换为 pbkdf2_sha256 以避免 Windows + Python 3.13 下 bcrypt 初始化异常
# pbkdf2_sha256 可靠、跨平台且不受 72 字节长度限制
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码和哈希密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    return pwd_context.hash(password)