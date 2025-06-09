import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { useHealthCenters } from '../contexts/HealthCentersContext';
import { ArrowLeft, Edit, Trash2, Building2, MapPin, Clock, User, Shield, Plus } from 'lucide-react';

const HealthCentersManagement: React.FC = () => {
  const navigate = useNavigate();
  const { centers, updateCenter, deleteCenter } = useHealthCenters();
  const [filteredCenters, setFilteredCenters] = useState(centers);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterDistrict, setFilterDistrict] = useState('');
  const [filterDerechohabiencia, setFilterDerechohabiencia] = useState('');

  React.useEffect(() => {
    setFilteredCenters(centers);
  }, [centers]);

  React.useEffect(() => {
    let filtered = centers;

    if (searchTerm) {
      filtered = filtered.filter(center =>
        center.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.direccion.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.responsable?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.clues?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterType) {
      filtered = filtered.filter(center => center.tipo === filterType);
    }

    if (filterDistrict) {
      filtered = filtered.filter(center => center.distrito === filterDistrict);
    }

    setFilteredCenters(filtered);
  }, [centers, searchTerm, filterType, filterDistrict, filterDerechohabiencia]);

  const getTypeBadge = (tipo: string) => {
    const colors = {
      'Hospital': 'bg-red-100 text-red-800',
      'Centro de Salud': 'bg-blue-100 text-blue-800',
      'Clínica': 'bg-green-100 text-green-800',
      'Farmacia': 'bg-purple-100 text-purple-800',
      'Consultorio Médico': 'bg-yellow-100 text-yellow-800',
      'Consultorio Dental': 'bg-pink-100 text-pink-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[tipo as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {tipo}
      </span>
    );
  };

  const editCenter = (centerId: string) => {
    console.log(`Edit center ${centerId}`);
    // In a real app, this would open an edit modal
  };

  const handleDeleteCenter = (centerId: string) => {
    if (confirm('¿Está seguro de que desea eliminar este centro de salud?')) {
      deleteCenter(centerId);
    }
  };

  const stats = {
    total: centers.length,
    hospitales: centers.filter(c => c.tipo === 'Hospital').length,
    centros: centers.filter(c => c.tipo === 'Centro de Salud').length,
    clinicas: centers.filter(c => c.tipo === 'Clínica').length,
    otros: centers.filter(c => !['Hospital', 'Centro de Salud', 'Clínica'].includes(c.tipo)).length
  };

  const districts = [...new Set(centers.map(c => c.distrito))].sort();
  const types = [...new Set(centers.map(c => c.tipo))].sort();

  return (
    <Layout title="Gestión de Centros de Salud">
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
            <h2 className="text-2xl font-bold text-gray-900">Gestión de Centros de Salud</h2>
          </div>
          
          <button 
            onClick={() => navigate('/health-centers-map')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="h-5 w-5 mr-2" />
            Cargar Datos
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">Total Centros</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-red-600">{stats.hospitales}</div>
            <div className="text-sm text-gray-600">Hospitales</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-blue-600">{stats.centros}</div>
            <div className="text-sm text-gray-600">Centros de Salud</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-green-600">{stats.clinicas}</div>
            <div className="text-sm text-gray-600">Clínicas</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-purple-600">{stats.otros}</div>
            <div className="text-sm text-gray-600">Otros</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Buscar Centro
              </label>
              <input
                type="text"
                placeholder="Buscar por nombre, dirección, responsable o CLUES..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los tipos</option>
                {types.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Distrito
              </label>
              <select
                value={filterDistrict}
                onChange={(e) => setFilterDistrict(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los distritos</option>
                {districts.map(district => (
                  <option key={district} value={district}>{district}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Centers Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Centro de Salud
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ubicación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Responsable
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contacto
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Coordenadas
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCenters.map((center) => (
                  <tr key={center.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{center.nombre}</div>
                        <div className="text-sm text-gray-500">CLUES: {center.clues || 'N/A'}</div>
                        <div className="text-sm text-gray-500">Código: {center.codigo_establecimiento}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm text-gray-900 flex items-center">
                          <MapPin className="h-4 w-4 mr-1 text-gray-400" />
                          {center.municipio}
                        </div>
                        <div className="text-sm text-gray-500">{center.distrito}</div>
                        <div className="text-sm text-gray-500">{center.direccion}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getTypeBadge(center.tipo)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <User className="h-4 w-4 mr-1 text-gray-400" />
                        {center.responsable || 'No especificado'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {center.telefono && (
                        <div className="text-sm text-gray-900">{center.telefono}</div>
                      )}
                      {center.email && (
                        <div className="text-sm text-gray-500">{center.email}</div>
                      )}
                      {!center.telefono && !center.email && (
                        <div className="text-sm text-gray-500">No disponible</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {center.lat.toFixed(4)}, {center.lng.toFixed(4)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => editCenter(center.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Editar centro"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteCenter(center.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Eliminar centro"
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
          
          {filteredCenters.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-500">
                {centers.length === 0 
                  ? 'No hay centros de salud cargados. Vaya a "Cargar Datos" para importar información.'
                  : 'No se encontraron centros de salud que coincidan con los filtros.'
                }
              </div>
            </div>
          )}
        </div>

        {/* Information Panel */}
        {centers.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-medium text-blue-800 mb-2">
              Información del Sistema:
            </h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Los datos se cargan desde múltiples fuentes (GOBI, OpenStreetMap, Excel)</li>
              <li>• La información se guarda automáticamente en el navegador</li>
              <li>• Use "Cargar Datos" para actualizar o agregar nuevos centros</li>
              <li>• Los centros se pueden editar y eliminar individualmente</li>
              <li>• Las coordenadas se usan para mostrar los centros en el mapa</li>
            </ul>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default HealthCentersManagement;