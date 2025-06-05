import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/AdminDashboard';
import AnalystDashboard from './pages/AnalystDashboard';
import HealthCenterDashboard from './pages/HealthCenterDashboard';
import ReportForm from './pages/ReportForm';
import NotFound from './pages/NotFound';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          
          <Route path="/admin" element={
            <ProtectedRoute requiredRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/analyst" element={
            <ProtectedRoute requiredRoles={['analista', 'admin']}>
              <AnalystDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/health-center" element={
            <ProtectedRoute requiredRoles={['centro_salud']}>
              <HealthCenterDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/report/new" element={
            <ProtectedRoute requiredRoles={['centro_salud']}>
              <ReportForm />
            </ProtectedRoute>
          } />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;