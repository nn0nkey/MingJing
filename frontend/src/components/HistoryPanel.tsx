import { useState, useMemo, useEffect } from 'react';
import { Clock, Trash2, ChevronDown, ChevronUp, Copy, Check, Search, Filter, Download, BarChart3, CheckSquare, Square } from 'lucide-react';
import type { HistoryItem } from '../api';

interface HistoryPanelProps {
  history: HistoryItem[];
  onClear: () => void;
  onSelect: (item: HistoryItem) => void;
  onDelete: (id: string) => void;
  onBatchDelete?: (ids: string[]) => void;
}

export function HistoryPanel({ history, onClear, onSelect, onDelete, onBatchDelete }: HistoryPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'text' | 'file'>('all');
  const [operationFilter, setOperationFilter] = useState<'all' | 'analyze' | 'anonymize'>('all');
  const [dateFilter, setDateFilter] = useState<'all' | 'today' | 'week' | 'month' | 'custom'>('all');
  const [showStats, setShowStats] = useState(false);
  const [showAdvancedFilter, setShowAdvancedFilter] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<string[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchMode, setBatchMode] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // 防抖搜索：300ms 延迟
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const parseTimestamp = (timestamp: string): Date => {
    return new Date(timestamp);
  };

  const formatTime = (timestamp: string) => {
    const date = parseTimestamp(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (timestamp: string) => {
    const date = parseTimestamp(timestamp);
    const today = new Date();
    const isToday = date.toDateString() === today.toDateString();
    if (isToday) return '今天';
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) return '昨天';
    
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // 获取所有实体类型
  const allEntityTypes = useMemo(() => {
    const types = new Set<string>();
    history.forEach(item => {
      item.results.forEach(r => types.add(r.entity_type));
    });
    return Array.from(types).sort();
  }, [history]);

  // 筛选和搜索逻辑
  const filteredHistory = useMemo(() => {
    let filtered = history;

    // 类型筛选
    if (filterType !== 'all') {
      filtered = filtered.filter(item => item.type === filterType);
    }

    // 操作类型筛选
    if (operationFilter !== 'all') {
      filtered = filtered.filter(item => (item.operation_type || 'analyze') === operationFilter);
    }

    // 日期筛选
    if (dateFilter === 'custom') {
      // 自定义日期范围
      if (startDate || endDate) {
        filtered = filtered.filter(item => {
          const itemDate = parseTimestamp(item.timestamp);
          const start = startDate ? new Date(startDate) : new Date('1970-01-01');
          const end = endDate ? new Date(endDate) : new Date('2099-12-31');
          end.setHours(23, 59, 59, 999); // 包含结束日当天
          return itemDate >= start && itemDate <= end;
        });
      }
    } else if (dateFilter !== 'all') {
      const now = new Date();
      filtered = filtered.filter(item => {
        const itemDate = parseTimestamp(item.timestamp);
        const diffDays = Math.floor((now.getTime() - itemDate.getTime()) / (1000 * 60 * 60 * 24));
        
        if (dateFilter === 'today') return diffDays === 0;
        if (dateFilter === 'week') return diffDays <= 7;
        if (dateFilter === 'month') return diffDays <= 30;
        return true;
      });
    }

    // 搜索筛选（支持 ID 搜索）——使用防抖后的搜索词
    if (debouncedSearchQuery.trim()) {
      const query = debouncedSearchQuery.toLowerCase();
      filtered = filtered.filter(item => 
        item.id.toLowerCase().includes(query) ||
        item.text.toLowerCase().includes(query) ||
        item.filename?.toLowerCase().includes(query) ||
        item.results.some(r => r.entity_type.toLowerCase().includes(query) || r.text.toLowerCase().includes(query))
      );
    }

    // 实体类型筛选
    if (selectedEntityTypes.length > 0) {
      filtered = filtered.filter(item => 
        item.results.some(r => selectedEntityTypes.includes(r.entity_type))
      );
    }

    // 置信度筛选
    if (minScore > 0) {
      filtered = filtered.filter(item => 
        item.results.some(r => r.score >= minScore / 100)
      );
    }

    return filtered;
  }, [history, filterType, operationFilter, dateFilter, debouncedSearchQuery, startDate, endDate, selectedEntityTypes, minScore]);

  // 统计数据
  const stats = useMemo(() => {
    const entityTypeCount: Record<string, number> = {};
    let totalEntities = 0;

    filteredHistory.forEach(item => {
      item.results.forEach(result => {
        entityTypeCount[result.entity_type] = (entityTypeCount[result.entity_type] || 0) + 1;
        totalEntities++;
      });
    });

    const sortedTypes = Object.entries(entityTypeCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    return {
      totalRecords: filteredHistory.length,
      totalEntities,
      entityTypes: sortedTypes,
      textRecords: filteredHistory.filter(i => i.type === 'text').length,
      fileRecords: filteredHistory.filter(i => i.type === 'file').length,
      analyzeRecords: filteredHistory.filter(i => (i.operation_type || 'analyze') === 'analyze').length,
      anonymizeRecords: filteredHistory.filter(i => (i.operation_type || 'analyze') === 'anonymize').length,
    };
  }, [filteredHistory]);

  // 分页数据
  const paginatedHistory = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredHistory.slice(startIndex, endIndex);
  }, [filteredHistory, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage);

  // 当筛选条件变化时，重置到第一页
  useEffect(() => {
    setCurrentPage(1);
  }, [filterType, operationFilter, dateFilter, debouncedSearchQuery, startDate, endDate, selectedEntityTypes, minScore]);

  // 导出为 JSON
  const exportJSON = () => {
    const data = JSON.stringify(filteredHistory, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `history_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 导出为 CSV
  const exportCSV = () => {
    const headers = ['时间', '类型', '文件名', '文本内容', '敏感信息数量', '敏感信息详情'];
    const rows = filteredHistory.map(item => [
      item.timestamp,
      item.type,
      item.filename || '',
      item.text.replace(/[\n\r]/g, ' '),
      item.results.length,
      item.results.map(r => `${r.entity_type}:${r.text}`).join('; ')
    ]);
    
    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `history_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 按日期分组（使用分页后的数据）
  const groupedHistory = paginatedHistory.reduce((acc, item) => {
    const dateKey = formatDate(item.timestamp);
    if (!acc[dateKey]) acc[dateKey] = [];
    acc[dateKey].push(item);
    return acc;
  }, {} as Record<string, HistoryItem[]>);

  if (history.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>暂无历史记录</p>
        <p className="text-sm mt-1">分析结果将自动保存在这里</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          历史记录 ({filteredHistory.length}/{history.length})
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowStats(!showStats)}
            className="text-sm text-blue-500 hover:text-blue-600 flex items-center gap-1"
          >
            <BarChart3 className="w-3 h-3" />
            统计
          </button>
          <div className="relative group">
            <button className="text-sm text-green-500 hover:text-green-600 flex items-center gap-1">
              <Download className="w-3 h-3" />
              导出
            </button>
            <div className="absolute right-0 mt-1 w-32 bg-white border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={exportJSON}
                className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
              >
                导出 JSON
              </button>
              <button
                onClick={exportCSV}
                className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
              >
                导出 CSV
              </button>
            </div>
          </div>
          <button
            onClick={() => {
              setBatchMode(!batchMode);
              setSelectedIds(new Set());
            }}
            className={`text-sm flex items-center gap-1 ${
              batchMode ? 'text-blue-600' : 'text-gray-600 hover:text-gray-700'
            }`}
          >
            {batchMode ? <CheckSquare className="w-3 h-3" /> : <Square className="w-3 h-3" />}
            批量选择
          </button>
          {batchMode && selectedIds.size > 0 && (
            <button
              onClick={() => {
                if (onBatchDelete && confirm(`确定要删除选中的 ${selectedIds.size} 条记录吗？`)) {
                  onBatchDelete(Array.from(selectedIds));
                  setSelectedIds(new Set());
                  setBatchMode(false);
                }
              }}
              className="text-sm text-red-500 hover:text-red-600 flex items-center gap-1"
            >
              <Trash2 className="w-3 h-3" />
              删除选中 ({selectedIds.size})
            </button>
          )}
          <button
            onClick={onClear}
            className="text-sm text-red-500 hover:text-red-600 flex items-center gap-1"
          >
            <Trash2 className="w-3 h-3" />
            清空全部
          </button>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <div className="space-y-2">
        {/* 搜索框 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索文本、文件名或实体类型..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
        </div>

        {/* 筛选按钮 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <div className="flex gap-2">
              <button
                onClick={() => setFilterType('all')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  filterType === 'all'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                全部
              </button>
              <button
                onClick={() => setFilterType('text')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  filterType === 'text'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                文本
              </button>
              <button
                onClick={() => setFilterType('file')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  filterType === 'file'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                文件
              </button>
            </div>
            <div className="h-4 w-px bg-gray-300 mx-1" />
            <div className="flex gap-2">
              <button
                onClick={() => setOperationFilter('all')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  operationFilter === 'all'
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                全部操作
              </button>
              <button
                onClick={() => setOperationFilter('analyze')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  operationFilter === 'analyze'
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                识别
              </button>
              <button
                onClick={() => setOperationFilter('anonymize')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  operationFilter === 'anonymize'
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                脱敏
              </button>
            </div>
            <div className="h-4 w-px bg-gray-300 mx-1" />
            <div className="flex gap-2">
              <button
                onClick={() => setDateFilter('all')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  dateFilter === 'all'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                全部时间
              </button>
              <button
                onClick={() => setDateFilter('today')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  dateFilter === 'today'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                今天
              </button>
              <button
                onClick={() => setDateFilter('week')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  dateFilter === 'week'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                最近7天
              </button>
              <button
                onClick={() => setDateFilter('month')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  dateFilter === 'month'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                最近30天
              </button>
              <button
                onClick={() => setDateFilter('custom')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  dateFilter === 'custom'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                自定义
              </button>
            </div>
          </div>
          <button
            onClick={() => setShowAdvancedFilter(!showAdvancedFilter)}
            className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <Filter className="w-3 h-3" />
            {showAdvancedFilter ? '隐藏高级筛选' : '高级筛选'}
          </button>
        </div>

        {/* 自定义日期范围 */}
        {dateFilter === 'custom' && (
          <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
            <span className="text-xs text-gray-600">日期范围:</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-2 py-1 text-xs border rounded focus:ring-2 focus:ring-green-500 outline-none"
            />
            <span className="text-xs text-gray-400">至</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="px-2 py-1 text-xs border rounded focus:ring-2 focus:ring-green-500 outline-none"
            />
            {(startDate || endDate) && (
              <button
                onClick={() => {
                  setStartDate('');
                  setEndDate('');
                }}
                className="text-xs text-red-500 hover:text-red-600"
              >
                清除
              </button>
            )}
          </div>
        )}

        {/* 高级筛选面板 */}
        {showAdvancedFilter && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
            <h4 className="text-xs font-medium text-gray-700">高级筛选条件</h4>
            
            {/* 实体类型筛选 */}
            <div>
              <label className="text-xs text-gray-600 mb-1 block">实体类型（多选）</label>
              <div className="flex flex-wrap gap-2">
                {allEntityTypes.map(type => (
                  <button
                    key={type}
                    onClick={() => {
                      setSelectedEntityTypes(prev => 
                        prev.includes(type) 
                          ? prev.filter(t => t !== type)
                          : [...prev, type]
                      );
                    }}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      selectedEntityTypes.includes(type)
                        ? 'bg-blue-500 text-white'
                        : 'bg-white text-gray-600 hover:bg-gray-100 border'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
              {selectedEntityTypes.length > 0 && (
                <button
                  onClick={() => setSelectedEntityTypes([])}
                  className="text-xs text-red-500 hover:text-red-600 mt-2"
                >
                  清除选择
                </button>
              )}
            </div>

            {/* 置信度筛选 */}
            <div>
              <label className="text-xs text-gray-600 mb-1 block">
                最低置信度: {minScore}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        )}
      </div>

      {/* 统计面板 */}
      {showStats && (
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            统计分析
          </h4>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.totalRecords}</div>
              <div className="text-xs text-gray-500 mt-1">总记录数</div>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-red-600">{stats.totalEntities}</div>
              <div className="text-xs text-gray-500 mt-1">敏感信息</div>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-green-600">{stats.textRecords}</div>
              <div className="text-xs text-gray-500 mt-1">文本记录</div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.fileRecords}</div>
              <div className="text-xs text-gray-500 mt-1">文件记录</div>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-indigo-600">{stats.analyzeRecords}</div>
              <div className="text-xs text-gray-500 mt-1">识别操作</div>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.anonymizeRecords}</div>
              <div className="text-xs text-gray-500 mt-1">脱敏操作</div>
            </div>
          </div>
          {stats.entityTypes.length > 0 && (
            <div className="bg-white rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-2">Top 10 敏感信息类型</div>
              <div className="space-y-2">
                {stats.entityTypes.map(([type, count]) => (
                  <div key={type} className="flex items-center gap-2">
                    <div className="text-xs text-gray-600 w-32 truncate">{type}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-blue-500 h-full transition-all"
                        style={{ width: `${(count / stats.totalEntities) * 100}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 w-8 text-right">{count}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 无结果提示 */}
      {filteredHistory.length === 0 && history.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>没有找到匹配的记录</p>
          <p className="text-sm mt-1">尝试调整搜索或筛选条件</p>
        </div>
      )}

      {/* 历史列表 */}
      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {Object.entries(groupedHistory).map(([date, items]) => (
          <div key={date}>
            <div className="text-xs text-gray-400 mb-2 sticky top-0 bg-white py-1">{date}</div>
            <div className="space-y-2">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="border rounded-lg overflow-hidden bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  {/* 摘要行 */}
                  <div
                    className="p-3 cursor-pointer flex items-center justify-between"
                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {batchMode && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const newSelected = new Set(selectedIds);
                            if (newSelected.has(item.id)) {
                              newSelected.delete(item.id);
                            } else {
                              newSelected.add(item.id);
                            }
                            setSelectedIds(newSelected);
                          }}
                          className="flex-shrink-0"
                        >
                          {selectedIds.has(item.id) ? (
                            <CheckSquare className="w-5 h-5 text-blue-600" />
                          ) : (
                            <Square className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                      <span className="px-1.5 py-0.5 text-xs bg-gray-200 text-gray-600 rounded font-mono">
                        ID: {item.id}
                      </span>
                      <span className="text-xs text-gray-400">{formatTime(item.timestamp)}</span>
                      <span className={`px-1.5 py-0.5 text-xs rounded ${
                        (item.operation_type || 'analyze') === 'analyze' 
                          ? 'bg-indigo-100 text-indigo-700' 
                          : 'bg-orange-100 text-orange-700'
                      }`}>
                        {(item.operation_type || 'analyze') === 'analyze' ? '识别' : '脱敏'}
                      </span>
                      {item.type === 'file' && (
                        <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                          文件
                        </span>
                      )}
                      <span className={`px-1.5 py-0.5 text-xs rounded ${
                        item.results.length > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {item.results.length} 个敏感信息
                      </span>
                        </div>
                        <p className="text-sm text-gray-700 truncate">
                          {item.filename || item.text.slice(0, 50)}
                          {!item.filename && item.text.length > 50 && '...'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(item);
                        }}
                        className="p-1.5 text-blue-500 hover:bg-blue-100 rounded transition-colors"
                        title="重新加载"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(item.id);
                        }}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      {expandedId === item.id ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      )}
                    </div>
                  </div>

                  {/* 展开详情 */}
                  {expandedId === item.id && (
                    <div className="border-t bg-white p-3">
                      {/* 原文 */}
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-gray-500">原文</span>
                          <button
                            onClick={() => copyToClipboard(item.text, item.id)}
                            className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1"
                          >
                            {copiedId === item.id ? (
                              <>
                                <Check className="w-3 h-3" />
                                已复制
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
                                复制
                              </>
                            )}
                          </button>
                        </div>
                        <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded max-h-32 overflow-y-auto whitespace-pre-wrap">
                          {item.text}
                        </p>
                      </div>

                      {/* 识别结果 */}
                      {item.results.length > 0 && (
                        <div>
                          <span className="text-xs text-gray-500 mb-1 block">识别结果</span>
                          <div className="space-y-1">
                            {item.results.map((result, idx) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                                    {result.entity_type}
                                  </span>
                                  <span className="font-mono text-gray-700">{result.text}</span>
                                </div>
                                <span className="text-gray-400 text-xs">
                                  {(result.score * 100).toFixed(0)}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* 分页控件 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <div className="text-sm text-gray-500">
            显示 {(currentPage - 1) * itemsPerPage + 1} - {Math.min(currentPage * itemsPerPage, filteredHistory.length)} 条，共 {filteredHistory.length} 条
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              首页
            </button>
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="text-sm text-gray-600">
              第 {currentPage} / {totalPages} 页
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              末页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
