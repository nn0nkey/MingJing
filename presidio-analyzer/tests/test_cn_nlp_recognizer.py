"""
Test Chinese NLP Recognizer.

运行此测试前需要安装中文spaCy模型：
    python -m spacy download zh_core_web_sm
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_spacy_chinese_model():
    """检查是否安装了中文spaCy模型。"""
    try:
        import spacy
        models = spacy.util.get_installed_models()
        chinese_models = [m for m in models if m.startswith('zh_')]
        return len(chinese_models) > 0
    except ImportError:
        return False


# 如果没有安装中文模型，跳过测试
pytestmark = pytest.mark.skipif(
    not check_spacy_chinese_model(),
    reason="需要安装中文spaCy模型: python -m spacy download zh_core_web_sm"
)


class TestCnNlpRecognizer:
    """测试中文NLP识别器。"""

    @pytest.fixture
    def analyzer(self):
        """创建配置好的分析引擎。"""
        from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
        from presidio_analyzer.nlp_engine import SpacyNlpEngine, NerModelConfiguration
        from presidio_analyzer.predefined_recognizers.country_specific.china import CnNlpRecognizer
        
        # 获取已安装的中文模型
        import spacy
        models = spacy.util.get_installed_models()
        chinese_model = next((m for m in models if m.startswith('zh_')), None)
        
        if not chinese_model:
            pytest.skip("未安装中文spaCy模型")
        
        # 配置NER模型
        ner_config = NerModelConfiguration(
            model_to_presidio_entity_mapping={
                "PER": "PERSON",
                "PERSON": "PERSON",
                "LOC": "LOCATION",
                "GPE": "LOCATION",
                "FAC": "LOCATION",
                "ORG": "ORGANIZATION",
                "DATE": "DATE_TIME",
                "TIME": "DATE_TIME",
                "NORP": "NRP",
            },
            low_confidence_score_multiplier=0.6,
            low_score_entity_names=["ORG", "ORGANIZATION"],
            labels_to_ignore=["CARDINAL", "ORDINAL", "MONEY", "PERCENT", "QUANTITY"],
        )
        
        # 创建NLP引擎
        nlp_engine = SpacyNlpEngine(
            models=[{"lang_code": "zh", "model_name": chinese_model}],
            ner_model_configuration=ner_config,
        )
        nlp_engine.load()
        
        # 创建识别器注册表
        registry = RecognizerRegistry()
        registry.supported_languages = ["zh"]
        registry.add_recognizer(CnNlpRecognizer())
        
        # 创建分析引擎
        return AnalyzerEngine(
            registry=registry,
            nlp_engine=nlp_engine,
            supported_languages=["zh"]
        )

    def test_person_recognition(self, analyzer):
        """测试人名识别。"""
        text = "张三是我们公司的员工。"
        results = analyzer.analyze(text=text, language="zh", entities=["PERSON"])
        
        # 检查是否识别到人名
        person_results = [r for r in results if r.entity_type == "PERSON"]
        assert len(person_results) > 0, f"未识别到人名，结果: {results}"
        
        # 检查识别的文本
        for r in person_results:
            detected_text = text[r.start:r.end]
            print(f"识别到人名: {detected_text} (score: {r.score})")

    def test_location_recognition(self, analyzer):
        """测试地名识别。"""
        text = "我住在北京市朝阳区。"
        results = analyzer.analyze(text=text, language="zh", entities=["LOCATION"])
        
        # 检查是否识别到地名
        location_results = [r for r in results if r.entity_type == "LOCATION"]
        assert len(location_results) > 0, f"未识别到地名，结果: {results}"
        
        for r in location_results:
            detected_text = text[r.start:r.end]
            print(f"识别到地名: {detected_text} (score: {r.score})")

    def test_organization_recognition(self, analyzer):
        """测试组织机构识别。"""
        text = "他在阿里巴巴集团工作。"
        results = analyzer.analyze(text=text, language="zh", entities=["ORGANIZATION"])
        
        # 检查是否识别到组织
        org_results = [r for r in results if r.entity_type == "ORGANIZATION"]
        assert len(org_results) > 0, f"未识别到组织机构，结果: {results}"
        
        for r in org_results:
            detected_text = text[r.start:r.end]
            print(f"识别到组织: {detected_text} (score: {r.score})")

    def test_mixed_entities(self, analyzer):
        """测试混合实体识别。"""
        text = """
        用户信息：
        姓名：李明
        地址：上海市浦东新区张江高科技园区
        工作单位：腾讯科技有限公司
        """
        
        results = analyzer.analyze(
            text=text, 
            language="zh", 
            entities=["PERSON", "LOCATION", "ORGANIZATION"]
        )
        
        print("\n混合实体识别结果:")
        for r in results:
            detected_text = text[r.start:r.end]
            print(f"  {r.entity_type}: {detected_text} (score: {r.score:.2f})")
        
        # 至少应该识别到一些实体
        assert len(results) > 0, "未识别到任何实体"

    def test_score_adjustment(self, analyzer):
        """测试分数调整逻辑。"""
        # 有上下文词汇的情况
        text_with_context = "联系人姓名：王小明"
        results = analyzer.analyze(text=text_with_context, language="zh", entities=["PERSON"])
        
        if results:
            print(f"有上下文: {text_with_context[results[0].start:results[0].end]} -> {results[0].score}")
        
        # 无上下文词汇的情况
        text_without_context = "王小明说今天天气不错"
        results2 = analyzer.analyze(text=text_without_context, language="zh", entities=["PERSON"])
        
        if results2:
            print(f"无上下文: {text_without_context[results2[0].start:results2[0].end]} -> {results2[0].score}")


def test_import():
    """测试导入。"""
    from presidio_analyzer.predefined_recognizers.country_specific.china import CnNlpRecognizer
    
    recognizer = CnNlpRecognizer()
    assert recognizer.supported_language == "zh"
    assert "PERSON" in recognizer.supported_entities
    assert "LOCATION" in recognizer.supported_entities
    assert "ORGANIZATION" in recognizer.supported_entities


if __name__ == "__main__":
    # 直接运行测试
    if check_spacy_chinese_model():
        pytest.main([__file__, "-v", "-s"])
    else:
        print("=" * 60)
        print("未安装中文spaCy模型！")
        print()
        print("请运行以下命令安装：")
        print("  python -m spacy download zh_core_web_sm")
        print()
        print("或者安装更大的模型以获得更好的精度：")
        print("  python -m spacy download zh_core_web_lg")
        print("=" * 60)
