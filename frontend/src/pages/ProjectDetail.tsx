import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell
} from 'recharts';
import { ArrowLeft, MapPin, Calendar, Building, Shield, AlertTriangle } from 'lucide-react';
import { getProject, getFraudAlerts } from '../utils/api';
import { getGradeClass, getSeverityClass, formatNumber, getScoreColor } from '../utils/helpers';

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getProject(Number(id)),
      getFraudAlerts({ project_id: Number(id) }),
    ]).then(([p, a]) => {
      setProject(p.data);
      setAlerts(a.data);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>
  );
  if (!project) return <div className="text-red-500">Projeto não encontrado</div>;

  const rating = project.rating;
  const dimensions = rating ? [
    { name: 'Adicionalidade', value: rating.additionality_score, fullMark: 100 },
    { name: 'Permanência', value: rating.permanence_score, fullMark: 100 },
    { name: 'Leakage', value: rating.leakage_score, fullMark: 100 },
    { name: 'MRV', value: rating.mrv_score, fullMark: 100 },
    { name: 'Co-benefícios', value: rating.co_benefits_score, fullMark: 100 },
    { name: 'Governança', value: rating.governance_score, fullMark: 100 },
    { name: 'Baseline', value: rating.baseline_integrity_score, fullMark: 100 },
  ] : [];

  const barData = dimensions.map(d => ({
    ...d,
    fill: getScoreColor(d.value),
  }));

  return (
    <div className="space-y-6">
      {/* Back */}
      <Link to="/projects" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="w-4 h-4" /> Voltar para projetos
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              {rating && (
                <span className={`inline-flex items-center justify-center w-14 h-9 rounded-lg text-sm font-bold ${getGradeClass(rating.grade)}`}>
                  {rating.grade}
                </span>
              )}
              <h1 className="text-xl font-bold text-slate-900">{project.name}</h1>
            </div>
            <p className="text-slate-500 text-sm mt-2 max-w-2xl">{project.description}</p>
            <div className="flex flex-wrap gap-4 mt-4 text-sm text-slate-600">
              <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" />{project.country}{project.region ? `, ${project.region}` : ''}</span>
              <span className="flex items-center gap-1.5"><Building className="w-4 h-4" />{project.registry || 'Sem registro'}</span>
              <span className="flex items-center gap-1.5"><Calendar className="w-4 h-4" />Vintage {project.vintage_year}</span>
              <span className="flex items-center gap-1.5"><Shield className="w-4 h-4" />{project.methodology || 'N/A'}</span>
            </div>
          </div>
          <div className="text-right">
            {rating && (
              <div>
                <p className="text-4xl font-bold" style={{ color: getScoreColor(rating.overall_score) }}>
                  {rating.overall_score.toFixed(1)}
                </p>
                <p className="text-sm text-slate-500">Score de Qualidade</p>
                <p className="text-xs text-slate-400 mt-1">Confiança: {(rating.confidence_level * 100).toFixed(0)}%</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Créditos Emitidos" value={formatNumber(project.total_credits_issued)} />
        <StatCard label="Créditos Aposentados" value={formatNumber(project.total_credits_retired)} />
        <StatCard label="Créditos Disponíveis" value={formatNumber(project.total_credits_available)} />
        <StatCard label="Área (ha)" value={project.area_hectares ? formatNumber(project.area_hectares) : 'N/A'} />
      </div>

      {/* Rating Decomposition */}
      {rating && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Radar */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Decomposição do Rating (Radar)</h3>
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={dimensions}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="name" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar name="Score" dataKey="value" stroke="#059669" fill="#059669" fillOpacity={0.3} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Bar */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Sub-Scores por Dimensão</h3>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={barData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={100} />
                <Tooltip />
                <Bar dataKey="value" name="Score" radius={[0, 4, 4, 0]}>
                  {barData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Explanation */}
      {rating?.explanation && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-3">Explicação do Rating</h3>
          <p className="text-slate-600 leading-relaxed">{rating.explanation}</p>
        </div>
      )}

      {/* Risk Flags */}
      {rating?.risk_flags?.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Flags de Risco</h3>
          <div className="space-y-3">
            {rating.risk_flags.map((flag: any, idx: number) => (
              <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg ${
                flag.severity === 'high' ? 'bg-red-50 border border-red-200' :
                flag.severity === 'medium' ? 'bg-amber-50 border border-amber-200' :
                'bg-yellow-50 border border-yellow-200'
              }`}>
                <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${
                  flag.severity === 'high' ? 'text-red-500' : 'text-amber-500'
                }`} />
                <div>
                  <p className="font-medium text-slate-900">{flag.message}</p>
                  <p className="text-xs text-slate-500 mt-1">Tipo: {flag.type} | Severidade: {flag.severity}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fraud Alerts */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            Alertas de Fraude ({alerts.length})
          </h3>
          <div className="space-y-3">
            {alerts.map((alert: any) => (
              <div key={alert.id} className="border border-slate-200 rounded-lg p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityClass(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs text-slate-400">{alert.alert_type}</span>
                    </div>
                    <h4 className="font-medium text-slate-900">{alert.title}</h4>
                    <p className="text-sm text-slate-600 mt-1">{alert.description}</p>
                    {alert.recommendation && (
                      <p className="text-sm text-emerald-700 mt-2 italic">{alert.recommendation}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-xl font-bold text-slate-900 mt-1">{value}</p>
    </div>
  );
}
