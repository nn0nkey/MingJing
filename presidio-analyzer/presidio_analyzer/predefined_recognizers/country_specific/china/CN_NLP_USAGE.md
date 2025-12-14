# 中文NLP识别器使用指南

## 概述

中文敏感信息识别分为两类：

| 类型 | 识别方式 | 适用场景 |
|------|---------|---------|
| **正则识别** | 基于正则表达式 | 格式固定的信息（身份证、手机号、银行卡等） |
| **NLP识别** | 基于spaCy中文模型 | 格式不固定的信息（人名、地名、机构名等） |

## 安装中文spaCy模型

```bash
# 安装spaCy（如果尚未安装）
pip install spacy

# 下载中文模型（选择一个）
python -m spacy download zh_core_web_sm   # 小型模型，速度快
python -m spacy download zh_core_web_md   # 中型模型，平衡
python -m spacy download zh_core_web_lg   # 大型模型，精度高
python -m spacy download zh_core_web_trf  # Transformer模型，精度最高
```

## 使用方式

### 方式1：使用配置文件（推荐）

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# 使用中文配置文件
provider = NlpEngineProvider(conf_file="presidio_analyzer/conf/spacy_chinese.yaml")
nlp_engine = provider.create_engine()

# 创建分析引擎
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    supported_languages=["zh"]
)

# 分析文本
text = "张三住在北京市朝阳区，在阿里巴巴公司工作。"
results = analyzer.analyze(text=text, language="zh")

for result in results:
    print(f"{result.entity_type}: {text[result.start:result.end]} (score: {result.score})")
```

### 方式2：手动配置

```python
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine, NerModelConfiguration
from presidio_analyzer.predefined_recognizers.country_specific.china import (
    CnNlpRecognizer,
    CnIdCardRecognizer,
    CnPhoneRecognizer,
    CnBankCardRecognizer,
)

# 配置NER模型映射
ner_config = NerModelConfiguration(
    model_to_presidio_entity_mapping={
        "PER": "PERSON",
        "PERSON": "PERSON",
        "LOC": "LOCATION",
        "GPE": "LOCATION",
        "ORG": "ORGANIZATION",
        "DATE": "DATE_TIME",
        "TIME": "DATE_TIME",
    },
    low_confidence_score_multiplier=0.6,
    low_score_entity_names=["ORG", "ORGANIZATION"],
    labels_to_ignore=["CARDINAL", "ORDINAL", "MONEY", "PERCENT", "QUANTITY"],
)

# 创建NLP引擎
nlp_engine = SpacyNlpEngine(
    models=[{"lang_code": "zh", "model_name": "zh_core_web_lg"}],
    ner_model_configuration=ner_config,
)
nlp_engine.load()

# 创建识别器注册表
registry = RecognizerRegistry()
registry.supported_languages = ["zh"]

# 添加正则识别器
registry.add_recognizer(CnIdCardRecognizer())
registry.add_recognizer(CnPhoneRecognizer())
registry.add_recognizer(CnBankCardRecognizer())

# 添加NLP识别器
registry.add_recognizer(CnNlpRecognizer())

# 创建分析引擎
analyzer = AnalyzerEngine(
    registry=registry,
    nlp_engine=nlp_engine,
    supported_languages=["zh"]
)

# 分析文本
text = """
用户信息：
姓名：张三
身份证：110101199003074518
手机：13812345678
地址：北京市朝阳区中关村大街1号
工作单位：阿里巴巴集团
"""

results = analyzer.analyze(text=text, language="zh")
for result in results:
    print(f"{result.entity_type}: {text[result.start:result.end]} (score: {result.score:.2f})")
```

## 识别器分类

### 正则识别器（无需NLP模型）

| 识别器 | 实体类型 | 说明 |
|-------|---------|------|
| CnIdCardRecognizer | CN_ID_CARD | 身份证号 |
| CnPhoneRecognizer | CN_PHONE | 手机号/固话 |
| CnBankCardRecognizer | CN_BANK_CARD | 银行卡号 |
| CnPassportRecognizer | CN_PASSPORT | 护照号 |
| CnVehiclePlateRecognizer | CN_VEHICLE_PLATE | 车牌号 |
| CnEmailRecognizer | CN_EMAIL | 邮箱地址 |
| CnIpAddressRecognizer | CN_IP_ADDRESS | IP地址 |
| CnJwtRecognizer | CN_JWT | JWT Token |
| CnCloudKeyRecognizer | CN_CLOUD_KEY | 云服务密钥 |
| ... | ... | ... |

### NLP识别器（需要spaCy中文模型）

| 识别器 | 实体类型 | 说明 |
|-------|---------|------|
| CnNlpRecognizer | PERSON | 人名（张三、李四） |
| CnNlpRecognizer | LOCATION | 地名/地址（北京市、朝阳区） |
| CnNlpRecognizer | ORGANIZATION | 组织机构（阿里巴巴、腾讯公司） |
| CnNlpRecognizer | DATE_TIME | 日期时间（2024年1月1日） |

## 为什么需要NLP？

| 信息类型 | 正则可行性 | 原因 |
|---------|-----------|------|
| 身份证号 | ✅ 可行 | 固定18位格式，有校验码 |
| 手机号 | ✅ 可行 | 固定11位格式，有号段规则 |
| 银行卡号 | ✅ 可行 | 固定长度，有Luhn校验 |
| **人名** | ❌ 不可行 | 长度不固定，无格式规则 |
| **地址** | ❌ 不可行 | 格式多样，需要语义理解 |
| **机构名** | ❌ 不可行 | 格式多样，需要语义理解 |

## 模型选择建议

| 模型 | 大小 | 速度 | 精度 | 适用场景 |
|-----|------|------|------|---------|
| zh_core_web_sm | ~15MB | 最快 | 一般 | 快速原型、资源受限 |
| zh_core_web_md | ~45MB | 快 | 较好 | 一般生产环境 |
| zh_core_web_lg | ~400MB | 中等 | 好 | 高精度需求 |
| zh_core_web_trf | ~400MB | 慢 | 最好 | 最高精度需求 |

## 评分策略

NLP识别器的评分策略：

| 条件 | 分数调整 |
|-----|---------|
| 基础分数 | 0.85 |
| 有上下文词汇 | +0.1 |
| 人名有常见姓氏 | +0.1 |
| 地名有行政区划后缀 | +0.1 |
| 机构名有组织后缀 | +0.1 |
| 实体太短 | ×0.5 |

最终分数 ≥ 0.5 直接确认，< 0.5 需要LLM验证。
