import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { getPortfolios, getPortfolioDetail } from '../utils/api';
import { formatNumber, formatCurrency, getGradeClass, getGradeColor, getScoreColor } from '../utils/helpers';

const COLORS = ['#059669','#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1'];
const PAGE_SIZE = 20;

// Tab configuration for recommendation actions
const TAB_CONFIG: Record<string, { label: string; color: string; bgClass: string; borderClass: string; badgeClass: string; iconBg: string; icon: 'sell' | 'rebalance' | 'hold' }> = {
  sell: {
    label: 'Vender',
    color: 'red',
    bgClass: 'bg-red-50 border-red-200',
    borderClass: 'border-red-500 text-red-700',
    badgeClass: 'bg-red-200 text-red-800',
    iconBg: 'bg-red-100',
    icon: 'sell',
  },
  rebalance: {
    label: 'Rebalancear',
    color: 'amber',
    bgClass: 'bg-amber-50 border-amber-200',
    borderClass: 'border-amber-500 text-amber-700',
    badgeClass: 'bg-amber-200 text-amber-800',
    iconBg: 'bg-amber-100',
    icon: 'rebalance',
  },
  hold: {
    label: 'Manter',
    color: 'green',
    bgClass: 'bg-green-50 border-green-200',
    borderClass: 'border-green-500 text-green-700',
    badgeClass: 'bg-green-200 text-green-800',
    iconBg: 'bg-green-100',
    icon: 'hold',
  },
};

