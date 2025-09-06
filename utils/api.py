import hashlib
import base64
import utils
from cryptography.fernet import Fernet

def _get_key_from_password(password):
    """Генерация ключа из пароля"""
    password_bytes = password.encode('utf-8')
    # Используем хеш пароля как ключ
    key = hashlib.sha256(password_bytes).digest()
    return base64.urlsafe_b64encode(key)

def _encrypt_with_password(text, password):
    """Шифрование с паролем"""
    key = _get_key_from_password(password)
    cipher_suite = Fernet(key)
    encrypted = cipher_suite.encrypt(text.encode('utf-8'))
    return encrypted.decode('utf-8')

def _decrypt_with_password(encrypted_text, password):
    """Расшифрование с паролем"""
    key = _get_key_from_password(password)
    cipher_suite = Fernet(key)
    decrypted = cipher_suite.decrypt(encrypted_text.encode('utf-8'))
    return decrypted.decode('utf-8')

def get_api(password = "Schedule"):
    return _decrypt_with_password(utils.get_settings("telegram_bot", "api_encrypted"), password)

def set_new_api(api, password):
    print(f"Please enter this text into settings: {_encrypt_with_password(text=api, password=password)}")