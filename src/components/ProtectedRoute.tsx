import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRoles = [] 
}) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If specific roles are required, check if user has one of them
  if (requiredRoles.length > 0 && !requiredRoles.includes(user.rol)) {
    // Redirect to appropriate dashboard based on role
    if (user.rol === 'admin') {
      return <Navigate to="/admin\" replace />;
    } else if (user.rol === 'analista') {
      return <Navigate to="/analyst" replace />;
    } else if (user.rol === 'centro_salud') {
      return <Navigate to="/health-center\" replace />;
    }
    
    // Fallback to main dashboard
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;