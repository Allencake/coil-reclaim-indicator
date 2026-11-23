# 数据包字段：`coil-reclaim/v1`

指标在K线收盘时用 `alert()` 发出一个扁平的 JSON 对象，一个事件一个包。没有值的字段是 `null`，价格按品种最小跳动取整。示例见 [`examples/sample_packet.json`](../examples/sample_packet.json)（示例数字，不是真实行情）。

## 事件 `event`

| 值 | 什么时候发 | Agent 该做什么 |
|---|---|---|
| `SESSION_BIAS` | 每个开启的时段首小时第一根K线 | 说出今天这段只做多、只做空还是不做 |
| `STOP_ORDER_PLACED` | 突破K线收在区间外，且所有检查都过了 | 按方向 → 区域 → 触发复核，给 LONG / SHORT / SKIP |
| `STOP_ORDER_CANCELLED` | 没先回踩就突破、收回区间里、挂单过期 | SKIP，原因在 `note` |
| `ENTRY` | 回踩之后挂单成交 | 确认止损、1R、目标和仓位 |
| `BREAKEVEN` | 到 1R，或 1R 之前碰到价位 | 止损挪到进场价，按规则平一部分 |
| `TOO_FAST_TAKE_PROFIT` | 浮盈 ≥ 1.5R 且连续 3 根同向 | 建议止盈（后面跟一个 `EXIT`） |
| `EXIT` | 止损、保本、目标、走太快、到时间 | 报告 `result_r` |
| `BAR_CLOSE` | 只在「每根收盘」模式下，没有别的事件的K线 | 只当背景 |

## 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `schema` | string | 固定 `coil-reclaim/v1` |
| `event` | string | 见上表 |
| `tag` | string | 指标设置里的「数据包标签」，多张图时用来区分 |
| `symbol` | string | 交易所前缀加代码，如 `BINANCE:BTCUSDT.P` |
| `timeframe` | string | 图表周期，如 `15` |
| `ts` | string | K线收盘时间，ISO 8601，UTC |
| `price` | number | 这根K线收盘价 |
| `session` | string | `Asia` / `London` / `NYSE`（最近开始的那个时段） |
| `session_live` | bool | 现在是否在首小时窗口内 |
| `session_trades` / `max_trades` | int | 本时段已成交笔数 / 上限 |
| `bias` | string | `BUY` / `SELL` / `NONE`，时段第一根K线定下，整段不变 |
| `daily_candle` | string | 昨天日线：`UP` / `DOWN` / `FLAT` |
| `h4_candle` | string | 时段开始前最后一根已收盘 4 小时K线：`UP` / `DOWN` / `FLAT` |
| `staircase` | string | `UP`（高点低点都抬高）/ `DOWN` / `BOX` / `UNKNOWN` |
| `staircase_tf` | string | `weekly`；周线数据不够时用 `daily` |
| `bias_reason` | string | 方向的理由，如 `两根同色`、`颜色不一致 → 周线台阶向上` |
| `mode` | string | `BREAKOUT`；盘前 4 小时已经顺方向走完时为 `PULLBACK` |
| `daily_ceiling` / `daily_floor` | number/null | 价格上方最近的未破日线天花板 / 下方最近的未破日线地板 |
| `position_pct` | number/null | 价格在地板和天花板之间的位置，0 = 地板，100 = 天花板 |
| `at_daily_ceiling` / `at_daily_floor` | bool | 价格贴着日线价位（0.25 倍日线 ATR 以内，或盘中穿过但日线没收破） |
| `blocked_today` | bool | 顺方向顶到日线价位，今天不再做这个方向 |
| `in_clean_zone` | bool | 当前价格在有效干净区里 |
| `next_ceiling` / `next_floor` | number/null | 上方 / 下方最近的未破价位（日线、4 小时、1 小时任一） |
| `side` | string | 当前或最近一笔：`LONG` / `SHORT` / `NONE` |
| `range_top` / `range_bottom` | number/null | 区间，按K线实体算 |
| `range_candles` | int/null | 区间K线数 |
| `liquidity_grab` | bool | 区间里有K线刺破更早的低点（做空看高点）又收回来 |
| `breakout_in_clean_zone` | bool | 突破K线的高点（做空看低点）在干净区里 |
| `breakout_high` / `breakout_low` | number/null | 突破K线高低点 |
| `rubber_band` | bool | 突破后已经回踩过（橡皮筋） |
| `order_price` | number/null | 挂单价：做多 = 突破K线高点，做空 = 低点 |
| `order_expires_after` | int | 挂单几根K线后作废 |
| `status` | string | `FLAT` / `ORDER_WORKING` / `OPEN` / `CANCELLED` / `CLOSED` |
| `entry` | number/null | 成交价 |
| `stop` | number/null | 当前止损；挂单中是计划止损，保本后等于 `entry` |
| `take_profit_1r` | number/null | 1R 价位 |
| `target` | number/null | 最终目标 |
| `target_source` | string | 目标是什么：`日线天花板`、`4小时地板`、`3R封顶 · 前面没价位`、`1:1` |
| `breakeven` | bool | 止损是否已在进场价 |
| `close_pct_at_1r` | number | 1R 平仓比例（「只做1:1」模式为 0） |
| `open_r` | number/null | 浮动盈亏，单位 R |
| `exit_price` / `result_r` | number/null | 出场价 / 整笔结果（含 1R 部分平仓），单位 R |
| `risk_pct` | number | 设置里的每笔风险 %，给 Agent 算仓位 |
| `note` | string | 挂单、取消、保本或出场的原因 |
