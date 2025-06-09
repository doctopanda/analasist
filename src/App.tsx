import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { DataProvider } from './contexts/DataContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/AdminDashboard';
import AnalystDashboard from './pages/AnalystDashboard';
import HealthCenterDashboard from './pages/HealthCenterDashboard';
import ReportForm from './pages/ReportForm';
import HealthCentersPage from './pages/HealthCentersPage';
import NotFound from './pages/NotFound';

// Admin Management Pages
import UsersManagement from './pages/UsersManagement';
import HealthCentersManagement from './pages/HealthCentersManagement';
import ReportsManagement from './pages/ReportsManagement';
import AlertsManagement from './pages/AlertsManagement';

function App() {
  return (
    <AuthProvider>
      <DataProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            
            <Route path="/admin" element={
              <ProtectedRoute requiredRoles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            } />
            
            {/* Admin Management Routes */}
            <Route path="/admin/users" element={
              <ProtectedRoute requiredRoles={['admin']}>
                <UsersManagement />
              </ProtectedRoute>
            } />
            
            <Route path="/admin/health-centers" element={
              <ProtectedRoute requiredRoles={['admin']}>
                <HealthCentersManagement />
              </ProtectedRoute>
            } />
            
            <Route path="/admin/reports" element={
              <ProtectedRoute requiredRoles={['admin']}>
                <ReportsManagement />
              </ProtectedRoute>
            } />
            
            <Route path="/admin/alerts" element={
              <ProtectedRoute requiredRoles={['admin']}>
                <AlertsManagement />
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
            
            <Route path="/health-centers-map" element={
              <ProtectedRoute requiredRoles={['admin', 'analista']}>
                <HealthCentersPage />
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
      </DataProvider>
    </AuthProvider>
  );
}

export default App;