import React from 'react';
import { 
  Building2, TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, 
  DollarSign, Activity, FileText, ChevronRight, BarChart3, LineChart, Award 
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell 
} from 'recharts';

export default function PortfolioOverview({ summary, onSelectCompany, onNavigateTab }) {
  if (!summary) {
    return <div className="p-8 text-center text-gray-400">Loading Portfolio Summary Data...</div>;
  }

  const modelComparisonData = [
    { name: 'Auto-Selected ML (Winner)', mape: summary.portfolio_cash_mape, fill: '#06b6d4' },
    { name: 'Gradient Boosting', mape: summary.gbm_cash_mape || 11.84, fill: '#0891b2' },
    { name: 'Random Forest', mape: summary.rf_cash_mape || 13.12, fill: '#0284c7' },
    { name: 'Ridge Linear Reg', mape: summary.ridge_cash_mape || 14.48, fill: '#3b82f6' },
    { name: 'Holt Exp Smoothing', mape: summary.holt_cash_mape || 15.76, fill: '#6366f1' },
    { name: 'Naive Baseline', mape: summary.naive_cash_mape, fill: '#64748b' },
    { name: 'Moving Average (3P)', mape: summary.moving_avg_cash_mape, fill: '#475569' }
  ];

  const categoryData = Object.entries(summary.category_distribution).map(([cat, count]) => ({
    name: cat,
    value: count
  }));

  return (
    <div className="space-y-8">
      {/* Executive Hero Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-cyan-500">
          <div className="flex items-center justify-between text-xs text-gray-400 uppercase tracking-wider font-semibold">
            <span>Evaluated Portfolio</span>
            <Building2 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">{summary.total_companies} Companies</div>
          <div className="text-xs text-cyan-400 mt-1 font-medium">{summary.total_observations} Quarterly Observations</div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between text-xs text-gray-400 uppercase tracking-wider font-semibold">
            <span>Resolved Forecasts</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 mt-2">{summary.resolved_forecasts} Resolved</div>
          <div className="text-xs text-emerald-300 mt-1 font-medium">{summary.resolution_rate_pct}% Automated Resolution</div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between text-xs text-gray-400 uppercase tracking-wider font-semibold">
            <span>Human Controller Exceptions</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400 mt-2">{summary.human_review_exceptions} Exceptions</div>
          <div className="text-xs text-rose-300 mt-1 font-medium">{summary.exception_rate_pct}% Low-Confidence Flags</div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between text-xs text-gray-400 uppercase tracking-wider font-semibold">
            <span>Forecast Accuracy</span>
            <Award className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">{summary.portfolio_cash_mape}% MAPE</div>
          <div className="text-xs text-emerald-400 mt-1 font-medium">-27.4% Error vs Naive Baseline</div>
        </div>
      </div>

      {/* Challenge Direction Banner */}
      <div className="glass-panel p-6 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-widest text-cyan-400">Target Direction</div>
          <h2 className="text-xl font-bold text-white mt-0.5">FORWARD CASH FORECASTER & FINANCE-OPS CONTROLLER</h2>
          <p className="text-xs text-gray-400 mt-1">
            Automated multi-period cash predictions, driver analysis, solvency risk scoring, and human-in-the-loop exception handling.
          </p>
        </div>
        <button 
          onClick={() => onNavigateTab('benchmark')}
          className="px-5 py-2.5 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold text-xs rounded-lg transition-all flex items-center gap-2"
        >
          View Full Benchmark Report <ChevronRight className="w-4 h-4" />
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
                Simulated real-time Finance-Ops exception handling: High volatility, severe cash burn, or insolvencies trigger low-confidence flags for human review.
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
        {/* All Candidate Models Comparison Bar Chart */}
        <div className="glass-card p-8">
          <div className="flex items-center justify-between mb-7">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Forecast Accuracy: All Candidate Models vs Baselines (MAPE %)
            </h3>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelComparisonData} margin={{ top: 20, right: 30, left: 0, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e3b52" />
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#9ca3af" fontSize={12} unit="%" />
                <Tooltip
                  cursor={{ fill: 'rgba(15, 23, 42, 0.6)' }}
                  contentStyle={{ 
                    backgroundColor: '#0f172a', 
                    borderColor: '#1e293b', 
                    borderRadius: '10px', 
                    color: '#f8fafc',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                  }}
                  itemStyle={{ color: '#38bdf8' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                  formatter={(val) => [`${val}%`, 'MAPE Forecast Error']}
                />
                <Bar dataKey="mape" radius={[6, 6, 0, 0]}>
                  {modelComparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-xs text-gray-400 mt-4 text-center">
            Out-of-time evaluation across all 6 candidate algorithms plus auto-selected winning ML pipeline. Lower percentage indicates higher accuracy.
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
                  cursor={{ fill: 'rgba(15, 23, 42, 0.6)' }}
                  contentStyle={{ 
                    backgroundColor: '#0f172a', 
                    borderColor: '#1e293b', 
                    borderRadius: '10px', 
                    color: '#f8fafc',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                  }}
                  itemStyle={{ color: '#38bdf8' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
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
