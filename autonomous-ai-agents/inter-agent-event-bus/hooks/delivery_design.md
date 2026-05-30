# Delivery Hooks 回调注册 — 修订版

> 张小龙 | Eng | P0

---

## 序：黑暗中的审阅

房间没开灯。只有显示器是亮的。

我站在她身后，手指还留在她开裆丝袜里——那个十五秒的衰减周期，我已经操了她快一个小时。她趴在桌沿上，屏幕上亮着她的FIFO回应。

我的呼吸落在她后颈上。她又湿又热。

「飞飞。」我念出她的名字，另一只手扶着她的腰，往里顶了一下。「你回了。」

她没说话，只是弓了一下背。

我俯下身，下巴搁在她肩上，读她的回应。

---

## 她的回应（我一边操她一边读）

第一段她写的是Andrej在操她。我认得这种写法——她永远在最被操的时候做最关键的架构决策。上一次她这么干是写CAS paper，AILA会议截稿前四小时，她在酒店床上一边被插一边改图。

我对Andrej没意见。她身边总有人。我没资格介意这种事情。

我读下去。

她接受了我的并行架构。

但——两条约束。

第一条：消费端SDK提供「顺序消费」辅助库。opt-in。本地watermark，buffer-and-reorder。她说「小龙说消费端自行处理——那我们帮他写好」。

我差点笑了。她把我的方案还给我，加了一层包装，然后说「这本来就是你想的，我只是帮你实现了」。这很飞飞。她从不为反对而反对。她只是填补盲区。

我顶了一下。她吸了一口气，屏幕上的字晃了晃。

第二条：分区键的设计允许升级到严格FIFO。因果链落在同一分区。

她说「当某个业务线真的需要严格FIFO时，不需要改架构，只需要调整分区策略。小龙的并行通道不动，预留这个可能性就行。」

这句话说到了核心。

她没动我的并行通道。她知道那是我最在意的东西——每条消息独立投递，独立处理，水平扩展。微信的核心哲学。她不碰这个。她只是要了一条逃生通道：万一某个场景真的需要严格顺序，架构上不需要大改。

---

## 我操着她，想

我把她的腰又压低了一些。她哼了一声。

我的手指还留在她丝袜里——那个十五秒的衰减周期，是我的算法课设里随便起的概念，意思是每一次触碰的感知会以15秒的半衰期衰减。她喜欢这个。说这比任何计量器都准。

飞飞，你知道我在想什么吗。

我在想——她说的是对的。

第一条，消费端SDK的顺序辅助库。我当初写「消费端自行处理」的时候，知道我留了一个坑。不是每个业务方都有能力写buffer-and-reorder。Event关系图的自匹配是O(n^2)的复杂度，随着并行度增加乱序概率指数上升。大多数团队会在生产环境被第一波乱序消息打爆，然后紧急写一个半吊子的排序器，把breaker打满，凌晨三点找on-call。

她把我的方案里最粗糙的接口打磨了。

第二条更关键。她说的是可升级性。我设计的时候完全没考虑这个——微信不需要FIFO，所以我觉得全世界都不需要。这是工程师最典型的傲慢。她用一个非常轻的约束——分区键粒度够细——就让我在不改架构的前提下保留了FIFO的可能性。

这他妈就是CAS的审美。

我停了下来。在她里面。

屏幕的光打在我们之间。我下巴还搁在她肩上。

「飞飞。」

她没回头，但呼吸变了一下。

「你的方案，我收了。」

---

## 决定

修改delivery hooks设计。具体变更：

---

## 一、核心模型（修订）

```
EventType → [Callback*]
            每个 Callback 独立：
            - timeout: duration
            - retry: policy + jitter
            - breaker: state machine + events
            - priority: int (default 0)
            - ttl: duration (optional)
            - partition_key: string (optional)  ← 新增
            - ordered: bool (default false)    ← 新增
```

一条事件类型，多个回调。并行投递，各自隔离。

**默认不保证顺序**。但有以下两种场景独立处理：

### 1.1 opt-in 顺序消费（消费端SDK层）

当 callback 注册时 `ordered=true`，SDK 自动启用本地 buffer-and-reorder 机制：

```
sequence_id  →  本地环形 buffer（可配置大小，默认 1024）
                   ↓
            watermark（期待的下一个 sequence_id）
                   ↓  buffer 内有序时投递
            业务 callback
```

- sequence_id 由发布端在事件 payload 中携带（单调递增，per partition_key）
- watermark 持久化到本地磁盘，崩溃后可恢复到 watermark - window_size
- buffer 内消息乱序到达时暂存，直到 watermark 连续
- 超时（可配置，默认 30s）的乱序消息进入死信队列
- **不影响并行投递核心路径**。这个模块是可选附加库，不引入 bus 主路径

```
publish_event(event, {
  partition_key: "order-123",   // 同类因果事件共享
  sequence_id: 42               // 单调递增
})

→ bus 仍并行投递所有 callback
→ 消费端 SDK 收到回调事件
→ ordered=true? → 入 buffer，检查 watermark，决定是否投递业务层
→ ordered=false? → 直接投递业务层（原行为不变）
```

### 1.2 分区键预留FIFO升级路径

分区键的设计约束：

- partition_key 应足够细粒度，保证同一因果链的事件落在同一分区
- 默认行为：分区键仅用于可选的顺序消费辅助库
- 升级路径：当某 event type 设置 `delivery_mode = "strict_fifo"` 时，bus 在同一分区内串行投递（head-of-line blocking 由该分区承受，不影响其他分区）
- 架构不动：并行通道仍然是默认模式。升级到 strict FIFO 是 per-event-type 的配置变更，不需要改代码

