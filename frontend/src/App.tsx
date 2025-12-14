import { useState, useEffect, useCallback } from 'react';
import { Shield, Search, AlertCircle, CheckCircle, Loader2, Settings, Upload, Activity, Wrench, History, Sliders, Copy, Download } from 'lucide-react';
import { analyzeText, getEntities, healthCheck, getHistory, addHistory, deleteHistory, clearHistory, anonymizeText, anonymizeFile } from './api';
import type { EntityResult, EntityTypeInfo, HealthResponse, HistoryItem } from './api';
import { FileUpload } from './components/FileUpload';
import { RulesManager } from './components/RulesManager';
import { Metrics } from './components/Metrics';
import { HistoryPanel } from './components/HistoryPanel';
import { ConfigManager } from './components/ConfigManager';
import { ToastContainer, type ToastType } from './components/Toast';

// 实体类型颜色映射
const entityColors: Record<string, string> = {
  CN_ID_CARD: 'bg-red-100 text-red-800 border-red-300',
  CN_PHONE: 'bg-blue-100 text-blue-800 border-blue-300',
  CN_BANK_CARD: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  CN_EMAIL: 'bg-green-100 text-green-800 border-green-300',
  CN_IP_ADDRESS: 'bg-purple-100 text-purple-800 border-purple-300',
  CN_POSTAL_CODE: 'bg-gray-100 text-gray-800 border-gray-300',
  CN_VEHICLE_PLATE: 'bg-orange-100 text-orange-800 border-orange-300',
  CN_PASSPORT: 'bg-pink-100 text-pink-800 border-pink-300',
  PERSON: 'bg-indigo-100 text-indigo-800 border-indigo-300',
  LOCATION: 'bg-teal-100 text-teal-800 border-teal-300',
  ORGANIZATION: 'bg-cyan-100 text-cyan-800 border-cyan-300',
  CN_JWT: 'bg-amber-100 text-amber-800 border-amber-300',
  CN_CLOUD_KEY: 'bg-rose-100 text-rose-800 border-rose-300',
  default: 'bg-slate-100 text-slate-800 border-slate-300',
};

const getEntityColor = (type: string) => entityColors[type] || entityColors.default;

