import { useState, useEffect } from 'react';
import { Save, RefreshCw, AlertCircle, CheckCircle, ChevronDown, ChevronUp, Plus, X, Trash2 } from 'lucide-react';

interface RecognizerConfig {
  enabled: boolean;
  base_score: number;
  description?: string;
}

interface Config {
  system: {
    name: string;
    version: string;
    language: string;
    debug: boolean;
    log_level: string;
  };
  nlp_engine: {
    type: string;
    model: string;
    default_score: number;
    entity_mapping: Record<string, string>;
    labels_to_ignore: string[];
  };
  llm_verifier: {
    enabled: boolean;
    mode: string;
    score_threshold: number;
    context_window: number;
    api: {
      base_url: string;
      model: string;
      timeout: number;
    };
    local: {
      model_path: string;
      device: string;
      max_new_tokens: number;
    };
  };
  scoring: {
    high_confidence: number;
    low_confidence: number;
    type_scores: Record<string, number>;
  };
  recognizers: {
    enabled: string[];
    disabled: string[];
    settings: Record<string, RecognizerConfig>;
  };
  context_words: Record<string, string[]>;
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function Section({ title, children, defaultOpen = false }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span className="font-medium text-gray-700">{title}</span>
        {isOpen ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
      </button>
      {isOpen && <div className="p-4 border-t">{children}</div>}
    </div>
  );
}

export function ConfigManager() {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [llmStatus, setLlmStatus] = useState<any>(null);

  // 加载配置
  const loadConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const [configRes, llmRes] = await Promise.all([
        fetch('/api/config'),
        fetch('/api/llm/status'),
      ]);
      
      if (configRes.ok) {
        const data = await configRes.json();
        setConfig(data);
      }
      if (llmRes.ok) {
        const data = await llmRes.json();
        setLlmStatus(data);
      }
    } catch (err: any) {
      setError('加载配置失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  // 更新单个配置项
  const updateConfig = async (key: string, value: any) => {
    try {
      const response = await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value }),
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || '更新失败');
      }
      
      setSuccess(`配置 ${key} 已更新`);
      setTimeout(() => setSuccess(null), 3000);
      
