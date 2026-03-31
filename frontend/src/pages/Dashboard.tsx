import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import { TreePine, ShieldAlert, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, ChevronDown, ChevronUp, Euro, RefreshCw, Activity } from 'lucide-react';
import { getDashboardMetrics, getFraudSummary, getRiskMatrix, getCarbonPrice } from '../utils/api';
import { formatNumber, formatCurrency, getGradeColor, getSeverityColor } from '../utils/helpers';


export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [fraudSummary, setFraudSummary] = useState<any>(null);
  const [riskMatrix, setRiskMatrix] = useState<any>(null);
  const [carbonPrice, setCarbonPrice] = useState<any>(null);
  const [priceLoading, setPriceLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [expandedCell, setExpandedCell] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getDashboardMetrics(),
      getFraudSummary(),
      getRiskMatrix(),
    ]).then(([m, f, r]) => {
      setMetrics(m.data);
      setFraudSummary(f.data);
      setRiskMatrix(r.data);
    }).catch(console.error)
      .finally(() => setLoading(false));

    loadCarbonPrice();
    // Auto-refresh carbon price every 5 minutes
    const interval = setInterval(loadCarbonPrice, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadCarbonPrice = async () => {
    setPriceLoading(true);
    try {
      const res = await getCarbonPrice();
      setCarbonPrice(res.data);
    } catch (err) { console.error('Erro ao carregar cotação:', err); }
    finally { setPriceLoading(false); }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>
  );

  if (!metrics) return <div className="text-red-500">Erro ao carregar dados</div>;

  const gradeData = Object.entries(metrics.grade_distribution || {}).map(([grade, count]) => ({
    grade, count, fill: getGradeColor(grade),
  }));

  const typeData = Object.entries(metrics.project_type_distribution || {}).map(([name, value]) => ({
    name: name.length > 15 ? name.slice(0, 15) + '...' : name, value,
  }));

  const countryData = Object.entries(metrics.country_distribution || {}).map(([name, value]) => ({
    name, value,
  }));

  const severityData = Object.entries(fraudSummary?.by_severity || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1), value, fill: getSeverityColor(name),
  }));

  // Risk matrix cell colors
  const getCellColor = (qualityKey: string, riskKey: string) => {
    const colorMap: Record<string, Record<string, string>> = {
      high: {
        none: 'bg-emerald-100 border-emerald-300 text-emerald-800',
        low: 'bg-emerald-50 border-emerald-200 text-emerald-700',
        medium: 'bg-amber-100 border-amber-300 text-amber-800',
        high: 'bg-red-100 border-red-300 text-red-800',
      },
      medium: {
        none: 'bg-blue-50 border-blue-200 text-blue-700',
        low: 'bg-amber-50 border-amber-200 text-amber-700',
        medium: 'bg-orange-100 border-orange-300 text-orange-800',
        high: 'bg-red-200 border-red-400 text-red-900',
      },
      low: {
        none: 'bg-amber-100 border-amber-300 text-amber-800',
        low: 'bg-orange-100 border-orange-300 text-orange-800',
        medium: 'bg-red-200 border-red-400 text-red-900',
        high: 'bg-red-300 border-red-500 text-red-950',
      },
    };
    return colorMap[qualityKey]?.[riskKey] || 'bg-slate-50 border-slate-200 text-slate-600';
  };

  const getCellStatus = (qualityKey: string, riskKey: string) => {
    if (qualityKey === 'high' && (riskKey === 'none' || riskKey === 'low')) return 'Seguro';
    if (qualityKey === 'low' && (riskKey === 'medium' || riskKey === 'high')) return 'Crítico';
    if (qualityKey === 'low' || riskKey === 'high') return 'Alto Risco';
    if (qualityKey === 'medium' || riskKey === 'medium') return 'Atenção';
    return 'Seguro';
  };

  const toggleCell = (key: string) => {
    setExpandedCell(expandedCell === key ? null : key);
  };

  const qualityLevels = riskMatrix?.quality_levels || [];
  const riskLevels = riskMatrix?.risk_levels || [];
  const grid = riskMatrix?.grid || {};

  // Carbon price data
  const priceChange = carbonPrice?.change_percent || 0;
  const priceIsUp = priceChange >= 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Visão geral da plataforma Carbon Verify</p>
      </div>

      {/* Carbon Price Ticker - Real-time */}
      {carbonPrice && (
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 rounded-xl p-5 text-white shadow-lg">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                <Activity className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium text-slate-400">Cotação do Crédito de Carbono (EU ETS)</h3>
                  {priceLoading && <RefreshCw className="w-3 h-3 text-slate-400 animate-spin" />}
                </div>
                <div className="flex items-baseline gap-3 mt-1">
                  <span className="text-3xl font-bold text-white">
                    {formatCurrency(carbonPrice.price_eur)}
                  </span>
                  <span className="text-sm text-slate-400">/tCO2e</span>
                  <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-sm font-medium ${
                    priceIsUp ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {priceIsUp ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                    {priceIsUp ? '+' : ''}{priceChange.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-6 text-sm">
              <div>
                <p className="text-slate-400 text-xs">Bolsa</p>
                <p className="font-medium">{carbonPrice.exchange || 'EU ETS (EEX)'}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Faixa do Dia</p>
                <p className="font-medium">
                  {formatCurrency(carbonPrice.day_low_eur || carbonPrice.price_eur * 0.98)} - {formatCurrency(carbonPrice.day_high_eur || carbonPrice.price_eur * 1.02)}
                </p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Volume</p>
                <p className="font-medium">{carbonPrice.volume || 'N/A'}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Atualizado</p>
                <p className="font-medium">{carbonPrice.last_updated || new Date().toLocaleTimeString('pt-BR')}</p>
              </div>
              <button onClick={loadCarbonPrice} disabled={priceLoading}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50"
                title="Atualizar cotação">
                <RefreshCw className={`w-4 h-4 ${priceLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Projetos Analisados"
          value={formatNumber(metrics.total_projects)}
          icon={TreePine}
          color="emerald"
        />
        <KPICard
          title="Score Médio de Qualidade"
          value={metrics.avg_quality_score.toFixed(1)}
          subtitle="/100"
          icon={TrendingUp}
          color="blue"
        />
        <KPICard
          title="Alertas de Fraude"
          value={formatNumber(metrics.fraud_alerts_count)}
          icon={ShieldAlert}
          color="red"
        />
        <KPICard
          title="Valor do Portfolio"
          value={formatCurrency(metrics.portfolio_value_eur || metrics.portfolio_value_usd || 0)}
          icon={Euro}
          color="amber"
        />
      </div>

      {/* Risk Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-4">
          <CheckCircle className="w-10 h-10 text-green-600 shrink-0" />
          <div>
            <p className="text-2xl font-bold text-green-700">{metrics.risk_summary.low_risk}</p>
            <p className="text-sm text-green-600">Baixo Risco (Score &gt; 60)</p>
          </div>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-4">
          <AlertTriangle className="w-10 h-10 text-amber-600 shrink-0" />
          <div>
            <p className="text-2xl font-bold text-amber-700">{metrics.risk_summary.medium_risk}</p>
            <p className="text-sm text-amber-600">Risco Médio (Score 40-60)</p>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-4">
          <ShieldAlert className="w-10 h-10 text-red-600 shrink-0" />
          <div>
            <p className="text-2xl font-bold text-red-700">{metrics.risk_summary.high_risk}</p>
            <p className="text-sm text-red-600">Alto Risco (Score &lt; 40)</p>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Distribuição de Ratings</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={gradeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="grade" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" name="Projetos" radius={[4, 4, 0, 0]}>
                {gradeData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Alertas por Severidade</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%" cy="50%"
                innerRadius={60} outerRadius={100}
                paddingAngle={3}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {severityData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Projetos por Tipo</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={typeData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
              <Tooltip />
              <Bar dataKey="value" name="Projetos" fill="#059669" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Projetos por País</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={countryData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="value" name="Projetos" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Matrix - Tabela Quadriculada */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900">Matriz de Risco: Qualidade vs Alertas de Fraude</h3>
          <p className="text-sm text-slate-500 mt-1">
            Cada célula mostra a quantidade de projetos na interseção entre nível de qualidade e nível de risco. Clique para expandir e ver os projetos.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="p-3 text-left text-sm font-semibold text-slate-600 bg-slate-50 border border-slate-200 w-48">
                  Qualidade \\ Risco
                </th>
                {riskLevels.map((rl: any) => (
                  <th key={rl.key} className="p-3 text-center text-sm font-semibold text-slate-600 bg-slate-50 border border-slate-200 min-w-[160px]">
                    {rl.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {qualityLevels.map((ql: any) => (
                <tr key={ql.key}>
                  <td className="p-3 text-sm font-semibold text-slate-700 bg-slate-50 border border-slate-200">
                    {ql.label}
                  </td>
                  {riskLevels.map((rl: any) => {
                    const cell = grid[ql.key]?.[rl.key];
                    const count = cell?.count || 0;
                    const cellKey = `${ql.key}-${rl.key}`;
                    const isExpanded = expandedCell === cellKey;
                    const colorClass = getCellColor(ql.key, rl.key);
                    const statusLabel = getCellStatus(ql.key, rl.key);

                    return (
                      <td key={rl.key} className={`border border-slate-200 p-0 align-top`}>
                        <button
                          onClick={() => count > 0 && toggleCell(cellKey)}
                          className={`w-full p-3 text-center transition-all ${colorClass} ${count > 0 ? 'cursor-pointer hover:opacity-80' : 'cursor-default opacity-60'}`}
                          disabled={count === 0}
                        >
                          <div className="flex flex-col items-center gap-1">
                            <span className="text-2xl font-bold">{count}</span>
                            <span className="text-xs font-medium opacity-75">{count === 1 ? 'projeto' : 'projetos'}</span>
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full mt-1 ${
                              statusLabel === 'Seguro' ? 'bg-green-200/50 text-green-900' :
                              statusLabel === 'Atenção' ? 'bg-amber-200/50 text-amber-900' :
                              statusLabel === 'Alto Risco' ? 'bg-red-200/50 text-red-900' :
                              'bg-red-300/50 text-red-950'
                            }`}>
                              {statusLabel}
                            </span>
                            {count > 0 && (
                              <span className="mt-1">
                                {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                              </span>
                            )}
                          </div>
                        </button>

                        {isExpanded && cell?.projects && (
                          <div className="border-t border-slate-200 bg-white p-2 max-h-48 overflow-y-auto">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="border-b border-slate-100">
                                  <th className="text-left py-1 px-1 font-medium text-slate-500">Projeto</th>
                                  <th className="text-center py-1 px-1 font-medium text-slate-500">Score</th>
                                  <th className="text-center py-1 px-1 font-medium text-slate-500">Grade</th>
                                </tr>
                              </thead>
                              <tbody>
                                {cell.projects.slice(0, 15).map((p: any) => (
                                  <tr key={p.project_id} className="border-b border-slate-50 hover:bg-slate-50">
                                    <td className="py-1 px-1">
                                      <Link to={`/projects/${p.project_id}`} className="text-emerald-600 hover:underline truncate block max-w-[120px]" title={p.name}>
                                        {p.name.length > 20 ? p.name.slice(0, 20) + '...' : p.name}
                                      </Link>
                                    </td>
                                    <td className="py-1 px-1 text-center font-medium">{p.quality_score?.toFixed(0)}</td>
                                    <td className="py-1 px-1 text-center font-bold">{p.grade}</td>
                                  </tr>
                                ))}
                                {cell.projects.length > 15 && (
                                  <tr>
                                    <td colSpan={3} className="py-1 px-1 text-center text-slate-400 italic">
                                      +{cell.projects.length - 15} mais projetos...
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-600">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-emerald-100 border border-emerald-300"></div>
            <span>Seguro</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-amber-100 border border-amber-300"></div>
            <span>Atenção</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-orange-100 border border-orange-300"></div>
            <span>Alto Risco</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-red-300 border border-red-500"></div>
            <span>Crítico</span>
          </div>
        </div>
      </div>

      {/* Top Fraud Projects */}
      {fraudSummary?.top_affected_projects?.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Projetos com Mais Alertas de Fraude</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Projeto</th>
                  <th className="text-center py-3 px-4 font-medium text-slate-600">Alertas</th>
                  <th className="text-right py-3 px-4 font-medium text-slate-600">Ação</th>
                </tr>
              </thead>
              <tbody>
                {fraudSummary.top_affected_projects.map((p: any) => (
                  <tr key={p.project_id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-4 font-medium">{p.project_name}</td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                        {p.alert_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link to={`/projects/${p.project_id}`} className="text-emerald-600 hover:text-emerald-700 font-medium">
                        Ver detalhes
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function KPICard({ title, value, subtitle, icon: Icon, color }: {
  title: string; value: string; subtitle?: string; icon: any; color: string;
}) {
  const colorClasses: Record<string, string> = {
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
  };
  const iconClasses: Record<string, string> = {
    emerald: 'bg-emerald-100 text-emerald-600',
    blue: 'bg-blue-100 text-blue-600',
    red: 'bg-red-100 text-red-600',
    amber: 'bg-amber-100 text-amber-600',
  };

  return (
    <div className={`rounded-xl border p-5 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium opacity-80">{title}</p>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-2xl font-bold">
        {value}
        {subtitle && <span className="text-sm font-normal opacity-60">{subtitle}</span>}
      </p>
    </div>
  );
}
