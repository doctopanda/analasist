import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import StatCard from '../components/StatCard';
import ChartCard from '../components/ChartCard';
import { useData } from '../contexts/DataContext';
import { Users, Building2, FileText, AlertTriangle, Mail, Upload, Download, PlusCircle } from 'lucide-react';

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { getStatistics, users, reports, alerts, healthCenters } = useData();
  const [showUserModal, setShowUserModal] = useState(false);
  const [showCenterModal, setShowCenterModal] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    rol: '',
    centro_salud_id: ''
  });
  const [newCenter, setNewCenter] = useState({
    nombre: '',
    codigo: '',
    direccion: '',
    estado: 'Sonora',
    municipio: '',
    distrito: '',
    tipo: '',
    telefono: '',
    email: '',
    responsable: ''
  });

  const stats = getStatistics();

  // Generate chart data from real data
  const usersByRole = [
    { name: 'Administradores', value: users.filter(u => u.rol === 'admin').length },
    { name: 'Analistas', value: users.filter(u => u.rol === 'analista').length },
    { name: 'Centros de Salud', value: users.filter(u => u.rol === 'centro_salud').length }
  ];

  const reportsByMonth = [
    { name: 'Ene', value: reports.filter(r => r.fecha_subida.includes('2025-01')).length },
    { name: 'Feb', value: reports.filter(r => r.fecha_subida.includes('2025-02')).length },
    { name: 'Mar', value: reports.filter(r => r.fecha_subida.includes('2025-03')).length },
    { name: 'Abr', value: reports.filter(r => r.fecha_subida.includes('2025-04')).length },
    { name: 'May', value: reports.filter(r => r.fecha_subida.includes('2025-05')).length },
    { name: 'Jun', value: reports.filter(r => r.fecha_subida.includes('2025-06')).length }
  ];

  const centersByType = [
    { name: 'Hospitales', value: healthCenters.filter(c => c.tipo === 'Hospital').length },
    { name: 'Centros de Salud', value: healthCenters.filter(c => c.tipo === 'Centro de Salud').length },
    { name: 'Clínicas', value: healthCenters.filter(c => c.tipo === 'Clínica').length },
    { name: 'Otros', value: healthCenters.filter(c => !['Hospital', 'Centro de Salud', 'Clínica'].includes(c.tipo)).length }
  ];

  const alertsBySeverity = [
    { name: 'Baja', value: alerts.filter(a => a.severidad === 'baja').length },
    { name: 'Media', value: alerts.filter(a => a.severidad === 'media').length },
    { name: 'Alta', value: alerts.filter(a => a.severidad === 'alta').length },
    { name: 'Crítica', value: alerts.filter(a => a.severidad === 'critica').length }
  ];

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Creating user:', newUser);
    setShowUserModal(false);
    setNewUser({ username: '', password: '', rol: '', centro_salud_id: '' });
  };

  const handleCreateCenter = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Creating health center:', newCenter);
    setShowCenterModal(false);
    setNewCenter({
      nombre: '',
      codigo: '',
      direccion: '',
      estado: 'Sonora',
      municipio: '',
      distrito: '',
      tipo: '',
      telefono: '',
      email: '',
      responsable: ''
    });
  };

  // Handle stat card clicks
  const handleStatCardClick = (cardType: string) => {
    switch (cardType) {
      case 'users':
        navigate('/admin/users');
        break;
      case 'centers':
        navigate('/admin/health-centers');
        break;
      case 'reports':
        navigate('/admin/reports');
        break;
      case 'alerts':
        navigate('/admin/alerts');
        break;
      default:
        break;
    }
  };

  return (
    <Layout title="Panel de Administración">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-800">Gestión del Sistema</h2>
        <div className="space-x-4">
          <button
            onClick={() => setShowCenterModal(true)}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            <Building2 className="h-5 w-5 mr-2" />
            Nuevo Centro de Salud
          </button>
          <button
            onClick={() => setShowUserModal(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <PlusCircle className="h-5 w-5 mr-2" />
            Nuevo Usuario
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div onClick={() => handleStatCardClick('users')} className="cursor-pointer">
          <StatCard 
            title="Usuarios Totales" 
            value={stats.totalUsers} 
            icon={Users} 
            color="bg-blue-600"
          />
        </div>
        <div onClick={() => handleStatCardClick('centers')} className="cursor-pointer">
          <StatCard 
            title="Centros de Salud" 
            value={stats.totalHealthCenters} 
            icon={Building2} 
            color="bg-green-600"
          />
        </div>
        <div onClick={() => handleStatCardClick('reports')} className="cursor-pointer">
          <StatCard 
            title="Reportes Totales" 
            value={stats.totalReports} 
            icon={FileText} 
            color="bg-amber-600"
          />
        </div>
        <div onClick={() => handleStatCardClick('alerts')} className="cursor-pointer">
          <StatCard 
            title="Alertas Activas" 
            value={stats.activeAlerts} 
            icon={AlertTriangle} 
            color="bg-red-600"
          />
        </div>
      </div>

      {/* Health Center Modal */}
      {showCenterModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Registrar Nuevo Centro de Salud</h3>
            <form onSubmit={handleCreateCenter}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="nombre" className="block text-sm font-medium text-gray-700">
                    Nombre del Centro
                  </label>
                  <input
                    type="text"
                    id="nombre"
                    value={newCenter.nombre}
                    onChange={(e) => setNewCenter({ ...newCenter, nombre: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="codigo" className="block text-sm font-medium text-gray-700">
                    Código de Establecimiento
                  </label>
                  <input
                    type="text"
                    id="codigo"
                    value={newCenter.codigo}
                    onChange={(e) => setNewCenter({ ...newCenter, codigo: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div className="md:col-span-2">
                  <label htmlFor="direccion" className="block text-sm font-medium text-gray-700">
                    Dirección
                  </label>
                  <input
                    type="text"
                    id="direccion"
                    value={newCenter.direccion}
                    onChange={(e) => setNewCenter({ ...newCenter, direccion: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="estado" className="block text-sm font-medium text-gray-700">
                    Estado
                  </label>
                  <input
                    type="text"
                    id="estado"
                    value={newCenter.estado}
                    disabled
                    className="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 shadow-sm"
                  />
                </div>
                <div>
                  <label htmlFor="municipio" className="block text-sm font-medium text-gray-700">
                    Municipio
                  </label>
                  <select
                    id="municipio"
                    value={newCenter.municipio}
                    onChange={(e) => setNewCenter({ ...newCenter, municipio: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Seleccionar municipio</option>
                    <option value="Hermosillo">Hermosillo</option>
                    <option value="Cajeme">Cajeme</option>
                    <option value="Nogales">Nogales</option>
                    <option value="San Luis Río Colorado">San Luis Río Colorado</option>
                    <option value="Navojoa">Navojoa</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="distrito" className="block text-sm font-medium text-gray-700">
                    Distrito
                  </label>
                  <select
                    id="distrito"
                    value={newCenter.distrito}
                    onChange={(e) => setNewCenter({ ...newCenter, distrito: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Seleccionar distrito</option>
                    <option value="Distrito 1">Distrito 1</option>
                    <option value="Distrito 2">Distrito 2</option>
                    <option value="Distrito 3">Distrito 3</option>
                    <option value="Distrito 4">Distrito 4</option>
                    <option value="Distrito 5">Distrito 5</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="tipo" className="block text-sm font-medium text-gray-700">
                    Tipo de Centro
                  </label>
                  <select
                    id="tipo"
                    value={newCenter.tipo}
                    onChange={(e) => setNewCenter({ ...newCenter, tipo: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Seleccionar tipo</option>
                    <option value="Hospital">Hospital</option>
                    <option value="Centro de Salud">Centro de Salud</option>
                    <option value="Clínica">Clínica</option>
                    <option value="Unidad Móvil">Unidad Móvil</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="telefono" className="block text-sm font-medium text-gray-700">
                    Teléfono
                  </label>
                  <input
                    type="tel"
                    id="telefono"
                    value={newCenter.telefono}
                    onChange={(e) => setNewCenter({ ...newCenter, telefono: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Correo Electrónico
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={newCenter.email}
                    onChange={(e) => setNewCenter({ ...newCenter, email: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="responsable" className="block text-sm font-medium text-gray-700">
                    Responsable
                  </label>
                  <input
                    type="text"
                    id="responsable"
                    value={newCenter.responsable}
                    onChange={(e) => setNewCenter({ ...newCenter, responsable: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCenterModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  Registrar Centro
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* User Modal */}
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
                      {healthCenters.map(center => (
                        <option key={center.id} value={center.id}>{center.nombre}</option>
                      ))}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChartCard 
          title="Usuarios por Rol" 
          type="pie" 
          data={usersByRole} 
        />
        <ChartCard 
          title="Centros por Tipo" 
          type="pie" 
          data={centersByType} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChartCard 
          title="Reportes por Mes" 
          type="bar" 
          data={reportsByMonth} 
        />
        <ChartCard 
          title="Alertas por Severidad" 
          type="bar" 
          data={alertsBySeverity} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">Resumen del Sistema</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Usuarios Activos:</span>
              <span className="font-medium text-green-600">{stats.activeUsers}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Reportes Pendientes:</span>
              <span className="font-medium text-yellow-600">{stats.pendingReports}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Alertas Críticas:</span>
              <span className="font-medium text-red-600">{stats.criticalAlerts}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Centros Registrados:</span>
              <span className="font-medium text-blue-600">{stats.totalHealthCenters}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">Acciones Rápidas</h3>
          <div className="space-y-4">
            <button 
              onClick={() => navigate('/health-centers-map')}
              className="w-full flex items-center px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              <Upload className="h-5 w-5 mr-3 text-gray-600" />
              <span>Cargar Datos de Centros</span>
            </button>
            <button className="w-full flex items-center px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200">
              <Mail className="h-5 w-5 mr-3 text-gray-600"  />
              <span>Enviar Notificación Masiva</span>
            </button>
            <button className="w-full flex items-center px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200">
              <Download className="h-5 w-5 mr-3 text-gray-600" />
              <span>Generar Reporte General</span>
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Actividad Reciente</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.slice(0, 5).map((report) => (
                <tr key={report.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Reporte</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    Nuevo reporte {report.folio} - {report.diagnostico}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{report.usuario_subida}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.fecha_subida).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
};

export default AdminDashboard;