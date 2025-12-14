# 中国敏感信息类型识别器

本文档列出了所有支持的中国敏感信息类型识别器，包括正则模式、上下文词和置信度评分。

## 概览

| 实体类型 | 中文名称 | 识别器类 | 正则模式数 | 上下文词数 |
|---------|---------|---------|-----------|-----------|
| CN_ID_CARD | 身份证 | CnIdCardRecognizer | 3 | 40 |
| CN_PHONE | 手机号/固话 | CnPhoneRecognizer | 7 | 58 |
| CN_BANK_CARD | 银行卡 | CnBankCardRecognizer | 9 | 74 |
| CN_PASSPORT | 护照 | CnPassportRecognizer | 9 | 35 |
| CN_DRIVER_LICENSE | 驾驶证 | CnDriverLicenseRecognizer | 3 | 47 |
| CN_SOCIAL_CREDIT_CODE | 统一社会信用代码 | CnSocialCreditCodeRecognizer | 3 | 38 |
| CN_VEHICLE_PLATE | 车牌号 | CnVehiclePlateRecognizer | 7 | 38 |
| CN_POSTAL_CODE | 邮政编码 | CnPostalCodeRecognizer | 2 | 30 |
| CN_MILITARY_ID | 军人证 | CnMilitaryIdRecognizer | 4 | 39 |
| CN_MEDICAL_LICENSE | 医师执业证 | CnMedicalLicenseRecognizer | 4 | 44 |
| CN_EMAIL | 邮箱 | CnEmailRecognizer | 7 | 49 |
| CN_IP_ADDRESS | IP地址 | CnIpAddressRecognizer | 8 | 58 |
| CN_MAC_ADDRESS | MAC地址 | CnMacAddressRecognizer | 4 | 42 |
| CN_JDBC_CONNECTION | JDBC连接 | CnJdbcRecognizer | 8 | 48 |
| CN_JWT | JWT令牌 | CnJwtRecognizer | 3 | 35 |
| CN_CLOUD_KEY | 云服务密钥 | CnCloudKeyRecognizer | 6 | 54 |
| CN_WECHAT_ID | 微信ID | CnWechatRecognizer | 6 | 50 |
| CN_SENSITIVE_FIELD | 敏感字段 | CnSensitiveFieldRecognizer | 7 | 49 |

**总计: 18 个识别器, 100 个正则模式, 828 个上下文词**

---

## 1. CN_ID_CARD (身份证)

### 格式
- **18位**: RRRRRRYYYYMMDDSSSC
  - RRRRRR: 行政区划代码 (6位)
  - YYYYMMDD: 出生日期 (8位)
  - SSS: 顺序码 (3位，奇数男性，偶数女性)
  - C: 校验码 (0-9 或 X)

### 验证算法
- GB 11643-1999 校验码算法
- 省份代码验证 (1-6开头)
- 出生日期有效性验证

### 正则模式
| 模式名称 | 置信度 | 说明 |
|---------|--------|------|
| CN ID Card (High) | 0.6 | 完整格式验证，有效省份前缀 |
| CN ID Card (Medium) | 0.4 | 18位有效结构 |
| CN ID Card (Low) | 0.15 | 任意18位数字+X |

### 上下文词
**中文正式**: 身份证, 身份证号, 身份证号码, 居民身份证, 公民身份号码, 证件号, 证件号码...
**中文口语**: 身份, 证号, 证件, 号码
**场景相关**: 持证人, 实名认证, 身份验证, 身份核验...
**英文**: id card, id number, identification, identity card, citizen id, national id...
**拼音缩写**: sfz, sfzh, zjh, zjhm

---

## 2. CN_PHONE (手机号/固话)

