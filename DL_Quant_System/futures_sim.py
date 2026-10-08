# -*- coding: utf-8 -*-
"""期货高频沙盘 · 模拟交易引擎与实时行情 v2

功能模块：
1. 实时行情：AkShare 新浪快照（含真实买一/卖一对价、昨结）→ 分钟K线兜底 → 本地随机游走模拟兜底
2. 模拟账户：开多/开空/平仓/反手；对价/超价/市价/限价四种下单方式；持仓分笔(FIFO)；
   保证金与资金校验；手续费；滑点；止盈止损；条件单（埋单）；限价挂单撮合；模拟强平；
   出入金；成交记录；资金曲线；交易统计
3. 策略桥：复用全局 generated_code，经 strategy_sandbox 执行后驱动自动交易（含冷却）
4. 账户持久化：本地 JSON 落盘（保存/载入），供重启后恢复模拟盘

注意：本模块全部为模拟撮合，不接入任何实盘交易接口。
"""

import json
import math
import os
import random
import time
from datetime import datetime

# ============================================================
# 品种参数表（与期货全量审计页保持一致）
# ============================================================
DEFAULT_MULT = {
    'SA': 20, 'RB': 10, 'I': 100, 'HC': 10, 'FG': 20, 'V': 5, 'P': 10, 'M': 10,
    'Y': 10, 'C': 10, 'CS': 10, 'JD': 10, 'CU': 5, 'AL': 5, 'ZN': 5, 'NI': 1,
    'AU': 1000, 'AG': 15, 'RU': 10, 'TA': 5, 'MA': 10, 'CF': 5, 'SR': 10,
    'OI': 10, 'RM': 10, 'ZC': 100, 'JM': 60, 'J': 100, 'UR': 20,
}
DEFAULT_BASE_PRICE = {
    'SA': 1500, 'RB': 3300, 'I': 800, 'HC': 3500, 'FG': 1200, 'V': 6000,
    'P': 8000, 'M': 3000, 'Y': 8000, 'C': 2400, 'CS': 2800, 'JD': 3500,
    'CU': 70000, 'AL': 20000, 'ZN': 23000, 'NI': 130000, 'AU': 600, 'AG': 7000,
    'RU': 13000, 'TA': 5000, 'MA': 2500, 'CF': 14000, 'SR': 5500, 'OI': 8000,
    'RM': 2500, 'ZC': 800, 'JM': 1300, 'J': 2000, 'UR': 1800,
}

_SIM_STATE = {}    # 模拟行情：symbol -> {'price': float, 'rng': Random}
_DEPTH_STATE = {}  # 五档盘口演化：symbol -> {'asks_v': [...], 'bids_v': [...], 'mid': float, 't': float}
_TAPE_STATE = {}   # 模拟逐笔成交：symbol -> list[dict]


def normalize_symbol(sym):
    """规范化合约代码：大写去空白，空则默认 SA0。"""
    s = str(sym or '').strip().upper().replace(' ', '')
    return s if s else 'SA0'


def symbol_letters(symbol):
    """提取品种字母部分（如 SA2409 -> SA）。"""
    s = normalize_symbol(symbol)
    letters = ''
    for ch in s:
        if ch.isalpha():
            letters += ch
        else:
            break
    return letters


def continuous_symbol(symbol):
    """转为连续合约代码（SA2409 -> SA0；已是 SA0 则原样）。"""
    letters = symbol_letters(symbol)
    return (letters + '0') if letters else normalize_symbol(symbol)