      // 重新加载配置
      await loadConfig();
    } catch (err: any) {
      setError(err.message);
    }
  };

  // 配置 LLM
  const configureLLM = async (mode: string, formData: FormData) => {
    setSaving(true);
    try {
      const response = await fetch(`/api/llm/configure/${mode}`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || '配置失败');
      }
      
      setSuccess('LLM 配置已更新');
      setTimeout(() => setSuccess(null), 3000);
      await loadConfig();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // 重载引擎
  const reloadEngine = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/reload', { method: 'POST' });
      if (!response.ok) throw new Error('重载失败');
      
      setSuccess('引擎已重新加载');
      setTimeout(() => setSuccess(null), 3000);
      await loadConfig();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">加载配置中...</div>;
  }

  if (!config) {
    return <div className="text-center py-8 text-red-500">无法加载配置</div>;
  }

  return (
    <div className="space-y-4">
      {/* 提示信息 */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
          <button onClick={() => setError(null)}><X className="w-4 h-4 text-red-500" /></button>
        </div>
      )}
      
      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <span className="text-green-700">{success}</span>
        </div>
      )}

      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">配置管理</h2>
        <div className="flex gap-2">
          <button
            onClick={loadConfig}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
          <button
            onClick={reloadEngine}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Save className="w-4 h-4" />
            重载引擎
          </button>
        </div>
      </div>

      {/* NLP 引擎配置 */}
      <Section title="🧠 NLP 引擎配置" defaultOpen={true}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">引擎类型</label>
              <select
                value={config.nlp_engine.type}
                onChange={(e) => updateConfig('nlp_engine.type', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="spacy">spaCy</option>
                <option value="stanza">Stanza</option>
                <option value="transformers">Transformers</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
              <input
                type="text"
                value={config.nlp_engine.model}
                onChange={(e) => updateConfig('nlp_engine.model', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="zh_core_web_md"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              默认置信分数: {config.nlp_engine.default_score}
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={config.nlp_engine.default_score * 100}
              onChange={(e) => updateConfig('nlp_engine.default_score', Number(e.target.value) / 100)}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">实体映射</label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(config.nlp_engine.entity_mapping).map(([from, to]) => (
                <div key={from} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                  <span className="text-sm font-mono">{from}</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-sm font-mono text-blue-600">{to}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* LLM 验证器配置 */}
      <Section title="🤖 LLM 验证器配置" defaultOpen={true}>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <span className="font-medium">当前模式:</span>
              <span className={`ml-2 px-2 py-0.5 text-sm rounded ${
                llmStatus?.mode === 'api' ? 'bg-green-100 text-green-700' :
                llmStatus?.mode === 'local' ? 'bg-blue-100 text-blue-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {llmStatus?.mode || config.llm_verifier.mode}
              </span>
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.llm_verifier.enabled}
                onChange={(e) => updateConfig('llm_verifier.enabled', e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">启用验证</span>
            </label>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                触发阈值: {config.llm_verifier.score_threshold}
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={config.llm_verifier.score_threshold * 100}
                onChange={(e) => updateConfig('llm_verifier.score_threshold', Number(e.target.value) / 100)}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">低于此分数的结果将触发 LLM 验证</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                上下文窗口: {config.llm_verifier.context_window} 字符
              </label>
              <input
                type="range"
                min="10"
                max="100"
                value={config.llm_verifier.context_window}
                onChange={(e) => updateConfig('llm_verifier.context_window', Number(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          {/* API 模式配置 */}
          <div className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-700 mb-3">API 模式</h4>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              configureLLM('api', formData);
            }} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input
                  name="api_key"
                  type="password"
                  placeholder="API Key"
                  className="px-3 py-2 border rounded-lg"
                />
                <input
                  name="api_base"
                  type="text"
                  defaultValue={config.llm_verifier.api.base_url}
                  placeholder="API Base URL"
                  className="px-3 py-2 border rounded-lg"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input
                  name="model"
                  type="text"
                  defaultValue={config.llm_verifier.api.model}
                  placeholder="模型名称"
                  className="px-3 py-2 border rounded-lg"
                />
                <input
                  name="timeout"
                  type="number"
                  defaultValue={config.llm_verifier.api.timeout}
                  placeholder="超时(秒)"
                  className="px-3 py-2 border rounded-lg"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                配置 API 模式
              </button>
            </form>
          </div>

          {/* 本地模型配置 */}
          <div className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-700 mb-3">本地模型</h4>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              configureLLM('local', formData);
            }} className="space-y-3">
              <input
                name="model_path"
                type="text"
                defaultValue={config.llm_verifier.local.model_path}
                placeholder="模型路径或 HuggingFace 模型名"
                className="w-full px-3 py-2 border rounded-lg"
              />
              <div className="grid grid-cols-2 gap-3">
                <select name="device" defaultValue={config.llm_verifier.local.device} className="px-3 py-2 border rounded-lg">
                  <option value="auto">自动选择设备</option>
                  <option value="cpu">CPU</option>
                  <option value="cuda">CUDA (GPU)</option>
                  <option value="mps">MPS (Apple Silicon)</option>
                </select>
                <input
                  name="max_new_tokens"
                  type="number"
                  defaultValue={config.llm_verifier.local.max_new_tokens}
                  placeholder="最大生成 Token"
                  className="px-3 py-2 border rounded-lg"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                配置本地模型
              </button>
            </form>
          </div>
        </div>
      </Section>

      {/* 置信度阈值配置 */}
      <Section title="📊 置信度阈值配置">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                高置信度阈值: {config.scoring.high_confidence}
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={config.scoring.high_confidence * 100}
                onChange={(e) => updateConfig('scoring.high_confidence', Number(e.target.value) / 100)}
                className="w-full"
              />
              <p className="text-xs text-gray-500">高于此值直接确认</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                低置信度阈值: {config.scoring.low_confidence}
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={config.scoring.low_confidence * 100}
                onChange={(e) => updateConfig('scoring.low_confidence', Number(e.target.value) / 100)}
                className="w-full"
              />
              <p className="text-xs text-gray-500">低于此值直接丢弃</p>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">类型分数</label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(config.scoring.type_scores).map(([type, score]) => (
                <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm">{type}</span>
                  <input
                    type="number"
                    value={score}
                    min="0"
                    max="1"
                    step="0.1"
                    onChange={(e) => updateConfig(`scoring.type_scores.${type}`, Number(e.target.value))}
                    className="w-20 px-2 py-1 border rounded text-sm"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* 识别器配置 */}
      <Section title="🔍 识别器配置">
        <div className="space-y-4">
          <p className="text-sm text-gray-500">启用/禁用识别器，调整基础分数</p>
          <div className="max-h-[400px] overflow-y-auto space-y-2">
            {Object.entries(config.recognizers.settings).map(([name, settings]) => (
              <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings.enabled}
                    onChange={(e) => updateConfig(`recognizers.settings.${name}.enabled`, e.target.checked)}
                    className="rounded"
                  />
                  <div>
                    <span className="font-mono text-sm">{name}</span>
                    {settings.description && (
                      <span className="text-xs text-gray-500 ml-2">{settings.description}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">分数:</span>
                  <input
                    type="number"
                    value={settings.base_score}
                    min="0"
                    max="1"
                    step="0.05"
                    onChange={(e) => updateConfig(`recognizers.settings.${name}.base_score`, Number(e.target.value))}
                    className="w-16 px-2 py-1 border rounded text-sm"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* 上下文词配置 */}
      <Section title="📝 上下文词配置">
        <div className="space-y-4">
          <p className="text-sm text-gray-500">配置各实体类型的上下文关键词，用于提升识别准确度</p>
          <div className="max-h-[400px] overflow-y-auto space-y-3">
            {Object.entries(config.context_words).map(([entityType, words]) => (
              <div key={entityType} className="border rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm">{entityType}</span>
                  <span className="text-xs text-gray-500">{words.length} 个词</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {words.map((word, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                    >
                      {word}
                      <button
                        onClick={() => {
                          const newWords = words.filter((_, i) => i !== idx);
                          updateConfig(`context_words.${entityType}`, newWords);
                        }}
                        className="hover:text-red-500"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  <button
                    onClick={() => {
                      const newWord = prompt('输入新的上下文词:');
                      if (newWord?.trim()) {
                        updateConfig(`context_words.${entityType}`, [...words, newWord.trim()]);
                      }
                    }}
                    className="inline-flex items-center gap-1 px-2 py-0.5 border border-dashed border-gray-300 text-gray-500 text-xs rounded hover:border-blue-500 hover:text-blue-500"
                  >
                    <Plus className="w-3 h-3" />
                    添加
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Section>
    </div>
  );
}
