#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变动成本、贡献毛利与盈亏平衡 CPA 计算器。

用于 DTC 选品尽调的第 7 轮：把前六轮的结论压成一张成本表，
输出贡献毛利（= 盈亏平衡 CPA）与四档敏感度。

示例
----
python contribution_margin.py --price 45 --cogs 3.20 --qty 3 \
    --packaging 1.40 --labor 0.50 --shipping 5.20 \
    --duty-rate 0.10 --duty-base 12 \
    --payment-pct 0.034 --payment-fixed 0.30 \
    --platform-pct 0.02 --refund-rate 0.08 --cs 0.50

全部参数默认按「美国单市场、一件代发、第三方支付通道」的常见值预设，
只需覆盖实际拿到的数字。
"""

import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_rows(a):
    """按成本表顺序返回 [(项目, 金额, 依据)]。"""
    cogs_total = a.cogs * a.qty
    duty = a.duty_base * a.duty_rate
    payment = a.price * a.payment_pct + a.payment_fixed
    platform = a.price * a.platform_pct
    refund = a.price * a.refund_rate

    rows = [
        (f"货品 {a.qty} 件 x ${a.cogs:.2f}", cogs_total, "货源实价区间中偏上，不含新客价"),
        ("包装（礼盒/贺卡/内袋）", a.packaging, "同类包装报价区间"),
        ("组装 / 贴标人工", a.labor, "分钟数 x 时薪折算，不可写 0"),
        ("头程 / 直发运费", a.shipping, "含跟踪号，需货代报价替换"),
        (f"关税（申报 ${a.duty_base:.2f} x {a.duty_rate:.0%}）", duty, "税率未取得时用占位值并做敏感度"),
        (f"支付手续费 {a.payment_pct:.1%} + ${a.payment_fixed:.2f}", payment, "按通道实际费率"),
        (f"平台交易费 {a.platform_pct:.1%}", platform, "第三方支付附加费"),
        (f"退款 / 损耗 {a.refund_rate:.0%}", refund, "品类经验值，上线后换实测"),
        ("客服（按单摊）", a.cs, "工时 x 时薪 / 单量"),
    ]
    return rows


def summarize(rows, price):
    total = sum(r[1] for r in rows)
    margin = price - total
    pct = margin / price if price else 0.0
    return total, margin, pct


def verdict(margin):
    if margin < 12:
        return "死", "美国冷流量买不到这么便宜的转化"
    if margin < 18:
        return "高风险", "只有在素材极强时可行"
    if margin < 25:
        return "可做", "需要稳定投放能力"
    return "好", "可承受测试成本"


def scenario_rows(a, base_total):
    """返回 [(情景名, 新变动成本, 新售价)]。

    售价变动的情景必须同时返回新售价，否则贡献毛利会错用原价。
    """
    out = []

    # 物流上浮 50%
    out.append(("物流 +50%", base_total + a.shipping * 0.5, a.price))
    # 关税翻倍
    out.append(("关税翻倍", base_total + a.duty_base * a.duty_rate, a.price))
    # 退款率翻倍
    out.append((f"退款率 {a.refund_rate:.0%}→{a.refund_rate * 2:.0%}",
                base_total + a.price * a.refund_rate, a.price))
    # 售价下调 10%（支付/平台/退款按比例的部分同步下降）
    new_price = a.price * 0.9
    pct_share = a.payment_pct + a.platform_pct + a.refund_rate
    out.append((f"售价降至 ${new_price:.2f}",
                base_total - a.price * pct_share * 0.1, new_price))
    # 货品取上界
    if a.cogs_high and a.cogs_high > a.cogs:
        out.append((f"货品取上界 ${a.cogs_high:.2f}",
                    base_total + (a.cogs_high - a.cogs) * a.qty, a.price))
    return out


def _w(s):
    """按终端显示宽度计长（CJK 算 2 列）。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _pad(s, width, align="left"):
    gap = max(0, width - _w(s))
    return s + " " * gap if align == "left" else " " * gap + s