### 格式
- **手机号**: 11位，1开头
  - 中国移动: 134-139, 147, 148, 150-152, 157-159, 172, 178, 182-184, 187-188, 195, 197, 198
  - 中国联通: 130-132, 145, 146, 155-156, 166, 167, 171, 175-176, 185-186, 196
  - 中国电信: 133, 149, 153, 173, 174, 177, 180-181, 189, 190, 191, 193, 199
  - 中国广电: 192
  - 虚拟运营商: 162, 165, 167, 170, 171
- **固话**: 区号(3-4位) + 本地号码(7-8位)
- **服务号码**: 400/800 + 7位

### 正则模式
| 模式名称 | 置信度 | 说明 |
|---------|--------|------|
| CN Mobile (High) | 0.6 | 有效运营商前缀 |
| CN Mobile (Medium) | 0.4 | 任意1[3-9]开头11位 |
| CN Mobile (Separated) | 0.5 | 带分隔符 138-1234-5678 |
| CN Mobile (Country Code) | 0.7 | +86前缀 |
| CN Landline (High) | 0.5 | 固话带区号 |
| CN Landline (Parentheses) | 0.5 | (010)12345678 |
| CN Service Number | 0.5 | 400/800服务号 |

### 上下文词
**手机相关**: 手机, 手机号, 手机号码, 移动电话, 移动号码, 本机号码...
**电话相关**: 电话, 电话号码, 联系电话, 座机, 固话, 固定电话, 传真...
**场景相关**: 联系人, 紧急联系, 客服电话, 热线, 来电, 去电, 通话, 拨打...
**英文**: phone, mobile, cell, cellphone, tel, telephone, contact, fax, landline, hotline...

---

## 3. CN_BANK_CARD (银行卡)

### 格式
- **银联卡**: 62开头，16-19位
- **Visa**: 4开头，16位
- **MasterCard**: 5[1-5]或2[2-7]开头，16位
- **JCB**: 35开头，16位
- **American Express**: 34/37开头，15位

### 验证算法
- Luhn算法 (ISO/IEC 7812)

### 正则模式
| 模式名称 | 置信度 | 说明 |
|---------|--------|------|
| CN Bank Card UnionPay 16 | 0.6 | 银联16位 |
| CN Bank Card UnionPay 19 | 0.6 | 银联19位 |
| CN Bank Card Visa | 0.5 | Visa卡 |
| CN Bank Card MasterCard | 0.5 | 万事达卡 |
| CN Bank Card JCB | 0.5 | JCB卡 |
| CN Bank Card Amex | 0.5 | 美国运通 |
| CN Bank Card Generic | 0.3 | 通用16-19位 |
| CN Bank Card Separated 16/19 | 0.5 | 带分隔符 |

### 上下文词
**卡片类型**: 银行卡, 银行卡号, 卡号, 储蓄卡, 借记卡, 信用卡, 贷记卡, 银联卡...
**账户相关**: 账号, 账户, 开户账号, 收款账号, 付款账号, 转账账号...
**银行名称**: 工商银行, 建设银行, 农业银行, 中国银行, 招商银行, 工行, 建行...
**操作相关**: 转账, 汇款, 收款, 付款, 支付, 结算, 绑定银行卡...
**英文**: bank card, card number, account, debit card, credit card, unionpay, visa, mastercard...

---

## 4. CN_PASSPORT (护照)

### 格式
- **普通护照**: E + 8位数字，或 EA/EB/EC/ED/EE + 7位数字
- **外交护照**: D + 8位数字
- **公务护照**: S + 8位数字，或 SE + 7位数字
- **公务普通护照**: P + 8位数字
- **旧版护照**: G + 8位数字，或 14/15 + 7位数字
- **港澳通行证**: C/W + 8位数字
- **台湾通行证**: L/T + 8位数字

### 上下文词
**护照相关**: 护照, 护照号, 护照号码, 普通护照, 外交护照, 公务护照, 因私护照...
**通行证相关**: 通行证, 港澳通行证, 台湾通行证, 往来港澳通行证...
**场景相关**: 出境, 入境, 出入境, 签证, 签注, 护照有效期...
**英文**: passport, passport number, travel document, travel permit, entry permit...

