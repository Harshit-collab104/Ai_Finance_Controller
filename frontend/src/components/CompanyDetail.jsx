import React, { useState, useEffect } from 'react';
import { 
  Building2, TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, 
  DollarSign, Activity, FileText, ChevronRight, BarChart3, LineChart, ShieldAlert, CheckCircle2 
} from 'lucide-react';
import { 
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { apiFetch } from '../apiConfig';

export default function CompanyDetail({ companies, selectedCompanyId, onSelectCompany }) {
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedCompanyId) {
      fetchCompanyDetail(selectedCompanyId);
    }
  }, [selectedCompanyId]);

  const fetchCompanyDetail = async (cId) => {
    setLoading(true);
    try {
      const res = await apiFetch(`/api/companies/${cId}`);
      const data = await res.json();
      setCompanyData(data);
    } catch (err) {
      console.error("Failed to fetch company details:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading Financial Records for {selectedCompanyId}...</div>;
  }

  if (!companyData) {
    return <div className="p-8 text-center text-gray-400">Select a company to inspect financial statements & forecasts.</div>;
  }

  const { company_id, company_name, category, latest_metrics, ratios, history, cash_forecast, confidence, risk } = companyData;

  const chartData = history.map(h => ({
    period: h.period,
    Cash: h.cash,
    Revenue: h.revenue,
    OperatingCashFlow: h.operating_cash_flow,
    NetIncome: h.net_income,
    type: 'Historical'
  }));

  const lastPeriod = history[history.length - 1].period;
  const [lastYearStr, lastQStr] = lastPeriod.split('-Q');
  let yr = parseInt(lastYearStr);
  let q = parseInt(lastQStr);

  cash_forecast.predictions_30_60_90.forEach((p, idx) => {
    q += 1;
    if (q > 4) {
      q = 1;
      yr += 1;
    }
    const fPeriod = `${yr}-Q${q} (FC)`;
    chartData.push({
      period: fPeriod,
      ForecastCash: p,
      type: 'Forecast'
    });
  });

  const isPositiveChange = cash_forecast.expected_change >= 0;
  const isResolved = confidence.resolution_status === 'RESOLVED';
  const displayName = company_name && company_name !== 'CO' ? company_name : `Company ${company_id}`;

  return (
    <div className="space-y-6">
      {/* Top Header & Resolution Status Badge */}
      <div className="glass-panel p-5 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white">{displayName}</h2>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-md bg-gray-800 text-gray-300 border border-gray-700">
                {company_id}
              </span>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {category}
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-0.5">Latest Financial Statement Period: {latest_metrics.period}</div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 border ${
            isResolved 
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
              : 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse'
          }`}>
            {isResolved ? <CheckCircle2 className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
            Status: {confidence.resolution_status}
          </div>

          <select 
            value={selectedCompanyId} 
            onChange={(e) => onSelectCompany(e.target.value)}
            className="bg-gray-900 text-white text-sm border border-gray-700 rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
          >
            {companies.map(c => (
              <option key={c.company_id} value={c.company_id}>
                {c.company_id} - {c.company_name && c.company_name !== 'CO' ? c.company_name : `Company ${c.company_id}`} ({c.category})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Finance-Ops Loop 5-Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="glass-card p-5">
          <div className="text-xs text-gray-400 mb-1 font-medium">Current Financial Position</div>
          <div className="text-2xl font-bold text-white">{latest_metrics.cash.toFixed(2)} Cr</div>
          <div className="text-xs text-gray-400 mt-1">Revenue: {latest_metrics.revenue.toFixed(1)} Cr | Net Inc: {latest_metrics.net_income.toFixed(1)} Cr</div>
        </div>

        <div className="glass-card p-5">
          <div className="text-xs text-gray-400 mb-1 font-medium">Forward 90-Day Cash Forecast</div>
          <div className="text-2xl font-bold text-cyan-400">
            {cash_forecast.predictions_30_60_90[2].toFixed(2)} Cr
          </div>
          <div className={`text-xs font-semibold mt-1 flex items-center gap-1 ${isPositiveChange ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isPositiveChange ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            {cash_forecast.expected_change > 0 ? '+' : ''}{cash_forecast.expected_change.toFixed(2)} Cr expected shift
          </div>
        </div>

        <div className="glass-card p-5">
          <div className="text-xs text-gray-400 mb-1 font-medium">Financial Risk Assessment</div>
          <div className={`text-2xl font-bold mt-0.5 ${
            risk.risk_level === 'HIGH RISK' ? 'text-rose-400' :
            risk.risk_level === 'MEDIUM RISK' ? 'text-amber-400' : 'text-emerald-400'
          }`}>
            {risk.risk_level}
          </div>
          <div className="text-xs text-gray-400 mt-1">Risk Score: {typeof risk.risk_score === 'number' ? risk.risk_score.toFixed(1) : risk.risk_score}/10</div>
        </div>

        <div className="glass-card p-5">
          <div className="text-xs text-gray-400 mb-1 font-medium">Forecast Confidence</div>
          <div className="mt-1">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
              confidence.confidence_status.includes('HIGH') ? 'badge-high' :
              confidence.confidence_status.includes('MEDIUM') ? 'badge-medium' : 'badge-low'
            }`}>
              {confidence.confidence_status.includes('HIGH') ? <ShieldCheck className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
              {confidence.confidence_status} ({confidence.confidence_score * 100}%)
            </span>
          </div>
          <div className="text-xs text-gray-400 mt-2 truncate">Model: {cash_forecast.model}</div>
        </div>
      </div>

      {/* Operational Controller Action Card */}
      <div className={`p-5 rounded-xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
        isResolved 
          ? 'bg-cyan-500/10 border-cyan-500/30' 
          : 'bg-rose-500/10 border-rose-500/30'
      }`}>
        <div className="space-y-1">
          <div className="text-xs uppercase font-bold tracking-wider text-gray-400">Grounded Controller Action & Recommendation</div>
          <div className={`text-sm font-semibold ${isResolved ? 'text-cyan-200' : 'text-rose-200'}`}>
            {confidence.controller_action}
          </div>
        </div>
        <div className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-gray-300">
          Target: {confidence.target}
        </div>
      </div>

      {/* Main Historical vs Forecast Trajectory Chart */}
      <div className="glass-card p-6">
        <div className="flex flex-wrap items-center justify-between mb-4 gap-2">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <LineChart className="w-5 h-5 text-cyan-400" />
            Historical Cash Position vs 90-Day Forward Forecast Trajectory
          </h3>
          <div className="text-xs text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/30">
            Statistical Model: {cash_forecast.model}
          </div>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2e3b52" />
              <XAxis dataKey="period" stroke="#9ca3af" fontSize={11} />
              <YAxis stroke="#9ca3af" fontSize={11} label={{ value: 'Amount (Cr)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
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
              <Legend wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }} />
              <Bar dataKey="Revenue" fill="#3b82f6" opacity={0.3} barSize={20} />
              <Line type="monotone" dataKey="Cash" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} name="Historical Cash" />
              <Line type="monotone" dataKey="OperatingCashFlow" stroke="#f59e0b" strokeWidth={2} strokeDasharray="3 3" name="Operating Cash Flow" />
              <Line type="monotone" dataKey="ForecastCash" stroke="#06b6d4" strokeWidth={3} strokeDasharray="5 5" dot={{ r: 6, fill: '#06b6d4' }} name="Forecasted Cash (FC)" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Ratios & Drivers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Key Financial Indicators
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-800">
              <div className="text-xs text-gray-400">Current Ratio</div>
              <div className="text-lg font-bold text-white mt-0.5">{ratios.current_ratio?.toFixed(2)}</div>
              <div className="text-xs text-gray-400">Quick Ratio: {ratios.quick_ratio?.toFixed(2)}</div>
            </div>

            <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-800">
              <div className="text-xs text-gray-400">Debt-to-Equity</div>
              <div className="text-lg font-bold text-white mt-0.5">{ratios.debt_to_equity?.toFixed(2)}</div>
              <div className="text-xs text-gray-400">Interest Coverage: {ratios.interest_coverage?.toFixed(1)}x</div>
            </div>

            <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-800">
              <div className="text-xs text-gray-400">Gross Margin</div>
              <div className="text-lg font-bold text-white mt-0.5">{(ratios.gross_margin * 100)?.toFixed(1)}%</div>
              <div className="text-xs text-gray-400">Net Margin: {(ratios.net_profit_margin * 100)?.toFixed(1)}%</div>
            </div>

            <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-800">
              <div className="text-xs text-gray-400">Cash Burn Rate</div>
              <div className="text-lg font-bold text-white mt-0.5">{ratios.cash_burn_rate?.toFixed(2)} Cr</div>
              <div className="text-xs text-gray-400">OCF Trend Slope: {ratios.ocf_trend_slope?.toFixed(2)}</div>
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            Operational Drivers & Risk Analysis
          </h3>
          <div className="space-y-4">
            <div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Calculated Operational Drivers:</div>
              <ul className="space-y-1">
                {confidence.financial_drivers.map((d, idx) => (
                  <li key={idx} className="text-xs text-gray-300 flex items-start gap-2">
                    <span className="text-cyan-400 font-bold">•</span> {d}
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-3 border-t border-gray-800">
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Primary Confidence & Exception Triggers:</div>
              <ul className="space-y-1">
                {confidence.reasons.map((r, idx) => (
                  <li key={idx} className="text-xs text-gray-300 flex items-start gap-2">
                    <span className="text-rose-400 font-bold">•</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
