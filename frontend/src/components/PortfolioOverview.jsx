import React from 'react';
import {
  Building2, TrendingUp, AlertTriangle, CheckCircle2,
  DollarSign, Activity, FileSpreadsheet, Percent, Clock, ShieldCheck
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, Cell
} from 'recharts';

export default function PortfolioOverview({ summary, onSelectCompany, onNavigateTab }) {
  if (!summary) {
    return <div className="p-8 text-center text-gray-400">Loading Portfolio Summary...</div>;
  }

  const categoryData = Object.entries(summary.category_distribution || {}).map(([name, value]) => ({
    name,
    value
  }));

  const modelComparisonData = [
    { name: 'Winning ML Models', mape: summary.portfolio_cash_mape, fill: '#06b6d4' },
    { name: 'Naive Baseline', mape: summary.naive_cash_mape, fill: '#f43f5e' },
    { name: 'Moving Avg (3P)', mape: summary.moving_avg_cash_mape, fill: '#f59e0b' }
  ];

  return (
    <div className="space-y-9">
      {/* Top Operations Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-7">
        <div className="glass-card p-6">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-sm font-medium">Companies Processed</span>
            <Building2 className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-white">{summary.total_companies}</div>
          <div className="text-xs text-gray-400 mt-1">{summary.total_observations} Quarterly Financial Statements</div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-sm font-medium">Finance-Ops Resolution Rate</span>
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-emerald-400">{summary.resolution_rate_pct}%</div>
          <div className="text-xs text-emerald-300 mt-1">{summary.resolved_forecasts} Forecasts Confidently Resolved</div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-sm font-medium">Human-Review Exception Rate</span>
            <AlertTriangle className="w-5 h-5 text-rose-400" />
          </div>
          <div className="text-3xl font-bold text-rose-400">{summary.exception_rate_pct}%</div>
          <div className="text-xs text-rose-300 mt-1">{summary.human_review_exceptions} Cases Flagged for Review</div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-sm font-medium">Forecast Accuracy (MAPE)</span>
            <Percent className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-cyan-400">{summary.portfolio_cash_mape}%</div>
          <div className="text-xs text-gray-400 mt-1">MAE: {summary.portfolio_cash_mae} Cr | RMSE: {summary.portfolio_cash_rmse} Cr</div>
        </div>
      </div>

      {/* Latency & Batch Throughput Card */}
      <div className="glass-panel p-6 rounded-xl flex flex-wrap items-center justify-between gap-5">
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-cyan-400" />
          <div className="text-xs text-gray-300">
            <span className="font-semibold text-white">Batch Execution Throughput:</span> Processed {summary.total_companies} companies ({summary.total_observations} observations) in <span className="text-cyan-400 font-bold">{summary.execution_time_sec} seconds</span> ({summary.avg_time_per_company_sec} s/company).
          </div>
        </div>
        <button
          onClick={() => onNavigateTab('benchmark')}
          className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-gray-800 hover:bg-gray-700 text-cyan-300 border border-cyan-500/30 transition-all"
        >
          View Ops Benchmark
        </button>
      </div>

      {/* Exception Alert Banner if any exceptions exist */}
      {summary.human_review_exceptions > 0 && (
        <div className="p-6 rounded-xl border border-rose-500/30 bg-rose-500/10 flex flex-wrap items-center justify-between gap-5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-400 flex-shrink-0" />
            <div>
              <div className="font-semibold text-rose-200">
                {summary.human_review_exceptions} Companies Require Human Controller Review ({summary.exception_rate_pct}% Exception Rate)
              </div>
              <div className="text-xs text-rose-300">
                Historical volatility, severe cash burn, or truncated observations triggered low-confidence exception flags.
              </div>
            </div>
          </div>
          <button
            onClick={() => onNavigateTab('benchmark')}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-500 hover:bg-rose-600 text-white transition-all"
          >
            Review Exception Report
          </button>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-9">
        {/* Model Baseline Comparison */}
        <div className="glass-card p-8">
          <div className="flex items-center justify-between mb-7">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Forecast Accuracy: Winning ML vs Baselines (MAPE %)
            </h3>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelComparisonData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e3b52" />
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f293d', borderColor: '#2e3b52', borderRadius: '8px', color: '#fff' }}
                  formatter={(val) => [`${val}%`, 'MAPE']}
                />
                <Bar dataKey="mape" radius={[6, 6, 0, 0]}>
                  {modelComparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-xs text-gray-400 mt-2 text-center">
            Out-of-time evaluation on held-out 2024 actuals. Lower percentage indicates higher accuracy.
          </div>
        </div>

        {/* Corporate Profile Breakdown */}
        <div className="glass-card p-8">
          <div className="flex items-center justify-between mb-7">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-cyan-400" />
              Company Distribution by Corporate Profile
            </h3>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} layout="vertical" margin={{ top: 10, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e3b52" />
                <XAxis type="number" stroke="#9ca3af" fontSize={12} />
                <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={11} width={100} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f293d', borderColor: '#2e3b52', borderRadius: '8px', color: '#fff' }}
                />
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-xs text-gray-400 mt-2 text-center">
            Synthetic dataset comprises 55 companies across 7 distinct financial profiles.
          </div>
        </div>
      </div>
    </div>
  );
}
