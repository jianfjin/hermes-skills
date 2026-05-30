# SQLite WAL 事件总线生产化：审查经验（2026-05-29）

本文档记录了 Phase 1 实施计划经过 Linus Torvalds 和 Guido van Rossum 真实 profile 审查后确立的最佳实践。

---

## 1. WAL 配置的变与不变

### 初始方案（v1，被Linus批评）
```sql
PRAGMA mmap_size=268435456;  -- ❌ 256MB内存映射，纯CV大法
```
Linus评价：「在内存受限的VM上OOM-kills你的进程。Drop it unless you have profiler data showing mmap actually helps. Event bus是追加写+偏移量查询的模式，mmap几乎没有任何帮助。」

### 修正方案（v2）
- mmap_size主动移除
- 保留：journal_mode=WAL, synchronous=NORMAL, busy_timeout=5000, page_size=4096

### 需要WAL checkpoint策略（v1完全缺失）
wal_autocheckpoint=1000（即每1000页自动checkpoint）不够——默认PASSIVE模式会让路给reader，导致WAL无限增长。

**修正**：增加定时 PRAGMA wal_checkpoint(TRUNCATE) 任务（建议30秒间隔）。
SQLite WAL文件长到GB级的生产事故是常见的——这是生产环境致命缺陷。

---

## 2. 不要用polling

### 问题
500ms + random(0,200)ms jitter 的轮询方案。Linus评价：「通知延迟底限是500ms——这在计算机系统里叫'永远'。Polling = 放弃治疗。随机jitter只是装点门面。」

### 方案
用 sqlite3_update_hook + inotify 双通道实时通知：
- Listener线程（架构中唯一）注册sqlite3_update_hook回调
- 同时inotify监听WAL文件目录
- 收到通知后向所有reader agent推送：「有新event可读」
- Reader agent不再主动poll

---

## 3. 连接管理：1 Writer + N Reader 直连

### 问题
ConnectionPool(max_connections=4, idle_timeout=60s) 是过度设计。

Linus：「SQLite连接不是socket。你只需要两种连接模式：一个writer连接，N个reader连接（每个agent一个）。带idle_timeout的'pool'暗示你以为SQLite连接创建开销很大——其实不大。你在制造故障模式来解决不存在的问题。」

Guido：「Context manager在哪里？如果看到pool.get_conn()没有配对的pool.release(conn)在finally块里，我会退回去重写。」

### 方案
```python
@contextmanager
def reader() -> Connection:
    """Acquire a read-only SQLite connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        yield conn
    finally:
        conn.close()

# 使用
with reader() as conn:
    cursor = conn.execute("SELECT * FROM events WHERE id > ?", (last_id,))
```

---

## 4. 不要重复处理SQLITE_BUSY

### 问题
v1 方案同时做了三件事情：
1. `PRAGMA busy_timeout=5000` — SQLite的C层自动忙等待
2. Python retry回退(5次, 50ms base, max 2s)
3. @retry_on_busy装饰器

Guido：「你在穿三层雨衣对抗SQLite。Pythonic的修复：选一个。Either trust busy_timeout (the 'one obvious way'), or remove it and own the retry. Don't do both.」

### 方案选择
- 推荐：信任 `busy_timeout=5000`，移除Python侧的所有重试循环和装饰器
- 备选：移除busy_timeout，编写自己的指数退避循环

---

## 5. 必须定义Event Schema（v1最大缺失）

Linus：「你在设计一个event bus，但没有定义EVENT MODEL。event长什么样？consumer怎么跟踪位置？回答这个问题，一半的性能/连接/schema问题自动解决了。跳过它，你就是在对一个还没定义好的设计调拨弄旋钮。」

### 最小可行Event Schema
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,          -- 'agent:heartbeat', 'feifei:task_complete'
    payload TEXT NOT NULL,        -- JSON string
    publisher TEXT NOT NULL,      -- which agent published
    created_at REAL NOT NULL,     -- unix epoch
    ttl_seconds INTEGER DEFAULT 86400
);

CREATE TABLE consumer_cursors (
    consumer_id TEXT NOT NULL,
    topic_pattern TEXT NOT NULL,
    last_event_id INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (consumer_id, topic_pattern)
);

CREATE TABLE dead_letters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_event_id INTEGER,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at REAL NOT NULL
);
```

---

## 6. 还需要检查NFS

WAL模式在网络文件系统上损坏数据是SQLite文档明确警告的。

```python
import os, stat, subprocess

def check_nfs(db_dir: str):
    """Refuse to start if the database directory is on NFS/CIFS."""
    result = subprocess.run(
        ["stat", "-f", "-c", "%T", db_dir],
        capture_output=True, text=True
    )
    fstype = result.stdout.strip()
    if fstype in ("nfs", "cifs", "fuse.sshfs"):
        raise RuntimeError(
            f"WAL mode is incompatible with {fstype}. "
            f"Move the database to a local filesystem."
        )
```

---

## 7. 死信策略：三条件 + 溢出归档

| 条件 | 行为 | 日志 | 
|------|------|------|
| SQLITE_BUSY用尽所有重试 | 写入dead_letters表 | ERROR | 
 | Consumer落后超过1000条 | 仅保留最后1000条+归档 | WARNING |
| 磁盘剩余<100MB | 暂停写入，持续报警 | CRITICAL |

---

## 8. 不要手工部署

9步逐条命令部署 = 等待发生的Bug。「有人顺序不对。有人venv路径不同。Deploy by script or container.」

用 `deploy_phase1.sh` 一键脚本完成全部步骤，包含幂等检查和回滚。

---

## 参考资料

- Phase 1 v2 完整方案：`~/projects/ai-digital-person-app/docs/inter-agent-event-bus-Phase1-v2-完整方案-20260529.md`
- Linus+Guido 完整评审：`~/projects/ai-digital-person-app/docs/phase1-review-linus-guido.md`
- 张小龙/赵小龙原版方案：`~/projects/ai-digital-person-app/docs/inter-agent-event-bus-Phase1-技术方案-张小龙制定-20260529.md`
