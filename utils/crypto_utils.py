import hashlib

class CryptoUtils:
    """密码加密工具类，与Flutter app保持一致的哈希算法"""
    
    # 与app端相同的盐值
    SALT = 'nianfo_app_salt_2024'
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        使用SHA-256加密密码，与Flutter app保持一致
        
        Args:
            password: 原始密码
            
        Returns:
            str: 哈希后的密码（64位十六进制字符串）
        """
        # 添加盐值
        salted_password = password + cls.SALT
        
        # 使用SHA-256哈希
        hash_object = hashlib.sha256(salted_password.encode('utf-8'))
        return hash_object.hexdigest()
    
    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        """
        验证密码是否正确
        
        Args:
            password: 原始密码
            hashed_password: 存储的哈希密码
            
        Returns:
            bool: 密码是否正确
        """
        return cls.hash_password(password) == hashed_password
    
    @classmethod
    def is_hashed_password(cls, password: str) -> bool:
        """
        检查密码是否已经是哈希格式
        
        Args:
            password: 密码字符串
            
        Returns:
            bool: 是否为哈希密码
        """
        # SHA-256哈希是64位十六进制字符串
        if len(password) != 64:
            return False
        
        # 检查是否为十六进制
        try:
            int(password, 16)
            return True
        except ValueError:
            return False