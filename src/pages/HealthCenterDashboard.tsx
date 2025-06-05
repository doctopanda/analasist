import React from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import StatCard from '../components/StatCard';
import { FileText, CheckCircle, Clock, AlertTriangle, PlusCircle } from 'lucide-react';

// Mock data for reports
const recentReports = [
  { id: 'FOL-1045', date: '2025-06-15', diagnosis: 'Dengue', status: 'Enviado' },
  { id: 'FOL-1044', date: '2025-06-14', diagnosis: 'COVID-19', status: 'Enviado' },
  { id: 'FOL-1043', date: '2025-06-12', diagnosis: 'Influenza', status: 'Enviado' },
  { id: 'FOL-1042', date: '2025-06-10', diagnosis: 'Dengue', status: 'Enviado' },
  { id: 'FOL-1041', date: '2025-06-08', diagnosis: 'Zika', status: 'Enviado' }
];

const HealthCenterDashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Layout title="Centro de Salud">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          title="Reportes Totales" 
          value={45} 
          icon={FileText} 
          color="bg-blue-600"
        />
        <StatCard 
          title="Reportes Enviados" 
          value={45} 
          icon={CheckCircle} 
          color="bg-green-600"
        />
        <StatCard 
          title="Pendientes" 
          value={0} 
          icon={Clock} 
          color="bg-amber-600"
        />
        <StatCard 
          title="Con Alertas" 
          value={3} 
          icon={AlertTriangle} 
          color="bg-red-600"
        />
      </div>

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-800">Reportes Recientes</h2>
        <button
          onClick={() => navigate('/report/new')}
          className="flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusCircle className="h-5 w-5 mr-2" />
          Nuevo Reporte
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Folio</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Diagnóstico</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentReports.map((report) => (
                <tr key={report.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{report.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{report.date}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{report.diagnosis}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      {report.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <button className="text-blue-600 hover:text-blue-900 mr-3">Ver</button>
                    <button className="text-blue-600 hover:text-blue-900">Imprimir</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="bg-gray-50 px-6 py-3 flex justify-between items-center">
          <div className="text-sm text-gray-500">
            Mostrando 5 de 45 reportes
          </div>
          <div className="flex space-x-2">
            <button className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-100">
              Anterior
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-100">
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default HealthCenterDashboard;