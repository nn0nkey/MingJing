"""
统一规则管理器

支持:
- 加载/保存所有正则规则（内置+自定义）
- 动态添加/修改/删除规则
- 内置规则可修改但不可删除
- 自定义规则可完全增删改
- 规则验证
- 从规则生成识别器
"""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger("mingjing.rules")

# 规则文件路径
RULES_DIR = Path(__file__).parent
ALL_RULES_FILE = RULES_DIR / "all_rules.yaml"
DEFAULT_RULES_FILE = ALL_RULES_FILE  # 兼容旧代码


@dataclass
class PatternConfig:
    """正则模式配置"""
    regex: str
    name: str
    score: float = 0.5
    
    def validate(self) -> bool:
        """验证正则表达式是否有效"""
        try:
            re.compile(self.regex)
            return True
        except re.error:
            return False


@dataclass
class Rule:
    """统一规则（内置+自定义）"""
    name: str
    entity_type: str
    patterns: List[PatternConfig] = field(default_factory=list)
    context: List[str] = field(default_factory=list)
    enabled: bool = True
    description: str = ""
    category: str = "其他"
    source: str = "custom"  # builtin 或 custom
    validator: Optional[str] = None  # 验证器名称
    
    def validate(self) -> tuple[bool, str]:
        """
        验证规则是否有效
        
        :return: (是否有效, 错误信息)
        """
        if not self.name:
            return False, "规则名称不能为空"
        if not self.entity_type:
            return False, "实体类型不能为空"
        if not self.patterns:
            return False, "至少需要一个正则模式"
        
        for i, pattern in enumerate(self.patterns):
            if not pattern.validate():
                return False, f"正则模式 {i+1} 无效: {pattern.regex}"
        
        return True, ""
    
    def is_builtin(self) -> bool:
        """是否是内置规则"""
        return self.source == "builtin"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "category": self.category,
            "source": self.source,
            "patterns": [asdict(p) for p in self.patterns],
            "context": self.context,
            "enabled": self.enabled,
            "validator": self.validator,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        """从字典创建"""
        patterns = [
            PatternConfig(
                regex=p.get("regex", ""),
                name=p.get("name", ""),
                score=p.get("score", 0.5),
            )
            for p in data.get("patterns", [])
        ]
        return cls(
            name=data.get("name", ""),
            entity_type=data.get("entity_type", ""),
            description=data.get("description", ""),
            category=data.get("category", "其他"),
            source=data.get("source", "custom"),
            patterns=patterns,
            context=data.get("context", []),
            enabled=data.get("enabled", True),
            validator=data.get("validator"),
        )


# 兼容旧代码
CustomRule = Rule


