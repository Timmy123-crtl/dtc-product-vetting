#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""广告起步线反推：退出 Meta 学习期需要多少预算。

Meta 官方口径：广告组需在 7 天内累积约 50 个优化事件才能退出学习期。
本脚本回答三个问题：
  1. 给定总预算与 CPA，每周能积累多少事件、够不够退出学习期
  2. 要退出学习期，最少需要多少日预算 / 总预算
  3. 若同站同时推 N 个品，预算是否够分摊

示例
----
python learning_phase.py --budget 1000 --days 28 --cpa 15
python learning_phase.py --budget 1000 --days 28 --cpa 15 --products 2
python learning_phase.py --weekly-orders 50 --cpa 15
"""

import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TARGET_EVENTS = 50  # 每个广告组 / 7 天


def main():
    p = argparse.ArgumentParser(description="按 Meta 学习期口径反推广告预算")
    p.add_argument("--budget", type=float, help="测试总预算（美元）")
    p.add_argument("--days", type=int, default=28, help="测试天数，默认 28")
    p.add_argument("--cpa", type=float, required=True, help="预期获客成本（美元）")
    p.add_argument("--margin", type=float, default=None,
                   help="贡献毛利，用于判断 CPA 是否已经超过可承受上限")
    p.add_argument("--products", type=int, default=1, help="同站同时推的品数，默认 1")
    p.add_argument("--weekly-orders", type=float, default=None,
                   help="反向模式：已知目标周订单数，求所需预算")
    a = p.parse_args()

    print("=" * 60)
    print("Meta 学习期反推  |  门槛：7 天内约 50 个优化事件/广告组")
    print("=" * 60)

    if a.margin is not None:
        if a.cpa >= a.margin:
            print(f"警告：CPA ${a.cpa:.2f} >= 贡献毛利 ${a.margin:.2f}，每单亏损 "
                  f"${a.cpa - a.margin:.2f}。测试可以，但不要放量。")
        else:
            print(f"单笔净利：${a.margin - a.cpa:.2f}（毛利 ${a.margin:.2f} - CPA ${a.cpa:.2f}）")

    if a.budget:
        daily = a.budget / a.days
        per_day_orders = daily / a.cpa
        per_week = per_day_orders * 7
        need_per_product = TARGET_EVENTS / a.products
        print(f"\n预算 ${a.budget:,.0f} / {a.days} 天 = ${daily:,.2f}/天")
        print(f"折合 {per_day_orders:.1f} 单/天 = {per_week:.0f} 单/周")
        if a.products > 1:
            split = per_week / a.products
            print(f"分给 {a.products} 个品：每品 {split:.0f} 单/周（门槛 {TARGET_EVENTS}）")
            effective = split
        else:
            effective = per_week
        ratio = effective / TARGET_EVENTS
        print(f"每品达成率：{ratio:.0%} of {TARGET_EVENTS} 单/周")
        if ratio >= 1:
            print("结论：预算足以让单个广告组退出学习期。")
        else:
            gap_orders = TARGET_EVENTS - effective
            gap_money = (TARGET_EVENTS / 7) * a.cpa * a.days * a.products - a.budget
            print(f"结论：不足以退出学习期，每品缺约 {gap_orders:.0f} 单/周，"
                  f"需追加预算约 ${gap_money:,.0f}（同期 {a.days} 天）")
            print("这一档预算的作用是「测 CPA 能不能压到目标值」，不是「跑通」。")

    if a.weekly_orders:
        daily_orders = a.weekly_orders / 7
        daily_budget = daily_orders * a.cpa
        print(f"\n目标 {a.weekly_orders:.0f} 单/周 = {daily_orders:.1f} 单/天")
        print(f"所需日预算：${daily_budget:,.2f}")
        print(f"14 天（一个学习期）：${daily_budget * 14:,.0f}")
        print(f"28 天（含验证期）：${daily_budget * 28:,.0f}")
        if a.products > 1:
            print(f"若 {a.products} 个品并行：总日预算需 ${daily_budget * a.products:,.2f}")

    print("\n提醒：预算只决定「能不能积累够事件」，不决定「能不能赚钱」。"
          "后者由 CPA 与贡献毛利的关系决定。")


if __name__ == "__main__":
    main()