# ============================================================
# 实时行情
# ============================================================
def fetch_live_quote(ak, symbol, force_sim=False):
    """获取实时报价。返回 dict：
    {symbol, price, bid, ask, last_close, change, pct, time, volume, hold, source, err}
    source: 'live' 新浪快照 / 'minute' 分钟K线兜底 / 'sim' 随机模拟
    """
    symbol = normalize_symbol(symbol)
    quote = {'symbol': symbol, 'price': 0.0, 'bid': 0.0, 'ask': 0.0,
             'last_close': 0.0, 'change': 0.0, 'pct': 0.0,
             'time': '', 'volume': 0.0, 'hold': 0.0, 'source': 'sim', 'err': ''}

    if ak is not None and not force_sim:
        # 1) 新浪实时快照（含买一/卖一，即"对价"）
        for code in (symbol, continuous_symbol(symbol)):
            try:
                df = ak.futures_zh_spot(symbol=code)
                if df is not None and not df.empty:
                    row = df.iloc[-1]
                    price = float(row.get('current_price') or 0)
                    bid = float(row.get('bid_price') or 0)
                    ask = float(row.get('ask_price') or 0)
                    last_close = float(row.get('last_close') or 0)
                    if price <= 0:
                        price = float(row.get('avg_price') or last_close or 0)
                    if price <= 0:
                        price = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else 0
                    if bid <= 0:
                        bid = price
                    if ask <= 0:
                        ask = price
                    if price <= 0:
                        continue
                    change = price - last_close if last_close > 0 else 0.0
                    pct = change / last_close * 100.0 if last_close > 0 else 0.0
                    t = str(row.get('time') or '')
                    if len(t) == 6:
                        t = f"{t[:2]}:{t[2:4]}:{t[4:]}"
                    quote.update({'price': round(price, 2), 'bid': round(bid, 2),
                                  'ask': round(ask, 2), 'last_close': round(last_close, 2),
                                  'change': round(change, 2), 'pct': round(pct, 2),
                                  'time': t,
                                  'volume': float(row.get('volume') or 0),
                                  'hold': float(row.get('hold') or 0),
                                  'source': 'live'})
                    return quote
            except Exception as exc:
                quote['err'] = str(exc)[:120]

        # 2) 分钟K线兜底（取最后一根收盘价，买卖价按最小价位合成）
        try:
            bars = ak.futures_zh_minute_sina(symbol=symbol, period='1')
            if bars is None or bars.empty:
                cont = continuous_symbol(symbol)
                if cont != symbol:
                    bars = ak.futures_zh_minute_sina(symbol=cont, period='1')
            if bars is not None and not bars.empty:
                last = bars.iloc[-1]
                price = float(last['close'])
                prev_close = float(bars.iloc[-2]['close']) if len(bars) >= 2 else price
                change = price - prev_close
                pct = change / prev_close * 100.0 if prev_close else 0.0
                t = str(last.get('datetime', ''))
                t = t[11:19] if len(t) >= 19 else t
                quote.update({'price': round(price, 2), 'bid': round(price - 1, 2),
                              'ask': round(price + 1, 2), 'last_close': round(prev_close, 2),
                              'change': round(change, 2), 'pct': round(pct, 2),
                              'time': t,
                              'volume': float(last.get('volume') or 0),
                              'hold': float(last.get('hold') or 0),
                              'source': 'minute'})
                return quote
        except Exception as exc:
            quote['err'] = str(exc)[:120]

    # 3) 随机游走模拟兜底（休市/断网也能玩）
    state = _SIM_STATE.get(symbol)
    if state is None:
        base = DEFAULT_BASE_PRICE.get(symbol_letters(symbol), 2000.0)
        state = {'price': base, 'rng': random.Random(abs(hash(symbol)) % 10 ** 9),
                 'prev': base}
        _SIM_STATE[symbol] = state
    state['prev'] = state['price']
    step = state['rng'].choice([-3, -2, -1, 0, 1, 2, 3])
    state['price'] = max(1.0, state['price'] + step)
    change = state['price'] - state['prev']
    pct = change / state['prev'] * 100.0 if state['prev'] else 0.0
    quote.update({'price': round(state['price'], 1), 'bid': round(state['price'] - 1, 1),
                  'ask': round(state['price'] + 1, 1),
                  'last_close': round(state['prev'], 1),
                  'change': round(change, 1), 'pct': round(pct, 2),
                  'time': datetime.now().strftime('%H:%M:%S'), 'source': 'sim'})
    return quote


