"""
历史记录数据库管理
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = Path(__file__).parent / "history.db"


@dataclass
class HistoryRecord:
    id: Optional[int]
    text: str
    results: List[dict]
    record_type: str  # 'text' or 'file'
    filename: Optional[str]
    created_at: datetime
    updated_at: datetime
    operation_type: str = 'analyze'  # 'analyze' or 'anonymize'
    
    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "text": self.text,
            "results": self.results,
            "type": self.record_type,
            "filename": self.filename,
            "timestamp": self.updated_at.isoformat(),
            "operation_type": self.operation_type,
        }


class HistoryDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _get_conn(self):
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    results TEXT NOT NULL,
                    record_type TEXT NOT NULL DEFAULT 'text',
                    filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operation_type TEXT DEFAULT 'analyze'
                )
            """)
            
            # 迁移：为已存在的表添加 operation_type 列
            try:
                cursor = conn.execute("PRAGMA table_info(history)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'operation_type' not in columns:
                    logger.info("添加 operation_type 列到现有表")
                    conn.execute("ALTER TABLE history ADD COLUMN operation_type TEXT DEFAULT 'analyze'")
                    conn.commit()
                    logger.info("operation_type 列添加成功")
            except Exception as e:
                logger.warning(f"迁移 operation_type 列时出错: {e}")
            
            # 创建索引加速查询
            conn.execute("CREATE INDEX IF NOT EXISTS idx_text ON history(text)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON history(updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_record_type ON history(record_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operation_type ON history(operation_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON history(created_at DESC)")
            # 复合索引用于常见查询组合
            conn.execute("CREATE INDEX IF NOT EXISTS idx_type_operation ON history(record_type, operation_type)")
            conn.commit()
        logger.info(f"历史记录数据库初始化完成: {self.db_path}")
    
    def add_or_update(self, text: str, results: List[dict], record_type: str = 'text', filename: str = None, operation_type: str = 'analyze') -> HistoryRecord:
        """添加或更新历史记录（相同文本更新而不是新增）"""
        now = datetime.now()
        results_json = json.dumps(results, ensure_ascii=False)
        
        with self._get_conn() as conn:
            # 检查是否存在相同文本和操作类型（识别和脱敏分开记录）
            cursor = conn.execute(
                "SELECT id FROM history WHERE text = ? AND record_type = ? AND operation_type = ?",
                (text, record_type, operation_type)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                conn.execute(
                    "UPDATE history SET results = ?, updated_at = ?, filename = ?, operation_type = ? WHERE id = ?",
                    (results_json, now, filename, operation_type, existing[0])
                )
                record_id = existing[0]
                logger.debug(f"更新历史记录: id={record_id}")
            else:
                # 插入新记录
                cursor = conn.execute(
                    "INSERT INTO history (text, results, record_type, filename, created_at, updated_at, operation_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (text, results_json, record_type, filename, now, now, operation_type)
                )
                record_id = cursor.lastrowid
                logger.debug(f"新增历史记录: id={record_id}")
            
            conn.commit()
        
        return HistoryRecord(
            id=record_id,
            text=text,
            results=results,
            record_type=record_type,
            filename=filename,
            created_at=now,
            updated_at=now,
            operation_type=operation_type
        )
    
    def get_all(self, limit: int = 100) -> List[HistoryRecord]:
        """获取所有历史记录，按更新时间倒序"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT id, text, results, record_type, filename, created_at, updated_at, operation_type FROM history ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
            records = []
            for row in cursor.fetchall():
                records.append(HistoryRecord(
                    id=row[0],
                    text=row[1],
                    results=json.loads(row[2]),
                    record_type=row[3],
                    filename=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                    operation_type=row[7] if len(row) > 7 and row[7] else 'analyze',
                ))
            return records
    
    def delete(self, record_id: int) -> bool:
        """删除指定记录"""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_all(self) -> int:
        """清空所有记录"""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM history")
            conn.commit()
            return cursor.rowcount


# 单例
_history_db: Optional[HistoryDB] = None

def get_history_db() -> HistoryDB:
    global _history_db
    if _history_db is None:
        _history_db = HistoryDB()
    return _history_db
