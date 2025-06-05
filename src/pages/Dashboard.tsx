import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to role-specific dashboard
    if (user) {
      if (user.rol === 'admin') {
        navigate('/admin');
      } else if (user.rol === 'analista') {
        navigate('/analyst');
      } else if (user.rol === 'centro_salud') {
        navigate('/health-center');
      }
    }
  }, [user, navigate]);

  return (
    <Layout title="Dashboard">
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    </Layout>
  );
};

export default Dashboard;