class RulesManager:
    """
    统一规则管理器
    
    管理所有正则规则（内置+自定义）
    - 内置规则：可修改正则、分数、上下文，但不可删除
    - 自定义规则：可完全增删改
    
    用法:
        manager = RulesManager()
        
        # 获取所有规则
        rules = manager.get_all_rules()
        
        # 获取内置/自定义规则
        builtin = manager.get_builtin_rules()
        custom = manager.get_custom_rules()
        
        # 添加规则（仅自定义）
        manager.add_rule(Rule(...))
        
        # 更新规则（内置和自定义都可以）
        manager.update_rule("规则名称", Rule(...))
        
        # 删除规则（仅自定义）
        manager.delete_rule("规则名称")
        
        # 保存到文件
        manager.save()
    """
    
    def __init__(self, rules_file: Optional[Path] = None):
        """
        初始化规则管理器
        
        :param rules_file: 规则文件路径
        """
        self._rules_file = rules_file or ALL_RULES_FILE
        self._rules: Dict[str, Rule] = {}
        self._load_rules()
    
    def _load_rules(self) -> None:
        """从文件加载规则"""
        if not self._rules_file.exists():
            logger.warning(f"规则文件不存在: {self._rules_file}")
            return
        
        try:
            with open(self._rules_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # 新格式：rules 列表
            rules_data = data.get("rules", [])
            # 兼容旧格式：custom_rules 列表
            if not rules_data:
                rules_data = data.get("custom_rules", [])
            
            for rule_data in rules_data:
                rule = Rule.from_dict(rule_data)
                self._rules[rule.name] = rule
            
            builtin_count = len([r for r in self._rules.values() if r.is_builtin()])
            custom_count = len(self._rules) - builtin_count
            logger.info(f"加载了 {len(self._rules)} 条规则（内置: {builtin_count}, 自定义: {custom_count}）")
        except Exception as e:
            logger.error(f"加载规则文件失败: {e}")
    
    def save(self, path: Optional[Path] = None) -> None:
        """
        保存规则到文件
        
        :param path: 保存路径，为空则使用默认路径
        """
        save_path = path or self._rules_file
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "rules": [rule.to_dict() for rule in self._rules.values()]
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        logger.info(f"保存了 {len(self._rules)} 条规则到 {save_path}")
    
    def reload(self) -> None:
        """重新加载规则"""
        self._rules.clear()
        self._load_rules()
    
    def get_all_rules(self) -> List[Rule]:
        """获取所有规则"""
        return list(self._rules.values())
    
    def get_enabled_rules(self) -> List[Rule]:
        """获取所有启用的规则"""
        return [r for r in self._rules.values() if r.enabled]
    
    def get_builtin_rules(self) -> List[Rule]:
        """获取所有内置规则"""
        return [r for r in self._rules.values() if r.is_builtin()]
    
    def get_custom_rules(self) -> List[Rule]:
        """获取所有自定义规则"""
        return [r for r in self._rules.values() if not r.is_builtin()]
    
    def get_rule(self, name: str) -> Optional[Rule]:
        """获取指定规则"""
        return self._rules.get(name)
    
    def add_rule(self, rule: Rule) -> tuple[bool, str]:
        """
        添加规则（仅自定义规则）
        
        :param rule: 规则对象
        :return: (是否成功, 消息)
        """
        # 验证规则
        valid, error = rule.validate()
        if not valid:
            return False, error
        
        # 检查是否已存在
        if rule.name in self._rules:
            return False, f"规则 '{rule.name}' 已存在"
        
        # 新增规则默认为自定义
        rule.source = "custom"
        self._rules[rule.name] = rule
        return True, f"规则 '{rule.name}' 添加成功"
    
    def update_rule(self, name: str, rule: Rule) -> tuple[bool, str]:
        """
        更新规则（内置和自定义都可以）
        
        :param name: 原规则名称
        :param rule: 新规则对象
        :return: (是否成功, 消息)
        """
        if name not in self._rules:
            return False, f"规则 '{name}' 不存在"
        
        old_rule = self._rules[name]
        
        # 验证规则
        valid, error = rule.validate()
        if not valid:
            return False, error
        
        # 保持原来的 source（内置规则不能变成自定义）
        rule.source = old_rule.source
        
        # 内置规则不允许改名
        if old_rule.is_builtin() and name != rule.name:
            return False, f"内置规则 '{name}' 不允许改名"
        
        # 如果名称变更，需要删除旧的
        if name != rule.name:
            del self._rules[name]
        
        self._rules[rule.name] = rule
        return True, f"规则 '{rule.name}' 更新成功"
    
    def delete_rule(self, name: str) -> tuple[bool, str]:
        """
        删除规则（仅自定义规则）
        
        :param name: 规则名称
        :return: (是否成功, 消息)
        """
        if name not in self._rules:
            return False, f"规则 '{name}' 不存在"
        
        rule = self._rules[name]
        if rule.is_builtin():
            return False, f"内置规则 '{name}' 不允许删除"
        
        del self._rules[name]
        return True, f"规则 '{name}' 删除成功"
    
    def enable_rule(self, name: str) -> tuple[bool, str]:
        """启用规则"""
        if name not in self._rules:
            return False, f"规则 '{name}' 不存在"
        self._rules[name].enabled = True
        return True, f"规则 '{name}' 已启用"
    
    def disable_rule(self, name: str) -> tuple[bool, str]:
        """禁用规则"""
        if name not in self._rules:
            return False, f"规则 '{name}' 不存在"
        self._rules[name].enabled = False
        return True, f"规则 '{name}' 已禁用"
    
    def test_rule(self, name: str, text: str) -> List[Dict[str, Any]]:
        """
        测试规则
        
        :param name: 规则名称
        :param text: 测试文本
        :return: 匹配结果列表
        """
        rule = self._rules.get(name)
        if not rule:
            return []
        
        results = []
        for pattern in rule.patterns:
            try:
                regex = re.compile(pattern.regex)
                for match in regex.finditer(text):
                    results.append({
                        "pattern_name": pattern.name,
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "score": pattern.score,
                    })
            except re.error:
                continue
        
        return results
    
    def validate_regex(self, regex: str) -> tuple[bool, str]:
        """
        验证正则表达式
        
        :param regex: 正则表达式
        :return: (是否有效, 错误信息)
        """
        try:
            re.compile(regex)
            return True, "正则表达式有效"
        except re.error as e:
            return False, f"正则表达式无效: {e}"


# 全局规则管理器实例
_rules_manager: Optional[RulesManager] = None


def get_rules_manager(rules_file: Optional[Path] = None, reload: bool = False) -> RulesManager:
    """获取全局规则管理器实例"""
    global _rules_manager
    if _rules_manager is None or reload:
        _rules_manager = RulesManager(rules_file)
    return _rules_manager
