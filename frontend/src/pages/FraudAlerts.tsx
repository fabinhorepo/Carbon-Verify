import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, CheckCircle, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, AlertTriangle, Info, BookOpen } from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis
} from 'recharts';
import { getFraudAlertsGroupedByType, getFraudAlertsByType, getFraudSummary, updateFraudAlert } from '../utils/api';
import { getSeverityClass, getSeverityColor } from '../utils/helpers';

const PAGE_SIZE = 10;

export default function FraudAlerts() {
  const [groupedData, setGroupedData] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('');
  const [tabData, setTabData] = useState<any>(null);
  const [tabPage, setTabPage] = useState(1);
  const [tabLoading, setTabLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [g, s] = await Promise.all([
        getFraudAlertsGroupedByType(),
        getFraudSummary(),
      ]);
      setGroupedData(g.data);
      setSummary(s.data);
      const types = Object.keys(g.data.types || {});
      if (types.length > 0) {
        setActiveTab(types[0]);
        await loadTabData(types[0], 1);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadTabData = async (alertType: string, page: number) => {
    setTabLoading(true);
    try {
      const res = await getFraudAlertsByType(alertType, { page, page_size: PAGE_SIZE });
      setTabData(res.data);
      setTabPage(page);
    } catch (err) {
      console.error(err);
    } finally {
      setTabLoading(false);
    }
  };

  const handleTabChange = (type: string) => {
    setActiveTab(type);
    setTabPage(1);
    setShowExplanation(true);
    loadTabData(type, 1);
  };

  const handleStatusUpdate = async (alertId: number, status: string) => {
    try {
      await updateFraudAlert(alertId, { status, reviewed_by: 'Analyst' });
      loadTabData(activeTab, tabPage);
    } catch (err) {
      console.error(err);
    }
  };

  const goToPage = (p: number) => {
    if (p >= 1 && p <= (tabData?.total_pages || 1)) {
      loadTabData(activeTab, p);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>
  );

  const types = groupedData?.types || {};
  const typeKeys = Object.keys(types);
  const totalAlerts = groupedData?.total_alerts || 0;

  const severityData = Object.entries(summary?.by_severity || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1), value, fill: getSeverityColor(name),
  }));

  const typeData = typeKeys.map(key => ({
    name: types[key].explanation?.title?.split('(')[0]?.trim() || key.replace(/_/g, ' '),
    value: types[key].total,
  }));

  const currentExplanation = types[activeTab]?.explanation;
  const startItem = tabData ? (tabPage - 1) * PAGE_SIZE + 1 : 0;
  const endItem = tabData ? Math.min(tabPage * PAGE_SIZE, tabData.total) : 0;

  const getTabColor = (type: string) => {
    const info = types[type];
    if (!info) return 'border-slate-300 text-slate-600';
    const total = info.total;
    if (total > 100) return 'border-red-400 text-red-700 bg-red-50';
    if (total > 30) return 'border-amber-400 text-amber-700 bg-amber-50';
    return 'border-blue-400 text-blue-700 bg-blue-50';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Fraud Detection</h1>
        <p className="text-slate-500 mt-1">
          Detecção de inconsistências e sinais de fraude &middot; {totalAlerts} alertas em {typeKeys.length} categorias
        </p>
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
                <YAxis type="category" dataKey="name" tick={{ fontSize: 9 }} width={100} />
                <Tooltip />
                <Bar dataKey="value" fill="#ef4444" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Tabs by Fraud Type */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="border-b border-slate-200 overflow-x-auto">
          <div className="flex min-w-max">
            {typeKeys.map(type => {
              const info = types[type];
              const isActive = activeTab === type;
              return (
                <button
                  key={type}
                  onClick={() => handleTabChange(type)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
                    isActive
                      ? 'border-emerald-600 text-emerald-700 bg-emerald-50'
                      : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <AlertTriangle className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                  <span>{info.explanation?.title?.split('(')[0]?.trim() || type.replace(/_/g, ' ')}</span>
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                    isActive ? 'bg-emerald-200 text-emerald-800' : getTabColor(type)
                  }`}>
                    {info.total}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Explanation Section */}
        {currentExplanation && (
          <div className="border-b border-slate-200">
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="w-full flex items-center justify-between px-6 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-500" />
                <span>Entenda este tipo de fraude</span>
              </div>
              <span className="text-xs text-slate-400">{showExplanation ? 'Ocultar' : 'Mostrar'}</span>
            </button>

            {showExplanation && (
              <div className="px-6 pb-5 space-y-4">
                <h3 className="text-lg font-bold text-slate-900">{currentExplanation.title}</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* O que é */}
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Info className="w-4 h-4 text-blue-600" />
                      <h4 className="font-semibold text-blue-800 text-sm">O que é?</h4>
                    </div>
                    <p className="text-sm text-blue-700 leading-relaxed">{currentExplanation.what_is}</p>
                  </div>

                  {/* Consequências */}
                  <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                      <h4 className="font-semibold text-red-800 text-sm">Consequências</h4>
                    </div>
                    <p className="text-sm text-red-700 leading-relaxed">{currentExplanation.consequences}</p>
                  </div>

                  {/* Situação Ideal */}
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <h4 className="font-semibold text-green-800 text-sm">Situação Ideal</h4>
                    </div>
                    <p className="text-sm text-green-700 leading-relaxed">{currentExplanation.ideal_situation}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Alerts List */}
        <div className="p-4 space-y-3">
          {tabLoading ? (
            <div className="text-center py-12 text-slate-400">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-600 mx-auto mb-2"></div>
              Carregando alertas...
            </div>
          ) : !tabData || tabData.items?.length === 0 ? (
            <div className="text-center py-12 text-slate-400">Nenhum alerta encontrado</div>
          ) : tabData.items.map((alert: any) => (
            <div key={alert.id} className="bg-slate-50 rounded-lg border border-slate-200 p-4 hover:shadow-sm transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${getSeverityClass(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${
                      alert.status === 'open' ? 'bg-blue-100 text-blue-700' :
                      alert.status === 'confirmed' ? 'bg-red-100 text-red-700' :
                      alert.status === 'dismissed' ? 'bg-green-100 text-green-700' :
                      'bg-amber-100 text-amber-700'
                    }`}>
                      {alert.status === 'open' ? 'Aberto' :
                       alert.status === 'confirmed' ? 'Confirmado' :
                       alert.status === 'dismissed' ? 'Descartado' : 'Em revisão'}
                    </span>
                    <span className="text-xs text-slate-400">Confiança: {(alert.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <Link to={`/projects/${alert.project_id}`} className="font-semibold text-emerald-700 hover:text-emerald-800 hover:underline">
                      {alert.project_name || `Projeto #${alert.project_id}`}
                    </Link>
                  </div>
                  <h3 className="font-semibold text-slate-900">{alert.title}</h3>
                  <p className="text-sm text-slate-600 mt-1">{alert.description}</p>
                  {alert.recommendation && (
                    <p className="text-sm text-emerald-700 mt-2 bg-emerald-50 p-2 rounded-md border border-emerald-200 italic">
                      {alert.recommendation}
                    </p>
                  )}
                  <div className="flex items-center gap-4 mt-3">
                    <Link to={`/projects/${alert.project_id}`} className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
                      Ver detalhes do projeto
                    </Link>
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
        {tabData && tabData.total > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50 gap-3">
            <div className="text-sm text-slate-500">
              Mostrando <span className="font-medium text-slate-700">{startItem}</span> a{' '}
              <span className="font-medium text-slate-700">{endItem}</span> de{' '}
              <span className="font-medium text-slate-700">{tabData.total}</span> alertas
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => goToPage(1)} disabled={tabPage === 1}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                <ChevronsLeft className="w-4 h-4" />
              </button>
              <button onClick={() => goToPage(tabPage - 1)} disabled={tabPage === 1}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: tabData.total_pages }, (_, i) => i + 1)
                .filter(p => p === 1 || p === tabData.total_pages || Math.abs(p - tabPage) <= 1)
                .reduce((acc: (number | string)[], p, idx, arr) => {
                  if (idx > 0 && typeof arr[idx - 1] === 'number' && (p as number) - (arr[idx - 1] as number) > 1) acc.push('...');
                  acc.push(p);
                  return acc;
                }, [])
                .map((p, idx) =>
                  typeof p === 'string' ? (
                    <span key={`e-${idx}`} className="px-2 text-slate-400 text-sm">...</span>
                  ) : (
                    <button key={p} onClick={() => goToPage(p as number)}
                      className={`min-w-[36px] h-9 rounded-md border text-sm font-medium transition-colors ${
                        tabPage === p ? 'bg-emerald-600 border-emerald-600 text-white' : 'border-slate-300 text-slate-600 hover:bg-white hover:text-slate-800'
                      }`}>
                      {p}
                    </button>
                  )
                )}
              <button onClick={() => goToPage(tabPage + 1)} disabled={tabPage === tabData.total_pages}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                <ChevronRight className="w-4 h-4" />
              </button>
              <button onClick={() => goToPage(tabData.total_pages)} disabled={tabPage === tabData.total_pages}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                <ChevronsRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
