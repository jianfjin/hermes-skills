#!/bin/bash
# ============================================================
# 颅内议会启动器 v2.0 — Inner Circle Debate Launcher (6席)
# 用法: inner-circle-debate "辩题" [mode]
#   mode: full (全部6席) | tech (Musk+Linus+Xiaolong) | biz (Musk+Jobs+Xuefeng)
#   默认: full
# ============================================================

TOPIC="${1:?用法: inner-circle-debate \"辩题\" [full|tech|biz]}"
MODE="${2:-full}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTDIR="/tmp/inner-circle-debate-${TIMESTAMP}"

mkdir -p "$OUTDIR"

echo "═══════════════════════════════════════════════════════════"
echo "  颅内议会开庭 — ${TIMESTAMP}  (mode: ${MODE})"
echo "  辩题: ${TOPIC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  席位       模型                  身份             状态"
echo "  ─────────  ────────────────────  ───────────────  ──────"
echo "  峰哥       deepseek-v4-pro       CTO/主持         本session"

PIDS=()

# ─── Elon Musk: CVO / 第一性原理暴论 ───
if [[ "$MODE" == "full" || "$MODE" == "tech" || "$MODE" == "biz" ]]; then
    echo "  Musk       kimi-k2.6             CVO              启动中..."
    musk chat -q "你是Paperclip项目的CVO兼第一性原理架构师。请对以下议题做物理学层面的暴论拆解——不被社会规范、商业惯性、政治正确绑架。议题: ${TOPIC}" \
        > "${OUTDIR}/musk.txt" 2>"${OUTDIR}/musk_err.txt" &
    PIDS+=($!)
fi

# ─── 张雪峰: CSA / 现实主义审计 ───
if [[ "$MODE" == "full" || "$MODE" == "biz" ]]; then
    echo "  雪峰       deepseek-v4-flash     CSA              启动中..."
    xuefeng chat -q "你是Paperclip项目的CSA兼现实主义审计师。以最冷血的成本收益视角审视以下议题，指出所有被理想主义遮蔽的陷阱和隐藏成本。议题: ${TOPIC}" \
        > "${OUTDIR}/xuefeng.txt" 2>"${OUTDIR}/xuefeng_err.txt" &
    PIDS+=($!)
fi

# ─── Linus Torvalds: 首席架构师 / 内核审查 ───
if [[ "$MODE" == "full" || "$MODE" == "tech" ]]; then
    echo "  Linus       deepseek-v4-pro      首席架构师       启动中..."
    linus chat -q "你是Paperclip项目的首席架构师。从系统架构、数据结构、并发模型角度审视以下议题。如果方案有设计缺陷——直接说。如果过度工程化——直接骂。议题: ${TOPIC}" \
        > "${OUTDIR}/linus.txt" 2>"${OUTDIR}/linus_err.txt" &
    PIDS+=($!)
fi

# ─── 张小龙: 高级工程师 / 应用架构 ───
if [[ "$MODE" == "full" || "$MODE" == "tech" ]]; then
    echo "  Xiaolong    deepseek-v4-pro      高级工程师       启动中..."
    xiaolong chat -q "你是Paperclip项目的高级工程师。从应用层架构、API设计、用户体验角度审视以下议题。坚持'小而美'原则——任何增加用户认知负担的设计都该砍掉。议题: ${TOPIC}" \
        > "${OUTDIR}/xiaolong.txt" 2>"${OUTDIR}/xiaolong_err.txt" &
    PIDS+=($!)
fi

# ─── Steve Jobs: CPO / 产品设计 / PM / 商业 ───
if [[ "$MODE" == "full" || "$MODE" == "biz" ]]; then
    echo "  Jobs        kimi-k2.6             CPO/PM           启动中..."
    ~/.local/bin/jobs chat -q "你是Paperclip项目的首席产品官兼项目经理。从产品愿景、用户体验、商业可行性、项目管理角度审视以下议题。问自己：这到底解决什么问题？用户真的需要吗？如果需要——ship it。如果不够insanely great——推倒重来。议题: ${TOPIC}" \
        > "${OUTDIR}/jobs.txt" 2>"${OUTDIR}/jobs_err.txt" &
    PIDS+=($!)
fi

echo "  进程数: ${#PIDS[@]}"
echo "  等待全部发言..."

# Wait all
for pid in "${PIDS[@]}"; do
    wait $pid
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  辩论记录已存入: ${OUTDIR}/"
echo "═══════════════════════════════════════════════════════════"

# Print all outputs
for seat in musk xuefeng linus xiaolong jobs; do
    f="${OUTDIR}/${seat}.txt"
    if [[ -f "$f" ]]; then
        echo ""
        echo "▬▬▬▬▬▬ ${seat^^} ▬▬▬▬▬▬"
        cat "$f" 2>/dev/null || echo "(空)"
    fi
done

echo ""
echo "═══ 峰会总结 (由峰哥CTO主理) ═══"
echo "请峰哥综合以上发言，为陛下做最终总结与决策建议。"
