import { useState, useEffect, useCallback } from 'react';
import { Plus, Edit2, Trash2, Play, Save, X, AlertCircle } from 'lucide-react';

interface Pattern {
  regex: string;
  name: string;
  score: number;
}

interface Rule {
  name: string;
  entity_type: string;
  description?: string;
  category?: string;
  source: 'builtin' | 'custom';
  patterns: Pattern[];
  context: string[];
  enabled: boolean;
}

interface RuleTestState {
  text: string;
  results: any[];
  loading: boolean;
  expanded: boolean;
}

export function RulesManager() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [isNew, setIsNew] = useState(false);
  // 每个规则独立的测试状态
  const [testStates, setTestStates] = useState<Record<string, RuleTestState>>({});

  // 加载自定义规则
  const loadRules = useCallback(async () => {
    try {
      const response = await fetch('/api/rules?source=custom');
      if (!response.ok) throw new Error('加载规则失败');
      const data = await response.json();
      setRules(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  // 保存规则
  const saveRule = async () => {
    if (!editingRule) return;

    try {
      const url = isNew ? '/api/rules' : `/api/rules/${editingRule.name}`;
      const method = isNew ? 'POST' : 'PUT';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingRule),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || '保存失败');
      }

      await loadRules();
      setEditingRule(null);
      setIsNew(false);
    } catch (err: any) {
      setError(err.message);
    }
  };

  // 删除规则
  const deleteRule = async (name: string) => {
    if (!confirm(`确定要删除规则 "${name}" 吗？`)) return;

    try {
      const response = await fetch(`/api/rules/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || '删除失败');
      }

      await loadRules();
    } catch (err: any) {
      setError(err.message);
    }
  };

  // 切换规则启用状态
  const toggleRuleEnabled = async (rule: Rule) => {
    try {
      const updatedRule = { ...rule, enabled: !rule.enabled };
      
      const response = await fetch(`/api/rules/${encodeURIComponent(rule.name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedRule),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || '更新失败');
      }

      await loadRules();
    } catch (err: any) {
      setError(err.message);
    }
  };

  // 获取规则的测试状态
  const getTestState = (name: string): RuleTestState => {
    return testStates[name] || { text: '', results: [], loading: false, expanded: false };
  };

  // 更新规则的测试状态
  const updateTestState = (name: string, updates: Partial<RuleTestState>) => {
    setTestStates(prev => ({
      ...prev,
      [name]: { ...getTestState(name), ...updates }
    }));
  };

  // 切换测试面板展开状态
  const toggleTestPanel = (name: string) => {
    updateTestState(name, { expanded: !getTestState(name).expanded });
  };

  // 测试规则
  const testRule = async (name: string) => {
    const state = getTestState(name);
    if (!state.text.trim()) {
      setError('请输入测试文本');
      return;
    }

    updateTestState(name, { loading: true });
    try {
      const formData = new FormData();
      formData.append('text', state.text);

      const response = await fetch(`/api/rules/${encodeURIComponent(name)}/test`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('测试失败');

      const data = await response.json();
      updateTestState(name, { results: data.results, loading: false });
    } catch (err: any) {
      setError(err.message);
      updateTestState(name, { loading: false });
    }
  };

  // 新建规则
  const createNewRule = () => {
    setEditingRule({
      name: '',
      entity_type: '',
      description: '',
      category: '其他',
      source: 'custom',
      patterns: [{ regex: '', name: '', score: 0.5 }],
      context: [],
      enabled: true,
    });
    setIsNew(true);
  };

  // 添加正则模式
  const addPattern = () => {
    if (!editingRule) return;
    setEditingRule({
      ...editingRule,
      patterns: [...editingRule.patterns, { regex: '', name: '', score: 0.5 }],
    });
  };

  // 删除正则模式
  const removePattern = (index: number) => {
    if (!editingRule) return;
    setEditingRule({
      ...editingRule,
      patterns: editingRule.patterns.filter((_, i) => i !== index),
    });
  };

  // 更新正则模式
  const updatePattern = (index: number, field: keyof Pattern, value: string | number) => {
    if (!editingRule) return;
    const newPatterns = [...editingRule.patterns];
    newPatterns[index] = { ...newPatterns[index], [field]: value };
    setEditingRule({ ...editingRule, patterns: newPatterns });
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">加载中...</div>;
  }

  return (
    <div className="space-y-4">
      {/* 错误提示 */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 标题栏 */}
      <div className="flex items-center justify-between border-b pb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">自定义规则</h2>
          <p className="text-sm text-gray-500">添加自定义正则规则来识别特定的敏感信息</p>
        </div>
        <button
          onClick={(e) => {
            e.preventDefault();
            createNewRule();
          }}
          type="button"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          新建规则
        </button>
      </div>

      {/* 规则列表 */}
      <div className="space-y-3">
        {rules.map((rule: Rule) => (
          <div
            key={rule.name}
            className={`bg-white rounded-xl shadow-sm border p-4 ${!rule.enabled ? 'opacity-60' : ''}`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleRuleEnabled(rule);
                  }}
                  type="button"
                  className="group relative"
                  title={rule.enabled ? '点击禁用' : '点击启用'}
                >
                  <span className={`block w-10 h-6 rounded-full transition-colors cursor-pointer ${
                    rule.enabled ? 'bg-green-500' : 'bg-gray-300'
                  }`}>
                    <span className={`block w-4 h-4 bg-white rounded-full shadow-sm transition-transform transform ${
                      rule.enabled ? 'translate-x-5' : 'translate-x-1'
                    } mt-1`} />
                  </span>
                </button>
                <h3 className="font-medium text-gray-800">{rule.description || rule.name}</h3>
                <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded font-mono">
                  {rule.entity_type}
                </span>
                {rule.category && (
                  <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                    {rule.category}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleTestPanel(rule.name);
                  }}
                  className={`p-2 rounded-lg transition-colors ${
                    getTestState(rule.name).expanded 
                      ? 'text-blue-600 bg-blue-50' 
                      : 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
                  }`}
                  title="测试规则"
                  type="button"
                >
                  <Play className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingRule(rule);
                    setIsNew(false);
                  }}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="编辑"
                  type="button"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteRule(rule.name);
                  }}
                  className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="删除"
                  type="button"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            {/* 规则信息 */}
            <div className="text-sm text-gray-600 mb-3">
              <p className="mb-1">
                <span className="text-gray-400">正则模式:</span> {rule.patterns.length} 个
              </p>
              <p>
                <span className="text-gray-400">上下文词:</span> {rule.context.length > 0 ? rule.context.slice(0, 8).join(', ') + (rule.context.length > 8 ? '...' : '') : '无'}
              </p>
            </div>

            {/* 内嵌测试面板 */}
            {getTestState(rule.name).expanded && (
              <div className="border-t pt-3 mt-3">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={getTestState(rule.name).text}
                    onChange={(e) => updateTestState(rule.name, { text: e.target.value })}
                    placeholder="输入测试文本..."
                    className="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        testRule(rule.name);
                      }
                    }}
                  />
                  <button
                    onClick={() => testRule(rule.name)}
                    disabled={getTestState(rule.name).loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2"
                  >
                    {getTestState(rule.name).loading ? (
                      <span className="animate-spin">⏳</span>
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    检测
                  </button>
                </div>
                
                {/* 测试结果 */}
                {getTestState(rule.name).results.length > 0 && (
                  <div className="mt-3 p-3 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-700 mb-2">✅ 匹配结果:</p>
                    <div className="space-y-1">
                      {getTestState(rule.name).results.map((result: any, i: number) => (
                        <div key={i} className="text-sm text-green-600">
                          <span className="font-mono bg-green-100 px-1 rounded">{result.text}</span>
                          <span className="text-gray-500 ml-2">
                            (位置: {result.start}-{result.end}, 分数: {(result.score * 100).toFixed(0)}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {getTestState(rule.name).text && getTestState(rule.name).results.length === 0 && !getTestState(rule.name).loading && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-500">
                    未匹配到任何内容
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {rules.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            暂无自定义规则，点击“新建规则”添加
          </div>
        )}
      </div>

      {/* 编辑弹窗 */}
      {editingRule && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold">
                  {isNew ? '新建规则' : '编辑规则'}
                </h3>
                <button
                  onClick={() => { setEditingRule(null); setIsNew(false); }}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* 基本信息 */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">规则名称</label>
                    <input
                      type="text"
                      value={editingRule.name}
                      onChange={(e) => setEditingRule({ ...editingRule, name: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      placeholder="如：内部工号"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">实体类型</label>
                    <input
                      type="text"
                      value={editingRule.entity_type}
                      onChange={(e) => setEditingRule({ ...editingRule, entity_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      placeholder="如：EMPLOYEE_ID"
                    />
                  </div>
                </div>

                {/* 正则模式 */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">正则模式</label>
                    <button
                      onClick={addPattern}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      + 添加模式
                    </button>
                  </div>
                  <div className="space-y-3">
                    {editingRule.patterns.map((pattern, index) => (
                      <div key={index} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-start gap-3">
                          <div className="flex-1 space-y-2">
                            <input
                              type="text"
                              value={pattern.name}
                              onChange={(e) => updatePattern(index, 'name', e.target.value)}
                              className="w-full px-3 py-2 border rounded-lg text-sm"
                              placeholder="模式名称"
                            />
                            <input
                              type="text"
                              value={pattern.regex}
                              onChange={(e) => updatePattern(index, 'regex', e.target.value)}
                              className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                              placeholder="正则表达式"
                            />
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">分数:</span>
                              <input
                                type="number"
                                value={pattern.score}
                                onChange={(e) => updatePattern(index, 'score', parseFloat(e.target.value))}
                                className="w-20 px-2 py-1 border rounded text-sm"
                                min="0"
                                max="1"
                                step="0.1"
                              />
                            </div>
                          </div>
                          {editingRule.patterns.length > 1 && (
                            <button
                              onClick={() => removePattern(index)}
                              className="p-1 text-red-500 hover:bg-red-50 rounded"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 上下文词 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    上下文词（逗号分隔）
                  </label>
                  <input
                    type="text"
                    value={editingRule.context.join(', ')}
                    onChange={(e) => setEditingRule({
                      ...editingRule,
                      context: e.target.value.split(',').map(s => s.trim()).filter(Boolean),
                    })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="如：工号, 员工编号"
                  />
                </div>

                {/* 启用状态 */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingRule.enabled}
                    onChange={(e) => setEditingRule({ ...editingRule, enabled: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600"
                  />
                  <span className="text-sm text-gray-700">启用此规则</span>
                </label>
              </div>

              {/* 操作按钮 */}
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                <button
                  onClick={() => { setEditingRule(null); setIsNew(false); }}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={saveRule}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Save className="w-4 h-4" />
                  保存
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
