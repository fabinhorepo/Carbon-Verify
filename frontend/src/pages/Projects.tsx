import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { getProjects } from '../utils/api';
import { getGradeClass, formatNumber, formatScore } from '../utils/helpers';

const PAGE_SIZE = 20;

export default function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterCountry, setFilterCountry] = useState('');
  const [filterRegistry, setFilterRegistry] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Listas de filtros estáticas (carregadas uma vez sem filtro)
  const [allTypes, setAllTypes] = useState<string[]>([]);
  const [allCountries, setAllCountries] = useState<string[]>([]);

  useEffect(() => {
    // Carregar opções de filtro com todos os projetos (primeira página grande)
    getProjects({ page: 1, page_size: 100 }).then(res => {
      const items = res.data.items || [];
      setAllTypes([...new Set(items.map((p: any) => p.project_type))] as string[]);
      setAllCountries([...new Set(items.map((p: any) => p.country))].sort() as string[]);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    loadProjects();
  }, [page]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setPage(1);
      loadProjects(1);
    }, 300);
    return () => clearTimeout(timeout);
  }, [search, filterType, filterCountry, filterRegistry]);

  const loadProjects = async (forcePage?: number) => {
    setLoading(true);
    try {
      const params: any = { page: forcePage || page, page_size: PAGE_SIZE };
      if (search) params.search = search;
      if (filterType) params.project_type = filterType;
      if (filterCountry) params.country = filterCountry;
      if (filterRegistry) params.registry = filterRegistry;
      const res = await getProjects(params);
      const data = res.data;
      setProjects(data.items || []);
      setTotalPages(data.total_pages || 1);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const goToPage = (p: number) => {
    if (p >= 1 && p <= totalPages) setPage(p);
  };

  const startItem = (page - 1) * PAGE_SIZE + 1;
  const endItem = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Projetos de Carbono</h1>
          <p className="text-slate-500 mt-1">Rating de qualidade AAA-D para cada projeto &middot; {total} projetos</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text" placeholder="Buscar projetos..."
            value={search} onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none text-sm"
          />
        </div>
        <select
          value={filterType} onChange={e => setFilterType(e.target.value)}
          className="px-3 py-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todos os tipos</option>
          {allTypes.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={filterCountry} onChange={e => setFilterCountry(e.target.value)}
          className="px-3 py-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todos os países</option>
          {allCountries.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select
          value={filterRegistry} onChange={e => setFilterRegistry(e.target.value)}
          className="px-3 py-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todos os registros</option>
          <option value="Verra">Verra</option>
          <option value="Gold Standard">Gold Standard</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left py-3 px-4 font-semibold text-slate-600">Projeto</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-600">Tipo</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-600">País</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-600">Registro</th>
                <th className="text-center py-3 px-4 font-semibold text-slate-600">Rating</th>
                <th className="text-center py-3 px-4 font-semibold text-slate-600">Score</th>
                <th className="text-center py-3 px-4 font-semibold text-slate-600">Créditos</th>
                <th className="text-center py-3 px-4 font-semibold text-slate-600">Alertas</th>
                <th className="text-right py-3 px-4 font-semibold text-slate-600"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={9} className="py-12 text-center text-slate-400">Carregando...</td></tr>
              ) : projects.length === 0 ? (
                <tr><td colSpan={9} className="py-12 text-center text-slate-400">Nenhum projeto encontrado</td></tr>
              ) : projects.map(p => (
                <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-medium text-slate-900 max-w-xs truncate">{p.name}</div>
                    <div className="text-xs text-slate-400">{p.external_id}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-700">
                      {p.project_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{p.country}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${
                      p.registry === 'Verra' ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'
                    }`}>
                      {p.registry || '—'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    {p.rating ? (
                      <span className={`inline-flex items-center justify-center w-12 h-7 rounded-md text-xs font-bold ${getGradeClass(p.rating.grade)}`}>
                        {p.rating.grade}
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center font-mono">
                    {p.rating ? formatScore(p.rating.overall_score) : '—'}
                  </td>
                  <td className="py-3 px-4 text-center text-slate-600">
                    {formatNumber(p.total_credits_issued)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    {p.fraud_alert_count > 0 ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                        {p.fraud_alert_count}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        0
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link to={`/projects/${p.id}`} className="text-emerald-600 hover:text-emerald-700 font-medium text-sm">
                      Detalhes
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && total > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50 gap-3">
            <div className="text-sm text-slate-500">
              Mostrando <span className="font-medium text-slate-700">{startItem}</span> a <span className="font-medium text-slate-700">{endItem}</span> de <span className="font-medium text-slate-700">{total}</span> projetos
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => goToPage(1)}
                disabled={page === 1}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Primeira página"
              >
                <ChevronsLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => goToPage(page - 1)}
                disabled={page === 1}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Página anterior"
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
                          : 'border-slate-300 text-slate-600 hover:bg-white hover:text-slate-800'
                      }`}
                    >
                      {p}
                    </button>
                  )
                )}

              <button
                onClick={() => goToPage(page + 1)}
                disabled={page === totalPages}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Próxima página"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => goToPage(totalPages)}
                disabled={page === totalPages}
                className="p-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-white hover:text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Última página"
              >
                <ChevronsRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