type TabType = 'analyze' | 'anonymize' | 'history' | 'rules' | 'config' | 'metrics';
type AnalyzeMode = 'text' | 'file';
type AnonymizeMode = 'text' | 'file';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('analyze');
  const [text, setText] = useState('');
  const [results, setResults] = useState<EntityResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [entities, setEntities] = useState<EntityTypeInfo[]>([]);
  const [selectedEntities, setSelectedEntities] = useState<string[]>([]);
  const [scoreThreshold, setScoreThreshold] = useState(0);
  const [useLlmVerify, setUseLlmVerify] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [maskSensitive] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [anonymizeFileObj, setAnonymizeFileObj] = useState<File | null>(null);
  const [anonymizeLoading, setAnonymizeLoading] = useState(false);
  const [analyzeMode, setAnalyzeMode] = useState<AnalyzeMode>('text');
  const [anonymizeMode, setAnonymizeMode] = useState<AnonymizeMode>('text');
  const [anonymizeTextInput, setAnonymizeTextInput] = useState('');
  const [anonymizeTextOutput, setAnonymizeTextOutput] = useState('');
  const [toasts, setToasts] = useState<Array<{ id: string; message: string; type: ToastType }>>([]);

  // Toast 通知函数
  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // 加载历史记录
  const loadHistoryData = useCallback(async () => {
    try {
      const data = await getHistory();
      setHistory(data);
    } catch (err) {
      console.error('加载历史记录失败:', err);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      try {
        const [healthData, entitiesData] = await Promise.all([
          healthCheck(),
          getEntities(),
        ]);
        setHealth(healthData);
        setEntities(entitiesData);
        // 默认全选所有实体类型
        setSelectedEntities(entitiesData.map((e: EntityTypeInfo) => e.name));
        // 加载历史记录
        loadHistoryData();
      } catch (err) {
        showToast('无法连接到后端服务，请确保后端已启动', 'error');
      }
    };
    init();
  }, [loadHistoryData, showToast]);

  const addToHistoryDB = useCallback(async (text: string, results: EntityResult[], type: 'text' | 'file' = 'text', filename?: string, operationType: 'analyze' | 'anonymize' = 'analyze') => {
    try {
      console.log('保存历史记录:', { type, operationType, filename, resultsCount: results.length });
      await addHistory(text, results, type, filename, operationType);
      // 重新加载历史记录
      loadHistoryData();
    } catch (err) {
      console.error('保存历史记录失败:', err);
    }
  }, [loadHistoryData]);

  const handleAnalyze = useCallback(async () => {
    if (!text.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await analyzeText(
        text,
        selectedEntities.length > 0 ? selectedEntities : undefined,
        scoreThreshold,
        useLlmVerify
      );
      setResults(response.results);
      addToHistoryDB(text, response.results, 'text');
      showToast(`识别完成，发现 ${response.results.length} 个敏感信息`, 'success');
    } catch (err: any) {
      showToast(err.response?.data?.detail || '分析失败，请重试', 'error');
    } finally {
      setLoading(false);
    }
  }, [text, selectedEntities, scoreThreshold, useLlmVerify, addToHistoryDB, showToast]);

  const handleSelectHistory = useCallback((item: HistoryItem) => {
    setText(item.text);
    setResults(item.results);
    setActiveTab('analyze');
  }, []);

  const handleDeleteHistory = useCallback(async (id: string) => {
    try {
      await deleteHistory(id);
      setHistory(prev => prev.filter(item => item.id !== id));
      showToast('删除成功', 'success');
    } catch (err) {
      showToast('删除失败，请重试', 'error');
    }
  }, [showToast]);

  const handleClearHistory = useCallback(async () => {
    if (confirm('确定要清空所有历史记录吗？')) {
      try {
        await clearHistory();
        setHistory([]);
        showToast('历史记录已清空', 'success');
      } catch (err) {
        showToast('清空失败，请重试', 'error');
      }
    }
  }, [showToast]);

  const handleBatchDelete = useCallback(async (ids: string[]) => {
    try {
      await Promise.all(ids.map(id => deleteHistory(id)));
      setHistory(prev => prev.filter(item => !ids.includes(item.id)));
      showToast(`成功删除 ${ids.length} 条记录`, 'success');
    } catch (err) {
      showToast('批量删除失败，请重试', 'error');
    }
  }, [showToast]);

  const groupedEntities = entities.reduce((acc, entity) => {
    if (!acc[entity.category]) acc[entity.category] = [];
    acc[entity.category].push(entity);
    return acc;
  }, {} as Record<string, EntityTypeInfo[]>);

  const tabs = [
    { id: 'analyze' as TabType, label: '识别', icon: Search },
    { id: 'anonymize' as TabType, label: '自动脱敏', icon: Upload },
    { id: 'history' as TabType, label: `历史记录${history.length > 0 ? ` (${history.length})` : ''}`, icon: History },
    { id: 'rules' as TabType, label: '规则管理', icon: Wrench },
    { id: 'config' as TabType, label: '配置管理', icon: Sliders },
    { id: 'metrics' as TabType, label: '性能监控', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">MingJing 明镜</h1>
              <p className="text-sm text-gray-500">中文敏感信息识别系统</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {health && (
              <div className="flex items-center gap-2 text-sm">
                <span className={`w-2 h-2 rounded-full ${health.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-gray-600">
                  {health.recognizers_count} 种识别器
                  {health.nlp_loaded && ' · NLP已加载'}
                </span>
              </div>
            )}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors lg:hidden"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 border-b overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {activeTab === 'analyze' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setAnalyzeMode('text')}
                className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                  analyzeMode === 'text'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                文本识别
              </button>
              <button
                type="button"
                onClick={() => setAnalyzeMode('file')}
                className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                  analyzeMode === 'file'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                文件识别
              </button>
            </div>

            {analyzeMode === 'text' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                  <div className="bg-white rounded-xl shadow-sm border p-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">输入待检测文本</label>
                    <textarea
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      placeholder="请输入需要检测敏感信息的文本..."
                      className="w-full h-48 p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    />
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-sm text-gray-500">{text.length} 字符</span>
                      <button
                        onClick={handleAnalyze}
                        disabled={loading || !text.trim()}
                        className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        {loading ? '分析中...' : '开始分析'}
                      </button>
                    </div>
                  </div>

                  {results.length > 0 && (
                    <div className="bg-white rounded-xl shadow-sm border p-4">
                      <h2 className="text-sm font-medium text-gray-700 mb-3">识别到 {results.length} 个敏感信息</h2>
                      <div className="space-y-2">
                        {results.map((result, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <span className={`px-2 py-1 text-xs font-medium rounded ${getEntityColor(result.entity_type)}`}>{result.entity_type}</span>
                              <span className="font-mono text-sm">{maskSensitive ? '●'.repeat(result.text.length) : result.text}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {result.verified && <span className="text-xs text-green-600 flex items-center gap-1"><CheckCircle className="w-3 h-3" />LLM验证</span>}
                              <span className="text-sm text-gray-500">{(result.score * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className={`space-y-4 ${showSettings ? '' : 'hidden lg:block'}`}>
                  <div className="bg-white rounded-xl shadow-sm border p-4">
                    <h2 className="text-sm font-medium text-gray-700 mb-3">识别类型</h2>
                    <div className="space-y-4 max-h-[400px] overflow-y-auto">
                      {Object.entries(groupedEntities).map(([category, items]) => (
                        <div key={category}>
                          <h3 className="text-xs font-medium text-gray-500 mb-2">{category}</h3>
                          <div className="space-y-1">
                            {items.map((entity) => (
                              <label key={entity.name} className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedEntities.includes(entity.name)}
                                  onChange={(e) => {
                                    if (e.target.checked) setSelectedEntities([...selectedEntities, entity.name]);
                                    else setSelectedEntities(selectedEntities.filter(x => x !== entity.name));
                                  }}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-700">{entity.description}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                    {selectedEntities.length > 0 && (
                      <button onClick={() => setSelectedEntities([])} className="mt-3 text-sm text-blue-600 hover:text-blue-700">
                        清除选择（识别所有类型）
                      </button>
                    )}
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border p-4">
                    <h2 className="text-sm font-medium text-gray-700 mb-3">高级设置</h2>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">置信度阈值: {(scoreThreshold * 100).toFixed(0)}%</label>
                        <input type="range" min="0" max="100" value={scoreThreshold * 100} onChange={(e) => setScoreThreshold(Number(e.target.value) / 100)} className="w-full" />
                      </div>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={useLlmVerify} onChange={(e) => setUseLlmVerify(e.target.checked)} className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                        <span className="text-sm text-gray-700">启用 LLM 二次验证</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {analyzeMode === 'file' && (
              <div className="mt-2">
                <FileUpload onResults={(result) => {
                  if (result.results && result.results.length > 0) {
                    const textPreview = result.results.map(r => r.text).join(', ');
                    addToHistoryDB(textPreview, result.results, 'file', result.filename);
                  }
                }} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'anonymize' && (
          <div className="max-w-5xl mx-auto space-y-4">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setAnonymizeMode('text')}
                className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                  anonymizeMode === 'text'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                文本脱敏
              </button>
              <button
                type="button"
                onClick={() => setAnonymizeMode('file')}
                className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                  anonymizeMode === 'file'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                文件脱敏
              </button>
            </div>

            {anonymizeMode === 'text' && (
              <div className="bg-white rounded-xl shadow-sm border p-4">
                <h2 className="text-sm font-medium text-gray-700 mb-3">文本脱敏</h2>
                <p className="text-sm text-gray-500 mb-3">
                  输入文本后，将根据当前选择的识别类型和置信度阈值对内容进行脱敏，并在右侧显示脱敏后的文本。
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">原始文本</label>
                    <textarea
                      value={anonymizeTextInput}
                      onChange={(e) => setAnonymizeTextInput(e.target.value)}
                      placeholder="请输入需要脱敏的文本..."
                      className="w-full h-64 p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    />
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-sm text-gray-500">{anonymizeTextInput.length} 字符</span>
                      <button
                        type="button"
                        disabled={!anonymizeTextInput.trim() || anonymizeLoading}
                        onClick={async () => {
                          try {
                            setAnonymizeLoading(true);
                            setError(null);
                            const result = await anonymizeText(
                              anonymizeTextInput,
                              selectedEntities.length > 0 ? selectedEntities : undefined,
                              scoreThreshold
                            );
                            setAnonymizeTextOutput(result.anonymized);
                            // 记录到历史（使用脱敏后的文本）
                            if (result.results.length > 0) {
                              await addToHistoryDB(result.anonymized, result.results, 'text', undefined, 'anonymize');
                              showToast(`脱敏完成，处理了 ${result.results.length} 个敏感信息`, 'success');
                            } else {
                              showToast('未检测到敏感信息', 'info');
                            }
                          } catch (e: any) {
                            showToast(e?.response?.data?.detail || '脱敏失败，请重试', 'error');
                          } finally {
                            setAnonymizeLoading(false);
                          }
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                      >
                        {anonymizeLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                        {anonymizeLoading ? '脱敏中...' : '开始脱敏'}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">脱敏后文本</label>
                    <textarea
                      value={anonymizeTextOutput}
                      readOnly
                      placeholder="脱敏结果将显示在这里..."
                      className="w-full h-64 p-3 border rounded-lg resize-none bg-gray-50 outline-none"
                    />
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-sm text-gray-500">{anonymizeTextOutput.length} 字符</span>
                      <button
                        type="button"
                        disabled={!anonymizeTextOutput}
                        onClick={() => {
                          navigator.clipboard.writeText(anonymizeTextOutput);
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                      >
                        <Copy className="w-4 h-4" />
                        复制结果
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {anonymizeMode === 'file' && (
              <div className="bg-white rounded-xl shadow-sm border p-4">
                <h2 className="text-sm font-medium text-gray-700 mb-3">文件脱敏</h2>
                <p className="text-sm text-gray-500 mb-3">
                  上传文件后，将根据当前选择的识别类型和置信度阈值对文件内容进行脱敏，并返回脱敏后的文件供下载。
                </p>
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      id="anonymize-file-input"
                      type="file"
                      accept=".txt,.log,.md,.csv,.tsv,.json,.jsonl,.docx,.xlsx,.xls,.zip"
                      onChange={(e) => {
                        const file = e.target.files?.[0] || null;
                        console.log('File selected:', file?.name);
                        setAnonymizeFileObj(file);
                      }}
                      className="hidden"
                    />
                    <label
                      htmlFor="anonymize-file-input"
                      className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700"
                    >
                      <Upload className="w-4 h-4" />
                      选择文件
                    </label>
                    <p className="mt-2 text-xs text-gray-500">
                      支持: TXT, CSV, JSON, DOCX, XLSX, ZIP
                    </p>
                  </div>

                  {anonymizeFileObj && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-900">
                            {anonymizeFileObj.name}
                          </span>
                          <span className="text-xs text-blue-600">
                            ({(anonymizeFileObj.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setAnonymizeFileObj(null)}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          重新选择
                        </button>
                      </div>
                    </div>
                  )}

                  <button
                    type="button"
                    disabled={!anonymizeFileObj || anonymizeLoading}
                    onClick={async () => {
                      if (!anonymizeFileObj) return;
                      try {
                        setAnonymizeLoading(true);
                        setError(null);
                        const blob = await anonymizeFile(
                          anonymizeFileObj,
                          selectedEntities.length > 0 ? selectedEntities : undefined,
                          scoreThreshold,
                        );
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = anonymizeFileObj.name;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                        // 记录到历史（文件脱敏成功）
                        await addToHistoryDB(
                          `文件脱敏: ${anonymizeFileObj.name}`,
                          [],
                          'file',
                          anonymizeFileObj.name,
                          'anonymize'
                        );
                        showToast(`文件脱敏成功: ${anonymizeFileObj.name}`, 'success');
                      } catch (e: any) {
                        showToast(e?.response?.data?.detail || '脱敏失败，请重试', 'error');
                      } finally {
                        setAnonymizeLoading(false);
                      }
                    }}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    {anonymizeLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    {anonymizeLoading ? '脱敏中...' : '开始脱敏并下载'}
                  </button>
                </div>

                <div className="mt-4 bg-gray-50 rounded-lg p-3">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">说明</h3>
                  <ul className="text-xs text-gray-500 space-y-1 list-disc pl-5">
                    <li>当前使用识别页配置的识别类型和置信度阈值。</li>
                    <li>支持 TXT/CSV/JSON 将以原格式返回；DOCX/XLSX 尽量保留原始排版；ZIP 将在压缩包内对支持的文件递归脱敏。</li>
                    <li>脱敏字符使用黑圆点 ●，长度与原内容一致，方便对比。</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <HistoryPanel 
              history={history} 
              onClear={handleClearHistory} 
              onSelect={handleSelectHistory} 
              onDelete={handleDeleteHistory}
              onBatchDelete={handleBatchDelete}
            />
          </div>
        )}

        {activeTab === 'rules' && <RulesManager />}

        {activeTab === 'config' && <ConfigManager />}

        {activeTab === 'metrics' && <Metrics />}
      </main>

      {/* Toast 通知容器 */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}

export default App;
