"""
中文敏感信息识别完整示例（含LLM验证）

使用方式:
1. API模式（需要API密钥）:
   python chinese_analyzer_with_llm.py --mode api --api-key sk-xxx

2. 本地模型模式（需要模型路径）:
   python chinese_analyzer_with_llm.py --mode local --model-path /path/to/model

3. 测试模式（无需外部依赖）:
   python chinese_analyzer_with_llm.py --mode mock
"""

import argparse
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import (
    SpacyNlpEngine, 
    NerModelConfiguration,
    create_verifier,
)
from presidio_analyzer.predefined_recognizers.country_specific.china import (
    CnIdCardRecognizer,
    CnPhoneRecognizer,
    CnBankCardRecognizer,
    CnEmailRecognizer,
    CnIpAddressRecognizer,
    CnPostalCodeRecognizer,
    CnVehiclePlateRecognizer,
    CnPassportRecognizer,
    CnJwtRecognizer,
    CnCloudKeyRecognizer,
    CnNlpRecognizer,
)


def create_chinese_analyzer(use_nlp: bool = True):
    """
    创建中文敏感信息分析引擎。
    
    :param use_nlp: 是否使用NLP识别器（需要spaCy中文模型）
    :return: AnalyzerEngine实例
    """
    # 创建识别器注册表
    registry = RecognizerRegistry()
    registry.supported_languages = ["zh"]
    
    # 添加正则识别器
    regex_recognizers = [
        CnIdCardRecognizer(),
        CnPhoneRecognizer(),
        CnBankCardRecognizer(),
        CnEmailRecognizer(),
        CnIpAddressRecognizer(),
        CnPostalCodeRecognizer(),
        CnVehiclePlateRecognizer(),
        CnPassportRecognizer(),
        CnJwtRecognizer(),
        CnCloudKeyRecognizer(),
    ]
    
    for recognizer in regex_recognizers:
        registry.add_recognizer(recognizer)
    
    nlp_engine = None
    
    if use_nlp:
        try:
            # 配置NER模型
            ner_config = NerModelConfiguration(
                model_to_presidio_entity_mapping={
                    "PER": "PERSON",
                    "LOC": "LOCATION",
                    "GPE": "LOCATION",
                    "ORG": "ORGANIZATION",
                },
                default_score=0.4,
            )
            
            # 创建NLP引擎
            nlp_engine = SpacyNlpEngine(
                models=[{"lang_code": "zh", "model_name": "zh_core_web_md"}],
                ner_model_configuration=ner_config,
            )
            nlp_engine.load()
            
            # 添加NLP识别器
            registry.add_recognizer(CnNlpRecognizer())
            print("✅ NLP引擎加载成功")
        except Exception as e:
            print(f"⚠️ NLP引擎加载失败: {e}")
            print("   将只使用正则识别器")
            use_nlp = False
    
    # 创建分析引擎
    analyzer = AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["zh"]
    )
    
    return analyzer


def analyze_with_llm_verification(
    text: str,
    analyzer: AnalyzerEngine,
    verifier,
    entities: list = None,
):
    """
    分析文本并进行LLM验证。
    
    :param text: 待分析文本
    :param analyzer: 分析引擎
    :param verifier: LLM验证器
    :param entities: 要识别的实体类型列表
    :return: 最终结果列表
    """
    # 第一步：使用识别器分析
    results = analyzer.analyze(text=text, language="zh", entities=entities)
    
    if not results:
        return []
    
    # 第二步：LLM验证低分结果
    verified = verifier.verify_results(text, results)
    
    # 第三步：整理最终结果
    final_results = []
    for original, verification in verified:
        entity_text = text[original.start:original.end]
        
        if verification:
            # 经过LLM验证
            if verification.is_sensitive:
                final_results.append({
                    "entity_type": original.entity_type,
                    "text": entity_text,
                    "start": original.start,
                    "end": original.end,
                    "original_score": original.score,
                    "final_score": verification.final_score,
                    "verified": True,
                    "llm_reason": verification.reason,
                })
            # 如果LLM判断不是敏感信息，则不加入结果
        else:
            # 无需验证，直接确认
            final_results.append({
                "entity_type": original.entity_type,
                "text": entity_text,
                "start": original.start,
                "end": original.end,
                "original_score": original.score,
                "final_score": original.score,
                "verified": False,
                "llm_reason": None,
            })
    
    return final_results


def main():
    parser = argparse.ArgumentParser(description="中文敏感信息识别（含LLM验证）")
    parser.add_argument("--mode", choices=["api", "local", "mock"], default="mock",
                        help="LLM验证模式: api/local/mock")
    parser.add_argument("--api-key", help="API密钥（api模式需要）")
    parser.add_argument("--api-base", default="https://api.openai.com/v1",
                        help="API基础URL")
    parser.add_argument("--model", default="gpt-3.5-turbo",
                        help="模型名称（api模式）或模型路径（local模式）")
    parser.add_argument("--no-nlp", action="store_true",
                        help="不使用NLP识别器")
    parser.add_argument("--text", help="要分析的文本")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("中文敏感信息识别系统")
    print("=" * 70)
    
    # 创建分析引擎
    analyzer = create_chinese_analyzer(use_nlp=not args.no_nlp)
    
    # 创建LLM验证器
    if args.mode == "api":
        if not args.api_key:
            print("❌ API模式需要提供 --api-key")
            sys.exit(1)
        verifier = create_verifier(
            mode="api",
            api_key=args.api_key,
            api_base=args.api_base,
            model=args.model,
        )
        print(f"✅ LLM验证器: API模式 ({args.model})")
    elif args.mode == "local":
        verifier = create_verifier(
            mode="local",
            model_path=args.model,
        )
        print(f"✅ LLM验证器: 本地模型 ({args.model})")
    else:
        verifier = create_verifier(mode="mock")
        print("✅ LLM验证器: 测试模式")
    
    print()
    
    # 测试文本
    if args.text:
        test_texts = [args.text]
    else:
        test_texts = [
            "用户张三，身份证号110101199003074518，手机13812345678。",
            "收货地址：北京市朝阳区中关村大街1号，邮编100000。",
            "工作单位：阿里巴巴集团，邮箱zhangsan@qq.com。",
            "服务器IP：192.168.1.100，版本号1.2.3.4。",
        ]
    
    for text in test_texts:
        print("-" * 70)
        print(f"文本: {text}")
        print()
        
        results = analyze_with_llm_verification(text, analyzer, verifier)
        
        if results:
            print("识别结果:")
            for r in results:
                verified_mark = "🔍" if r["verified"] else "✅"
                print(f"  {verified_mark} {r['entity_type']}: \"{r['text']}\"")
                print(f"     分数: {r['original_score']:.2f} → {r['final_score']:.2f}")
                if r["llm_reason"]:
                    print(f"     LLM理由: {r['llm_reason']}")
        else:
            print("  未识别到敏感信息")
        print()


if __name__ == "__main__":
    main()
