import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export interface EntityResult {
  entity_type: string;
  text: string;
  start: number;
  end: number;
  score: number;
  verified: boolean;
  llm_reason?: string;
}

export interface AnalyzeResponse {
  text: string;
  results: EntityResult[];
  count: number;
}

export interface EntityTypeInfo {
  name: string;
  description: string;
  category: string;
}

export interface HealthResponse {
  status: string;
  nlp_loaded: boolean;
  recognizers_count: number;
}

export const analyzeText = async (
  text: string,
  entities?: string[],
  scoreThreshold: number = 0,
  useLlmVerify: boolean = false
): Promise<AnalyzeResponse> => {
  const response = await api.post<AnalyzeResponse>('/analyze', {
    text,
    entities: entities?.length ? entities : null,
    score_threshold: scoreThreshold,
    use_llm_verify: useLlmVerify,
  });
  return response.data;
};

export const getEntities = async (): Promise<EntityTypeInfo[]> => {
  const response = await api.get<EntityTypeInfo[]>('/entities');
  return response.data;
};

export const healthCheck = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

// 历史记录 API
export interface HistoryItem {
  id: string;
  text: string;
  results: EntityResult[];
  type: 'text' | 'file';
  filename?: string;
  timestamp: string;
  operation_type?: 'analyze' | 'anonymize';  // Optional for backward compatibility
}

export const getHistory = async (limit: number = 100): Promise<HistoryItem[]> => {
  const response = await api.get<HistoryItem[]>('/history', { params: { limit } });
  return response.data;
};

export const addHistory = async (
  text: string,
  results: EntityResult[],
  type: 'text' | 'file' = 'text',
  filename?: string,
  operationType: 'analyze' | 'anonymize' = 'analyze'
): Promise<HistoryItem> => {
  console.log('API addHistory 调用参数:', { type, operationType, filename, textLength: text.length, resultsCount: results.length });
  
  const formData = new FormData();
  formData.append('text', text);
  formData.append('results', JSON.stringify(results));
  formData.append('record_type', type);
  formData.append('operation_type', operationType);
  if (filename) formData.append('filename', filename);
  
  console.log('FormData 内容:', {
    text: formData.get('text')?.toString().substring(0, 50),
    record_type: formData.get('record_type'),
    operation_type: formData.get('operation_type'),
    filename: formData.get('filename')
  });
  
  const response = await api.post<HistoryItem>('/history', formData);
  console.log('API 返回的历史记录:', response.data);
  return response.data;
};

export const deleteHistory = async (id: string): Promise<void> => {
  await api.delete(`/history/${id}`);
};

export const clearHistory = async (): Promise<void> => {
  await api.delete('/history');
};

// 智能脱敏函数：根据实体类型保留部分信息
const smartMask = (entityType: string, value: string): string => {
  if (!value) return value;
  const len = value.length;

  switch (entityType) {
    case 'CN_PHONE':
      // 手机号：138****5678 (保留前3后4)
      if (len === 11) {
        return value.substring(0, 3) + '****' + value.substring(7);
      }
      return value.substring(0, Math.min(3, len)) + '****';

    case 'CN_ID_CARD':
      // 身份证：3301**********1234 (保留前4后4)
      if (len === 18) {
        return value.substring(0, 4) + '*'.repeat(10) + value.substring(14);
      } else if (len === 15) {
        return value.substring(0, 4) + '*'.repeat(7) + value.substring(11);
      }
      return value.substring(0, 4) + '*'.repeat(Math.max(0, len - 8)) + value.substring(Math.max(4, len - 4));

    case 'CN_BANK_CARD':
      // 银行卡：6222 **** **** 1234 (保留前4后4)
      if (len >= 16) {
        return value.substring(0, 4) + ' **** **** ' + value.substring(len - 4);
      }
      return value.substring(0, 4) + '****' + value.substring(Math.max(4, len - 4));

    case 'CN_EMAIL':
      // 邮箱：abc***@example.com (保留前3和域名)
      const atIndex = value.indexOf('@');
      if (atIndex > 0) {
        const localPart = value.substring(0, atIndex);
        const domain = value.substring(atIndex);
        if (localPart.length <= 3) {
          return localPart[0] + '***' + domain;
        }
        return localPart.substring(0, 3) + '***' + domain;
      }
      return value.substring(0, 3) + '***';

    case 'PERSON':
      // 姓名：张* 或 欧阳** (保留姓氏)
      if (len === 2) {
        return value[0] + '*';
      } else if (len === 3) {
        return value[0] + '**';
      } else if (len >= 4) {
        // 复姓情况
        return value.substring(0, 2) + '*'.repeat(len - 2);
      }
      return value[0] + '*';

    case 'CN_PASSPORT':
    case 'CN_DRIVER_LICENSE':
    case 'CN_MILITARY_ID':
      // 证件号：保留前2后2
      if (len > 4) {
        return value.substring(0, 2) + '*'.repeat(len - 4) + value.substring(len - 2);
      }
      return '***';

    case 'CN_VEHICLE_PLATE':
      // 车牌：京A****8 (保留省份+首字母和最后1位)
      if (len >= 7) {
        return value.substring(0, 2) + '****' + value.substring(len - 1);
      }
      return value.substring(0, 2) + '****';

    case 'LOCATION':
      // 地址：保留前6个字
      if (len > 10) {
        return value.substring(0, 6) + '***';
      }
      return value.substring(0, Math.min(4, len)) + '***';

    default:
      // 其他类型：全部替换为黑圆点
      return '●'.repeat(len);
  }
};

// 自动脱敏 API
export const anonymizeText = async (
  text: string,
  entities?: string[],
  scoreThreshold: number = 0
): Promise<{ anonymized: string; results: EntityResult[] }> => {
  const response = await analyzeText(text, entities, scoreThreshold, false);
  let anonymized = text;
  // 从后往前替换，避免索引偏移
  const sortedResults = [...response.results].sort((a, b) => b.start - a.start);
  for (const result of sortedResults) {
    const mask = smartMask(result.entity_type, result.text);
    anonymized = anonymized.substring(0, result.start) + mask + anonymized.substring(result.end);
  }
  return { anonymized, results: response.results };
};

export const anonymizeFile = async (
  file: File,
  entities?: string[],
  scoreThreshold: number = 0
): Promise<Blob> => {
  const formData = new FormData();
  formData.append('file', file);
  if (entities && entities.length > 0) {
    formData.append('entities', entities.join(','));
  }
  formData.append('score_threshold', String(scoreThreshold));

  const response = await api.post('/anonymize/file', formData, {
    responseType: 'blob',
  });
  return response.data as Blob;
};

export default api;
