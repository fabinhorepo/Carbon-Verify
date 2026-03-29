import { Code2, ExternalLink, Key, Shield, Zap, BookOpen } from 'lucide-react';

const endpoints = [
  { method: 'POST', path: '/api/v1/auth/login', desc: 'Autenticação e obtenção de token JWT', auth: false },
  { method: 'POST', path: '/api/v1/auth/register', desc: 'Registro de novo usuário e organização', auth: false },
  { method: 'GET', path: '/api/v1/projects', desc: 'Listar projetos com filtros (tipo, país, score)', auth: false },
  { method: 'GET', path: '/api/v1/projects/{id}', desc: 'Detalhes do projeto com rating e alertas', auth: false },
  { method: 'POST', path: '/api/v1/projects', desc: 'Criar projeto e calcular rating automaticamente', auth: true },
  { method: 'GET', path: '/api/v1/projects/{id}/rating', desc: 'Rating detalhado com sub-scores e explicação', auth: false },
  { method: 'POST', path: '/api/v1/projects/{id}/recalculate-rating', desc: 'Recalcular rating de um projeto', auth: true },
  { method: 'GET', path: '/api/v1/fraud-alerts', desc: 'Listar alertas de fraude com filtros', auth: false },
  { method: 'GET', path: '/api/v1/fraud-alerts/summary', desc: 'Resumo dos alertas por severidade e tipo', auth: false },
  { method: 'PATCH', path: '/api/v1/fraud-alerts/{id}', desc: 'Atualizar status/revisão de alerta', auth: true },
  { method: 'GET', path: '/api/v1/portfolios', desc: 'Listar portfólios da organização', auth: true },
  { method: 'POST', path: '/api/v1/portfolios', desc: 'Criar novo portfólio', auth: true },
  { method: 'GET', path: '/api/v1/portfolios/{id}', desc: 'Detalhes com métricas e recomendações', auth: true },
  { method: 'POST', path: '/api/v1/portfolios/{id}/positions', desc: 'Adicionar posição ao portfólio', auth: true },
  { method: 'GET', path: '/api/v1/dashboard/metrics', desc: 'Métricas agregadas do dashboard', auth: true },
  { method: 'GET', path: '/api/v1/dashboard/risk-matrix', desc: 'Dados da matriz de risco', auth: true },
];

const methodColors: Record<string, string> = {
  GET: 'bg-blue-100 text-blue-700',
  POST: 'bg-green-100 text-green-700',
  PATCH: 'bg-amber-100 text-amber-700',
  PUT: 'bg-purple-100 text-purple-700',
  DELETE: 'bg-red-100 text-red-700',
};

export default function ApiDocs() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">API & Integração</h1>
        <p className="text-slate-500 mt-1">Documentação da API REST para integração com marketplaces e softwares ESG</p>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <a href="/api/docs" target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-3 p-4 bg-white rounded-xl border border-slate-200 hover:border-emerald-300 hover:shadow-sm transition-all">
          <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-900">Swagger UI</p>
            <p className="text-xs text-slate-500">Documentação interativa</p>
          </div>
          <ExternalLink className="w-4 h-4 text-slate-400 ml-auto" />
        </a>
        <a href="/api/redoc" target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-3 p-4 bg-white rounded-xl border border-slate-200 hover:border-blue-300 hover:shadow-sm transition-all">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Code2 className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-900">ReDoc</p>
            <p className="text-xs text-slate-500">Documentação detalhada</p>
          </div>
          <ExternalLink className="w-4 h-4 text-slate-400 ml-auto" />
        </a>
        <a href="/api/openapi.json" target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-3 p-4 bg-white rounded-xl border border-slate-200 hover:border-purple-300 hover:shadow-sm transition-all">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-900">OpenAPI Spec</p>
            <p className="text-xs text-slate-500">Especificação JSON</p>
          </div>
          <ExternalLink className="w-4 h-4 text-slate-400 ml-auto" />
        </a>
      </div>

      {/* Auth Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
            <Key className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Autenticação</h3>
            <p className="text-sm text-slate-500">Bearer Token (JWT) via header Authorization</p>
          </div>
        </div>
        <div className="bg-slate-900 rounded-lg p-4 text-sm font-mono text-slate-300 overflow-x-auto">
          <p className="text-slate-500"># 1. Obter token</p>
          <p>curl -X POST /api/v1/auth/login \</p>
          <p className="pl-4">-H "Content-Type: application/json" \</p>
          <p className="pl-4">-d '{`{"email":"demo@carbonverify.com","password":"demo123"}`}'</p>
          <br />
          <p className="text-slate-500"># 2. Usar token nas requisições</p>
          <p>curl /api/v1/dashboard/metrics \</p>
          <p className="pl-4">-H "Authorization: Bearer {'<token>'}"</p>
        </div>
      </div>

      {/* Endpoints Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900">Endpoints Disponíveis</h3>
          <p className="text-sm text-slate-500 mt-1">API REST v1 com versionamento semântico</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left py-3 px-4 font-semibold text-slate-600 w-20">Método</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-600">Endpoint</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-600">Descrição</th>
                <th className="text-center py-3 px-4 font-semibold text-slate-600 w-20">Auth</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map((ep, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${methodColors[ep.method]}`}>
                      {ep.method}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-sm text-slate-700">{ep.path}</td>
                  <td className="py-3 px-4 text-slate-600">{ep.desc}</td>
                  <td className="py-3 px-4 text-center">
                    {ep.auth ? (
                      <Shield className="w-4 h-4 text-amber-500 mx-auto" />
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Integration Partners */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Integrações Planejadas</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { name: 'Verra Registry', status: 'MVP', desc: 'Importação de metadados VCS' },
            { name: 'Gold Standard', status: 'MVP', desc: 'Importação de projetos GS' },
            { name: 'Carbonmark', status: 'Roadmap', desc: 'Marketplace de carbono' },
            { name: 'Toucan Protocol', status: 'Roadmap', desc: 'Créditos tokenizados' },
            { name: 'Plan A', status: 'Roadmap', desc: 'Software ESG' },
            { name: 'Normative', status: 'Roadmap', desc: 'Contabilidade de carbono' },
          ].map((partner, idx) => (
            <div key={idx} className="p-4 border border-slate-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="font-medium text-slate-900">{partner.name}</p>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  partner.status === 'MVP' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  {partner.status}
                </span>
              </div>
              <p className="text-sm text-slate-500">{partner.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
