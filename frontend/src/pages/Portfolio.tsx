import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, Shield, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { getPortfolios, getPortfolioDetail } from '../utils/api';
import { formatNumber, formatCurrency, getGradeClass, getGradeColor, getScoreColor } from '../utils/helpers';

const COLORS = ['#059669','#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1'];
const PAGE_SIZE = 20;

type PosSortField = 'project_name' | 'project_type' | 'country' | 'grade' | 'score' | 'quantity' | 'price_eur' | 'value';
type SortDir = 'asc' | 'desc';

const GRADE_ORDER: Record<string, number> = { 'AAA': 1, 'AA': 2, 'A': 3, 'BBB': 4, 'BB': 5, 'B': 6, 'CCC': 7, 'CC': 8, 'C': 9, 'D': 10 };

const TAB_CONFIG: Record<string, { label: string; color: string; bgClass: string; borderClass: string; badgeClass: string; iconBg: string }> = {
  sell: { label: 'Vender', color: 'red', bgClass: 'bg-red-50 border-red-200', borderClass: 'border-red-500 text-red-700', badgeClass: 'bg-red-200 text-red-800', iconBg: 'bg-red-100' },
  rebalance: { label: 'Rebalancear', color: 'amber', bgClass: 'bg-amber-50 border-amber-200', borderClass: 'border-amber-500 text-amber-700', badgeClass: 'bg-amber-200 text-amber-800', iconBg: 'bg-amber-100' },
  hold: { label: 'Manter', color: 'green', bgClass: 'bg-green-50 border-green-200', borderClass: 'border-green-500 text-green-700', badgeClass: 'bg-green-200 text-green-800', iconBg: 'bg-green-100' },
};

const SEVERITY_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-800 border-red-300',
  medium: 'bg-amber-100 text-amber-800 border-amber-300',
  low: 'bg-green-100 text-green-800 border-green-300',
};

