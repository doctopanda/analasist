import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { ArrowLeft, Edit, Trash2, UserPlus, Eye, EyeOff } from 'lucide-react';

interface User {
  id: number;
  username: string;
  rol: string;
  centro_salud_id?: number;
  centro_salud_nombre?: string;
  distrito?: string;
  fecha_registro: string;
  ultima_participacion: string;
  estado: 'activo' | 'inactivo';
}

const mockUsers: User[] = [
  {
    id: 1,
    username: 'admin',
    rol: 'admin',
    fecha_registro: '2024-01-15',
    ultima_participacion: '2025-01-15',
    estado: 'activo'
  },
  {
    id: 2,
    username: 'analista1',
    rol: 'analista',
    fecha_registro: '2024-02-20',
    ultima_participacion: '2025-01-14',
    estado: 'activo'
  },
  {
    id: 3,
    username: 'analista2',
    rol: 'analista',
    fecha_registro: '2024-03-10',
    ultima_participacion: '2025-01-10',
    estado: 'activo'
  },
  {
    id: 4,
    username: 'hospital1',
    rol: 'centro_salud',
    centro_salud_id: 1,
    centro_salud_nombre: 'Hospital General del Estado de Sonora',
    distrito: 'Distrito 1',
    fecha_registro: '2024-04-05',
    ultima_participacion: '2025-01-15',
    estado: 'activo'
  },
  {
    id: 5,
    username: 'centro_hermosillo',
    rol: 'centro_salud',
    centro_salud_id: 2,
    centro_salud_nombre: 'Centro de Salud Urbano Villa de Seris',
    distrito: 'Distrito 1',
    fecha_registro: '2024-04-12',
    ultima_participacion: '2025-01-13',
    estado: 'activo'
  },
  {
    id: 6,
    username: 'hospital_cajeme',
    rol: 'centro_salud',
    centro_salud_id: 3,
    centro_salud_nombre: 'Hospital General de Cajeme',
    distrito: 'Distrito 2',
    fecha_registro: '2024-05-01',
    ultima_participacion: '2025-01-12',
    estado: 'activo'
  },
  {
    id: 7,
    username: 'centro_nogales',
    rol: 'centro_salud',
    centro_salud_id: 4,
    centro_salud_nombre: 'Centro de Salud Nogales',
    distrito: 'Distrito 3',
    fecha_registro: '2024-05-15',
    ultima_participacion: '2025-01-11',
    estado: 'activo'
  },
  {
    id: 8,
    username: 'hospital_slrc',
    rol: 'centro_salud',
    centro_salud_id: 5,
    centro_salud_nombre: 'Hospital General San Luis Río Colorado',
    distrito: 'Distrito 4',
    fecha_registro: '2024-06-01',
    ultima_participacion: '2025-01-09',
    estado: 'activo'
  },
  {
    id: 9,
    username: 'centro_guaymas',
    rol: 'centro_salud',
    centro_salud_id: 6,
    centro_salud_nombre: 'Centro de Salud Guaymas',
    distrito: 'Distrito 2',
    fecha_registro: '2024-06-15',
    ultima_participacion: '2025-01-08',
    estado: 'activo'
  },
  {
    id: 10,
    username: 'clinica_navojoa',
    rol: 'centro_salud',
    centro_salud_id: 7,
    centro_salud_nombre: 'Clínica del IMSS Navojoa',
    distrito: 'Distrito 2',
    fecha_registro: '2024-07-01',
    ultima_participacion: '2025-01-07',
    estado: 'activo'
  },
  {
    id: 11,
    username: 'analista3',
    rol: 'analista',
    fecha_registro: '2024-08-01',
    ultima_participacion: '2024-12-15',
    estado: 'inactivo'
  },
  {
    id: 12,
    username: 'centro_agua_prieta',
    rol: 'centro_salud',
    centro_salud_id: 8,
    centro_salud_nombre: 'Centro de Salud Agua Prieta',
    distrito: 'Distrito 3',
    fecha_registro: '2024-08-15',
    ultima_participacion: '2025-01-06',
    estado: 'activo'
  },
  {
    id: 13,
    username: 'hospital_puerto_penasco',
    rol: 'centro_salud',
    centro_salud_id: 9,
    centro_salud_nombre: 'Hospital General Puerto Peñasco',
    distrito: 'Distrito 4',
    fecha_registro: '2024-09-01',
    ultima_participacion: '2025-01-05',
    estado: 'activo'
  },
  {
    id: 14,
    username: 'centro_caborca',
    rol: 'centro_salud',
    centro_salud_id: 10,
    centro_salud_nombre: 'Centro de Salud Caborca',
    distrito: 'Distrito 4',
    fecha_registro: '2024-09-15',
    ultima_participacion: '2025-01-04',
    estado: 'activo'
  },
  {
    id: 15,
    username: 'centro_cananea',
    rol: 'centro_salud',
    centro_salud_id: 11,
    centro_salud_nombre: 'Centro de Salud Cananea',
    distrito: 'Distrito 5',
    fecha_registro: '2024-10-01',
    ultima_participacion: '2025-01-03',
    estado: 'activo'
  },
  {
    id: 16,
    username: 'centro_magdalena',
    rol: 'centro_salud',
    centro_salud_id: 12,
    centro_salud_nombre: 'Centro de Salud Magdalena',
    distrito: 'Distrito 3',
    fecha_registro: '2024-10-15',
    ultima_participacion: '2025-01-02',
    estado: 'activo'
  }
];

