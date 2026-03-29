import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import { TreePine, ShieldAlert, DollarSign, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import { getDashboardMetrics, getFraudSummary, getRiskMatrix } from '../utils/api';
import { formatNumber, formatCurrency, getGradeColor, getSeverityColor } from '../utils/helpers';


export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [fraudSummary, setFraudSummary] = useState<any>(null);
  const [riskMatrix, setRiskMatrix] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
  }, []);

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Visão geral da plataforma Carbon Verify</p>
      </div>

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
          title="Valor do Portfólio"
          value={formatCurrency(metrics.portfolio_value_usd)}
          icon={DollarSign}
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
        {/* Grade Distribution */}
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

        {/* Fraud Severity */}
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
        {/* Project Types */}
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

        {/* Countries */}
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

      {/* Risk Matrix Scatter */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Matriz de Risco: Qualidade vs Alertas de Fraude</h3>
        <ResponsiveContainer width="100%" height={350}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis type="number" dataKey="quality_score" name="Score de Qualidade" domain={[0, 100]} tick={{ fontSize: 12 }} />
            <YAxis type="number" dataKey="fraud_alerts" name="Alertas de Fraude" tick={{ fontSize: 12 }} />
            <ZAxis range={[100, 400]} />
            <Tooltip
              content={({ payload }) => {
                if (!payload?.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border text-sm">
                    <p className="font-semibold">{d.name}</p>
                    <p>Score: {d.quality_score?.toFixed(1)} ({d.grade})</p>
                    <p>Alertas: {d.fraud_alerts}</p>
                    <p className="text-slate-500">{d.project_type}</p>
                  </div>
                );
              }}
            />
            <Scatter data={riskMatrix} fill="#059669">
              {riskMatrix.map((entry, idx) => (
                <Cell
                  key={idx}
                  fill={entry.quality_score >= 70 ? '#10b981' : entry.quality_score >= 50 ? '#f59e0b' : '#ef4444'}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
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
