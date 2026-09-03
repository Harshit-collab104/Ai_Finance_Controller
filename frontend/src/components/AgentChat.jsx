import React, { useState } from 'react';
import { Bot, User, Send, Sparkles, Building2, AlertTriangle, ShieldCheck, ArrowRight } from 'lucide-react';
import { apiFetch } from '../apiConfig';

function FormattedMessageText({ text }) {
  if (!text) return null;

  const lines = text.split('\n');

  return (
    <div className="space-y-2">
      {lines.map((line, lineIdx) => {
        let trimmed = line.trim();

        if (trimmed.startsWith('#')) {
          const content = trimmed.replace(/^#+\s*/, '');
          return (
            <h4 key={lineIdx} className="text-base font-bold text-white mt-3 mb-1 flex items-center gap-1.5">
              {parseInlineMarkdown(content)}
            </h4>
          );
        }

        if (trimmed.startsWith('>')) {
          const content = trimmed.replace(/^>\s*/, '');
          return (
            <div key={lineIdx} className="p-3 bg-cyan-500/10 border-l-4 border-cyan-500 rounded-r-lg text-cyan-200 text-xs my-2 font-medium">
              {parseInlineMarkdown(content)}
            </div>
          );
        }

        if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || (trimmed.startsWith('• '))) {
          const content = trimmed.replace(/^[\*\-\•]\s*/, '');
          return (
            <div key={lineIdx} className="flex items-start gap-2 ml-2 text-gray-300 text-xs">
              <span className="text-cyan-400 font-bold text-sm leading-none mt-0.5">•</span>
              <span>{parseInlineMarkdown(content)}</span>
            </div>
          );
        }

        if (!trimmed) {
          return <div key={lineIdx} className="h-1" />;
        }

        return (
          <p key={lineIdx} className="text-gray-200 leading-relaxed text-xs sm:text-sm">
            {parseInlineMarkdown(line)}
          </p>
        );
      })}
    </div>
  );
}

function parseInlineMarkdown(text) {
  const regex = /(\*\*.*?\*\*|`.*?`)/g;
  const parts = text.split(regex);

  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={idx} className="font-bold text-cyan-300">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={idx} className="font-mono text-xs bg-gray-800 text-cyan-400 px-1.5 py-0.5 rounded border border-gray-700">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export default function AgentChat({ selectedCompanyId, onSelectCompany, companies = [] }) {
  const activeCompanyObj = companies.find(c => c.company_id === selectedCompanyId);
  const activeCompanyName = activeCompanyObj && activeCompanyObj.company_name && activeCompanyObj.company_name !== 'CO'
    ? activeCompanyObj.company_name 
    : (selectedCompanyId === 'C014' ? 'Velox Medical Devices' : selectedCompanyId);

  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: `Hello! I am your **AI Finance Controller Agent**. I close the finance-ops loop across 55 companies: forecasting cash trajectory, analyzing operational drivers, assessing financial risk, and providing grounded controller recommendations.\n\nAsk me about company cash predictions, risk drivers, what-if scenarios, or low-confidence exception cases!`
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const samplePrompts = [
    `What will ${activeCompanyName}'s cash position look like next quarter?`,
    `Why is cash expected to decline for ${activeCompanyName}?`,
    `Is ${activeCompanyName} financially at risk?`,
    `What happens if revenue falls by 10% for ${activeCompanyName}?`,
    `List low-confidence exception companies requiring manual review.`
  ];

  const handleSend = async (queryText) => {
    const query = queryText || inputQuery;
    if (!query.trim()) return;

    const userMsg = { sender: 'user', text: query };
    setMessages(prev => [...prev, userMsg]);
    if (!queryText) setInputQuery('');

    setLoading(true);

    try {
      const res = await apiFetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, company_id: selectedCompanyId })
      });

      const data = await res.json();
      const botMsg = { 
        sender: 'bot', 
        text: data.answer,
        evidence: data.evidence
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Backend service unreachable. Make sure FastAPI backend is running.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card flex flex-col h-[750px]">
      {/* Agent Chat Header */}
      <div className="p-5 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-white flex items-center gap-2">
              AI Finance Controller Agent
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
            </h3>
            <div className="text-xs text-gray-400">Closing the Finance-Ops Loop: Forecast ➜ Drivers ➜ Risk ➜ Resolution ➜ Action</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Active Reference:</span>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
            {activeCompanyName}
          </span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-6 overflow-y-auto space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.sender === 'bot' && (
              <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 flex-shrink-0 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-2xl p-4 rounded-xl text-sm leading-relaxed ${
              msg.sender === 'user' 
                ? 'bg-cyan-600 text-white rounded-tr-none' 
                : 'bg-gray-900/90 text-gray-200 border border-gray-800 rounded-tl-none space-y-2'
            }`}>
              <FormattedMessageText text={msg.text} />

              {/* Model & Status Metadata without engine text */}
              {msg.sender === 'bot' && msg.evidence && msg.evidence.cash_forecast && (
                <div className="mt-3 pt-3 border-t border-gray-800 flex flex-wrap items-center gap-2 text-[11px] text-gray-400">
                  <span className="px-2 py-0.5 rounded bg-gray-800 border border-gray-700">
                    Model: {msg.evidence.cash_forecast.forecast_model}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-gray-800 border border-gray-700">
                    Status: {msg.evidence.cash_forecast.resolution_status}
                  </span>
                </div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-full bg-cyan-700 flex items-center justify-center text-white flex-shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 items-center text-gray-400 text-sm">
            <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center text-cyan-400 animate-spin">
              <Sparkles className="w-4 h-4" />
            </div>
            <span>Evaluating quantitative evidence, driver analysis & AI reasoning...</span>
          </div>
        )}
      </div>

      {/* Suggested Quick Prompts */}
      <div className="p-3 bg-gray-900/50 border-t border-gray-800 flex flex-wrap gap-2">
        <span className="text-xs text-gray-400 flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Suggested Prompts:
        </span>
        {samplePrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSend(p)}
            className="text-xs bg-gray-800/80 hover:bg-cyan-500/20 hover:text-cyan-300 text-gray-300 px-3 py-1 rounded-full border border-gray-700 transition-all text-left truncate max-w-xs"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="p-4 border-t border-gray-800 bg-gray-900/80 flex gap-3">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={`Ask AI Financial Controller about ${activeCompanyName}...`}
          className="flex-1 bg-gray-950 text-white placeholder-gray-500 text-sm px-4 py-2.5 rounded-lg border border-gray-800 focus:outline-none focus:border-cyan-500"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading}
          className="px-5 py-2.5 bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 text-white font-medium rounded-lg text-sm flex items-center gap-2 transition-all"
        >
          <Send className="w-4 h-4" />
          Send
        </button>
      </div>
    </div>
  );
}
