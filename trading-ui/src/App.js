import { useState, useEffect, useRef, useCallback, useMemo, useId } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

const API_BASE = 'http://localhost:8000';

// ─── Mock Data ────────────────────────────────────────────────
const MOCK_OVERVIEW = {
  opec_output:      { value: '27.2M bpd',  change: '-0.3M',  direction: 'down' },
  us_inventories:   { value: '432.1M bbl', change: '+2.1M',  direction: 'up'   },
  us_production:    { value: '13.2M bpd',  change: '+0.1M',  direction: 'up'   },
  rig_count:        { value: '588',         change: '-4',     direction: 'down' },
  wti_brent_spread: { value: '$3.76',       change: '-$0.12', direction: 'down' },
  crack_spread:     { value: '$24.50',      change: '+$1.20', direction: 'up'   },
  dxy_index:        { value: '104.32',      change: '-0.15',  direction: 'down' },
  natural_gas:      { value: '$2.84',       change: '+$0.06', direction: 'up'   },
};

const OV_LABELS = {
  opec_output: 'OPEC+ OUTPUT', us_inventories: 'US INVENTORIES',
  us_production: 'US PRODUCTION', rig_count: 'RIG COUNT',
  wti_brent_spread: 'WTI-BRENT SPREAD', crack_spread: 'CRACK SPREAD',
  dxy_index: 'DXY INDEX', natural_gas: 'NATURAL GAS',
};

const MOCK_NEWS = [
  { rank:1, datetime:'2026-05-04 14:30', source:'Reuters',         title:'OPEC+ Considers Further Production Cuts Amid Demand Concerns',   summary:'OPEC+ members are discussing additional output reductions of up to 500K bpd as global demand growth forecasts are revised downward for Q3 2026.', sentiment:'Positive', score:1  },
  { rank:2, datetime:'2026-05-04 12:15', source:'Bloomberg',       title:'US Crude Inventories Rise More Than Expected',                    summary:'EIA reports a 2.1 million barrel build in US crude stockpiles, exceeding analyst expectations of a 0.8 million barrel increase.',             sentiment:'Negative', score:-1 },
  { rank:3, datetime:'2026-05-04 10:00', source:'S&P Global',      title:'China Refinery Throughput Hits 3-Month High',                    summary:'Chinese refineries processed 14.8 million bpd in March, the highest level since December, signaling improving domestic demand.',              sentiment:'Positive', score:1  },
  { rank:4, datetime:'2026-05-04 08:45', source:'Financial Times', title:'Middle East Tensions Ease as Diplomatic Talks Progress',         summary:'Geopolitical risk premium decreases as regional diplomatic negotiations show positive momentum, reducing supply disruption fears.',            sentiment:'Negative', score:-1 },
  { rank:5, datetime:'2026-05-04 07:30', source:'IEA',             title:'IEA Maintains Global Oil Demand Growth Forecast at 1.1M bpd',   summary:'The International Energy Agency kept its 2026 oil demand growth forecast unchanged despite uncertainty over trade policy and slowdown risks.', sentiment:'Neutral',  score:0  },
];

const MOCK_PRICES = [
  { ticker:'GC=F', name:'Gold Futures',    price:3300.0, open:3290.0, high:3310.0, low:3285.0, vol:'180.2K', h52:3500.0, l52:2400.0, chg:10.0, pct:0.30 },
  { ticker:'CL=F', name:'WTI Crude Oil',   price:105.0,  open:99.73,  high:107.46, low:99.11,  vol:'316.4K', h52:130.0,  l52:65.0,  chg:5.27, pct:3.00 },
  { ticker:'BZ=F', name:'Brent Crude Oil', price:108.0,  open:102.5,  high:109.0,  low:101.5,  vol:'198.3K', h52:135.0,  l52:68.0,  chg:5.50, pct:2.95 },
  { ticker:'SI=F', name:'Silver Futures',  price:32.5,   open:32.0,   high:33.0,   low:31.8,   vol:'95.3K',  h52:36.0,   l52:22.0,  chg:0.50, pct:1.56 },
  { ticker:'NG=F', name:'Natural Gas',     price:2.84,   open:2.78,   high:2.90,   low:2.75,   vol:'55.1K',  h52:4.50,   l52:1.80,  chg:0.06, pct:2.17 },
];

