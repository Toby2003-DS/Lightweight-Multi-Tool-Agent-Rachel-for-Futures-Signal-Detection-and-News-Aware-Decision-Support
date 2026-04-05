import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';

const SYMBOLS = [
  { label: 'Gold', value: 'GC=F', display: 'XAU/USD' },
  { label: 'Crude Oil', value: 'CL=F', display: 'WTI/USD' },
  { label: 'Silver', value: 'SI=F', display: 'XAG/USD' },
  { label: 'Natural Gas', value: 'NG=F', display: 'NG/USD' },
  { label: 'Nasdaq', value: 'NQ=F', display: 'NQ100' },
  { label: 'S&P 500', value: 'ES=F', display: 'SPX500' },
];

const genData = () => {
  let price = 2000 + Math.random() * 500;
  return Array.from({ length: 80 }, (_, i) => {
    const open = price;
    const close = open + (Math.random() - 0.48) * 20;
    const high = Math.max(open, close) + Math.random() * 8;
    const low = Math.min(open, close) - Math.random() * 8;
    price = close;
    const t = new Date(Date.now() - (80 - i) * 15 * 60000);
    return { time: t.getHours() + ':' + String(t.getMinutes()).padStart(2,'0'), open, close, high, low };
  });
};

export default function App() {
  const [symbol, setSymbol] = useState(SYMBOLS[0]);
  const [data, setData] = useState(genData());
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hello! I'm Rachel — your AI futures analyst. Select a symbol and ask me anything." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef(null);
  const msgEnd = useRef(null);

  useEffect(() => {
    const fetchKline = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/kline?symbol=' + symbol.value);
        if (res.data && res.data.length > 0) {
          const formatted = res.data.map(d => ({
            time: new Date(d.time * 1000).getHours() + ':' + String(new Date(d.time * 1000).getMinutes()).padStart(2, '0'),
            open: d.open, high: d.high, low: d.low, close: d.close
          }));
          setData(formatted);
        }
      } catch {
        setData(genData());
      }
    };
    fetchKline();
    const interval = setInterval(fetchKline, 30000);
    return () => clearInterval(interval);
  }, [symbol]);

  useEffect(() => {
    msgEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width = canvas.offsetWidth;
    const H = canvas.height = canvas.offsetHeight;
    ctx.clearRect(0, 0, W, H);

    const prices = data.flatMap(d => [d.high, d.low]);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const pad = { top: 20, bottom: 30, left: 10, right: 60 };
    const chartW = W - pad.left - pad.right;
    const chartH = H - pad.top - pad.bottom;
    const toY = p => pad.top + chartH - ((p - minP) / (maxP - minP)) * chartH;
    const candleW = Math.max(2, chartW / data.length * 0.6);

    // grid
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = pad.top + (chartH / 5) * i;
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
      const price = maxP - ((maxP - minP) / 5) * i;
      ctx.fillStyle = '#555'; ctx.font = '11px monospace';
      ctx.fillText(price.toFixed(1), W - pad.right + 4, y + 4);
    }

    // candles
    data.forEach((d, i) => {
      const x = pad.left + (i / data.length) * chartW + candleW / 2;
      const color = d.close >= d.open ? '#00c087' : '#ff4d4d';
      ctx.strokeStyle = color; ctx.fillStyle = color;

      // wick
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, toY(d.high));
      ctx.lineTo(x, toY(d.low));
      ctx.stroke();

      // body
      const bodyTop = toY(Math.max(d.open, d.close));
      const bodyH = Math.max(1, Math.abs(toY(d.open) - toY(d.close)));
      ctx.fillRect(x - candleW / 2, bodyTop, candleW, bodyH);
    });

    // x labels
    ctx.fillStyle = '#555'; ctx.font = '11px monospace';
    const step = Math.floor(data.length / 8);
    data.forEach((d, i) => {
      if (i % step === 0) {
        const x = pad.left + (i / data.length) * chartW;
        ctx.fillText(d.time, x, H - 8);
      }
    });
  }, [data]);

  const send = useCallback(async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/chat', {
        message: '[' + symbol.label + '] ' + msg
      });
      setMessages(prev => [...prev, { role: 'assistant', text: res.data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Backend not connected yet. Start the FastAPI server to enable live chat.' }]);
    }
    setLoading(false);
  }, [input, loading, symbol]);

  const last = data[data.length - 1];
  const change = last ? (last.close - data[0].open).toFixed(2) : 0;
  const isUp = change >= 0;

  return (
    <div className="app">
      <header className="header">
        <div className="hl">
          <span className="logo">◈ RACHEL</span>
          <span className="tagline">AI Futures Trading Assistant</span>
        </div>
        <div className="hr">
          <span className="dot" /><span className="live">LIVE</span>
        </div>
      </header>
      <div className="main">
        <aside className="sidebar">
          <div className="stitle">MARKETS</div>
          {SYMBOLS.map(s => (
            <button key={s.value} className={'sbtn' + (symbol.value === s.value ? ' active' : '')} onClick={() => setSymbol(s)}>
              <span className="slabel">{s.label}</span>
              <span className="sdisplay">{s.display}</span>
            </button>
          ))}
        </aside>
        <div className="center">
          <div className="cheader">
            <span className="csymbol">{symbol.label}</span>
            <span className="csub">{symbol.display}</span>
            <span className="cprice">${last?.close.toFixed(2)}</span>
            <span className={'cchange ' + (isUp ? 'up' : 'dn')}>{isUp ? '▲' : '▼'} {Math.abs(change)}</span>
            <span className="cint">15m · live</span>
          </div>
          <canvas className="chart" ref={canvasRef} />
        </div>
        <div className="chat">
          <div className="ctitle">RACHEL — AI ANALYST</div>
          <div className="msgs">
            {messages.map((m, i) => (
              <div key={i} className={'msg ' + m.role}>
                <div className="bubble"><ReactMarkdown>{m.text}</ReactMarkdown></div>
              </div>
            ))}
            {loading && <div className="msg assistant"><div className="bubble loading"><span/><span/><span/></div></div>}
            <div ref={msgEnd} />
          </div>
          <div className="cinput">
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} placeholder={'Ask about ' + symbol.label + '...'} />
            <button onClick={send} disabled={loading}>▶</button>
          </div>
        </div>
      </div>
    </div>
  );
}