---

## 5. CN_DRIVER_LICENSE (驾驶证)

### 格式
- **18位**: 与身份证号相同
- **15位**: 旧版格式 (2004年前)
- **档案编号**: 12位数字

### 验证算法
- 与身份证相同的校验码算法

### 上下文词
**驾驶证相关**: 驾驶证, 驾驶证号, 驾照, 驾照号, 机动车驾驶证, 驾驶执照...
**档案相关**: 档案编号, 驾驶档案, 驾驶证档案
**准驾车型**: A1, A2, A3, B1, B2, C1, C2, C3, C4, D, E, F, M, N, P
**场景相关**: 驾驶人, 驾驶员, 司机, 初次领证, 有效期, 换证, 补证...
**英文**: driver license, driver's license, driving license, license number, dl...

---

## 6. CN_SOCIAL_CREDIT_CODE (统一社会信用代码)

### 格式
- **18位**: 登记管理部门代码(1位) + 机构类别代码(1位) + 行政区划码(6位) + 组织机构代码(9位) + 校验码(1位)
- 有效字符: 0-9, A-H, J-N, P-R, T-U, W-Y (不含 I, O, S, V, Z)

### 验证算法
- GB 32100-2015 校验码算法

### 上下文词
**正式称谓**: 统一社会信用代码, 社会信用代码, 信用代码, 统一代码...
**相关证件**: 营业执照, 工商注册, 组织机构代码, 税务登记, 纳税人识别号...
**企业相关**: 企业, 公司, 法人, 注册号, 登记号, 许可证号...
**场景相关**: 开票, 发票, 合同, 签约
**英文**: unified social credit code, uscc, business license, registration number, organization code, tax id...

---

## 7. CN_VEHICLE_PLATE (车牌号)

### 格式
- **普通号牌**: 省份简称 + 字母 + 5位字母数字 (7位)
- **新能源号牌**: 省份简称 + 字母 + 6位字母数字 (8位)
- **军用号牌**: 军/空/海/北/沈/兰/济/南/广/成 + 字母 + 5位
- **警用号牌**: 省份简称 + 字母 + 4位 + 警
- **使馆号牌**: 使 + 5位数字
- **港澳号牌**: 粤Z + 4位 + 港/澳

### 省份简称
京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼

### 上下文词
**车牌相关**: 车牌, 车牌号, 车牌号码, 牌照, 号牌, 机动车号牌...
**车辆相关**: 车辆, 机动车, 汽车, 轿车, 货车, 客车, 私家车, 出租车...
**登记相关**: 行驶证, 车辆登记, 机动车登记, 车主...
**场景相关**: 停车, 违章, 违停, 交通违法, 年检, 年审, 过户, 上牌...
**英文**: license plate, plate number, vehicle plate, car plate, registration plate...

---

## 8. CN_POSTAL_CODE (邮政编码)

### 格式
- **6位数字**: 省份代码(2位) + 邮区(1位) + 县市(1位) + 投递局(2位)
- 省份代码范围: 01-82

### 上下文词
**邮编相关**: 邮编, 邮政编码, 邮政区码, 邮区编号, 邮递区号...
**地址相关**: 地址, 住址, 通讯地址, 联系地址, 收货地址, 寄件地址...
**邮政相关**: 邮政, 邮局, 邮寄, 快递, 包裹, 信件...
**英文**: postal code, postcode, zip code, zip, mailing code, area code...

---

## 9. CN_MILITARY_ID (军人证)

### 格式
- **军官证**: 军字第 + 6-10位数字 + 号
- **士兵证**: 士字第 + 6-10位数字 + 号
- **文职干部证**: 文字第 + 6-10位数字 + 号
- **军人保障卡**: 10位数字