const UsersManagement: React.FC = () => {
  const navigate = useNavigate();
  const [users] = useState<User[]>(mockUsers);
  const [filteredUsers, setFilteredUsers] = useState<User[]>(mockUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  React.useEffect(() => {
    let filtered = users;

    if (searchTerm) {
      filtered = filtered.filter(user =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.centro_salud_nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.distrito?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterRole) {
      filtered = filtered.filter(user => user.rol === filterRole);
    }

    if (filterStatus) {
      filtered = filtered.filter(user => user.estado === filterStatus);
    }

    setFilteredUsers(filtered);
  }, [users, searchTerm, filterRole, filterStatus]);

  const getRoleBadge = (rol: string) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      analista: 'bg-blue-100 text-blue-800',
      centro_salud: 'bg-green-100 text-green-800'
    };
    
    const labels = {
      admin: 'Administrador',
      analista: 'Analista',
      centro_salud: 'Centro de Salud'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[rol as keyof typeof colors]}`}>
        {labels[rol as keyof typeof labels]}
      </span>
    );
  };

  const getStatusBadge = (estado: string) => {
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
        estado === 'activo' 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800'
      }`}>
        {estado === 'activo' ? 'Activo' : 'Inactivo'}
      </span>
    );
  };

  const toggleUserStatus = (userId: number) => {
    // In a real app, this would make an API call
    console.log(`Toggle status for user ${userId}`);
  };

  const editUser = (userId: number) => {
    // In a real app, this would open an edit modal or navigate to edit page
    console.log(`Edit user ${userId}`);
  };

  const deleteUser = (userId: number) => {
    // In a real app, this would show a confirmation dialog and make an API call
    if (confirm('¿Está seguro de que desea eliminar este usuario?')) {
      console.log(`Delete user ${userId}`);
    }
  };

  const stats = {
    total: users.length,
    activos: users.filter(u => u.estado === 'activo').length,
    admins: users.filter(u => u.rol === 'admin').length,
    analistas: users.filter(u => u.rol === 'analista').length,
    centros: users.filter(u => u.rol === 'centro_salud').length
  };

  return (
    <Layout title="Gestión de Usuarios">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/admin')}
              className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Volver al Panel
            </button>
            <h2 className="text-2xl font-bold text-gray-900">Gestión de Usuarios</h2>
          </div>
          
          <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            <UserPlus className="h-5 w-5 mr-2" />
            Nuevo Usuario
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">Total Usuarios</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-green-600">{stats.activos}</div>
            <div className="text-sm text-gray-600">Activos</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-purple-600">{stats.admins}</div>
            <div className="text-sm text-gray-600">Administradores</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-blue-600">{stats.analistas}</div>
            <div className="text-sm text-gray-600">Analistas</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-green-600">{stats.centros}</div>
            <div className="text-sm text-gray-600">Centros de Salud</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Buscar Usuario
              </label>
              <input
                type="text"
                placeholder="Buscar por usuario, centro o distrito..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filtrar por Rol
              </label>
              <select
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los roles</option>
                <option value="admin">Administrador</option>
                <option value="analista">Analista</option>
                <option value="centro_salud">Centro de Salud</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filtrar por Estado
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los estados</option>
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
              </select>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Centro de Salud
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Distrito
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha Registro
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Última Participación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{user.username}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getRoleBadge(user.rol)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {user.centro_salud_nombre || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{user.distrito || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{user.fecha_registro}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{user.ultima_participacion}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(user.estado)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => editUser(user.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Editar usuario"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => toggleUserStatus(user.id)}
                          className={`${user.estado === 'activo' ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}`}
                          title={user.estado === 'activo' ? 'Desactivar usuario' : 'Activar usuario'}
                        >
                          {user.estado === 'activo' ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                        <button
                          onClick={() => deleteUser(user.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Eliminar usuario"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredUsers.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-500">No se encontraron usuarios que coincidan con los filtros.</div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default UsersManagement;