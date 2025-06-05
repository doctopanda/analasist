import React, { useState } from 'react';
import Layout from '../components/Layout';
import StatCard from '../components/StatCard';
import ChartCard from '../components/ChartCard';
import { Users, Building2, FileText, AlertTriangle, Mail, Upload, Download, PlusCircle } from 'lucide-react';

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
  const [showUserModal, setShowUserModal] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    rol: '',
    centro_salud_id: ''
  });

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    // Here you would typically make an API call to create the user
    console.log('Creating user:', newUser);
    setShowUserModal(false);
    setNewUser({ username: '', password: '', rol: '', centro_salud_id: '' });
  };

  return (
    <Layout title="Panel de Administración">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-800">Gestión del Sistema</h2>
        <button
          onClick={() => setShowUserModal(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <PlusCircle className="h-5 w-5 mr-2" />
          Nuevo Usuario
        </button>
      </div>

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">Gestión de Usuarios</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">admin</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Administrador</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Activo
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <button className="text-blue-600 hover:text-blue-900 mr-3">Editar</button>
                    <button className="text-red-600 hover:text-red-900">Desactivar</button>
                  </td>
                </tr>
                {/* Add more user rows here */}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">Acciones Rápidas</h3>
          <div className="space-y-4">
            <button className="w-full flex items-center px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200">
              <Upload className="h-5 w-5 mr-3 text-gray-600" />
              <span>Subir Boletín Informativo</span>
            </button>
            <button className="w-full flex items-center px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200">
              <Mail className="h-5 w-5 mr-3 text-gray-600" />
              <span>Enviar Notificación Masiva</span>
            </button>
            <button className="w-full flex items-center px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200">
              <Download className="h-5 w-5 mr-3 text-gray-600" />
              <span>Generar Reporte General</span>
            </button>
          </div>
        </div>
      </div>

      {/* User creation modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Crear Nuevo Usuario</h3>
            <form onSubmit={handleCreateUser}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                    Usuario
                  </label>
                  <input
                    type="text"
                    id="username"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    id="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="rol" className="block text-sm font-medium text-gray-700">
                    Rol
                  </label>
                  <select
                    id="rol"
                    value={newUser.rol}
                    onChange={(e) => setNewUser({ ...newUser, rol: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Seleccionar rol</option>
                    <option value="admin">Administrador</option>
                    <option value="analista">Analista</option>
                    <option value="centro_salud">Centro de Salud</option>
                  </select>
                </div>
                {newUser.rol === 'centro_salud' && (
                  <div>
                    <label htmlFor="centro_salud_id" className="block text-sm font-medium text-gray-700">
                      Centro de Salud
                    </label>
                    <select
                      id="centro_salud_id"
                      value={newUser.centro_salud_id}
                      onChange={(e) => setNewUser({ ...newUser, centro_salud_id: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    >
                      <option value="">Seleccionar centro</option>
                      <option value="1">Hospital General de la Ciudad</option>
                      <option value="2">Centro de Salud Urbano</option>
                    </select>
                  </div>
                )}
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowUserModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  Crear Usuario
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
};

export default AdminDashboard;