const PRESET_QUESTIONS = [
  'Analyze gold futures - give me technical signals and latest news',
  'What is the trading recommendation for crude oil right now?',
  'Show me silver futures analysis with sentiment score',
  'Is natural gas bullish or bearish based on latest news?',
];

// ─── Helpers ──────────────────────────────────────────────────
function timeAgo(dt) {
  const diff = Math.floor((Date.now() - new Date(dt.replace(' ', 'T')).getTime()) / 60000);
  if (diff < 1) return 'just now';
  if (diff < 60) return `${diff}m ago`;
  if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
  return `${Math.floor(diff / 1440)}d ago`;
}

function genSpark(base, n = 40) {
  let v = base;
  return Array.from({ length: n }, () => {
    v += (Math.random() - 0.47) * 0.4;
    return +v.toFixed(2);
  });
}

function isMarketOpen() {
  const now = new Date();
  const day = now.getUTCDay(); // 0=Sun, 6=Sat
  const h = now.getUTCHours();
  const m = now.getUTCMinutes();
  const mins = h * 60 + m;
  // Futures roughly: Sun 23:00 UTC – Fri 22:00 UTC
  if (day === 6) return false;
  if (day === 0 && mins < 23 * 60) return false;
  if (day === 5 && mins >= 22 * 60) return false;
  return true;
}

