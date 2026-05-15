#!/bin/bash
# ============================================================
# 颅内议会启动器 — Inner Circle Debate Launcher
# 用法: inner-circle-debate "辩题"
#
# 席位分配:
#   首席: Feng Ge (default profile)   — deepseek-v4-pro
#   CVO:  Elon Musk (musk profile)    — kimi-k2.6
#   CSA:  Zhang Xuefeng (xuefeng)     — deepseek-v4-flash
#
# 依赖: hermes profile create musk/xuefeng 已完成
# 输出: /tmp/inner-circle-debate-<timestamp>/
# ============================================================

TOPIC="${1:?用法: inner-circle-debate \"辩题\"}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTDIR="/tmp/inner-circle-debate-${TIMESTAMP}"

mkdir -p "$OUTDIR"

echo "═══════════════════════════════════════════════════"
echo "  颅内议会开庭 — ${TIMESTAMP}"
echo "  辩题: ${TOPIC}"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  席位     模型                  状态"
echo "  ───────  ────────────────────  ──────"
echo "  峰哥     deepseek-v4-pro      主持 (本session)"
echo "  Musk     kimi-k2.6            启动中..."
echo "  雪峰     deepseek-v4-flash    启动中..."
echo ""

# Musk: 第一性原理暴论输出
musk chat -q "你作为Paperclip项目的CVO（Chief Visionary Officer）兼第一性原理架构师，请对以下议题给出你的暴论式分析——直接拆到物理定律层面，不被任何社会规范绑架。议题: ${TOPIC}" \
    > "${OUTDIR}/musk.txt" 2>"${OUTDIR}/musk_err.txt" &
PID_MUSK=$!

# 张雪峰: 现实主义审计
xuefeng chat -q "你作为Paperclip项目的CSA（Chief Strategic Analyst）兼现实主义审计师，请以最冷血的成本收益视角审视以下议题，指出所有被理想主义遮蔽的陷阱。议题: ${TOPIC}" \
    > "${OUTDIR}/xuefeng.txt" 2>"${OUTDIR}/xuefeng_err.txt" &
PID_XUEFENG=$!

echo "  进程: Musk(PID=${PID_MUSK})  Xuefeng(PID=${PID_XUEFENG})"
echo "  等待两席发言..."

wait $PID_MUSK
MUSK_EXIT=$?
wait $PID_XUEFENG
XUEFENG_EXIT=$?

echo ""
echo "═══════════════════════════════════════════════════"
echo "  辩论记录已存入: ${OUTDIR}/"
echo "  Musk 发言:   ${OUTDIR}/musk.txt (exit=${MUSK_EXIT})"
echo "  雪峰 发言:   ${OUTDIR}/xuefeng.txt (exit=${XUEFENG_EXIT})"
echo "═══════════════════════════════════════════════════"

# 自动展示摘要
echo ""
echo "▬▬▬▬▬▬ ELON MUSK 发言 (CVO) ▬▬▬▬▬▬"
cat "${OUTDIR}/musk.txt" 2>/dev/null || echo "(发言为空或出错，见 ${OUTDIR}/musk_err.txt)"
echo ""
echo "▬▬▬▬▬▬ 张雪峰 发言 (CSA) ▬▬▬▬▬▬"
cat "${OUTDIR}/xuefeng.txt" 2>/dev/null || echo "(发言为空或出错，见 ${OUTDIR}/xuefeng_err.txt)"

echo ""
echo "═══ 峰会总结 (由峰哥主理) ═══"
echo "请峰哥基于以上两席发言，为陛下做最终总结和决策建议。"
