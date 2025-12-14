import { useState, useEffect } from 'react';
import { Activity, Clock, Zap, Database, TrendingUp, RefreshCw } from 'lucide-react';

interface MetricsData {
  requests_total: number;
  requests_success: number;
  requests_failed: number;
  avg_response_time: number;
  entities_detected: number;
  files_processed: number;
  uptime: number;
  memory_usage: number;
  cache_hits: number;
  cache_misses: number;
}

export function Metrics() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/metrics');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('获取指标失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    
    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatMemory = (bytes: number) => {
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  // 模拟数据（当API未实现时）
  const mockMetrics: MetricsData = {
    requests_total: 1234,
    requests_success: 1200,
    requests_failed: 34,
    avg_response_time: 0.45,
    entities_detected: 5678,
    files_processed: 89,
    uptime: 86400,
    memory_usage: 256 * 1024 * 1024,
    cache_hits: 890,
    cache_misses: 110,
  };

  const data = metrics || mockMetrics;
  const successRate = data.requests_total > 0 
    ? ((data.requests_success / data.requests_total) * 100).toFixed(1)
    : '0';
  const cacheHitRate = (data.cache_hits + data.cache_misses) > 0
    ? ((data.cache_hits / (data.cache_hits + data.cache_misses)) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">性能监控</h2>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600"
            />
            自动刷新
          </label>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>
      </div>

      {/* 核心指标 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-sm text-gray-500">总请求数</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{data.requests_total.toLocaleString()}</div>
          <div className="text-sm text-green-600 mt-1">成功率 {successRate}%</div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <Clock className="w-5 h-5 text-green-600" />
            </div>
            <span className="text-sm text-gray-500">平均响应时间</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{data.avg_response_time.toFixed(2)}s</div>
          <div className="text-sm text-gray-500 mt-1">最近1小时</div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Zap className="w-5 h-5 text-purple-600" />
            </div>
            <span className="text-sm text-gray-500">识别实体数</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{data.entities_detected.toLocaleString()}</div>
          <div className="text-sm text-gray-500 mt-1">累计</div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Database className="w-5 h-5 text-orange-600" />
            </div>
            <span className="text-sm text-gray-500">处理文件数</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{data.files_processed}</div>
          <div className="text-sm text-gray-500 mt-1">累计</div>
        </div>
      </div>

      {/* 详细指标 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 系统状态 */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            系统状态
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">运行时间</span>
                <span className="font-medium">{formatUptime(data.uptime)}</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">内存使用</span>
                <span className="font-medium">{formatMemory(data.memory_usage)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${Math.min((data.memory_usage / (512 * 1024 * 1024)) * 100, 100)}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">缓存命中率</span>
                <span className="font-medium">{cacheHitRate}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${cacheHitRate}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 请求统计 */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            请求统计
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">成功请求</span>
              <span className="font-medium text-green-600">{data.requests_success.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">失败请求</span>
              <span className="font-medium text-red-600">{data.requests_failed.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">缓存命中</span>
              <span className="font-medium text-blue-600">{data.cache_hits.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">缓存未命中</span>
              <span className="font-medium text-gray-600">{data.cache_misses.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