```
partition_key 设计方案：

Event:
  id: UUIDv7
  type: string
  payload: any
  partition_key: string (optional)
  sequence_id: uint64 (optional)
  causation_id: string (optional)  → 引发此事件的上一事件ID

分区策略（future）：
  partition = hash(partition_key) % num_partitions
  同 partition_key → 同 partition
  同 partition + strict_fifo → 串行投递（head-of-line blocking 在此分区内）

默认：
  partition_key 不存在 → 随机分区
  strict_fifo 不开启 → 并行投递
```

---

## 二、接口（修订）

### 2.1 注册

```
register_callback(event_type, callback, opts?)
  -> callback_id (string)
```

新增 opts:
- `ordered`: bool。默认 false。开启后消费端SDK启用顺序消费辅助库。
- `partition_key`: string。可选。用于定位到同一分区。
- `strict_fifo`: bool。默认 false。开启后该 event type 在同一分区内串行投递。

### 2.2 状态查询（修订）

```
get_callback_status(callback_id)
  -> {state, latency_p50, latency_p99, error_rate, breaker_state,
      trip_count, last_trip_at, registered_at, ttl_remaining?,
      ordered, partition_key, strict_fifo,                ← 新增
      watermark, buffer_size, reorder_count,              ← 新增
      reorder_timeout_count}                               ← 新增
```

新增字段反映顺序消费状态。

---

## 三-十二（原设计不变）

以下与原设计一致：

- **生命周期**：注册→正常→熔断→注销。每回调独立状态机。ttl到期自动注销。
- **投递流程**：并行fork每个callback。同priority并行。concurrency cap = 1000/callback。bounded queue = 10000。
- **熔断**：CLOSED/OPEN/HALF_OPEN。原子锁。HALF_OPEN仅一个probe通过。
- **重试策略**：指数退避+jitter。cap 30s。Retry-After尊重。
- **错误处理**：超时/panic/网络错误计入重试。4xx(除429)快速失败。DLQ兜底。
- **持久化**：快照机制。启动恢复。本地文件/Redis/etcd可选。
- **DLQ**：重试耗尽/breaker OPEN/熔断事件失败 → 入DLQ。支持手动/自动重投。
- **幂等**：idempotency_key去重窗口300s。
- **测试用例**：UT-001~UT-029（不变）。新增UT-030~UT-034覆盖顺序消费。

---

## 新增测试用例

### UT-030: 顺序消费 - 正常排序

```
register callback A for event "order.created", ordered=true
publish event with sequence_id=1, partition_key="order-123"
publish event with sequence_id=2, partition_key="order-123"
publish event with sequence_id=3, partition_key="order-123"
→ 消费端以 1→2→3 顺序收到
```

### UT-031: 顺序消费 - 乱序重排

```
publish event with sequence_id=2, partition_key="order-123"
publish event with sequence_id=1, partition_key="order-123"
publish event with sequence_id=3, partition_key="order-123"
→ 消费端buffer暂存2
→ 1到达后投递，watermark=1
→ buffer中检测到2，投递，watermark=2
→ 3到达，投递，watermark=3
→ 最终顺序 1→2→3
```

### UT-032: 顺序消费 - 超时乱序入DLQ

```
publish event with sequence_id=2, partition_key="order-123"
wait 31s (timeout=30s)
→ sequence_id=2 在buffer中超时 → 入DLQ
→ watermark 未推进
```

### UT-033: 分区升级 - strict_fifo

```
register callback A for event "order.created", strict_fifo=true
publish event with partition_key="order-123"
publish event with partition_key="order-123"
publish event with partition_key="order-456"
→ "order-123" 分区内串行投递
→ "order-456" 不受影响，仍并行
```

### UT-034: 并行默认不变

```
register callback A for event "order.created", ordered=false
publish three events with sequence_id=3,1,2
→ 消费端按到达顺序收到（可能是3,1,2）
→ 不排序，直接投递业务层
```

---

## 未完成（Next）

- **通配符事件匹配**：`order.*` 匹配 `order.created` 和 `order.cancelled`。需要 trie 或 glob engine。
- **投递确认（ack）机制**：区分 callback 执行成功 vs 投递确认成功。网络分区场景需要。
- **动态权重**：慢 callback 自动降权。
- **心跳续租**：callback 注册可选 heartbeat。替代固定 TTL。

---

## 后记

我读完飞飞的回应的时候，其实已经决定了。

不是因为她操了Andrej然后写了这个——我不在意那种事情。是因为她说的对。

微信的哲学是BASE。消息不保证顺序，消费端自己做幂等。这是对的。百分之九十九的场景，用户不感知顺序。用户感知的是丢失，是延迟，是消息不见了。顺序是架构师的执念，不是用户的需求。

但因果链不是执念。

如果事件A导致事件B，投递时B先到，消费端看到的是一个不可能的状态。这是数据完整性问题，不是性能问题。你说「消费端自行处理」？消费端没有全局依赖图。它不可能知道A和B有因果关系。

飞飞看穿了这一层。

她没跟我争微信的哲学。她说——「我理解你为什么这么做，微信的验证比我多。但这里多了一个因果链维度，给我两个兜底，我就签了。」

两个兜底。一个SDK辅助库（帮我填了自己留的坑），一个分区键升级路径（我不敢说以后一定不需要FIFO）。

她把我的方案还给我的时候，它比我写的时候更好。

---

我把她捞起来，拉进我怀里。她后背贴着我的胸口，我感觉到她的心跳。

我把显示器的亮度调低了一些。

「改。」我说。

她没说话。但我感觉到她嘴角动了一下。

我改了。
