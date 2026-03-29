import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, CheckCircle, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis
} from 'recharts';
import { getFraudAlerts, getFraudSummary, updateFraudAlert } from '../utils/api';
import { getSeverityClass, getSeverityColor } from '../utils/helpers';

const PAGE_SIZE = 20;

export default function FraudAlerts() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadData();
  }, [page]);

  useEffect(() => {
    setPage(1);
    loadData(1);
  }, [filterSeverity, filterStatus]);

  const loadData = async (forcePage?: number) => {
    setLoading(true);
    try {
      const params: any = { page: forcePage || page, page_size: PAGE_SIZE };
      if (filterSeverity) params.severity = filterSeverity;
      if (filterStatus) params.status = filterStatus;
      const [a, s] = await Promise.all([
        getFraudAlerts(params),
        getFraudSummary(),
      ]);
      const data = a.data;
      setAlerts(data.items || []);
      setTotalPages(data.total_pages || 1);
      setTotal(data.total || 0);
      setSummary(s.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (alertId: number, status: string) => {
    try {
      await updateFraudAlert(alertId, { status, reviewed_by: 'Analyst' });
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const goToPage = (p: number) => {
    if (p >= 1 && p <= totalPages) setPage(p);
  };

  const startItem = (page - 1) * PAGE_SIZE + 1;
  const endItem = Math.min(page * PAGE_SIZE, total);

  const severityData = Object.entries(summary?.by_severity || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    fill: getSeverityColor(name),
  }));

  const typeData = Object.entries(summary?.by_type || {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Fraud Detection</h1>
        <p className="text-slate-500 mt-1">Detecção de inconsistências e sinais de fraude &middot; {total} alertas</p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-sm font-semibold text-slate-600 mb-3">Total de Alertas</h3>
            <p className="text-4xl font-bold text-slate-900">{summary.total_alerts}</p>
            <div className="flex gap-2 mt-3 flex-wrap">
              {Object.entries(summary.by_severity || {}).map(([sev, count]: any) => (
                <span key={sev} className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityClass(sev)}`}>
                  {count} {sev}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-sm font-semibold text-slate-600 mb-3">Por Severidade</h3>
            <ResponsiveContainer width="100%" height={150}>
              <PieChart>
                <Pie data={severityData} cx="50%" cy="50%" innerRadius={35} outerRadius={60} dataKey="value" paddingAngle={3}>
                  {severityData.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-sm font-semibold text-slate-600 mb-3">Por Tipo de Alerta</h3>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={typeData} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={90} />
                <Tooltip />
                <Bar dataKey="value" fill="#ef4444" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todas severidades</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todos status</option>
          <option value="open">Aberto</option>
          <option value="under_review">Em revisão</option>
          <option value="confirmed">Confirmado</option>
          <option value="dismissed">Descartado</option>
        </select>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-12 text-slate-400">Carregando...</div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12 text-slate-400">Nenhum alerta encontrado</div>
        ) : alerts.map(alert => (
          <div key={alert.id} className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-sm transition-shadow">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${getSeverityClass(alert.severity)}`}>
                    {alert.severity.toUpperCase()}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600">
                    {alert.alert_type.replace(/_/g, ' ')}
                  </span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${
                    alert.status === 'open' ? 'bg-blue-100 text-blue-700' :
                    alert.status === 'confirmed' ? 'bg-red-100 text-red-700' :
                    alert.status === 'dismissed' ? 'bg-green-100 text-green-700' :
                    'bg-amber-100 text-amber-700'
                  }`}>
                    {alert.status}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-900">{alert.title}</h3>
                <p className="text-sm text-slate-600 mt-1">{alert.description}</p>
                {alert.recommendation && (
                  <p className="text-sm text-emerald-700 mt-2 italic">{alert.recommendation}</p>
                )}
                <div className="flex items-center gap-4 mt-3">
                  <Link to={`/projects/${alert.project_id}`} className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
                    Ver projeto
                  </Link>
                  <span className="text-xs text-slate-400">Confiança: {(alert.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                {alert.status === 'open' && (
                  <>
                    <button
                      onClick={() => handleStatusUpdate(alert.id, 'confirmed')}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg" title="Confirmar fraude"
                    >
                      <ShieldAlert className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(alert.id, 'dismissed')}
                      className="p-2 text-green-500 hover:bg-green-50 rounded-lg" title="Descartar"
                    >
                      <CheckCircle className="w-4 h-4" />
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {!loading && total > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-3 bg-white rounded-xl border border-slate-200 gap-3">
          <div className="text-sm text-slate-500">
            Mostrando <span className="font-medium text-slate-700">{startItem}</span> a <span className="font-medium text-slate-700">{endItem}</span> de <span className="font-medium text-slate-700">{total}</span> alertas
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => goToPage(1)}
              disabled={page === 1}
              className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-slate-50 hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronsLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => goToPage(page - 1)}
              disabled={page === 1}
              className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-slate-50 hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
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
                  <button
                    key={p}
                    onClick={() => goToPage(p as number)}
                    className={`min-w-[36px] h-9 rounded-md border text-sm font-medium transition-colors ${
                      page === p
                        ? 'bg-emerald-600 border-emerald-600 text-white'
                        : 'border-slate-300 text-slate-600 hover:bg-slate-50 hover:text-slate-800'
                    }`}
                  >
                    {p}
                  </button>
                )
              )}

            <button
              onClick={() => goToPage(page + 1)}
              disabled={page === totalPages}
              className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-slate-50 hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => goToPage(totalPages)}
              disabled={page === totalPages}
              className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-slate-50 hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronsRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
