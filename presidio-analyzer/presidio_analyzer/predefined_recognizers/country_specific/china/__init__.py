"""
China-specific recognizers for Presidio.

Supports recognition of Chinese sensitive information including:
- Personal identification (身份证, 护照, 驾驶证, 军人证)
- Contact information (手机号, 固话, 邮箱)
- Financial information (银行卡)
- Business information (统一社会信用代码)
- Vehicle information (车牌号)
- Location information (邮政编码)
- Medical information (医师执业证)
- Network information (IP地址, MAC地址, JDBC连接)
- Authentication (JWT, 云密钥, 微信ID, 敏感字段)
"""

# 个人身份信息
from .cn_id_card_recognizer import CnIdCardRecognizer
from .cn_passport_recognizer import CnPassportRecognizer
from .cn_driver_license_recognizer import CnDriverLicenseRecognizer
from .cn_military_id_recognizer import CnMilitaryIdRecognizer

# 联系方式
from .cn_phone_recognizer import CnPhoneRecognizer
from .cn_email_recognizer import CnEmailRecognizer

# 金融信息
from .cn_bank_card_recognizer import CnBankCardRecognizer

# 企业信息
from .cn_social_credit_code_recognizer import CnSocialCreditCodeRecognizer

# 车辆信息
from .cn_vehicle_plate_recognizer import CnVehiclePlateRecognizer

# 地址信息
from .cn_postal_code_recognizer import CnPostalCodeRecognizer

# 医疗信息
from .cn_medical_license_recognizer import CnMedicalLicenseRecognizer

# 网络信息
from .cn_ip_address_recognizer import CnIpAddressRecognizer
from .cn_mac_address_recognizer import CnMacAddressRecognizer
from .cn_jdbc_recognizer import CnJdbcRecognizer

# 认证信息
from .cn_jwt_recognizer import CnJwtRecognizer
from .cn_cloud_key_recognizer import CnCloudKeyRecognizer
from .cn_wechat_recognizer import CnWechatRecognizer
from .cn_sensitive_field_recognizer import CnSensitiveFieldRecognizer

# NLP识别器（需要spaCy中文模型）
from .cn_nlp_recognizer import CnNlpRecognizer

__all__ = [
    # 个人身份信息
    "CnIdCardRecognizer",           # 身份证
    "CnPassportRecognizer",         # 护照
    "CnDriverLicenseRecognizer",    # 驾驶证
    "CnMilitaryIdRecognizer",       # 军人证
    
    # 联系方式
    "CnPhoneRecognizer",            # 手机号/固话
    "CnEmailRecognizer",            # 邮箱
    
    # 金融信息
    "CnBankCardRecognizer",         # 银行卡
    
    # 企业信息
    "CnSocialCreditCodeRecognizer", # 统一社会信用代码
    
    # 车辆信息
    "CnVehiclePlateRecognizer",     # 车牌号
    
    # 地址信息
    "CnPostalCodeRecognizer",       # 邮政编码
    
    # 医疗信息
    "CnMedicalLicenseRecognizer",   # 医师执业证
    
    # 网络信息
    "CnIpAddressRecognizer",        # IP地址
    "CnMacAddressRecognizer",       # MAC地址
    "CnJdbcRecognizer",             # JDBC连接字符串
    
    # 认证信息
    "CnJwtRecognizer",              # JWT Token
    "CnCloudKeyRecognizer",         # 云服务密钥
    "CnWechatRecognizer",           # 微信/企业微信ID
    "CnSensitiveFieldRecognizer",   # 敏感字段(密码/密钥等)
    
    # NLP识别器
    "CnNlpRecognizer",              # 人名/地名/机构名（需要spaCy中文模型）
]
