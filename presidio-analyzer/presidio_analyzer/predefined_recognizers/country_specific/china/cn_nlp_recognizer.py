"""
Chinese NLP-based Entity Recognizer.

使用 spaCy 中文模型进行命名实体识别，适用于：
- 人名 (PERSON)
- 地名/地址 (LOCATION)
- 组织机构 (ORGANIZATION)
- 日期时间 (DATE_TIME)

这些实体类型难以用正则表达式准确识别，需要NLP模型。
"""

import logging
from typing import List, Optional, Set, Tuple

from presidio_analyzer import (
    AnalysisExplanation,
    LocalRecognizer,
    RecognizerResult,
)

logger = logging.getLogger("presidio-analyzer")


class CnNlpRecognizer(LocalRecognizer):
    """
    使用 spaCy 中文模型识别命名实体。
    
    支持的实体类型:
    - PERSON: 人名（如：张三、李四、王小明）
    - LOCATION: 地名/地址（如：北京市、朝阳区、中关村大街）
    - ORGANIZATION: 组织机构（如：阿里巴巴、腾讯公司、北京大学）
    - DATE_TIME: 日期时间（如：2024年1月1日、下午3点）
    
    注意：此识别器依赖 AnalyzerEngine 提供的 NLP artifacts，
    不能单独使用，必须配合 SpacyNlpEngine 使用。
    """

    # 支持的实体类型
    ENTITIES = [
        "PERSON",       # 人名
        "LOCATION",     # 地名/地址
        "ORGANIZATION", # 组织机构
        "DATE_TIME",    # 日期时间
        "NRP",          # 国籍/宗教/政治团体
    ]

    # 中文上下文词汇，用于提高置信度
    CONTEXT_WORDS = {
        "PERSON": [
            "姓名", "名字", "本人", "用户", "客户", "员工", "先生", "女士",
            "联系人", "负责人", "经办人", "申请人", "持卡人", "收件人", "发件人",
            "法人", "代表", "签名", "签字", "户主", "业主", "房主",
        ],
        "LOCATION": [
            "地址", "住址", "居住地", "户籍", "籍贯", "所在地", "位置",
            "省", "市", "区", "县", "镇", "乡", "村", "街道", "路", "号",
            "小区", "楼", "单元", "室", "门牌", "邮寄地址", "收货地址",
            "公司地址", "家庭地址", "工作地址", "通讯地址",
        ],
        "ORGANIZATION": [
            "公司", "企业", "单位", "机构", "组织", "部门", "集团",
            "有限公司", "股份公司", "责任公司", "合伙企业",
            "银行", "医院", "学校", "大学", "学院", "研究所", "研究院",
            "工作单位", "就职单位", "所属单位", "开户行", "发卡行",
        ],
        "DATE_TIME": [
            "日期", "时间", "出生日期", "生日", "出生年月", "入职日期",
            "有效期", "到期日", "签发日期", "注册日期", "创建时间",
        ],
    }

    DEFAULT_EXPLANATION = "由 spaCy 中文 NER 模型识别为 {}"

    def __init__(
        self,
        supported_language: str = "zh",
        supported_entities: Optional[List[str]] = None,
        ner_strength: float = 0.4,
        check_label_groups: Optional[List[Tuple[Set, Set]]] = None,
        context: Optional[List[str]] = None,
    ):
        """
        初始化中文NLP识别器。
        
        :param supported_language: 支持的语言，默认 "zh"
        :param supported_entities: 支持的实体类型列表
        :param ner_strength: NER模型的默认置信度（0.4，需要验证后提升）
        :param context: 上下文词汇列表
        """
        self.ner_strength = ner_strength
        
        # 合并所有上下文词汇
        all_context = []
        for words in self.CONTEXT_WORDS.values():
            all_context.extend(words)
        
        context = context if context else all_context
        supported_entities = supported_entities if supported_entities else self.ENTITIES
        
        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            context=context,
        )

    def load(self) -> None:
        """加载模型（NLP模型由 AnalyzerEngine 加载，此处无需操作）。"""
        pass

    def build_explanation(
        self, original_score: float, explanation: str
    ) -> AnalysisExplanation:
        """创建识别结果的解释说明。"""
        return AnalysisExplanation(
            recognizer=self.name,
            original_score=original_score,
            textual_explanation=explanation,
        )

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        """
        分析文本并返回识别到的实体。
        
        :param text: 待分析的文本
        :param entities: 要识别的实体类型列表
        :param nlp_artifacts: NLP处理结果（由 SpacyNlpEngine 提供）
        :return: 识别结果列表
        """
        results = []
        
        if not nlp_artifacts:
            logger.warning("跳过 CnNlpRecognizer，未提供 NLP artifacts...")
            return results

        ner_entities = nlp_artifacts.entities
        ner_scores = nlp_artifacts.scores

        for ner_entity, ner_score in zip(ner_entities, ner_scores):
            entity_label = ner_entity.label_
            
            # 检查实体类型是否在请求的实体列表中
            if entity_label not in entities:
                continue
            
            # 检查实体类型是否被此识别器支持
            if entity_label not in self.supported_entities:
                logger.debug(
                    f"跳过实体 {entity_label}，不在支持的实体列表中"
                )
                continue

            # 获取实体文本
            entity_text = text[ner_entity.start_char:ner_entity.end_char]
            
            # 应用额外的验证规则
            adjusted_score = self._adjust_score(
                entity_label, entity_text, text, ner_entity.start_char, ner_entity.end_char, ner_score
            )
            
            if adjusted_score <= 0:
                continue

            textual_explanation = self.DEFAULT_EXPLANATION.format(entity_label)
            explanation = self.build_explanation(adjusted_score, textual_explanation)
            
            result = RecognizerResult(
                entity_type=entity_label,
                start=ner_entity.start_char,
                end=ner_entity.end_char,
                score=adjusted_score,
                analysis_explanation=explanation,
                recognition_metadata={
                    RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                    RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                },
            )
            results.append(result)

        return results

    def _adjust_score(
        self, 
        entity_type: str, 
        entity_text: str, 
        full_text: str,
        start: int,
        end: int,
        base_score: float
    ) -> float:
        """
        根据上下文和实体特征调整置信分数。
        
        :param entity_type: 实体类型
        :param entity_text: 实体文本
        :param full_text: 完整文本
        :param start: 实体起始位置
        :param end: 实体结束位置
        :param base_score: 基础分数
        :return: 调整后的分数
        """
        score = base_score
        
        # 检查上下文词汇
        context_start = max(0, start - 20)
        context_end = min(len(full_text), end + 20)
        context = full_text[context_start:context_end]
        
        context_words = self.CONTEXT_WORDS.get(entity_type, [])
        for word in context_words:
            if word in context:
                score = min(1.0, score + 0.1)  # 有上下文词汇，提高分数
                break
        
        # 实体类型特定的验证
        if entity_type == "PERSON":
            score = self._validate_person(entity_text, score)
        elif entity_type == "LOCATION":
            score = self._validate_location(entity_text, score)
        elif entity_type == "ORGANIZATION":
            score = self._validate_organization(entity_text, score)
        
        return score

    def _validate_person(self, text: str, score: float) -> float:
        """验证人名实体。"""
        # 中文人名通常2-4个字
        if len(text) < 2 or len(text) > 6:
            score *= 0.5
        
        # 常见姓氏检查（提高置信度）
        common_surnames = "王李张刘陈杨黄赵周吴徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾萧田董潘袁蔡蒋余于杜叶程魏苏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦傅方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤"
        if text and text[0] in common_surnames:
            score = min(1.0, score + 0.1)
        
        return score

    def _validate_location(self, text: str, score: float) -> float:
        """验证地名实体。"""
        # 地名通常包含行政区划后缀
        location_suffixes = ["省", "市", "区", "县", "镇", "乡", "村", "街道", "路", "道", "巷", "弄", "号", "楼", "室"]
        for suffix in location_suffixes:
            if text.endswith(suffix):
                score = min(1.0, score + 0.1)
                break
        
        # 太短的地名可能是误识别
        if len(text) < 2:
            score *= 0.5
        
        return score

    def _validate_organization(self, text: str, score: float) -> float:
        """验证组织机构实体。"""
        # 组织机构通常包含特定后缀
        org_suffixes = ["公司", "集团", "银行", "医院", "学校", "大学", "学院", "研究所", "研究院", "中心", "局", "部", "厅", "委", "会", "协会", "基金会"]
        for suffix in org_suffixes:
            if text.endswith(suffix):
                score = min(1.0, score + 0.1)
                break
        
        # 太短的组织名可能是误识别
        if len(text) < 3:
            score *= 0.5
        
        return score