export default function Portfolio() {
  const [portfolioId, setPortfolioId] = useState<number | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [posPage, setPosPage] = useState(1);
  const [posTotalPages, setPosTotalPages] = useState(1);
  const [posTotal, setPosTotal] = useState(0);
  const [activeRecTab, setActiveRecTab] = useState<string>('sell');
  const [recPages, setRecPages] = useState<Record<string, number>>({ sell: 1, rebalance: 1, hold: 1 });

  // Sorting state for positions table
  const [posSortField, setPosSortField] = useState<PosSortField | null>(null);
  const [posSortDir, setPosSortDir] = useState<SortDir>('asc');

  useEffect(() => { loadPortfolios(); }, []);

  useEffect(() => {
    if (portfolioId) loadDetail(portfolioId, posPage, recPages);
  }, [posPage]);

  const loadPortfolios = async () => {
    try {
      const res = await getPortfolios();
      if (res.data.length > 0) {
        setPortfolioId(res.data[0].id);
        await loadDetail(res.data[0].id, 1, { sell: 1, rebalance: 1, hold: 1 });
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const loadDetail = async (id: number, page: number, currentRecPages: Record<string, number>) => {
    try {
      const recPage = currentRecPages[activeRecTab] || 1;
      const d = await getPortfolioDetail(id, { page, page_size: PAGE_SIZE, rec_page: recPage, rec_page_size: PAGE_SIZE });
      setDetail(d.data);
      const pagination = d.data?.metrics?.positions_pagination;
      if (pagination) { setPosTotalPages(pagination.total_pages || 1); setPosTotal(pagination.total || 0); }
      const grouped = d.data?.metrics?.recommendations_grouped;
      if (grouped) {
        const tabOrder = ['sell', 'rebalance', 'hold'];
        if (!(grouped[activeRecTab]?.total > 0)) {
          const firstAvailable = tabOrder.find(t => grouped[t]?.total > 0);
          if (firstAvailable) setActiveRecTab(firstAvailable);
        }
      }
    } catch (err) { console.error(err); }
  };

  const loadRecPage = useCallback(async (tab: string, page: number) => {
    if (!portfolioId) return;
    const newRecPages = { ...recPages, [tab]: page };
    setRecPages(newRecPages);
    try {
      const d = await getPortfolioDetail(portfolioId, { page: posPage, page_size: PAGE_SIZE, rec_page: page, rec_page_size: PAGE_SIZE });
      setDetail(d.data);
    } catch (err) { console.error(err); }
  }, [portfolioId, posPage, recPages]);

  const goToPage = (p: number) => { if (p >= 1 && p <= posTotalPages) setPosPage(p); };

  const goToRecPage = (tab: string, p: number) => {
    const grouped = detail?.metrics?.recommendations_grouped;
    const totalPages = grouped?.[tab]?.total_pages || 1;
    if (p >= 1 && p <= totalPages) loadRecPage(tab, p);
  };

  // Sorting handlers
  const handlePosSort = (field: PosSortField) => {
    if (posSortField === field) {
      if (posSortDir === 'asc') setPosSortDir('desc');
      else { setPosSortField(null); setPosSortDir('asc'); }
    } else { setPosSortField(field); setPosSortDir('asc'); }
  };

  const getPosSortIcon = (field: PosSortField) => {
    if (posSortField !== field) return <ArrowUpDown className="w-3.5 h-3.5 opacity-40" />;
    return posSortDir === 'asc' ? <ArrowUp className="w-3.5 h-3.5 text-emerald-600" /> : <ArrowDown className="w-3.5 h-3.5 text-emerald-600" />;
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
    </div>
  );

  const metrics = detail?.metrics;
  const positions = metrics?.positions || [];

  // Sort positions
  const sortedPositions = [...positions].sort((a: any, b: any) => {
    if (!posSortField) return 0;
    const dir = posSortDir === 'asc' ? 1 : -1;
    switch (posSortField) {
      case 'project_name': return dir * (a.project_name || '').localeCompare(b.project_name || '');
      case 'project_type': return dir * (a.project_type || '').localeCompare(b.project_type || '');
      case 'country': return dir * (a.country || '').localeCompare(b.country || '');
      case 'grade': return dir * ((GRADE_ORDER[a.grade] || 99) - (GRADE_ORDER[b.grade] || 99));
      case 'score': return dir * ((a.score || 0) - (b.score || 0));
      case 'quantity': return dir * ((a.quantity || 0) - (b.quantity || 0));
      case 'price_eur': return dir * ((a.price_eur || 0) - (b.price_eur || 0));
      case 'value': return dir * (((a.quantity || 0) * (a.price_eur || 0)) - ((b.quantity || 0) * (b.price_eur || 0)));
      default: return 0;
    }
  });

  const typeData = Object.entries(metrics?.project_type_distribution || {}).map(([name, value]: any, idx) => ({
    name: name.length > 12 ? name.slice(0, 12) + '...' : name, value, fill: COLORS[idx % COLORS.length],
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
  const recGrouped = metrics?.recommendations_grouped || {};
  const tabOrder = ['sell', 'rebalance', 'hold'];
  const availableTabs = tabOrder.filter(t => recGrouped[t]?.total > 0);

  const SortableHeader = ({ field, label, align = 'left' }: { field: PosSortField; label: string; align?: string }) => (
    <th className={`py-3 px-4 font-semibold text-slate-600 cursor-pointer hover:bg-slate-100 select-none transition-colors text-${align}`}
      onClick={() => handlePosSort(field)}>
      <div className={`flex items-center gap-1.5 ${align === 'center' ? 'justify-center' : align === 'right' ? 'justify-end' : ''}`}>
        <span>{label}</span>
        {getPosSortIcon(field)}
      </div>
    </th>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard de Portfólio</h1>
        <p className="text-slate-500 mt-1">Risco agregado, qualidade e recomendações de rebalanceamento &middot; {posTotal} posições &middot; {metrics?.total_recommendations || 0} recomendações</p>
      </div>

      {detail && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard label="Total de Créditos" value={formatNumber(metrics?.total_credits || 0)} color="emerald" />
            <SummaryCard label="Valor Total" value={formatCurrency(metrics?.total_value_eur || 0)} color="blue" />
            <SummaryCard label="Score Médio" value={`${(metrics?.avg_quality_score || 0).toFixed(1)}/100`} color="amber" />
            <SummaryCard label="Projetos Únicos" value={String(metrics?.total_recommendations || 0)} color="purple" />
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

          {/* Positions Table with Sortable Headers */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-6 pb-0 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Posições do Portfólio</h3>
              {posSortField && (
                <div className="flex items-center gap-2 text-xs text-slate-500 mb-4">
                  <span>Ordenado por: <span className="font-medium text-emerald-600">
                    {{ project_name: 'Projeto', project_type: 'Tipo', country: 'País', grade: 'Rating', score: 'Score', quantity: 'Quantidade', price_eur: 'Preço', value: 'Valor' }[posSortField]}
                  </span></span>
                  <span>({posSortDir === 'asc' ? 'crescente' : 'decrescente'})</span>
                  <button onClick={() => { setPosSortField(null); setPosSortDir('asc'); }}
                    className="text-red-500 hover:text-red-700 ml-1">Limpar</button>
                </div>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <SortableHeader field="project_name" label="Projeto" />
                    <SortableHeader field="project_type" label="Tipo" />
                    <SortableHeader field="country" label="País" />
                    <SortableHeader field="grade" label="Rating" align="center" />
                    <SortableHeader field="score" label="Score" align="center" />
                    <SortableHeader field="quantity" label="Quantidade" align="right" />
                    <SortableHeader field="price_eur" label="Preço (€)" align="right" />
                    <SortableHeader field="value" label="Valor" align="right" />
                  </tr>
                </thead>
                <tbody>
                  {sortedPositions.map((pos: any) => (
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
                      <td className="py-3 px-4 text-right font-mono">{formatCurrency(pos.price_eur)}</td>
                      <td className="py-3 px-4 text-right font-mono font-medium">{formatCurrency(pos.quantity * pos.price_eur)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {posTotal > 0 && (
              <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50 gap-3">
                <div className="text-sm text-slate-500">
                  Mostrando <span className="font-medium text-slate-700">{posStartItem}</span> a <span className="font-medium text-slate-700">{posEndItem}</span> de <span className="font-medium text-slate-700">{posTotal}</span> posições
                </div>
                <PaginationControls currentPage={posPage} totalPages={posTotalPages} onPageChange={goToPage} />
              </div>
            )}
          </div>

          {/* Recommendations with Tabs + Pagination */}
          {availableTabs.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="p-6 pb-0">
                <h3 className="text-lg font-semibold text-slate-900 mb-1">Recomendações de Rebalanceamento</h3>
                <p className="text-sm text-slate-500 mb-4">
                  Projetos agrupados por ação recomendada &middot; {metrics?.total_recommendations || 0} recomendações únicas (sem duplicação)
                </p>
              </div>

              <div className="flex border-b border-slate-200 px-6">
                {availableTabs.map(tabKey => {
                  const cfg = TAB_CONFIG[tabKey];
                  const td = recGrouped[tabKey];
                  const count = td?.total || 0;
                  const isActive = activeRecTab === tabKey;
                  return (
                    <button key={tabKey}
                      onClick={() => { setActiveRecTab(tabKey); loadRecPage(tabKey, recPages[tabKey] || 1); }}
                      className={`relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                        isActive ? `${cfg.borderClass} border-b-2 -mb-px` : 'text-slate-500 hover:text-slate-700 border-b-2 border-transparent -mb-px'
                      }`}>
                      {tabKey === 'sell' && <TrendingDown className="w-4 h-4" />}
                      {tabKey === 'rebalance' && <AlertTriangle className="w-4 h-4" />}
                      {tabKey === 'hold' && <TrendingUp className="w-4 h-4" />}
                      {cfg.label}
                      <span className={`inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-xs font-bold ${isActive ? cfg.badgeClass : 'bg-slate-200 text-slate-600'}`}>
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>

              <div className="p-6">
                {availableTabs.map(tabKey => {
                  if (tabKey !== activeRecTab) return null;
                  const cfg = TAB_CONFIG[tabKey];
                  const td = recGrouped[tabKey] || { items: [], total: 0, page: 1, total_pages: 1 };
                  const items = td.items || [];
                  const recCurrentPage = td.page || 1;
                  const recTotalPages = td.total_pages || 1;
                  const recTotal = td.total || 0;
                  const recStart = (recCurrentPage - 1) * PAGE_SIZE + 1;
                  const recEnd = Math.min(recCurrentPage * PAGE_SIZE, recTotal);

                  return (
                    <div key={tabKey}>
                      <div className="space-y-3">
                        {items.map((rec: any, idx: number) => (
                          <div key={`${rec.project_id || idx}-${idx}`} className={`p-4 rounded-lg border ${cfg.bgClass}`}>
                            <div className="flex items-start gap-3">
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
                                  {rec.project_type && rec.project_type !== 'N/A' && (
                                    <span className="text-xs bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded">{rec.project_type}</span>
                                  )}
                                  {rec.country && rec.country !== 'N/A' && (
                                    <span className="text-xs bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded">{rec.country}</span>
                                  )}
                                </div>

                                <p className="text-sm text-slate-600 mt-1.5">{rec.reason}</p>

                                {rec.reasons && rec.reasons.length > 0 && (
                                  <div className="mt-2 space-y-1">
                                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Motivos:</p>
                                    <ul className="text-xs text-slate-600 space-y-0.5 ml-3">
                                      {rec.reasons.map((r: string, ri: number) => (
                                        <li key={ri} className="flex items-start gap-1.5">
                                          <span className="text-slate-400 mt-0.5">&#8226;</span>
                                          <span>{r}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {rec.risk_flags && rec.risk_flags.length > 0 && (
                                  <div className="mt-2 flex flex-wrap gap-1.5">
                                    {rec.risk_flags.map((flag: any, fi: number) => (
                                      <span key={fi} className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${SEVERITY_COLORS[flag.severity] || SEVERITY_COLORS.medium}`}>
                                        <Shield className="w-3 h-3" />
                                        {flag.message}
                                      </span>
                                    ))}
                                  </div>
                                )}

                                {rec.total_quantity > 0 && (
                                  <div className="mt-2 flex gap-4 text-xs text-slate-500">
                                    <span>Créditos: <span className="font-mono font-medium text-slate-700">{formatNumber(rec.total_quantity)}</span></span>
                                    {rec.total_value > 0 && (
                                      <span>Valor: <span className="font-mono font-medium text-slate-700">{formatCurrency(rec.total_value)}</span></span>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                        {items.length === 0 && (
                          <p className="text-sm text-slate-500 text-center py-8">Nenhuma recomendação nesta categoria.</p>
                        )}
                      </div>

                      {recTotal > PAGE_SIZE && (
                        <div className="flex flex-col sm:flex-row items-center justify-between mt-4 pt-4 border-t border-slate-200 gap-3">
                          <div className="text-sm text-slate-500">
                            Mostrando <span className="font-medium text-slate-700">{recStart}</span> a <span className="font-medium text-slate-700">{recEnd}</span> de <span className="font-medium text-slate-700">{recTotal}</span> recomendações
                          </div>
                          <PaginationControls currentPage={recCurrentPage} totalPages={recTotalPages} onPageChange={(p) => goToRecPage(tabKey, p)} />
                        </div>
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

function PaginationControls({ currentPage, totalPages, onPageChange }: { currentPage: number; totalPages: number; onPageChange: (page: number) => void; }) {
  return (
    <div className="flex items-center gap-1">
      <button onClick={() => onPageChange(1)} disabled={currentPage === 1}
        className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <ChevronsLeft className="w-4 h-4" />
      </button>
      <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1}
        className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <ChevronLeft className="w-4 h-4" />
      </button>
      {Array.from({ length: totalPages }, (_, i) => i + 1)
        .filter(p => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
        .reduce((acc: (number | string)[], p, idx, arr) => {
          if (idx > 0 && typeof arr[idx - 1] === 'number' && (p as number) - (arr[idx - 1] as number) > 1) acc.push('...');
          acc.push(p);
          return acc;
        }, [])
        .map((p, idx) =>
          typeof p === 'string' ? (
            <span key={`ellipsis-${idx}`} className="px-2 text-slate-400 text-sm">...</span>
          ) : (
            <button key={p} onClick={() => onPageChange(p as number)}
              className={`min-w-[36px] h-9 rounded-md border text-sm font-medium transition-colors ${
                currentPage === p ? 'bg-emerald-600 border-emerald-600 text-white' : 'border-slate-300 text-slate-600 hover:bg-white hover:text-slate-800'
              }`}>
              {p}
            </button>
          )
        )}
      <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages}
        className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <ChevronRight className="w-4 h-4" />
      </button>
      <button onClick={() => onPageChange(totalPages)} disabled={currentPage === totalPages}
        className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <ChevronsRight className="w-4 h-4" />
      </button>
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
