import React from 'react';
import Layout from '../components/Layout';
import StatCard from '../components/StatCard';
import ChartCard from '../components/ChartCard';
import { Users, Building2, FileText, AlertTriangle } from 'lucide-react';

// Mock data
const usersByRole = [
  { name: 'Administradores', value: 1 },
  { name: 'Analistas', value: 3 },
  { name: 'Centros de Salud', value: 12 }
];

const reportsByMonth = [
  { name: 'Ene', value: 45 },
  { name: 'Feb', value: 52 },
  { name: 'Mar', value: 49 },
  { name: 'Abr', value: 63 },
  { name: 'May', value: 58 },
  { name: 'Jun', value: 64 }
];

const reportsByDiagnosis = [
  { name: 'Dengue', value: 35 },
  { name: 'COVID-19', value: 40 },
  { name: 'Influenza', value: 25 },
  { name: 'Zika', value: 15 },
  { name: 'Chikungunya', value: 10 }
];

const AdminDashboard: React.FC = () => {
  return (
    <Layout title="Panel de Administración">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          title="Usuarios Totales" 
          value={16} 
          icon={Users} 
          color="bg-blue-600"
        />
        <StatCard 
          title="Centros de Salud" 
          value={12} 
          icon={Building2} 
          color="bg-green-600"
        />
        <StatCard 
          title="Reportes Totales" 
          value={331} 
          icon={FileText} 
          color="bg-amber-600"
        />
        <StatCard 
          title="Alertas Activas" 
          value={3} 
          icon={AlertTriangle} 
          color="bg-red-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChartCard 
          title="Usuarios por Rol" 
          type="pie" 
          data={usersByRole} 
        />
        <ChartCard 
          title="Reportes por Mes" 
          type="bar" 
          data={reportsByMonth} 
        />
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Actividad Reciente</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acción</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">hospital1</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Nuevo reporte</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2025-06-15 10:23</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">192.168.1.45</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">analista1</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Acceso al sistema</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2025-06-15 09:45</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">192.168.1.32</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">admin</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Creación de usuario</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2025-06-14 16:12</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">192.168.1.1</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">hospital1</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Nuevo reporte</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2025-06-14 11:05</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">192.168.1.45</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">analista1</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Generación de reporte</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2025-06-13 14:30</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">192.168.1.32</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
};

export default AdminDashboard;