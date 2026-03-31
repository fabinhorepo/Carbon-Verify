import { Code2, ExternalLink, Key, Shield, Zap, BookOpen, Satellite, Radio } from 'lucide-react';

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
  { method: 'GET', path: '/api/v1/fraud-alerts/grouped-by-type', desc: 'Alertas agrupados por tipo de fraude', auth: false },
  { method: 'GET', path: '/api/v1/fraud-alerts/grouped-by-type/{type}', desc: 'Alertas paginados de um tipo específico', auth: false },
  { method: 'PATCH', path: '/api/v1/fraud-alerts/{id}', desc: 'Atualizar status/revisão de alerta', auth: true },
  { method: 'GET', path: '/api/v1/portfolios', desc: 'Listar portfólios da organização', auth: true },
  { method: 'POST', path: '/api/v1/portfolios', desc: 'Criar novo portfólio', auth: true },
  { method: 'GET', path: '/api/v1/portfolios/{id}', desc: 'Detalhes com métricas e recomendações', auth: true },
  { method: 'POST', path: '/api/v1/portfolios/{id}/positions', desc: 'Adicionar posição ao portfólio', auth: true },
  { method: 'GET', path: '/api/v1/dashboard/metrics', desc: 'Métricas agregadas do dashboard', auth: true },
  { method: 'GET', path: '/api/v1/dashboard/risk-matrix', desc: 'Dados da matriz de risco (tabela quadriculada)', auth: true },
];

const methodColors: Record<string, string> = {
  GET: 'bg-blue-100 text-blue-700',
  POST: 'bg-green-100 text-green-700',
  PATCH: 'bg-amber-100 text-amber-700',
  PUT: 'bg-purple-100 text-purple-700',
  DELETE: 'bg-red-100 text-red-700',
};

const satellites = [
  {
    name: 'Sentinel-5P (Copernicus)',
    operator: 'ESA / Copernicus',
    status: 'Roadmap',
    desc: 'Monitoramento de gases de efeito estufa (CO₂, CH₄, NO₂) com cobertura global diária. Resolução de 7x3.5 km para mapeamento de emissões e verificação de reduções.',
    coverage: 'Global diária',
    dataType: 'CO₂, CH₄, NO₂, O₃, SO₂',
    useCase: 'Verificação de reduções de emissões declaradas por projetos de energia renovável e metano',
  },
  {
    name: 'OCO-2 / OCO-3',
    operator: 'NASA / JPL',
    status: 'Roadmap',
    desc: 'Satélites dedicados à medição precisa de CO₂ atmosférico com alta resolução espectral. OCO-3 na ISS permite observações em ângulos variados.',
    coverage: 'Global (16 dias revisita)',
    dataType: 'CO₂ atmosférico (XCO₂)',
    useCase: 'Validação de sequestro de carbono em projetos REDD+ e reflorestamento via medições de CO₂ regional',
  },
  {
    name: 'Landsat 8/9',
    operator: 'NASA / USGS',
    status: 'Roadmap',
    desc: 'Imageamento multiespectral de alta resolução (30m) para monitoramento de uso do solo, desmatamento e cobertura vegetal. Dados gratuitos desde 1972.',
    coverage: 'Global (16 dias revisita)',
    dataType: 'Imagens multiespectrais (11 bandas)',
    useCase: 'Detecção de desmatamento, verificação de áreas de projeto REDD+ e monitoramento de reflorestamento (ARR)',
  },
  {
    name: 'Sentinel-2 (Copernicus)',
    operator: 'ESA / Copernicus',
    status: 'Roadmap',
    desc: 'Imageamento multiespectral de alta resolução (10m) com revisita de 5 dias. Ideal para monitoramento de vegetação, biomassa e mudanças no uso do solo.',
    coverage: 'Global (5 dias revisita)',
    dataType: 'Imagens multiespectrais (13 bandas)',
    useCase: 'Monitoramento contínuo de biomassa florestal, NDVI e verificação de permanência em projetos de carbono',
  },
  {
    name: 'GOES-16/17/18 (GOES-R)',
    operator: 'NOAA / NASA',
    status: 'Roadmap',
    desc: 'Satélites geoestacionários com monitoramento contínuo (a cada 5 minutos) de eventos climáticos extremos, incêndios florestais e qualidade do ar nas Américas.',
    coverage: 'Hemisfério Ocidental (contínuo)',
    dataType: 'Imagens IR/visível, detecção de incêndios, aerossóis',
    useCase: 'Alerta em tempo real de incêndios em áreas de projeto, avaliação de riscos de permanência e eventos climáticos',
  },
  {
    name: 'TROPOMI (Sentinel-5P)',
    operator: 'ESA / KNMI',
    status: 'Roadmap',
    desc: 'Instrumento de última geração a bordo do Sentinel-5P com resolução sem precedentes (5.5x3.5 km) para mapeamento de metano e outros gases traço.',
    coverage: 'Global diária',
    dataType: 'CH₄, CO, HCHO, aerossóis',
    useCase: 'Detecção de vazamentos de metano em projetos de captura, verificação de cookstoves e queima de biomassa',
  },
];

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
          <p className="text-sm text-slate-500 mt-1">API REST v1 com versionamento semântico &middot; {endpoints.length} endpoints</p>
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
                      <span className="text-slate-300">&mdash;</span>
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

      {/* Satellite Remote Sensing Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
            <Satellite className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Sensoriamento em Tempo Real Planejado</h3>
            <p className="text-sm text-slate-500">Integração com satélites de monitoramento climático para verificação contínua de projetos de carbono</p>
          </div>
        </div>

        <div className="mt-4 mb-6 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Radio className="w-5 h-5 text-indigo-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-indigo-800">Monitoramento por Satélite para Créditos de Carbono</p>
              <p className="text-sm text-indigo-700 mt-1">
                A integração com dados de sensoriamento remoto permitirá verificação independente e contínua dos projetos de carbono,
                incluindo detecção de desmatamento, medição de biomassa, monitoramento de emissões de gases de efeito estufa e
                alertas em tempo real sobre eventos que possam comprometer a integridade dos créditos.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {satellites.map((sat, idx) => (
            <div key={idx} className="p-5 border border-slate-200 rounded-lg hover:border-indigo-300 hover:shadow-sm transition-all">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Satellite className="w-4 h-4 text-indigo-500" />
                  <p className="font-semibold text-slate-900">{sat.name}</p>
                </div>
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                  {sat.status}
                </span>
              </div>
              <p className="text-sm text-slate-600 mb-3">{sat.desc}</p>
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide w-24 shrink-0 pt-0.5">Operador</span>
                  <span className="text-sm text-slate-700">{sat.operator}</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide w-24 shrink-0 pt-0.5">Cobertura</span>
                  <span className="text-sm text-slate-700">{sat.coverage}</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide w-24 shrink-0 pt-0.5">Dados</span>
                  <span className="text-sm text-slate-700">{sat.dataType}</span>
                </div>
                <div className="flex items-start gap-2 mt-2 pt-2 border-t border-slate-100">
                  <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wide w-24 shrink-0 pt-0.5">Uso no CV</span>
                  <span className="text-sm text-indigo-700 font-medium">{sat.useCase}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