export default function Portfolio() {
  const [portfolioId, setPortfolioId] = useState<number | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [posPage, setPosPage] = useState(1);
  const [posTotalPages, setPosTotalPages] = useState(1);
  const [posTotal, setPosTotal] = useState(0);
  const [activeRecTab, setActiveRecTab] = useState<string>('sell');

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (portfolioId) {
      loadDetail(portfolioId, posPage);
    }
  }, [posPage]);

  const loadPortfolios = async () => {
    try {
      const res = await getPortfolios();
      if (res.data.length > 0) {
        setPortfolioId(res.data[0].id);
        await loadDetail(res.data[0].id, 1);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (id: number, page: number) => {
    try {
      const d = await getPortfolioDetail(id, { page, page_size: PAGE_SIZE });
      setDetail(d.data);
      const pagination = d.data?.metrics?.positions_pagination;
      if (pagination) {
        setPosTotalPages(pagination.total_pages || 1);
        setPosTotal(pagination.total || 0);
      }
      // Set first available tab
      const grouped = d.data?.metrics?.recommendations_grouped;
      if (grouped) {
        const tabOrder = ['sell', 'rebalance', 'hold'];
        const firstAvailable = tabOrder.find(t => grouped[t]?.length > 0);
        if (firstAvailable) setActiveRecTab(firstAvailable);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const goToPage = (p: number) => {
    if (p >= 1 && p <= posTotalPages) setPosPage(p);
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>
  );

  const metrics = detail?.metrics;

  const typeData = Object.entries(metrics?.project_type_distribution || {}).map(([name, value]: any, idx) => ({
    name: name.length > 12 ? name.slice(0, 12) + '...' : name,
    value,
    fill: COLORS[idx % COLORS.length],
  }));

  const countryData = Object.entries(metrics?.country_distribution || {}).map(([name, value]: any, idx) => ({
    name, value, fill: COLORS[idx % COLORS.length],
  }));

  const gradeData = Object.entries(metrics?.grade_distribution || {}).map(([grade, count]: any) => ({
    grade, count, fill: getGradeColor(grade),
  }));

  const riskData = [
    { name: 'Baixo Risco', value: metrics?.risk_exposure?.low || 0, fill: '#22c55e' },
    { name: 'Risco Médio', value: metrics?.risk_exposure?.medium || 0, fill: '#f59e0b' },
    { name: 'Alto Risco', value: metrics?.risk_exposure?.high || 0, fill: '#ef4444' },
  ];

  const posStartItem = (posPage - 1) * PAGE_SIZE + 1;
  const posEndItem = Math.min(posPage * PAGE_SIZE, posTotal);

  // Grouped recommendations
  const recGrouped = metrics?.recommendations_grouped || {};
  const tabOrder = ['sell', 'rebalance', 'hold'];
  const availableTabs = tabOrder.filter(t => recGrouped[t]?.length > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard de Portfólio</h1>
        <p className="text-slate-500 mt-1">Risco agregado, qualidade e recomendações de rebalanceamento &middot; {posTotal} posições</p>
      </div>

      {detail && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard label="Total de Créditos" value={formatNumber(metrics?.total_credits || 0)} color="emerald" />
            <SummaryCard label="Valor Total" value={formatCurrency(metrics?.total_value_usd || 0)} color="blue" />
            <SummaryCard label="Score Médio" value={`${(metrics?.avg_quality_score || 0).toFixed(1)}/100`} color="amber" />
            <SummaryCard label="Posições" value={String(posTotal)} color="purple" />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Distribuição de Ratings no Portfólio</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={gradeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="grade" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" name="Créditos" radius={[4, 4, 0, 0]}>
                    {gradeData.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Exposição a Risco</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={riskData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} dataKey="value" paddingAngle={3}
                    label={({ name, value }) => value > 0 ? `${name}: ${formatNumber(value)}` : ''}>
                    {riskData.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Concentração por Tipo</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={typeData} cx="50%" cy="50%" outerRadius={90} dataKey="value"
                    label={({ name, value }) => `${name}: ${formatNumber(value)}`}>
                    {typeData.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Concentração Geográfica</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={countryData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={100} />
                  <Tooltip />
                  <Bar dataKey="value" name="Créditos" radius={[0, 4, 4, 0]}>
                    {countryData.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Positions Table with Pagination */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-6 pb-0">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Posições do Portfólio</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="text-left py-3 px-4 font-semibold text-slate-600">Projeto</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-600">Tipo</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-600">País</th>
                    <th className="text-center py-3 px-4 font-semibold text-slate-600">Rating</th>
                    <th className="text-center py-3 px-4 font-semibold text-slate-600">Score</th>
                    <th className="text-right py-3 px-4 font-semibold text-slate-600">Quantidade</th>
                    <th className="text-right py-3 px-4 font-semibold text-slate-600">Preço</th>
                    <th className="text-right py-3 px-4 font-semibold text-slate-600">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics?.positions?.map((pos: any) => (
                    <tr key={pos.position_id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-4">
                        <Link to={`/projects/${pos.project_id}`} className="font-medium text-emerald-600 hover:text-emerald-700">
                          {pos.project_name?.length > 35 ? pos.project_name.slice(0, 35) + '...' : pos.project_name}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-slate-600">{pos.project_type}</td>
                      <td className="py-3 px-4 text-slate-600">{pos.country}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-flex items-center justify-center w-10 h-6 rounded text-xs font-bold ${getGradeClass(pos.grade)}`}>
                          {pos.grade}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono" style={{ color: getScoreColor(pos.score) }}>
                        {pos.score.toFixed(1)}
                      </td>
                      <td className="py-3 px-4 text-right font-mono">{formatNumber(pos.quantity)}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatCurrency(pos.price_usd)}</td>
                      <td className="py-3 px-4 text-right font-mono font-medium">
                        {formatCurrency(pos.quantity * pos.price_usd)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {posTotal > 0 && (
              <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50 gap-3">
                <div className="text-sm text-slate-500">
                  Mostrando <span className="font-medium text-slate-700">{posStartItem}</span> a <span className="font-medium text-slate-700">{posEndItem}</span> de <span className="font-medium text-slate-700">{posTotal}</span> posições
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={() => goToPage(1)} disabled={posPage === 1}
                    className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                    <ChevronsLeft className="w-4 h-4" />
                  </button>
                  <button onClick={() => goToPage(posPage - 1)} disabled={posPage === 1}
                    className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                    <ChevronLeft className="w-4 h-4" />
                  </button>

                  {Array.from({ length: posTotalPages }, (_, i) => i + 1)
                    .filter(p => p === 1 || p === posTotalPages || Math.abs(p - posPage) <= 1)
                    .reduce((acc: (number | string)[], p, idx, arr) => {
                      if (idx > 0 && typeof arr[idx - 1] === 'number' && (p as number) - (arr[idx - 1] as number) > 1) {
                        acc.push('...');
                      }
                      acc.push(p);
                      return acc;
                    }, [])
                    .map((p, idx) =>
                      typeof p === 'string' ? (
                        <span key={`ellipsis-${idx}`} className="px-2 text-slate-400 text-sm">...</span>
                      ) : (
                        <button key={p} onClick={() => goToPage(p as number)}
                          className={`min-w-[36px] h-9 rounded-md border text-sm font-medium transition-colors ${
                            posPage === p
                              ? 'bg-emerald-600 border-emerald-600 text-white'
                              : 'border-slate-300 text-slate-600 hover:bg-white hover:text-slate-800'
                          }`}>
                          {p}
                        </button>
                      )
                    )}

                  <button onClick={() => goToPage(posPage + 1)} disabled={posPage === posTotalPages}
                    className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                  <button onClick={() => goToPage(posTotalPages)} disabled={posPage === posTotalPages}
                    className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                    <ChevronsRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* ─── Recommendations with Tabs ─────────────────────────────── */}
          {availableTabs.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="p-6 pb-0">
                <h3 className="text-lg font-semibold text-slate-900 mb-1">Recomendações de Rebalanceamento</h3>
                <p className="text-sm text-slate-500 mb-4">
                  Projetos agrupados por ação recomendada &middot; {metrics?.recommendations?.length || 0} recomendações
                </p>
              </div>

              {/* Tab Headers */}
              <div className="flex border-b border-slate-200 px-6">
                {availableTabs.map(tabKey => {
                  const cfg = TAB_CONFIG[tabKey];
                  const count = recGrouped[tabKey]?.length || 0;
                  const isActive = activeRecTab === tabKey;
                  return (
                    <button
                      key={tabKey}
                      onClick={() => setActiveRecTab(tabKey)}
                      className={`relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                        isActive
                          ? `${cfg.borderClass} border-b-2 -mb-px`
                          : 'text-slate-500 hover:text-slate-700 border-b-2 border-transparent -mb-px'
                      }`}
                    >
                      {tabKey === 'sell' && <TrendingDown className="w-4 h-4" />}
                      {tabKey === 'rebalance' && <AlertTriangle className="w-4 h-4" />}
                      {tabKey === 'hold' && <TrendingUp className="w-4 h-4" />}
                      {cfg.label}
                      <span className={`inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-xs font-bold ${
                        isActive ? cfg.badgeClass : 'bg-slate-200 text-slate-600'
                      }`}>
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {availableTabs.map(tabKey => {
                  if (tabKey !== activeRecTab) return null;
                  const cfg = TAB_CONFIG[tabKey];
                  const items = recGrouped[tabKey] || [];
                  return (
                    <div key={tabKey} className="space-y-3">
                      {items.map((rec: any, idx: number) => (
                        <div key={idx} className={`flex items-start gap-3 p-4 rounded-lg border ${cfg.bgClass}`}>
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${cfg.iconBg}`}>
                            {tabKey === 'sell' && <TrendingDown className="w-4 h-4 text-red-600" />}
                            {tabKey === 'rebalance' && <AlertTriangle className="w-4 h-4 text-amber-600" />}
                            {tabKey === 'hold' && <TrendingUp className="w-4 h-4 text-green-600" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${cfg.badgeClass}`}>
                                {cfg.label.toUpperCase()}
                              </span>
                              {rec.project_id ? (
                                <Link to={`/projects/${rec.project_id}`} className="font-medium text-slate-900 hover:text-emerald-600 truncate">
                                  {rec.project_name}
                                </Link>
                              ) : (
                                <span className="font-medium text-slate-900 truncate">{rec.project_name}</span>
                              )}
                              {rec.current_grade && rec.current_grade !== 'N/A' && (
                                <span className={`inline-flex items-center justify-center w-10 h-5 rounded text-xs font-bold ${getGradeClass(rec.current_grade)}`}>
                                  {rec.current_grade}
                                </span>
                              )}
                              {rec.current_score > 0 && (
                                <span className="text-xs font-mono" style={{ color: getScoreColor(rec.current_score) }}>
                                  {rec.current_score.toFixed(0)}/100
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-slate-600 mt-1">{rec.reason}</p>
                          </div>
                        </div>
                      ))}
                      {items.length === 0 && (
                        <p className="text-sm text-slate-500 text-center py-8">Nenhuma recomendação nesta categoria.</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colorMap: Record<string, string> = {
    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    amber: 'bg-amber-50 border-amber-200 text-amber-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
  };
  return (
    <div className={`rounded-xl border p-5 ${colorMap[color]}`}>
      <p className="text-sm font-medium opacity-70">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}