### 上下文词
**军人证件**: 军官证, 军人证, 士兵证, 士官证, 文职干部证, 军人保障卡...
**退役相关**: 退役军人证, 退役证, 退伍证, 复员证, 退役军人, 退伍军人...
**军队相关**: 军队, 部队, 军人, 军官, 士兵, 士官, 现役, 服役, 入伍, 退伍...
**证件相关**: 军字第, 士字第, 文字第, 证件号, 证号
**英文**: military id, military card, soldier id, officer id, military service...

---

## 10. CN_MEDICAL_LICENSE (医师执业证)

### 格式
- **医师执业证书**: 15位数字
- **医疗机构执业许可证**: 省份代码 + 年份 + 编号
- **资格证书**: 10-18位数字

### 上下文词
**医师相关**: 医师, 医生, 执业医师, 主治医师, 医师执业证, 医师资格证...
**护士相关**: 护士, 护师, 护士执业证, 护士资格证...
**药师相关**: 药师, 执业药师, 药剂师, 药师执业证...
**医疗机构**: 医疗机构, 医院, 诊所, 卫生院, 医疗机构执业许可证...
**资格相关**: 资格证, 资格证书, 注册号, 注册编号, 执业注册...
**英文**: medical license, medical practitioner, nurse license, pharmacist license...

---

## 11. CN_EMAIL (邮箱)

### 格式
- **标准邮箱**: user@domain.com
- **QQ邮箱**: 数字@qq.com
- **163/126邮箱**: user@163.com, user@126.com
- **企业邮箱**: user@company.com.cn

### 上下文词
**邮箱相关**: 邮箱, 邮件, 电子邮箱, 电子邮件, 邮箱地址, 收件人, 发件人...
**联系方式**: 联系方式, 联系人, 通讯录, 地址簿
**英文**: email, e-mail, mail, mailbox, sender, recipient, contact...

---

## 12. CN_IP_ADDRESS (IP地址)

### 格式
- **IPv4**: xxx.xxx.xxx.xxx
- **内网IP**: 10.x.x.x, 172.16-31.x.x, 192.168.x.x
- **回环地址**: 127.0.0.1
- **带端口**: xxx.xxx.xxx.xxx:port

### 上下文词
**IP相关**: IP, IP地址, 服务器地址, 主机地址, 内网IP, 公网IP...
**网络相关**: 网络, 网段, 子网, 网关, 路由, 服务器, 主机...
**英文**: ip, ip address, host, server, internal ip, private ip...

---

## 13. CN_MAC_ADDRESS (MAC地址)

### 格式
- **冒号分隔**: AA:BB:CC:DD:EE:FF
- **连字符分隔**: AA-BB-CC-DD-EE-FF
- **点分隔(Cisco)**: AABB.CCDD.EEFF
- **无分隔符**: AABBCCDDEEFF

### 上下文词
**MAC相关**: MAC, MAC地址, 物理地址, 硬件地址, 网卡地址...
**设备相关**: 网卡, 设备, 终端, 路由器, 交换机...
**英文**: mac, mac address, physical address, hardware address, nic...

---

## 14. CN_JDBC_CONNECTION (JDBC连接)

### 格式
- **MySQL**: jdbc:mysql://host:port/database
- **PostgreSQL**: jdbc:postgresql://host:port/database
- **Oracle**: jdbc:oracle:thin:@host:port:sid
- **MongoDB**: mongodb://host:port/database
- **Redis**: redis://host:port

### 上下文词
**数据库相关**: 数据库, 数据库连接, 连接字符串, MySQL, PostgreSQL, Oracle...
**配置相关**: 配置, 配置文件, 连接池, 数据源, JDBC...
**英文**: database, db, connection, datasource, driver...

---

## 15. CN_JWT (JWT令牌)

### 格式
- **标准JWT**: eyJxxx.eyJxxx.xxx (header.payload.signature)
- **无签名JWT**: eyJxxx.eyJxxx.