// ─── Sparkline ────────────────────────────────────────────────
function Spark({ data, up }) {
  const id = useId().replace(/:/g, '');
  const path = useMemo(() => {
    if (!data?.length) return null;
    const W = 200, H = 56;
    const min = Math.min(...data), max = Math.max(...data), rng = max - min || 1;
    const x = i => (i / (data.length - 1)) * W;
    const y = v => H - 8 - ((v - min) / rng) * (H - 16);
    const pts = data.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    const line = `M ${pts.join(' L ')}`;
    const fill = `${line} L ${W},${H} L 0,${H} Z`;
    return { line, fill, W, H };
  }, [data]);

  if (!path) return null;
  const col = up ? '#22c55e' : '#ef4444';

  return (
    <svg width={path.W} height={path.H} viewBox={`0 0 ${path.W} ${path.H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sg-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={col} stopOpacity="0.35" />
          <stop offset="100%" stopColor={col} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={path.fill} fill={`url(#sg-${id})`} />
      <path d={path.line} fill="none" stroke={col} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────
function PriceSkeleton() {
  return (
    <div className="price-card skeleton-card">
      <div className="skel skel-row" />
      <div className="skel skel-price" />
      <div className="skel skel-spark" />
      <div className="skel skel-stats" />
    </div>
  );
}

// ─── Overview ────────────────────────────────────────────────
function OverviewScreen({ ov }) {
  return (
    <div className="screen">
      <div className="hero">
        <div className="hero-glow" />
        <div className="hero-body">
          <div className="hero-eyebrow">AI FUTURES INTELLIGENCE</div>
          <h1 className="hero-h1">Futures <em>Intelligence</em></h1>
          <p className="hero-p">Real-time prices, market intelligence, and AI-powered analysis for futures markets including Gold, Oil, Silver, and more.</p>
        </div>
      </div>

      <div className="sec-hdr">
        <span className="sec-ico">⏱</span>
        <span className="sec-lbl">Market Overview</span>
        <span className="sec-hint">8 indicators</span>
      </div>

      <div className="ov-grid">
        {Object.entries(ov).map(([k, d], i) => (
          <div className="ov-card" key={k} style={{ animationDelay: `${i * 0.05}s` }}>
            <div className="ov-key">{OV_LABELS[k]}</div>
            <div className="ov-val">{d.value}</div>
            <div className={`ov-chg ${d.direction}`}>
              <span className="ov-arrow">{d.direction === 'up' ? '↗' : '↘'}</span>
              {d.change}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Prices ──────────────────────────────────────────────────
function PricesScreen({ prices, loading }) {
  if (loading) return (
    <div className="screen">
      <div className="sec-hdr">
        <span className="sec-ico bars"><b /><b /><b /></span>
        <span className="sec-lbl">Live Prices</span>
        <span className="live-pill"><span className="ldot" />Live</span>
      </div>
      <PriceSkeleton />
      <PriceSkeleton />
    </div>
  );

  return (
    <div className="screen">
      <div className="sec-hdr">
        <span className="sec-ico bars"><b /><b /><b /></span>
        <span className="sec-lbl">Live Prices</span>
        <span className="live-pill"><span className="ldot" />Live</span>
      </div>

      {prices.map((p, i) => (
        <div className="price-card" key={p.ticker} style={{ animationDelay: `${i * 0.1}s` }}>
          <div className="pc-row1">
            <div>
              <div className="pc-ticker">{p.ticker}</div>
              <div className="pc-name">{p.name}</div>
            </div>
            <span className={`pct-badge ${p.chg >= 0 ? 'up' : 'dn'}`}>
              {p.chg >= 0 ? '↗' : '↘'} {p.chg >= 0 ? '+' : ''}{p.pct.toFixed(2)}%
            </span>
          </div>

          <div className="pc-price-row">
            <span className="pc-price">${p.price.toFixed(2)}</span>
            <span className={`pc-abs ${p.chg >= 0 ? 'up' : 'dn'}`}>
              {p.chg >= 0 ? '+' : ''}{p.chg.toFixed(2)}
            </span>
          </div>

          <div className="pc-spark">
            <Spark data={p.spark} up={p.chg >= 0} />
          </div>

          <div className="pc-stats">
            {[['OPEN', `$${p.open.toFixed(2)}`, ''], ['HIGH', `$${p.high.toFixed(2)}`, 'up'], ['LOW', `$${p.low.toFixed(2)}`, 'dn'], ['VOL', p.vol, '']].map(([l, v, c]) => (
              <div key={l} className="pcst">
                <span className="pcst-l">{l}</span>
                <span className={`pcst-v ${c}`}>{v}</span>
              </div>
            ))}
          </div>

          <div className="pc-range">
            <div className="range-bar-wrap">
              <div className="range-bar">
                <div className="range-fill" style={{
                  left: `${((p.price - p.l52) / (p.h52 - p.l52)) * 100}%`,
                  width: '6px',
                }} />
              </div>
            </div>
            <div className="pc-52w">
              <span>52W L: <em className="dn">${p.l52.toFixed(2)}</em></span>
              <span>52W H: <em className="up">${p.h52.toFixed(2)}</em></span>
            </div>
          </div>

          {p.time && <div className="pc-updated">⚡ Updated {p.time}</div>}
        </div>
      ))}
    </div>
  );
}

// ─── News ────────────────────────────────────────────────────
const NEWS_SYMBOLS = [
  { label: 'Crude Oil', value: 'Crude Oil' },
  { label: 'Gold',      value: 'Gold'      },
  { label: 'Silver',    value: 'Silver'    },
  { label: 'Nat. Gas',  value: 'Natural Gas'},
  { label: 'Nasdaq',    value: 'Nasdaq'    },
  { label: 'S&P 500',   value: 'S&P 500'  },
];

function NewsScreen({ news, onRefresh, refreshing, newsSymbol, onSymbolChange }) {
  const bullish = news.filter(a => a.sentiment === 'Positive').length;
  const bearish  = news.filter(a => a.sentiment === 'Negative').length;
  const netScore = news.reduce((s, a) => s + (a.score || 0), 0);
  const overall  = netScore > 0 ? 'BULLISH' : netScore < 0 ? 'BEARISH' : 'NEUTRAL';

  return (
    <div className="screen">
      <div className="sec-hdr">
        <span className="sec-ico">📋</span>
        <span className="sec-lbl">Market News</span>
        <button className={`refresh-btn ${refreshing ? 'spinning' : ''}`} onClick={onRefresh} disabled={refreshing}>
          ↻ {refreshing ? 'Loading…' : 'Refresh'}
        </button>
      </div>
      <div className="symbol-tabs">
        {NEWS_SYMBOLS.map(s => (
          <button
            key={s.value}
            className={`symbol-tab ${newsSymbol === s.value ? 'active' : ''}`}
            onClick={() => onSymbolChange(s.value)}
            disabled={refreshing}
          >{s.label}</button>
        ))}
      </div>

      {/* Sentiment summary bar */}
      <div className="sentiment-summary">
        <div className="ss-overall">
          <span className="ss-label">Overall Sentiment</span>
          <span className={`ss-verdict ${overall.toLowerCase()}`}>{overall}</span>
        </div>
        <div className="ss-bar-wrap">
          <div className="ss-bar">
            <div className="ss-seg bullish" style={{ width: `${(bullish / news.length) * 100}%` }} />
            <div className="ss-seg neutral" style={{ width: `${((news.length - bullish - bearish) / news.length) * 100}%` }} />
            <div className="ss-seg bearish" style={{ width: `${(bearish / news.length) * 100}%` }} />
          </div>
        </div>
        <div className="ss-counts">
          <span className="up">↗ {bullish} Bullish</span>
          <span className="dn">↘ {bearish} Bearish</span>
          <span style={{ color: 'var(--muted)' }}>— {news.length - bullish - bearish} Neutral</span>
        </div>
      </div>

      <div className="news-list">
        {news.map((a, i) => (
          <div className="news-card" key={i} style={{ animationDelay: `${i * 0.07}s`, cursor: a.url ? 'pointer' : 'default' }} onClick={() => a.url && window.open(a.url, '_blank')}>
            <div className="nc-top">
              <div className="nc-title">{a.title}</div>
              <span className={`sent-badge ${a.sentiment.toLowerCase()}`}>
                {a.sentiment === 'Positive' ? '↗ Bullish' : a.sentiment === 'Negative' ? '↘ Bearish' : '— Neutral'}
              </span>
            </div>
            <div className="nc-body">{a.summary}</div>
            <div className="nc-foot">
              <span className="nc-source">{a.source}</span>
              <span className="nc-time">{timeAgo(a.datetime)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── AI Screen ───────────────────────────────────────────────
const MAX_CHARS = 500;

function AIScreen() {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  const send = useCallback(async (txt) => {
    const msg = (txt || input).trim();
    if (!msg || loading) return;
    setInput('');
    setStarted(true);
    setMsgs(p => [...p, { role: 'user', text: msg }]);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      });
      const d = await res.json();
      setMsgs(p => [...p, { role: 'assistant', text: d.response }]);
    } catch {
      setMsgs(p => [...p, { role: 'assistant', text: 'Backend offline — start the FastAPI server on port 8000 to enable live AI responses.' }]);
    }
    setLoading(false);
  }, [input, loading]);

  const charsLeft = MAX_CHARS - input.length;
  const nearLimit = charsLeft < 80;

  return (
    <div className="screen ai-screen">
      <div className="ai-hdr">
        <div className="ai-hdr-ico">✦</div>
        <div>
          <div className="ai-hdr-name">Rachel — AI Futures Analyst</div>
          <div className="ai-hdr-sub">Powered by zeroclaw · Ask anything about futures markets</div>
        </div>
        {started && (
          <button className="ai-clear" onClick={() => { setMsgs([]); setStarted(false); }} title="New chat">✕</button>
        )}
      </div>

      {!started ? (
        <div className="ai-empty">
          <div className="ai-empty-glow" />
          <div className="ai-empty-ico">✦</div>
          <div className="ai-empty-title">Rachel Futures Assistant</div>
          <div className="ai-empty-sub">Ask me about futures signals, market news, technical analysis, or trading recommendations.</div>
          <div className="preset-list">
            {PRESET_QUESTIONS.map((q, i) => (
              <button key={i} className="preset-btn" onClick={() => send(q)}>
                <span className="preset-arrow">→</span> {q}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="ai-msgs">
            {msgs.map((m, i) => (
              <div key={i} className={`ai-msg ${m.role}`}>
                {m.role === 'assistant' && <div className="ai-ava">✦</div>}
                <div className="ai-bubble">
                  <ReactMarkdown>{m.text}</ReactMarkdown>
                </div>
              </div>
            ))}
            {loading && (
              <div className="ai-msg assistant">
                <div className="ai-ava">✦</div>
                <div className="ai-bubble typing"><span /><span /><span /></div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Quick chips in chat view */}
          <div className="ai-chips">
            {PRESET_QUESTIONS.slice(0, 3).map((q, i) => (
              <button key={i} className="ai-chip" onClick={() => send(q)} disabled={loading}>{q}</button>
            ))}
          </div>
        </>
      )}

      <div className="ai-bar">
        <div className="ai-input-wrap">
          <input
            value={input}
            onChange={e => setInput(e.target.value.slice(0, MAX_CHARS))}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about futures markets..."
            disabled={loading}
          />
          {nearLimit && <span className={`char-count ${charsLeft < 20 ? 'urgent' : ''}`}>{charsLeft}</span>}
        </div>
        <button className="ai-send" onClick={() => send()} disabled={loading || !input.trim()}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Root ─────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState('overview');
  const [prices, setPrices] = useState([]);
  const [pricesLoading, setPricesLoading] = useState(true);
  const [news, setNews] = useState(MOCK_NEWS);
  const [refreshing, setRefreshing] = useState(false);
  const [marketOpen] = useState(isMarketOpen());

  const dateStr = new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric' });

  // Fetch prices
  useEffect(() => {
    const nowStr = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    const withSpark = MOCK_PRICES.map(d => ({ ...d, spark: genSpark(d.open, 40), time: nowStr }));
    setPrices(withSpark);

    const fetchLive = async () => {
      try {
        const results = await Promise.all(
          MOCK_PRICES.map(d =>
            fetch(`${API_BASE}/api/kline?symbol=${d.ticker}`).then(r => r.json()).catch(() => null)
          )
        );
        const now2 = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
        setPrices(MOCK_PRICES.map((d, i) => {
          const kd = results[i];
          if (!kd || !kd.length) return { ...d, spark: genSpark(d.open, 40), time: now2 };
          const last = kd[kd.length - 1], first = kd[0];
          const chg = last.close - first.open, pct = (chg / first.open) * 100;
          return { ...d, price: last.close, open: first.open, high: Math.max(...kd.map(c => c.high)), low: Math.min(...kd.map(c => c.low)), chg, pct, spark: kd.map(c => c.close), time: now2 };
        }));
      } catch { /* keep mock */ }
      finally { setPricesLoading(false); }
    };

    fetchLive();
    const iv = setInterval(fetchLive, 30000);
    return () => clearInterval(iv);
  }, []);

  const [newsSymbol, setNewsSymbol] = useState('Crude Oil');

  const refreshNews = useCallback(async (sym) => {
    const symbol = sym || newsSymbol;
    setRefreshing(true);
    try {
      const r = await fetch(`${API_BASE}/api/news?symbol=${encodeURIComponent(symbol)}&limit=5`);
      const d = await r.json();
      if (d.articles) setNews(d.articles);
      else throw new Error();
    } catch {
      setNews(prev => [...prev].sort(() => Math.random() - 0.5));
    } finally {
      setRefreshing(false);
    }
  }, [newsSymbol]);

  const handleSymbolChange = useCallback((sym) => {
    setNewsSymbol(sym);
    refreshNews(sym);
  }, [refreshNews]);

  useEffect(() => {
    refreshNews('Crude Oil');
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const TABS = [
    { id: 'overview', icon: '⏱',  label: 'Overview' },
    { id: 'prices',   icon: '📈', label: 'Prices'   },
    { id: 'news',     icon: '📋', label: 'News'     },
    { id: 'ai',       icon: '✦',  label: 'AI'       },
  ];

  return (
    <div className="app">
      <header className="topbar">
        <div className="tb-brand">
          <div className="tb-ico">🔥</div>
          <div>
            <div className="tb-name">Rachel</div>
            <div className="tb-sub">AI Futures Trading Assistant</div>
          </div>
        </div>
        <div className="tb-right">
          <div className={`mkt-status ${marketOpen ? 'open' : 'closed'}`}>
            <span className="mkt-dot" />
            <span className="mkt-txt">{marketOpen ? 'Market Open' : 'Market Closed'}</span>
          </div>
          <div className="tb-date">{dateStr}</div>
        </div>
      </header>

      <div className="content">
        {tab === 'overview' && <OverviewScreen ov={MOCK_OVERVIEW} />}
        {tab === 'prices'   && <PricesScreen prices={prices} loading={pricesLoading} />}
        {tab === 'news'     && <NewsScreen news={news} onRefresh={refreshNews} refreshing={refreshing} newsSymbol={newsSymbol} onSymbolChange={handleSymbolChange} />}
        {tab === 'ai'       && <AIScreen />}
      </div>

      <nav className="bottomnav">
        {TABS.map(t => (
          <button key={t.id} className={`bnav-btn ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
            {tab === t.id && <span className="bnav-pip" />}
            <span className="bnav-ico">{t.icon}</span>
            <span className="bnav-lbl">{t.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
