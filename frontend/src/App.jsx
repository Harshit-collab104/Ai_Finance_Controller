import React, { useState, useEffect } from 'react';
import { 
  Building2, LayoutDashboard, LineChart, MessageSquare, Sliders, 
  Award, ShieldAlert, Activity, RefreshCw 
} from 'lucide-react';
import { apiFetch } from './apiConfig';

import PortfolioOverview from './components/PortfolioOverview';
import CompanyDetail from './components/CompanyDetail';
import AgentChat from './components/AgentChat';
import ScenarioSimulator from './components/ScenarioSimulator';
import BenchmarkReport from './components/BenchmarkReport';

export default function App() {
  const [activeTab, setActiveTab] = useState('portfolio');
  const [summary, setSummary] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState('C014');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [sumRes, compRes] = await Promise.all([
        apiFetch('/api/portfolio/summary'),
        apiFetch('/api/companies')
      ]);

      const sumData = await sumRes.json();
      const compData = await compRes.json();
      setSummary(sumData);
      setCompanies(compData);
    } catch (err) {
      console.error("Backend connection error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-gray-100 flex flex-col">
      {/* Top Header Navigation */}
      <header className="border-b border-gray-800 bg-[#111827]/90 backdrop-blur-md sticky top-0 z-50 py-3.5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20 shrink-0">
              <Activity className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-lg font-bold text-white tracking-wide flex items-center gap-2">
                AI FORWARD CASH CONTROLLER
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  Forward Cash Forecaster
                </span>
              </h1>
            </div>
          </div>

          {/* Nav Tabs - All in One Line */}
          <nav className="flex items-center gap-1.5 bg-gray-900/80 p-1.5 rounded-xl border border-gray-800 overflow-x-auto max-w-full no-scrollbar shrink-0">
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${
                activeTab === 'portfolio' 
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Portfolio Overview
            </button>

            <button
              onClick={() => setActiveTab('company')}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${
                activeTab === 'company' 
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <LineChart className="w-4 h-4" />
              Company Deep-Dive
            </button>

            <button
              onClick={() => setActiveTab('agent')}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${
                activeTab === 'agent' 
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              AI Agent Chat
            </button>

            <button
              onClick={() => setActiveTab('scenario')}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${
                activeTab === 'scenario' 
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <Sliders className="w-4 h-4" />
              Scenario Simulator
            </button>

            <button
              onClick={() => setActiveTab('benchmark')}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${
                activeTab === 'benchmark' 
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <Award className="w-4 h-4" />
              Benchmark & Exceptions
            </button>
          </nav>
        </div>
      </header>

      {/* Main Body Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex-1 w-full">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 text-gray-400 gap-3">
            <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
            <div className="text-sm font-medium">Connecting to AI Forward Cash Controller Backend...</div>
          </div>
        ) : (
          <>
            {activeTab === 'portfolio' && (
              <PortfolioOverview 
                summary={summary} 
                onSelectCompany={(id) => { setSelectedCompanyId(id); setActiveTab('company'); }}
                onNavigateTab={(tab) => setActiveTab(tab)}
              />
            )}

            {activeTab === 'company' && (
              <CompanyDetail 
                companies={companies}
                selectedCompanyId={selectedCompanyId}
                onSelectCompany={setSelectedCompanyId}
              />
            )}

            {activeTab === 'agent' && (
              <AgentChat 
                selectedCompanyId={selectedCompanyId}
                onSelectCompany={setSelectedCompanyId}
                companies={companies}
              />
            )}

            {activeTab === 'scenario' && (
              <ScenarioSimulator 
                selectedCompanyId={selectedCompanyId}
                companies={companies}
              />
            )}

            {activeTab === 'benchmark' && (
              <BenchmarkReport />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-[#0b0f19] py-4 text-center text-xs text-gray-500">
        AI Finance Controller Challenge • Direction: Forward Cash Forecaster • 55 Companies • 1,240 Quarterly Observations
      </footer>
    </div>
  );
}