### 上下文词
**令牌相关**: 令牌, 访问令牌, 刷新令牌, Token, JWT...
**认证相关**: 认证, 授权, 鉴权, 身份验证, 登录凭证...
**英文**: json web token, access token, refresh token, bearer token, oauth...

---

## 16. CN_CLOUD_KEY (云服务密钥)

### 格式
- **阿里云AccessKey**: LTAI + 12-20位字母数字
- **腾讯云SecretId**: AKID + 32位字母数字
- **AWS AccessKey**: AKIA + 16位大写字母数字
- **通用API Key**: 16-64位字母数字

### 上下文词
**云服务**: 阿里云, 腾讯云, 华为云, 百度云, AWS, Azure, GCP...
**密钥相关**: 密钥, AccessKey, SecretKey, AppKey, API Key...
**英文**: access key, secret key, api key, credential, authentication...

---

## 17. CN_WECHAT_ID (微信ID)

### 格式
- **OpenID**: o + 27位字母数字
- **CorpID**: ww/wx + 16位十六进制
- **AppID**: wx + 16位十六进制
- **Secret**: 32位字母数字

### 上下文词
**微信相关**: 微信, 微信号, OpenID, UnionID, 公众号, 小程序...
**企业微信**: 企业微信, CorpID, AgentID...
**英文**: wechat, weixin, open id, union id, app id, corp id...

---

## 18. CN_SENSITIVE_FIELD (敏感字段)

### 格式
- **JSON格式**: "password": "value"
- **查询字符串**: password=value
- **赋值语句**: password = value
- **私钥头**: -----BEGIN PRIVATE KEY-----

### 上下文词
**密码相关**: 密码, 口令, 密钥, 凭证, 登录密码, 支付密码...
**账号相关**: 账号, 用户名, 登录名, 账户...
**英文**: password, passwd, pwd, secret, token, api key, private key...

---

## 使用示例

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.predefined_recognizers.country_specific.china import (
    CnIdCardRecognizer,
    CnPhoneRecognizer,
    CnBankCardRecognizer,
    CnPassportRecognizer,
    CnDriverLicenseRecognizer,
    CnSocialCreditCodeRecognizer,
    CnVehiclePlateRecognizer,
    CnPostalCodeRecognizer,
    CnMilitaryIdRecognizer,
    CnMedicalLicenseRecognizer,
    # 新增识别器
    CnEmailRecognizer,
    CnIpAddressRecognizer,
    CnMacAddressRecognizer,
    CnJdbcRecognizer,
    CnJwtRecognizer,
    CnCloudKeyRecognizer,
    CnWechatRecognizer,
    CnSensitiveFieldRecognizer,
)

# 创建识别器实例
id_recognizer = CnIdCardRecognizer()
phone_recognizer = CnPhoneRecognizer()
bank_recognizer = CnBankCardRecognizer()

# 分析文本
text = "用户身份证号：110101199003074514，手机：13812345678"

id_results = id_recognizer.analyze(text, ["CN_ID_CARD"])
phone_results = phone_recognizer.analyze(text, ["CN_PHONE"])

for result in id_results + phone_results:
    print(f"类型: {result.entity_type}, 位置: {result.start}-{result.end}, 分数: {result.score}")
```

---

## 置信度评分说明

| 分数范围 | 含义 |
|---------|------|
| 0.7-1.0 | 高置信度，格式完全匹配且通过验证 |
| 0.4-0.7 | 中置信度，格式匹配但需上下文确认 |
| 0.1-0.4 | 低置信度，可能匹配但需强上下文支持 |

上下文词匹配可以将置信度提升最多 0.4 分。

---

## 参考标准

- GB 11643-1999 公民身份号码
- GB 32100-2015 法人和其他组织统一社会信用代码编码规则
- GA 36-2018 机动车号牌
- ISO/IEC 7812 银行卡号码
- 中华人民共和国护照法
- 中华人民共和国执业医师法
