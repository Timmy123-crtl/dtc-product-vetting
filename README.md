# dtc-product-vetting

一个给 AI agent 用的**独立站选品尽调** skill：把 Kalodata / TikTok Shop 榜单上的热卖品，筛成「能上架、能投广告、能活过四周」的 SKU。

适用于**美国单市场 + 一件代发 + 无品牌无内容团队**这个约束组合。提炼自一次真实的选品项目：67 个候选、8 轮检索、7 轮验证、逐行成本表。

## 它解决什么问题

榜单销量第一的品，通常不是你能做的品。

那次实测里，美国站 GMV TOP20 有 **17 个是品牌直营**；43 个候选里，三个看起来最有机会的品**全部倒在成本表上**——单套 $32.99 的平衡 CPA 只有 **$12.12**，而美国冷流量买不到这么便宜的转化。

所以这套流程的核心不是「找卖得最好的」，而是**用一组前置条件把不可做的品提前枪毙，只对活下来的品花验证成本**。

## 安装

```bash
git clone https://github.com/<your-name>/dtc-product-vetting.git \
  ~/.workbuddy/skills/dtc-product-vetting
```

Windows:

```powershell
git clone https://github.com/<your-name>/dtc-product-vetting.git "$env:USERPROFILE\.workbuddy\skills\dtc-product-vetting"
```

装好后重开会话，skill 会被自动索引。触发方式是在对话里描述任务，例如：

- 「按选品尽调流程，从 Kalodata 美国站筛一批能做独立站的品」
- 「这个品能不能上独立站，帮我算贡献毛利和平衡 CPA」
- 「我的站只卖穿戴甲，要不要把手链加进来」

## 目录结构

```
dtc-product-vetting/
├── SKILL.md                      主入口：3 条铁律 + 7 阶段流程 + 5 条快速判死
├── references/
│   ├── 01-hard-filters.md        9 条硬筛的判据、关键词、淘汰归因
│   ├── 02-data-traps.md          13 个口径陷阱（8 主 + 5 补）
│   ├── 03-validation-rounds.md   六轮外部验证的操作路径与阈值
│   ├── 04-unit-economics.md      成本表行定义、bundle 定价、敏感度、学习期算术
│   └── 05-report-spec.md         报告章节骨架与 A/B/C/D/X 标注体系
├── scripts/
│   ├── contribution_margin.py    变动成本 / 贡献毛利 / 平衡 CPA / 敏感度
│   └── learning_phase.py         按 Meta 学习期口径反推广告预算
└── assets/
    └── report-template.html      单文件 HTML 报告模板（含深浅色）
```

## 七阶段流程

| 阶段 | 做什么 | 产出 |
|---|---|---|
| 0 | 先确认阻塞项（收款通路、代发地址、税负口径） | 阻塞项清单 |
| 1 | 立 9 条硬筛，取数前定稿 | 条件表 |
| 2 | Kalodata 建池，≥40 个唯一品 | 候选池全表 |
| 3 | 六轮外部验证（R1 形态 → R6 站点结构） | 逐轮淘汰记录 |
| 4 | 单位经济 + 敏感度 + 学习期反推 | 成本表 |
| 5 | 收敛为主推 / 备选 / 否决 + Kill 条件 | 结论表 |
| 6 | 按规范输出单文件 HTML | 报告 |

## 脚本用法

### 单位经济

```bash
python scripts/contribution_margin.py \
  --price 45 --cogs 3.20 --qty 3 \
  --packaging 1.40 --labor 0.50 --shipping 5.20 \
  --duty-rate 0.10 --duty-base 12 \
  --payment-pct 0.034 --payment-fixed 0.30 \
  --platform-pct 0.02 --refund-rate 0.08 --cs 0.50 \
  --cogs-high 5.56
```

输出（实测案例，售价 $45 三件套）：

```
变动成本合计                                24.73      55.0%
贡献毛利 / 平衡 CPA                         20.27      45.0%

判定：可做 —— 需要稳定投放能力
可承受的最高获客成本：$20.27/单；超过即亏。
```

带 `--json` 可输出结构化结果，便于串联。

### 广告起步线

```bash
python scripts/learning_phase.py --budget 1000 --days 28 --cpa 15
```

```
预算 $1,000 / 28 天 = $35.71/天
折合 2.4 单/天 = 17 单/周
每品达成率：33% of 50 单/周
结论：不足以退出学习期，缺约 33 单/周，需追加预算约 $2,000（同期 28 天）
这一档预算的作用是「测 CPA 能不能压到目标值」，不是「跑通」。
```

这个数很多人没算过：**Meta 学习期门槛是每个广告组 7 天约 50 个优化事件**，$1,000 的测试预算通常连三分之一都不到。先把这个数摆到桌面上，能省掉后面很多误判。

`--products 2` 可以算同站双品类并行时的分摊。

## 五条快速判死

不用走完整流程，这五条能砍掉大部分工时：

1. 单件平衡 CPA < $12 → 死
2. 对标 Walmart 现货溢价 > 3 倍且无组合/定制差异 → 死
3. 货源价带「新客专享」标签 → 该价不得进成本表
4. 品类词在 Trends 接近基线 → 没有自然需求
5. 品类头部由「带电 + 品牌」构成 → 一件代发进不去

## 依赖与边界

- 数据源需要账号：Kalodata（付费或试用，约 30 次/天）、SimilarWeb Pro、Google Trends（免费）、Meta 广告资料库（免费）、Walmart / AliExpress（公开页面）
- 价格锚、税率、合规口径全部针对**美国市场**，换市场需重做 R4–R6
- 流程假设零库存，不适用于备货模式
- 报告里的区间值与占位值必须逐行标注，未取得项不进入结论

## License

MIT