def render(a):
    rows = build_rows(a)
    total, margin, pct = summarize(rows, a.price)
    tag, why = verdict(margin)

    W1, W2, W3 = 38, 11, 11
    bar = "=" * (W1 + W2 + W3)

    print(bar)
    print(f"单位经济  |  售价 ${a.price:.2f}  |  {a.qty} 件装")
    print(bar)
    print(_pad("成本项", W1) + _pad("金额", W2, "right") + _pad("占售价", W3, "right"))
    print("-" * len(bar))
    for name, amt, _ in rows:
        share = amt / a.price if a.price else 0
        print(_pad(name, W1) + _pad(f"{amt:.2f}", W2, "right") + _pad(f"{share:.1%}", W3, "right"))
    print("-" * len(bar))
    print(_pad("变动成本合计", W1) + _pad(f"{total:.2f}", W2, "right")
          + _pad(f"{total / a.price:.1%}", W3, "right"))
    print(_pad("贡献毛利 / 平衡 CPA", W1) + _pad(f"{margin:.2f}", W2, "right")
          + _pad(f"{pct:.1%}", W3, "right"))
    print(f"\n判定：{tag} —— {why}")
    print(f"可承受的最高获客成本：${margin:.2f}/单；超过即亏。")

    W1b, W2b, W3b, W4b = 30, 11, 11, 11
    bar2 = "=" * (W1b + W2b + W3b + W4b)
    print("\n" + bar2)
    print("敏感度")
    print(bar2)
    print(_pad("情景", W1b) + _pad("变动成本", W2b, "right")
          + _pad("贡献毛利", W3b, "right") + _pad("较基准", W4b, "right"))
    print("-" * len(bar2))
    print(_pad("基准", W1b) + _pad(f"{total:.2f}", W2b, "right")
          + _pad(f"{margin:.2f}", W3b, "right") + _pad("—", W4b, "right"))
    worst = None
    for name, new_total, new_price in scenario_rows(a, total):
        m = new_price - new_total
        delta = m - margin
        print(_pad(name, W1b) + _pad(f"{new_total:.2f}", W2b, "right")
              + _pad(f"{m:.2f}", W3b, "right") + _pad(f"{delta:+.2f}", W4b, "right"))
        if worst is None or m < worst[1]:
            worst = (name, m)
    print("-" * len(bar2))
    print(f"最危险的一行：{worst[0]} → 贡献毛利 ${worst[1]:.2f}")
    print("这一行对应的数字，去问供应商或货代拿实数。再查榜单不会让它变准。")


def main():
    p = argparse.ArgumentParser(description="计算变动成本、贡献毛利与平衡 CPA")
    p.add_argument("--price", type=float, required=True, help="售价（美元）")
    p.add_argument("--cogs", type=float, required=True, help="单件货品成本（不带新客价）")
    p.add_argument("--qty", type=int, default=1, help="每单件数，默认 1")
    p.add_argument("--packaging", type=float, default=1.20, help="包装成本，默认 1.20")
    p.add_argument("--labor", type=float, default=0.50, help="组装人工，默认 0.50")
    p.add_argument("--shipping", type=float, default=5.20, help="直发运费，默认 5.20")
    p.add_argument("--duty-rate", type=float, default=0.10, help="关税税率，默认 0.10")
    p.add_argument("--duty-base", type=float, default=None,
                   help="申报价值，默认取货品+包装")
    p.add_argument("--payment-pct", type=float, default=0.034, help="支付费率，默认 3.4%%")
    p.add_argument("--payment-fixed", type=float, default=0.30, help="支付固定费，默认 0.30")
    p.add_argument("--platform-pct", type=float, default=0.02, help="平台费，默认 2%%")
    p.add_argument("--refund-rate", type=float, default=0.08, help="退款率，默认 8%%")
    p.add_argument("--cs", type=float, default=0.50, help="客服摊销，默认 0.50")
    p.add_argument("--cogs-high", type=float, default=None, help="货品成本上界，用于敏感度")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    a = p.parse_args()

    if a.duty_base is None:
        a.duty_base = a.cogs * a.qty + a.packaging

    if a.json:
        rows = build_rows(a)
        total, margin, pct = summarize(rows, a.price)
        print(json.dumps({
            "price": a.price,
            "rows": [{"item": n, "amount": round(v, 2)} for n, v, _ in rows],
            "variable_cost": round(total, 2),
            "contribution_margin": round(margin, 2),
            "contribution_margin_pct": round(pct, 4),
            "verdict": verdict(margin)[0],
            "scenarios": [
                {"name": n, "variable_cost": round(t, 2),
                 "contribution_margin": round(a.price - t, 2)}
                for n, t, _p in scenario_rows(a, total)
            ],
        }, ensure_ascii=False, indent=2))
        return

    render(a)


if __name__ == "__main__":
    main()
