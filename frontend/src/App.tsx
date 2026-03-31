import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import FraudAlerts from './pages/FraudAlerts';
import Portfolio from './pages/Portfolio';
import ApiDocs from './pages/ApiDocs';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectDetail />} />
          <Route path="fraud-alerts" element={<FraudAlerts />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="api-docs" element={<ApiDocs />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
