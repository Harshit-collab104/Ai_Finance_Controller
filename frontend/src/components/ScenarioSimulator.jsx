import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Sliders, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { apiFetch } from '../apiConfig';

export default function ScenarioSimulator({ selectedCompanyId, companies }) {
  const [revChange, setRevChange] = useState(-10);
  const [opexChange, setOpexChange] = useState(0);
  const [capexAdj, setCapexAdj] = useState(0);
  const [scenarioRes, setScenarioRes] = useState(null);
  const debounceTimerRef = useRef(null);

  // Debounced API fetch so backend calls don't flood on every pixel slider drag tick
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      runSimulation();
    }, 200);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [selectedCompanyId, revChange, opexChange, capexAdj]);

  const runSimulation = async () => {
    try {
      const res = await apiFetch('/api/scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: selectedCompanyId,
          revenue_change_pct: revChange / 100.0,
          opex_change_pct: opexChange / 100.0,
          capex_adjustment: capexAdj
        })
      });

      const data = await res.json();
      setScenarioRes(data);
    } catch (err) {
      console.error("Scenario simulation error:", err);
    }
  };

  const activeCompanyObj = companies.find(c => c.company_id === selectedCompanyId);
  const companyName = scenarioRes?.company_name || activeCompanyObj?.company_name || `Company ${selectedCompanyId}`;
  
  const curCash = scenarioRes?.baseline_latest?.cash_balance ?? activeCompanyObj?.current_cash ?? 50.0;
  const baseFc90d = scenarioRes?.baseline_latest?.forecast_cash_90d ?? activeCompanyObj?.forecast_cash_90d ?? 45.0;
  const curOpex = activeCompanyObj?.operating_expenses ?? (curCash * 0.25);

  // Instant 60FPS real-time synchronous chart computation for smooth slider drag
  const chartData = useMemo(() => {
    const revShift = revChange / 100.0;
    const opexShift = opexChange / 100.0;
    
    // Calculate 30-day, 60-day, and 90-day scenario impacts including OpEx shift
    const revDelta90 = (curCash * 0.35) * revShift;
    const opexDelta90 = (curOpex * 0.35) * opexShift;
    const totalImpact90 = revDelta90 - opexDelta90 - capexAdj;

    const impact30 = totalImpact90 * 0.33;
    const impact60 = totalImpact90 * 0.66;
    const impact90 = totalImpact90;

    const q1Base = curCash + (baseFc90d - curCash) * 0.33;
    const q2Base = curCash + (baseFc90d - curCash) * 0.66;
    const q3Base = baseFc90d;

    return [
      { period: 'Current', Baseline: curCash, Scenario: curCash },
      { period: 'Month 1 / Q1', Baseline: roundVal(q1Base), Scenario: roundVal(q1Base + impact30) },
      { period: 'Month 2 / Q2', Baseline: roundVal(q2Base), Scenario: roundVal(q2Base + impact60) },
      { period: 'Month 3 / Q3', Baseline: roundVal(q3Base), Scenario: roundVal(q3Base + impact90) },
    ];
  }, [selectedCompanyId, revChange, opexChange, capexAdj, curCash, baseFc90d, curOpex]);

  function roundVal(v) {
    return Math.max(0.0, Math.round(v * 100) / 100);
  }

  const scenario90d = chartData[3]?.Scenario || baseFc90d;
  const deltaImpact = roundVal(scenario90d - baseFc90d);

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="glass-panel p-5 rounded-xl flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400" />
            What-If Scenario Simulator: {companyName} ({selectedCompanyId})
          </h2>
          <div className="text-xs text-gray-400 mt-1">
            Simulate revenue shocks, operating cost changes, or CapEx adjustments on cash flow trajectory.
          </div>
        </div>
        <div className="text-xs text-amber-400 bg-amber-500/10 px-3 py-1.5 rounded-lg border border-amber-500/30">
          ⚠️ Scenario Simulation (Not Baseline Model Prediction)
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive Sliders Panel */}
        <div className="glass-card p-6 space-y-6 select-none">
          <h3 className="text-lg font-semibold text-white">Adjust Parameters</h3>

          {/* Revenue Change Slider */}
          <div>
            <div className="flex justify-between text-xs text-gray-300 font-medium mb-1">
              <span>Revenue Shift (%)</span>
              <span className={revChange >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {revChange > 0 ? '+' : ''}{revChange}%
              </span>
            </div>
            <input 
              type="range" 
              min="-30" 
              max="30" 
              value={revChange} 
              onChange={(e) => setRevChange(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 touch-none select-none"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1">
              <span>-30% Demand Shock</span>
              <span>0% Baseline</span>
              <span>+30% Expansion</span>
            </div>
          </div>

          {/* OpEx Change Slider */}
          <div>
            <div className="flex justify-between text-xs text-gray-300 font-medium mb-1">
              <span>Operating Expenses Shift (%)</span>
              <span className={opexChange <= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {opexChange > 0 ? '+' : ''}{opexChange}%
              </span>
            </div>
            <input 
              type="range" 
              min="-20" 
              max="20" 
              value={opexChange} 
              onChange={(e) => setOpexChange(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 touch-none select-none"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1">
              <span>-20% Cost Cut</span>
              <span>0% Baseline</span>
              <span>+20% Inflation</span>
            </div>
          </div>

          {/* CapEx Adjustment Slider */}
          <div>
            <div className="flex justify-between text-xs text-gray-300 font-medium mb-1">
              <span>CapEx Outflow Adjustment (Cr)</span>
              <span className={capexAdj <= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {capexAdj > 0 ? '+' : ''}{capexAdj} Cr
              </span>
            </div>
            <input 
              type="range" 
              min="-10" 
              max="10" 
              value={capexAdj} 
              onChange={(e) => setCapexAdj(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 touch-none select-none"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1">
              <span>-10 Cr CapEx Deferral</span>
              <span>0 Cr Baseline</span>
              <span>+10 Cr Expansion</span>
            </div>
          </div>

          <button 
            onClick={() => { setRevChange(-10); setOpexChange(0); setCapexAdj(0); }}
            className="w-full py-2 text-xs font-semibold text-gray-400 bg-gray-900 hover:text-white rounded-lg border border-gray-800 transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reset Parameters
          </button>
        </div>

        {/* Comparison Table & Instant Recharts Line Chart */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="glass-card p-4">
              <div className="text-xs text-gray-400">Baseline 90D Cash</div>
              <div className="text-lg font-bold text-white mt-1">{baseFc90d.toFixed(2)} Cr</div>
            </div>

            <div className="glass-card p-4">
              <div className="text-xs text-gray-400">Scenario 90D Cash</div>
              <div className="text-lg font-bold text-cyan-400 mt-1">{scenario90d.toFixed(2)} Cr</div>
            </div>

            <div className="glass-card p-4">
              <div className="text-xs text-gray-400">Scenario Net Impact</div>
              <div className={`text-lg font-bold mt-1 ${deltaImpact >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {deltaImpact > 0 ? '+' : ''}{deltaImpact.toFixed(2)} Cr
              </div>
            </div>

            <div className="glass-card p-4">
              <div className="text-xs text-gray-400">Adjusted Net Income</div>
              <div className="text-lg font-bold text-white mt-1">
                {(scenarioRes?.scenario_latest?.net_income ?? ((activeCompanyObj?.net_income || 0) * (1 + revChange/100.0 - opexChange/100.0))).toFixed(2)} Cr
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Baseline vs Scenario Cash Trajectory</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart 
                  key={`chart-${selectedCompanyId}`}
                  data={chartData} 
                  margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#2e3b52" />
                  <XAxis dataKey="period" stroke="#9ca3af" fontSize={11} />
                  <YAxis stroke="#9ca3af" fontSize={11} label={{ value: 'Cash (Cr)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
                  <Tooltip 
                    cursor={{ stroke: '#38bdf8', strokeWidth: 1, strokeDasharray: '4 4' }}
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
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="Baseline" 
                    stroke="#10b981" 
                    strokeWidth={2.5} 
                    name="Baseline Forecast" 
                    isAnimationActive={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="Scenario" 
                    stroke="#f43f5e" 
                    strokeWidth={2.5} 
                    strokeDasharray="4 4" 
                    name="Scenario Simulation" 
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