def build_depth(quote, tick=1.0, levels=5):
    """由一档买卖价合成五档盘口（盘口量平滑演化，不闪烁）。
    返回 (asks, bids)：list[(price, volume)]。"""
    symbol = quote.get('symbol', 'X')
    price = float(quote.get('price') or 0)
    bid1 = float(quote.get('bid') or 0)
    ask1 = float(quote.get('ask') or 0)
    tick = max(float(tick) or 0.01, 0.01)
    if bid1 <= 0:
        bid1 = price - tick
    if ask1 <= 0:
        ask1 = price + tick
    if ask1 <= bid1:
        ask1 = bid1 + tick
    now = time.time()
    mid = (bid1 + ask1) / 2.0
    st = _DEPTH_STATE.get(symbol)
    if st is None or now - st.get('t', 0) > 30 or abs(st.get('mid', 0) - mid) > 3 * tick:
        rng = random.Random(int(mid * 100) + int(now // 10))
        st = _DEPTH_STATE[symbol] = {
            'asks_v': [rng.randint(10, 500) for _ in range(levels)],
            'bids_v': [rng.randint(10, 500) for _ in range(levels)],
            'mid': mid, 't': now,
        }
    else:
        rng = random.Random(int(now * 1000))
        for lst in ('asks_v', 'bids_v'):
            for i in range(len(st[lst])):
                st[lst][i] = max(5, min(2000, st[lst][i] + rng.randint(-30, 30)))
        st['t'] = now
        st['mid'] = mid
    asks = [(round(ask1 + i * tick, 2), st['asks_v'][i]) for i in range(levels)]
    bids = [(round(bid1 - i * tick, 2), st['bids_v'][i]) for i in range(levels)]
    return asks, bids


def gen_tape(quote, n=6):
    """生成模拟逐笔成交明细（Time & Sales），返回最近 n 条（最新在前）。"""
    symbol = quote.get('symbol', 'X')
    price = float(quote.get('price') or 0)
    bid = float(quote.get('bid') or price)
    ask = float(quote.get('ask') or price)
    if price <= 0:
        return []
    tape = _TAPE_STATE.setdefault(symbol, [])
    rng = random.Random(int(time.time() * 1000))
    for _ in range(n):
        is_buy = rng.random() < 0.5
        px = ask if is_buy else bid
        tape.append({'time': datetime.now().strftime('%H:%M:%S'),
                     'price': round(px, 2), 'vol': rng.randint(1, 30),
                     'side': 'B' if is_buy else 'S'})
    if len(tape) > 200:
        tape = tape[-200:]
    _TAPE_STATE[symbol] = tape
    return list(reversed(tape[-n:]))


def fetch_minute_bars(ak, symbol, period='1', limit=2000):
    """取分钟K线，重命名为 Open/High/Low/Close/Volume + trade_date（升序）。
    period: '1'/'5'/'15'/'30'/'60'。limit 上限 2000（新浪接口实际最多返回约 1024 根，
    1分钟≈4.5个交易日、5分钟≈21个交易日、60分钟≈半年）。失败返回 None。"""
    symbol = normalize_symbol(symbol)
    if ak is None:
        return None
    try:
        df = ak.futures_zh_minute_sina(symbol=symbol, period=str(period))
    except Exception:
        return None
    if df is None or df.empty:
        try:
            cont = continuous_symbol(symbol)
            if cont != symbol:
                df = ak.futures_zh_minute_sina(symbol=cont, period=str(period))
        except Exception:
            return None
    if df is None or df.empty:
        return None
    import pandas as pd
    out = df.copy()
    out['trade_date'] = pd.to_datetime(out['datetime'], errors='coerce')
    out = out.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low',
                              'close': 'Close', 'volume': 'Volume'})
    out = out[['trade_date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    out = out.dropna(subset=['trade_date'])
    return out.tail(limit).reset_index(drop=True)


def merge_tick(bars_df, quote):
    """把最新报价合入K线：同一分钟更新最后一根的 Close/High/Low，否则追加新K线。
    若最后一根K线距当前超过 20 小时（休市/假期），不续接，避免图上出现远期假K线。"""
    import pandas as pd
    q = float(quote.get('price') or 0)
    if q <= 0:
        return bars_df
    if bars_df is None or bars_df.empty:
        now = pd.Timestamp.now()
        return pd.DataFrame([{'trade_date': now, 'Open': q, 'High': q,
                              'Low': q, 'Close': q, 'Volume': 0.0}])
    df = bars_df.copy()
    last = df.iloc[-1]
    last_min = pd.to_datetime(last['trade_date']).floor('min')
    now_min = pd.Timestamp.now().floor('min')
    if (now_min - last_min).total_seconds() > 72000:
        return df
    if last_min == now_min:
        idx = df.index[-1]
        df.at[idx, 'Close'] = q
        df.at[idx, 'High'] = max(float(last['High']), q)
        df.at[idx, 'Low'] = min(float(last['Low']), q)
    else:
        prev_close = float(last['Close'])
        row = pd.DataFrame([{'trade_date': now_min, 'Open': prev_close,
                             'High': max(prev_close, q), 'Low': min(prev_close, q),
                             'Close': q, 'Volume': float(quote.get('volume') or 0)}])
        df = pd.concat([df, row], ignore_index=True)
    return df


# ============================================================
# 模拟账户
# ============================================================
class SimAccount:
    """单合约期货模拟账户（内存态，支持 JSON 落盘）。

    约定：
    - position > 0 持多，< 0 持空，0 空仓；持仓按 lots_entries 分笔记录（FIFO）
    - balance（静态权益）= 初始资金 + 已实现盈亏 + 出入金 - 累计手续费
    - equity（动态权益）  = balance + 浮动盈亏
    - available（可用）    = balance - 占用保证金
    """

    def __init__(self, symbol='SA0', initial_cash=1000000.0, multiplier=20.0,
                 margin_rate=0.12, commission_rate=0.0001, slippage=0.0,
                 tick_size=1.0):
        self.symbol = normalize_symbol(symbol)
        self.initial_cash = float(initial_cash)
        self.balance = float(initial_cash)
        self.multiplier = float(multiplier)
        self.margin_rate = float(margin_rate)
        self.commission_rate = float(commission_rate)
        self.slippage = float(slippage)
        self.tick_size = float(tick_size)
        self.position = 0
        self.avg_price = 0.0
        self.last_price = 0.0
        self.realized_pnl = 0.0
        self.total_fee = 0.0
        self.lots_entries = []   # 持仓分笔 [{side, lots, price, time}]
        self.trades = []         # 成交/资金记录 [{time, action, lots, price, fee, pnl}]
        self.pending = []        # 限价挂单 [{idx, time, side, lots, price}]
        self.conditionals = []   # 条件单 [{idx, time, side, cond, trigger, lots}]
        self.equity_curve = []   # [(time_str, equity)]
        self.sl_price = None
        self.tp_price = None
        self.last_auto_time = 0.0
        self.last_error = ''
        self._order_idx = 0

    # ---------------- 分笔与指标 ----------------
    def _recompute_position(self):
        long_lots = sum(e['lots'] for e in self.lots_entries if e['side'] > 0)
        short_lots = sum(e['lots'] for e in self.lots_entries if e['side'] < 0)
        self.position = long_lots - short_lots
        if self.position > 0:
            self.avg_price = (sum(e['lots'] * e['price'] for e in self.lots_entries
                                  if e['side'] > 0) / long_lots)
        elif self.position < 0:
            self.avg_price = (sum(e['lots'] * e['price'] for e in self.lots_entries
                                  if e['side'] < 0) / short_lots)
        else:
            self.avg_price = 0.0

    def long_lots(self):
        return sum(e['lots'] for e in self.lots_entries if e['side'] > 0)

    def short_lots(self):
        return sum(e['lots'] for e in self.lots_entries if e['side'] < 0)

    def floating_pnl(self):
        if not self.lots_entries or self.last_price <= 0:
            return 0.0
        return sum((self.last_price - e['price']) * e['side'] * e['lots'] * self.multiplier
                   for e in self.lots_entries)

    def margin_used(self):
        if self.position == 0:
            return 0.0
        px = self.last_price if self.last_price > 0 else self.avg_price
        return abs(self.position) * px * self.multiplier * self.margin_rate

    def equity(self):
        return self.balance + self.floating_pnl()

    def available(self):
        return self.balance - self.margin_used()

    def risk_ratio(self):
        eq = self.equity()
        if eq <= 0:
            return 999.9
        return self.margin_used() / eq * 100.0

    def stats(self):
        """交易统计：胜率、盈亏比、平均盈亏、最大回撤等。"""
        closes = [t for t in self.trades if t['action'] in ('平多', '平空') and t['pnl'] != 0]
        wins = [t['pnl'] for t in closes if t['pnl'] > 0]
        losses = [t['pnl'] for t in closes if t['pnl'] < 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (
            999.0 if gross_win > 0 else 0.0)
        peak, max_dd = -float('inf'), 0.0
        for _, eq in self.equity_curve:
            peak = max(peak, eq)
            if peak > 0:
                max_dd = max(max_dd, (peak - eq) / peak)
        return {
            'trades': len(closes),
            'win_rate': len(wins) / len(closes) if closes else 0.0,
            'profit_factor': profit_factor,
            'avg_win': gross_win / len(wins) if wins else 0.0,
            'avg_loss': gross_loss / len(losses) if losses else 0.0,
            'gross_win': gross_win,
            'gross_loss': -gross_loss,
            'max_dd': max_dd,
        }

    # ---------------- 行情与撮合 ----------------
    def mark(self, price):
        self.last_price = float(price)
        now = datetime.now().strftime('%H:%M:%S')
        if not self.equity_curve or now != self.equity_curve[-1][0]:
            self.equity_curve.append((now, round(self.equity(), 2)))
            if len(self.equity_curve) > 3000:
                self.equity_curve = self.equity_curve[-3000:]

    def _fee(self, price, lots):
        return round(price * lots * self.multiplier * self.commission_rate, 2)

    def _log(self, action, lots, price, fee, pnl):
        self.trades.append({'time': datetime.now().strftime('%H:%M:%S'),
                            'action': action, 'lots': lots,
                            'price': round(price, 2), 'fee': fee, 'pnl': pnl})
        if len(self.trades) > 600:
            self.trades = self.trades[-600:]

    def check_margin(self, side, lots, ref_price):
        """净开仓保证金预检。返回 (ok, msg)。"""
        lots = int(lots)
        if lots <= 0 or ref_price <= 0:
            return False, '手数/价格无效'
        new_abs = abs(self.position + lots) if side == 'buy' else abs(self.position - lots)
        if new_abs <= abs(self.position):
            return True, ''
        needed = new_abs * ref_price * self.multiplier * self.margin_rate
        avail = self.available()
        if needed > avail + 1e-6:
            return False, (f'保证金不足：需约 {needed:,.0f}，可用 {avail:,.0f}'
                           f'（{abs(self.position)}手已占用 {self.margin_used():,.0f}）')
        return True, ''

    def _execute(self, side, lots, fill_price):
        """撮合一笔成交：side='buy'/'sell'，lots 手 @ fill_price。
        平反向仓按 FIFO 逐笔实现盈亏，剩余手数同向开仓。返回 (ok, msg)。"""
        lots = int(lots)
        if lots <= 0 or fill_price <= 0:
            return False, '手数/成交价无效'
        fee_total = self._fee(fill_price, lots)
        parts = []
        remain = lots

        if side == 'buy':
            closes = [e for e in self.lots_entries if e['side'] < 0]
            act = '平空'
        else:
            closes = [e for e in self.lots_entries if e['side'] > 0]
            act = '平多'
        for e in closes:
            if remain <= 0:
                break
            take = min(remain, e['lots'])
            if side == 'buy':
                pnl = (e['price'] - fill_price) * take * self.multiplier
            else:
                pnl = (fill_price - e['price']) * take * self.multiplier
            parts.append((act, take, pnl))
            e['lots'] -= take
            remain -= take
        self.lots_entries = [e for e in self.lots_entries if e['lots'] > 0]

        if remain > 0:
            action = '开多' if side == 'buy' else '开空'
            direction = 1 if side == 'buy' else -1
            self.lots_entries.append({'side': direction, 'lots': remain,
                                      'price': fill_price,
                                      'time': datetime.now().strftime('%H:%M:%S')})
            parts.append((action, remain, 0.0))

        self.balance -= fee_total
        self.total_fee += fee_total
        for action, pl, pnl in parts:
            self.realized_pnl += pnl
            self.balance += pnl
            self._log(action, pl, fill_price,
                      round(fee_total * pl / max(1, lots), 2), round(pnl, 2))
        self._recompute_position()
        desc = '、'.join(f'{a}{pl}手@{fill_price:.2f}' for a, pl, _ in parts)
        return True, '成交：' + desc

    def place_order(self, side, lots, order_type, price, bid, ask, limit_price=None):
        """下单入口。side: 'buy'/'sell'；
        order_type: 'opposite'对价 / 'super'超价 / 'market'市价 / 'limit'限价。
        限价未触及则挂单。返回 (ok, msg)。"""
        if side not in ('buy', 'sell'):
            return False, '方向无效'
        if order_type not in ('opposite', 'super', 'market', 'limit'):
            return False, '未知下单方式'
        lots = int(lots)
        if lots <= 0:
            return False, '手数需为正整数'
        price, bid, ask = float(price or 0), float(bid or 0), float(ask or 0)

        if order_type == 'limit':
            lp = float(limit_price or 0)
            if lp <= 0:
                return False, '请填写有效限价'
            ok, msg = self.check_margin(side, lots, lp)
            if not ok:
                return False, msg
            can_fill = ((side == 'buy' and ask > 0 and ask <= lp)
                        or (side == 'sell' and bid > 0 and bid >= lp))
            if not can_fill:
                self._order_idx += 1
                self.pending.append({'idx': self._order_idx,
                                     'time': datetime.now().strftime('%H:%M:%S'),
                                     'side': side, 'lots': lots, 'price': round(lp, 2)})
                return True, (f'限价单已挂出：{"买入" if side == "buy" else "卖出"}'
                              f'{lots}手 @ {lp:.2f}')
            fill = (min(ask, lp) + self.slippage) if side == 'buy' else (max(bid, lp) - self.slippage)
        elif order_type == 'opposite':
            ref = ask if side == 'buy' else bid
            if ref <= 0:
                ref = price
            fill = ref + (self.slippage if side == 'buy' else -self.slippage)
        elif order_type == 'super':
            ref = ask if side == 'buy' else bid
            if ref <= 0:
                ref = price
            extra = max(self.slippage, self.tick_size)
            fill = ref + (extra if side == 'buy' else -extra)
        else:  # market：按最新价 ± 至少一档滑点，模拟市价冲击
            ref = price
            if ref <= 0:
                ref = ask if side == 'buy' else bid
            extra = max(self.slippage, self.tick_size)
            fill = ref + (extra if side == 'buy' else -extra)

        if fill <= 0:
            return False, '行情无效，无法成交'
        ok, msg = self.check_margin(side, lots, fill)
        if not ok:
            return False, msg
        return self._execute(side, lots, max(fill, 0.01))

    # ---------------- 便捷动作 ----------------
    def open_long(self, lots, order_type, price, bid, ask, limit_price=None):
        return self.place_order('buy', lots, order_type, price, bid, ask, limit_price)

    def open_short(self, lots, order_type, price, bid, ask, limit_price=None):
        return self.place_order('sell', lots, order_type, price, bid, ask, limit_price)

    def close_long(self, lots, order_type, price, bid, ask, limit_price=None):
        if self.long_lots() <= 0:
            return False, '当前无多单'
        return self.place_order('sell', min(int(lots), self.long_lots()),
                                order_type, price, bid, ask, limit_price)

    def close_short(self, lots, order_type, price, bid, ask, limit_price=None):
        if self.short_lots() <= 0:
            return False, '当前无空单'
        return self.place_order('buy', min(int(lots), self.short_lots()),
                                order_type, price, bid, ask, limit_price)

    def close_all(self, price, bid, ask, order_type='opposite'):
        if self.position == 0:
            return False, '当前无持仓'
        side = 'sell' if self.position > 0 else 'buy'
        return self.place_order(side, abs(self.position), order_type, price, bid, ask)

    def reverse(self, lots, order_type, price, bid, ask, limit_price=None):
        """反手：平掉当前全部持仓并按给定手数开反向仓。"""
        if self.position == 0:
            return False, '当前无持仓，无法反手'
        target = -1 if self.position > 0 else 1
        target *= int(lots)
        return self.adjust_to(target, price, bid, ask, order_type, limit_price)

    def adjust_to(self, target, price, bid, ask, order_type='opposite', limit_price=None):
        """把持仓调整到 target（带符号手数）。返回 (ok, msg)。"""
        target = int(target)
        diff = target - self.position
        if diff == 0:
            return False, ''
        side = 'buy' if diff > 0 else 'sell'
        return self.place_order(side, abs(diff), order_type, price, bid, ask, limit_price)

    # ---------------- 资金 ----------------
    def deposit(self, amount):
        amount = float(amount)
        if amount <= 0:
            return False, '金额需为正数'
        self.balance += amount
        self.initial_cash += amount
        self._log('入金', 0, 0.0, 0.0, round(amount, 2))
        return True, f'入金 {amount:,.0f}，静态权益 {self.balance:,.0f}'

    def withdraw(self, amount):
        amount = float(amount)
        if amount <= 0:
            return False, '金额需为正数'
        if amount > self.available() + 1e-6:
            return False, f'可出金额仅 {self.available():,.0f}（占用保证金不可出）'
        self.balance -= amount
        self.initial_cash -= amount
        self._log('出金', 0, 0.0, 0.0, -round(amount, 2))
        return True, f'出金 {amount:,.0f}，静态权益 {self.balance:,.0f}'

    # ---------------- 每 tick 撮合 ----------------
    def check_pending(self, price, bid, ask):
        """限价挂单撮合：买单价>=卖一、卖单价<=买一即成交。返回成交提示列表。"""
        if not self.pending:
            return []
        msgs, keep = [], []
        for order in self.pending:
            hit = ((order['side'] == 'buy' and ask > 0 and ask <= order['price'])
                   or (order['side'] == 'sell' and bid > 0 and bid >= order['price']))
            if not hit:
                keep.append(order)
                continue
            ok, m = self.check_margin(order['side'], order['lots'], order['price'])
            if not ok:
                keep.append(order)
                continue
            ok, m = self._execute(order['side'], order['lots'], order['price'])
            if ok:
                msgs.append(f"挂单成交：{'买入' if order['side'] == 'buy' else '卖出'}"
                            f"{order['lots']}手 @ {order['price']:.2f}")
        self.pending = keep
        return msgs

    def cancel_pending(self, idx=None):
        """撤单。idx=None 撤全部。返回撤单数量。"""
        if idx is None:
            n = len(self.pending)
            self.pending = []
            return n
        before = len(self.pending)
        self.pending = [o for o in self.pending if o['idx'] != idx]
        return before - len(self.pending)

    def place_conditional(self, side, lots, cond, trigger):
        """埋入条件单：cond='gte'（价>=触发）或 'lte'（价<=触发），触发后按对价下单。"""
        if side not in ('buy', 'sell') or cond not in ('gte', 'lte'):
            return False, '条件单参数无效'
        lots = int(lots)
        trigger = float(trigger or 0)
        if lots <= 0 or trigger <= 0:
            return False, '手数/触发价无效'
        self._order_idx += 1
        self.conditionals.append({'idx': self._order_idx,
                                  'time': datetime.now().strftime('%H:%M:%S'),
                                  'side': side, 'cond': cond,
                                  'trigger': round(trigger, 2), 'lots': lots})
        cond_txt = '>=' if cond == 'gte' else '<='
        return True, (f'条件单已埋入：价格{cond_txt}{trigger:.2f} 时'
                      f'{"买入" if side == "buy" else "卖出"} {lots}手（对价）')

    def check_conditionals(self, price, bid, ask):
        """条件单触发检查。返回提示列表。"""
        if not self.conditionals:
            return []
        msgs, keep = [], []
        for c in self.conditionals:
            hit = ((c['cond'] == 'gte' and price >= c['trigger'])
                   or (c['cond'] == 'lte' and price <= c['trigger']))
            if not hit:
                keep.append(c)
                continue
            ok, m = self.place_order(c['side'], c['lots'], 'opposite', price, bid, ask)
            msgs.append(f"🎯 条件单触发（价格{'≥' if c['cond']=='gte' else '≤'}{c['trigger']:.2f}）：{m}")
        self.conditionals = keep
        return msgs

    def cancel_conditional(self, idx=None):
        if idx is None:
            n = len(self.conditionals)
            self.conditionals = []
            return n
        before = len(self.conditionals)
        self.conditionals = [c for c in self.conditionals if c['idx'] != idx]
        return before - len(self.conditionals)

    def check_sltp(self, price, bid, ask):
        """止盈止损触发检查：触发即按对价平仓。返回提示列表。"""
        if self.position == 0 or (self.sl_price is None and self.tp_price is None):
            return []
        msgs = []
        if self.position > 0:
            if self.sl_price is not None and price <= self.sl_price:
                ok, _ = self.place_order('sell', self.position, 'opposite', price, bid, ask)
                if ok:
                    msgs.append(f'🔥 止损触发：多单按买一价 {bid:.2f} 全部平仓')
            elif self.tp_price is not None and price >= self.tp_price:
                ok, _ = self.place_order('sell', self.position, 'opposite', price, bid, ask)
                if ok:
                    msgs.append(f'✅ 止盈触发：多单按买一价 {bid:.2f} 全部平仓')
        else:
            if self.sl_price is not None and price >= self.sl_price:
                ok, _ = self.place_order('buy', -self.position, 'opposite', price, bid, ask)
                if ok:
                    msgs.append(f'🔥 止损触发：空单按卖一价 {ask:.2f} 全部平仓')
            elif self.tp_price is not None and price <= self.tp_price:
                ok, _ = self.place_order('buy', -self.position, 'opposite', price, bid, ask)
                if ok:
                    msgs.append(f'✅ 止盈触发：空单按卖一价 {ask:.2f} 全部平仓')
        return msgs

    def liquidate_if_needed(self, price, bid, ask):
        """模拟强平：风险度>100% 时按对价强制平仓。返回提示（无触发返回空串）。"""
        if self.position == 0 or self.risk_ratio() < 100.0:
            return ''
        ok, m = self.close_all(price, bid, ask, 'opposite')
        if ok:
            return f'💥 模拟强平：风险度超过100%，持仓已全部平仓（{m}）'
        return ''


# ============================================================
# 账户持久化
# ============================================================
def default_account_path():
    """默认存档路径：DL_Quant_System/sim_accounts.json（已加入 .gitignore）。"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sim_accounts.json')


def account_to_dict(acct):
    return {
        'symbol': acct.symbol,
        'initial_cash': acct.initial_cash,
        'balance': acct.balance,
        'multiplier': acct.multiplier,
        'margin_rate': acct.margin_rate,
        'commission_rate': acct.commission_rate,
        'slippage': acct.slippage,
        'tick_size': acct.tick_size,
        'lots_entries': acct.lots_entries,
        'realized_pnl': acct.realized_pnl,
        'total_fee': acct.total_fee,
        'trades': acct.trades[-200:],
        'pending': acct.pending,
        'conditionals': acct.conditionals,
        'equity_curve': [[t, v] for t, v in acct.equity_curve[-500:]],
        'sl_price': acct.sl_price,
        'tp_price': acct.tp_price,
        'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def account_from_dict(d, symbol=None):
    sym = normalize_symbol(symbol or d.get('symbol', 'SA0'))
    acct = SimAccount(
        symbol=sym, initial_cash=float(d.get('initial_cash', 1000000)),
        multiplier=float(d.get('multiplier', 20)),
        margin_rate=float(d.get('margin_rate', 0.12)),
        commission_rate=float(d.get('commission_rate', 0.0001)),
        slippage=float(d.get('slippage', 0)),
        tick_size=float(d.get('tick_size', 1)))
    acct.balance = float(d.get('balance', acct.initial_cash))
    acct.lots_entries = [dict(e) for e in d.get('lots_entries', [])]
    acct.realized_pnl = float(d.get('realized_pnl', 0))
    acct.total_fee = float(d.get('total_fee', 0))
    acct.trades = [dict(t) for t in d.get('trades', [])]
    acct.pending = [dict(p) for p in d.get('pending', [])]
    acct.conditionals = [dict(c) for c in d.get('conditionals', [])]
    acct.equity_curve = [(str(t), float(v)) for t, v in d.get('equity_curve', [])]
    acct.sl_price = d.get('sl_price')
    acct.tp_price = d.get('tp_price')
    acct._recompute_position()
    if acct.pending:
        acct._order_idx = max(p['idx'] for p in acct.pending)
    if acct.conditionals:
        acct._order_idx = max(acct._order_idx, max(c['idx'] for c in acct.conditionals))
    return acct


def save_accounts(path, accounts):
    """accounts: {symbol: SimAccount}。落盘为 JSON。"""
    try:
        data = {sym: account_to_dict(a) for sym, a in accounts.items()}
        dirname = os.path.dirname(os.path.abspath(path))
        os.makedirs(dirname, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_accounts(path):
    """读取存档，返回 {symbol: SimAccount}；失败返回空 dict。"""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {sym: account_from_dict(d, sym) for sym, d in data.items()}
    except Exception:
        return {}


# ============================================================
# 策略桥
# ============================================================
def run_strategy_tick(strategy_code, bars_df):
    """在最新K线上执行全局策略（沙盒），返回 (df_with_Signal, last_signal, err)。"""
    if bars_df is None or len(bars_df) < 5:
        return bars_df, 0, 'K线数据不足'
    try:
        from strategy_sandbox import execute_strategy, prepare_strategy_source
    except Exception:
        return bars_df, 0, '沙盒模块缺失'
    try:
        res = execute_strategy(prepare_strategy_source(strategy_code), bars_df.copy())
    except Exception as exc:
        return bars_df, 0, str(exc)[:200]
    if res is None or 'Signal' not in res.columns:
        return bars_df, 0, '策略未生成 Signal 列'
    import pandas as pd
    out = bars_df.copy()
    sig = pd.to_numeric(res['Signal'], errors='coerce').fillna(0)
    out['Signal'] = sig.apply(lambda v: 1 if v > 0.1 else (-1 if v < -0.1 else 0))
    return out, int(out['Signal'].iloc[-1]), ''


# ============================================================
# 图表
# ============================================================
def build_sim_chart(bars_df, account=None, kind='candle'):
    """kind='candle'：K线+成交量+策略信号+持仓均价/现价参考线；
    kind='line'：分时线（收盘价线 + 当日均价线）。"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np

    if kind == 'line':
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                            row_heights=[0.72, 0.28])
        if bars_df is not None and not bars_df.empty:
            df = bars_df.tail(300)
            x = df['trade_date'].astype(str).str[11:16]
            vol = df['Volume'].fillna(0).clip(lower=1)
            avg = (df['Close'] * vol).cumsum() / vol.cumsum()
            fig.add_trace(go.Scatter(x=x, y=df['Close'], mode='lines',
                                     line=dict(color='#3b82f6', width=2),
                                     name='最新价'), row=1, col=1)
            fig.add_trace(go.Scatter(x=x, y=avg, mode='lines',
                                     line=dict(color='#f59e0b', width=1.4, dash='dot'),
                                     name='均价线'), row=1, col=1)
            vol_color = np.where(df['Close'].to_numpy() >= df['Open'].to_numpy(),
                                 '#ef4444', '#10b981')
            fig.add_trace(go.Bar(x=x, y=df['Volume'].fillna(0), marker_color=vol_color,
                                 name='成交量'), row=2, col=1)
        fig.update_layout(height=430, template='none', paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False,
                          dragmode='pan', hovermode='x', showlegend=False,
                          margin=dict(l=10, r=10, t=10, b=10))
        fig.update_xaxes(type='category', nticks=8, showgrid=True,
                         gridcolor='rgba(128,128,128,0.2)')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        row_heights=[0.72, 0.28])
    if bars_df is not None and not bars_df.empty:
        df = bars_df.tail(500)
        x = df['trade_date'].astype(str).str[11:16]
        fig.add_trace(go.Candlestick(
            x=x, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#ef4444', decreasing_line_color='#10b981',
            name='K线'), row=1, col=1)
        vol_color = np.where(df['Close'].to_numpy() >= df['Open'].to_numpy(), '#ef4444', '#10b981')
        fig.add_trace(go.Bar(x=x, y=df['Volume'].fillna(0), marker_color=vol_color,
                             name='成交量'), row=2, col=1)
        if 'Signal' in df.columns:
            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            if not buys.empty:
                fig.add_trace(go.Scatter(x=buys['trade_date'].astype(str).str[11:16],
                                         y=buys['Low'] * 0.998, mode='markers',
                                         marker=dict(symbol='triangle-up', size=13,
                                                     color='#3b82f6'),
                                         name='策略买点'), row=1, col=1)
            if not sells.empty:
                fig.add_trace(go.Scatter(x=sells['trade_date'].astype(str).str[11:16],
                                         y=sells['High'] * 1.002, mode='markers',
                                         marker=dict(symbol='triangle-down', size=13,
                                                     color='#f59e0b'),
                                         name='策略卖点'), row=1, col=1)
    if account is not None:
        if account.avg_price > 0 and account.position != 0:
            fig.add_hline(y=account.avg_price, line_dash='dot', line_color='#8b5cf6',
                          annotation_text=f'持仓均价 {account.avg_price:.2f}',
                          annotation_position='left', row=1, col=1)
        if account.last_price > 0:
            fig.add_hline(y=account.last_price, line_dash='dash', line_color='#94a3b8',
                          annotation_text=f'现价 {account.last_price:.2f}',
                          annotation_position='right', row=1, col=1)
    fig.update_layout(height=430, template='none', paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False,
                      dragmode='pan', hovermode='x', showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', nticks=8, showgrid=True,
                     gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    return fig


def build_equity_chart(equity_curve):
    """资金曲线。"""
    import plotly.graph_objects as go
    if not equity_curve:
        return go.Figure()
    x = [p[0] for p in equity_curve[-600:]]
    y = [p[1] for p in equity_curve[-600:]]
    fig = go.Figure(go.Scatter(x=x, y=y, mode='lines',
                               line=dict(color='#3b82f6', width=2),
                               fill='tozeroy', fillcolor='rgba(59,130,246,0.08)',
                               name='权益'))
    fig.update_layout(height=430, template='none', paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)', nticks=6)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    return fig
