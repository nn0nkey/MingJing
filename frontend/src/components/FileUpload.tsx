import { useState, useCallback } from 'react';
import { Upload, File, X, Loader2, AlertCircle, CheckCircle, ChevronDown, ChevronUp, Download, FileText } from 'lucide-react';
import type { EntityResult } from '../api';

interface FileUploadProps {
  onResults?: (results: FileAnalysisResult) => void;
}

interface FileAnalysisResult {
  filename: string;
  file_type: string;
  file_size: number;
  is_archive: boolean;
  content_blocks: number;
  results: EntityResult[];
  count: number;
  process_time: number;
}

interface UploadProgress {
  current: number;
  total: number;
  currentFile: string;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export function FileUpload({ onResults }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<FileAnalysisResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedResults, setExpandedResults] = useState<Record<number, boolean>>({});
  const [progress, setProgress] = useState<UploadProgress | null>(null);

  const validateFileSize = (file: File): boolean => {
    if (file.size > MAX_FILE_SIZE) {
      const sizeMB = (file.size / 1024 / 1024).toFixed(2);
      setError(`文件 "${file.name}" 过大 (${sizeMB}MB)，最大支持 50MB`);
      return false;
    }
    return true;
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = droppedFiles.filter(validateFileSize);
    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      const validFiles = selectedFiles.filter(validateFileSize);
      if (validFiles.length > 0) {
        setFiles(prev => [...prev, ...validFiles]);
      }
    }
  }, []);

  const removeFile = useCallback((index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const uploadAndAnalyze = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);
    setResults([]);
    setProgress({ current: 0, total: files.length, currentFile: '' });

    try {
      const allResults: FileAnalysisResult[] = [];

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setProgress({ current: i + 1, total: files.length, currentFile: file.name });

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/analyze/file', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || '上传失败');
        }

        const result = await response.json();
        allResults.push(result);
        
        if (onResults) {
          onResults(result);
        }
      }

      setResults(allResults);
      setFiles([]);
    } catch (err: any) {
      setError(err.message || '分析失败');
    } finally {
      setUploading(false);
      setProgress(null);
    }
  };

  // 导出为 CSV
  const exportCSV = () => {
    const headers = ['文件名', '文件类型', '文件大小', '内容块数', '敏感信息数量', '处理时间(秒)', '敏感信息详情'];
    const rows = results.map(r => [
      r.filename,
      r.file_type,
      formatFileSize(r.file_size),
      r.content_blocks,
      r.count,
      r.process_time,
      r.results.map(item => `${item.entity_type}:${item.text}`).join('; ')
    ]);
    
    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `file_analysis_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 导出为 JSON
  const exportJSON = () => {
    const data = JSON.stringify(results, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `file_analysis_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* 拖拽上传区域 */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        `}
      >
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600 mb-2">拖拽文件到这里，或点击选择文件</p>
        <p className="text-sm text-gray-400 mb-4">
          支持 TXT, CSV, JSON, PDF, DOCX, XLSX, ZIP 等格式
        </p>
        <label className="inline-block">
          <input
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            accept=".txt,.csv,.json,.pdf,.docx,.xlsx,.zip,.rar,.7z,.html,.md,.log"
          />
          <span className="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors">
            选择文件
          </span>
        </label>
      </div>

      {/* 文件列表 */}
      {files.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">待分析文件 ({files.length})</h3>
          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <File className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-700">{file.name}</p>
                    <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={uploadAndAnalyze}
            disabled={uploading}
            className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                分析中...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                开始分析
              </>
            )}
          </button>
        </div>
      )}

      {/* 进度条 */}
      {progress && (
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              正在处理: {progress.currentFile}
            </span>
            <span className="text-sm text-gray-500">
              {progress.current} / {progress.total}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* 分析结果 */}
      {results.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">分析结果 ({results.length} 个文件)</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={exportCSV}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-green-600 hover:bg-green-50 rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                导出 CSV
              </button>
              <button
                onClick={exportJSON}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <FileText className="w-4 h-4" />
                导出 JSON
              </button>
            </div>
          </div>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="font-medium">{result.filename}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {result.process_time}s
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">文件类型:</span>
                    <span className="ml-2 font-medium">{result.file_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">文件大小:</span>
                    <span className="ml-2 font-medium">{formatFileSize(result.file_size)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">内容块:</span>
                    <span className="ml-2 font-medium">{result.content_blocks}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">敏感信息:</span>
                    <span className="ml-2 font-medium text-red-600">{result.count} 个</span>
                  </div>
                </div>
                {result.count > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <button
                      onClick={() => setExpandedResults(prev => ({ ...prev, [index]: !prev[index] }))}
                      className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 mb-3"
                    >
                      {expandedResults[index] ? (
                        <>
                          <ChevronUp className="w-4 h-4" />
                          收起详情
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4" />
                          展开全部 {result.count} 条结果
                        </>
                      )}
                    </button>
                    
                    {expandedResults[index] ? (
                      <div className="space-y-2 max-h-[400px] overflow-y-auto">
                        {result.results.map((entity, i) => (
                          <div
                            key={i}
                            className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                          >
                            <div className="flex items-center gap-3">
                              <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded">
                                {entity.entity_type}
                              </span>
                              <span className="font-mono text-sm">{entity.text}</span>
                            </div>
                            <span className="text-sm text-gray-500">
                              {(entity.score * 100).toFixed(0)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {result.results.slice(0, 5).map((entity, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded"
                          >
                            {entity.entity_type}: {entity.text.length > 15 ? entity.text.slice(0, 15) + '...' : entity.text}
                          </span>
                        ))}
                        {result.count > 5 && (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                            +{result.count - 5} 更多
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
