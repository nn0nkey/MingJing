#!/usr/bin/env python3
"""
Test Chinese recognizers for Presidio.
测试中国敏感信息识别器
"""

import sys
sys.path.insert(0, '/Users/liaojialin.6/PyCharmMiscProject/presidio-2.2.360/presidio-analyzer')

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.predefined_recognizers.country_specific.china import (
    CnIdCardRecognizer,
    CnPhoneRecognizer,
    CnBankCardRecognizer,
)


def test_id_card_recognizer():
    """测试身份证识别器"""
    print("=" * 60)
    print("测试 1: 身份证号识别 (CN_ID_CARD)")
    print("=" * 60)
    
    recognizer = CnIdCardRecognizer()
    
    # 测试用例
    test_cases = [
        # (文本, 是否应该识别到, 说明)
        ("我的身份证号是110101199003077758", True, "有效身份证号 + 上下文"),
        ("身份证：11010119900307775X", True, "有效身份证号（X结尾）"),
        ("证件号码：110101199003077758", True, "有上下文"),
        ("110101199003077758", True, "无上下文，但格式正确"),
        ("订单号：110101199003077758", False, "上下文不匹配（可能误报）"),
        ("123456789012345678", False, "无效的身份证号（校验码错误）"),
        ("111111111111111111", False, "全相同数字"),
    ]
    
    for text, should_match, desc in test_cases:
        # 使用 analyze 方法
        results = recognizer.analyze(text, ["CN_ID_CARD"])
        
        if results:
            # 验证校验码
            for r in results:
                matched_text = text[r.start:r.end]
                is_valid = recognizer.validate_result(matched_text)
                print(f"✅ 识别到: '{matched_text}' | 置信度: {r.score:.2f} | 校验: {'通过' if is_valid else '失败'} | {desc}")
        else:
            status = "✅" if not should_match else "❌"
            print(f"{status} 未识别 | {desc}")
    print()


def test_phone_recognizer():
    """测试手机号识别器"""
    print("=" * 60)
    print("测试 2: 手机号识别 (CN_PHONE)")
    print("=" * 60)
    
    recognizer = CnPhoneRecognizer()
    
    test_cases = [
        ("我的手机号是13812345678", True, "中国移动号码"),
        ("联系电话：15912345678", True, "中国移动号码 + 上下文"),
        ("手机：18612345678", True, "中国联通号码"),
        ("电话 138-1234-5678", True, "带分隔符"),
        ("tel: 138 1234 5678", True, "带空格分隔"),
        ("订单号：13812345678", False, "上下文不匹配（可能误报）"),
        ("12345678901", False, "无效号段"),
        ("11111111111", False, "全相同数字"),
    ]
    
    for text, should_match, desc in test_cases:
        results = recognizer.analyze(text, ["CN_PHONE"])
        
        if results:
            for r in results:
                matched_text = text[r.start:r.end]
                is_valid = recognizer.validate_result(matched_text)
                print(f"✅ 识别到: '{matched_text}' | 置信度: {r.score:.2f} | 校验: {'通过' if is_valid else '失败'} | {desc}")
        else:
            status = "✅" if not should_match else "❌"
            print(f"{status} 未识别 | {desc}")
    print()


def test_bank_card_recognizer():
    """测试银行卡识别器"""
    print("=" * 60)
    print("测试 3: 银行卡号识别 (CN_BANK_CARD)")
    print("=" * 60)
    
    recognizer = CnBankCardRecognizer()
    
    test_cases = [
        # 使用 Luhn 校验有效的测试卡号
        ("银行卡号 6212340000000001", True, "银联卡号 16位"),
        ("银行卡号 6212345678900000003", True, "银联卡号 19位"),
        ("卡号 6212 3400 0000 0001", True, "带空格分隔 16位"),
        ("账号 6212-3456-7890-0000-003", True, "带横线分隔 19位"),
        ("信用卡 4532015112830366", True, "Visa 卡 16位（Luhn 校验通过）"),
        ("1234567890123456", False, "Luhn 校验失败"),
        ("0000000000000000", False, "全零"),
    ]
    
    for text, should_match, desc in test_cases:
        results = recognizer.analyze(text, ["CN_BANK_CARD"])
        
        if results:
            for r in results:
                matched_text = text[r.start:r.end]
                is_valid = recognizer.validate_result(matched_text)
                print(f"✅ 识别到: '{matched_text}' | 置信度: {r.score:.2f} | 校验: {'通过' if is_valid else '失败'} | {desc}")
        else:
            status = "✅" if not should_match else "❌"
            print(f"{status} 未识别 | {desc}")
    print()


def test_integrated():
    """测试集成 - 直接使用识别器"""
    print("=" * 60)
    print("测试 4: 集成测试 (直接调用识别器)")
    print("=" * 60)
    
    # 创建识别器
    id_recognizer = CnIdCardRecognizer()
    phone_recognizer = CnPhoneRecognizer()
    bank_recognizer = CnBankCardRecognizer()
    
    # 测试文本（使用 Luhn 校验有效的银行卡号）
    test_text = """
    用户信息：
    姓名：张三
    身份证号：110101199003077758
    手机号：13812345678
    银行卡：6212345678900000003
    邮箱：zhangsan@example.com
    """
    
    print(f"测试文本:\n{test_text}")
    print("-" * 40)
    
    # 分析
    all_results = []
    all_results.extend(id_recognizer.analyze(test_text, ["CN_ID_CARD"]))
    all_results.extend(phone_recognizer.analyze(test_text, ["CN_PHONE"]))
    all_results.extend(bank_recognizer.analyze(test_text, ["CN_BANK_CARD"]))
    
    print(f"识别结果 ({len(all_results)} 个):")
    for r in all_results:
        matched_text = test_text[r.start:r.end]
        print(f"  - {r.entity_type}: '{matched_text}' | 置信度: {r.score:.2f} | 位置: [{r.start}:{r.end}]")
    print()


def test_checksum_validation():
    """测试校验算法"""
    print("=" * 60)
    print("测试 5: 校验算法验证")
    print("=" * 60)
    
    id_recognizer = CnIdCardRecognizer()
    bank_recognizer = CnBankCardRecognizer()
    
    # 身份证校验
    print("身份证校验码测试:")
    id_cards = [
        ("110101199003077758", True),   # 有效
        ("11010119900307775X", True),   # 有效（X结尾）
        ("110101199003077759", False),  # 无效（校验码错误）
        ("123456789012345678", False),  # 无效
    ]
    for id_card, expected in id_cards:
        result = id_recognizer.validate_result(id_card)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {id_card} -> {'有效' if result else '无效'} (预期: {'有效' if expected else '无效'})")
    
    print()
    
    # 银行卡 Luhn 校验
    print("银行卡 Luhn 校验测试:")
    bank_cards = [
        ("4532015112830366", True),     # 有效 Visa
        ("6222021234567890123", False), # 测试号（可能无效）
        ("1234567890123456", False),    # 无效
    ]
    for card, expected in bank_cards:
        result = bank_recognizer.validate_result(card)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {card} -> {'有效' if result else '无效'} (预期: {'有效' if expected else '无效'})")
    print()


if __name__ == "__main__":
    print("🇨🇳 中国敏感信息识别器测试\n")
    
    test_id_card_recognizer()
    test_phone_recognizer()
    test_bank_card_recognizer()
    test_integrated()
    test_checksum_validation()
    
    print("=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
