import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { ArrowLeft, AlertTriangle, MapPin, Calendar, TrendingUp, Eye, CheckCircle, X } from 'lucide-react';

interface Alert {
  id: number;
  tipo: 'brote' | 'incremento' | 'cluster' | 'anomalia';
  titulo: string;
  descripcion: string;
  municipio: string;
  distrito: string;
  diagnostico: string;
  casos_detectados: number;
  fecha_deteccion: string;
  coordenadas: { lat: number; lng: number };
  severidad: 'baja' | 'media' | 'alta' | 'critica';
  estado: 'activa' | 'investigando' | 'resuelta' | 'descartada';
  acciones_tomadas?: string;
}

const mockAlerts: Alert[] = [
  {
    id: 1,
    tipo: 'brote',
    titulo: 'Posible brote de Dengue en Hermosillo',
    descripcion: 'Se han detectado 8 casos de dengue en un radio de 2km en la colonia Villa de Seris en los últimos 7 días.',
    municipio: 'Hermosillo',
    distrito: 'Distrito 1',
    diagnostico: 'Dengue',
    casos_detectados: 8,
    fecha_deteccion: '2025-01-15',
    coordenadas: { lat: 29.0892, lng: -110.9618 },
    severidad: 'alta',
    estado: 'activa',
    acciones_tomadas: 'Equipo de epidemiología enviado para investigación de campo'
  },
  {
    id: 2,
    tipo: 'incremento',
    titulo: 'Incremento de casos de COVID-19 en Cajeme',
    descripcion: 'Aumento del 40% en casos de COVID-19 comparado con la semana anterior.',
    municipio: 'Cajeme',
    distrito: 'Distrito 2',
    diagnostico: 'COVID-19',
    casos_detectados: 12,
    fecha_deteccion: '2025-01-14',
    coordenadas: { lat: 27.3833, lng: -109.9167 },
    severidad: 'media',
    estado: 'investigando',
    acciones_tomadas: 'Refuerzo de medidas preventivas en centros de salud'
  },
  {
    id: 3,
    tipo: 'cluster',
    titulo: 'Cluster de Influenza en Puerto Peñasco',
    descripcion: 'Agrupación de 6 casos de influenza en trabajadores del sector turístico.',
    municipio: 'Puerto Peñasco',
    distrito: 'Distrito 4',
    diagnostico: 'Influenza',
    casos_detectados: 6,
    fecha_deteccion: '2025-01-13',
    coordenadas: { lat: 31.3167, lng: -113.5333 },
    severidad: 'media',
    estado: 'activa',
    acciones_tomadas: 'Campaña de vacunación dirigida al sector turístico'
  },
  {
    id: 4,
    tipo: 'anomalia',
    titulo: 'Patrón inusual de Zika en Navojoa',
    descripcion: 'Casos de Zika fuera de la temporada típica de transmisión.',
    municipio: 'Navojoa',
    distrito: 'Distrito 2',
    diagnostico: 'Zika',
    casos_detectados: 3,
    fecha_deteccion: '2025-01-12',
    coordenadas: { lat: 27.0667, lng: -109.4333 },
    severidad: 'baja',
    estado: 'investigando'
  },
  {
    id: 5,
    tipo: 'brote',
    titulo: 'Brote de Chikungunya en Nogales',
    descripcion: 'Confirmación de brote con 5 casos relacionados epidemiológicamente.',
    municipio: 'Nogales',
    distrito: 'Distrito 3',
    diagnostico: 'Chikungunya',
    casos_detectados: 5,
    fecha_deteccion: '2025-01-10',
    coordenadas: { lat: 31.3081, lng: -110.9342 },
    severidad: 'alta',
    estado: 'resuelta',
    acciones_tomadas: 'Control vectorial intensivo completado, casos aislados y tratados'
  }
];

const AlertsManagement: React.FC = () => {
  const navigate = useNavigate();
  const [alerts] = useState<Alert[]>(mockAlerts);
  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>(mockAlerts);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  React.useEffect(() => {
    let filtered = alerts;

    if (searchTerm) {
      filtered = filtered.filter(alert =>
        alert.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.municipio.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.diagnostico.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterType) {
      filtered = filtered.filter(alert => alert.tipo === filterType);
    }

    if (filterSeverity) {
      filtered = filtered.filter(alert => alert.severidad === filterSeverity);
    }

    if (filterStatus) {
      filtered = filtered.filter(alert => alert.estado === filterStatus);
    }

    setFilteredAlerts(filtered);
  }, [alerts, searchTerm, filterType, filterSeverity, filterStatus]);

  const getTypeBadge = (tipo: string) => {
    const colors = {
      'brote': 'bg-red-100 text-red-800',
      'incremento': 'bg-orange-100 text-orange-800',
      'cluster': 'bg-yellow-100 text-yellow-800',
      'anomalia': 'bg-purple-100 text-purple-800'
    };

    const labels = {
      'brote': 'Brote',
      'incremento': 'Incremento',
      'cluster': 'Cluster',
      'anomalia': 'Anomalía'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[tipo as keyof typeof colors]}`}>
        {labels[tipo as keyof typeof labels]}
      </span>
    );
  };

  const getSeverityBadge = (severidad: string) => {
    const colors = {
      'baja': 'bg-green-100 text-green-800',
      'media': 'bg-yellow-100 text-yellow-800',
      'alta': 'bg-orange-100 text-orange-800',
      'critica': 'bg-red-100 text-red-800'
    };

    const labels = {
      'baja': 'Baja',
      'media': 'Media',
      'alta': 'Alta',
      'critica': 'Crítica'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[severidad as keyof typeof colors]}`}>
        {labels[severidad as keyof typeof labels]}
      </span>
    );
  };

  const getStatusBadge = (estado: string) => {
    const colors = {
      'activa': 'bg-red-100 text-red-800',
      'investigando': 'bg-blue-100 text-blue-800',
      'resuelta': 'bg-green-100 text-green-800',
      'descartada': 'bg-gray-100 text-gray-800'
    };

    const labels = {
      'activa': 'Activa',
      'investigando': 'Investigando',
      'resuelta': 'Resuelta',
      'descartada': 'Descartada'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[estado as keyof typeof colors]}`}>
        {labels[estado as keyof typeof labels]}
      </span>
    );
  };

  const viewAlert = (alert: Alert) => {
    setSelectedAlert(alert);
  };

  const resolveAlert = (alertId: number) => {
    console.log(`Resolve alert ${alertId}`);
  };

  const dismissAlert = (alertId: number) => {
    console.log(`Dismiss alert ${alertId}`);
  };

  const stats = {
    total: alerts.length,
    activas: alerts.filter(a => a.estado === 'activa').length,
    criticas: alerts.filter(a => a.severidad === 'critica').length,
    investigando: alerts.filter(a => a.estado === 'investigando').length,
    resueltas: alerts.filter(a => a.estado === 'resuelta').length
  };

  return (
    <Layout title="Gestión de Alertas Epidemiológicas">
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
            <h2 className="text-2xl font-bold text-gray-900">Alertas Epidemiológicas</h2>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">Total Alertas</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-red-600">{stats.activas}</div>
            <div className="text-sm text-gray-600">Activas</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-red-800">{stats.criticas}</div>
            <div className="text-sm text-gray-600">Críticas</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-blue-600">{stats.investigando}</div>
            <div className="text-sm text-gray-600">Investigando</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-green-600">{stats.resueltas}</div>
            <div className="text-sm text-gray-600">Resueltas</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Buscar Alerta
              </label>
              <input
                type="text"
                placeholder="Buscar por título, municipio o diagnóstico..."
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
                <option value="brote">Brote</option>
                <option value="incremento">Incremento</option>
                <option value="cluster">Cluster</option>
                <option value="anomalia">Anomalía</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Severidad
              </label>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todas las severidades</option>
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
                <option value="critica">Crítica</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estado
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los estados</option>
                <option value="activa">Activa</option>
                <option value="investigando">Investigando</option>
                <option value="resuelta">Resuelta</option>
                <option value="descartada">Descartada</option>
              </select>
            </div>
          </div>
        </div>

        {/* Alerts Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Alerta
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ubicación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Diagnóstico
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Casos
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severidad
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
                {filteredAlerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 flex items-center">
                          <AlertTriangle className="h-4 w-4 mr-2 text-orange-500" />
                          {alert.titulo}
                        </div>
                        <div className="flex items-center mt-1">
                          {getTypeBadge(alert.tipo)}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <MapPin className="h-4 w-4 mr-1 text-gray-400" />
                        {alert.municipio}
                      </div>
                      <div className="text-sm text-gray-500">{alert.distrito}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{alert.diagnostico}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <TrendingUp className="h-4 w-4 mr-1 text-red-500" />
                        {alert.casos_detectados}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <Calendar className="h-4 w-4 mr-1 text-gray-400" />
                        {alert.fecha_deteccion}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getSeverityBadge(alert.severidad)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(alert.estado)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => viewAlert(alert)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Ver detalles"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        {alert.estado === 'activa' && (
                          <>
                            <button
                              onClick={() => resolveAlert(alert.id)}
                              className="text-green-600 hover:text-green-900"
                              title="Marcar como resuelta"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => dismissAlert(alert.id)}
                              className="text-red-600 hover:text-red-900"
                              title="Descartar alerta"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredAlerts.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-500">No se encontraron alertas que coincidan con los filtros.</div>
            </div>
          )}
        </div>

        {/* Alert Detail Modal */}
        {selectedAlert && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-medium text-gray-900">{selectedAlert.titulo}</h3>
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tipo</label>
                    <div className="mt-1">{getTypeBadge(selectedAlert.tipo)}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Severidad</label>
                    <div className="mt-1">{getSeverityBadge(selectedAlert.severidad)}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Estado</label>
                    <div className="mt-1">{getStatusBadge(selectedAlert.estado)}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Casos Detectados</label>
                    <div className="mt-1 text-sm text-gray-900">{selectedAlert.casos_detectados}</div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Descripción</label>
                  <div className="mt-1 text-sm text-gray-900">{selectedAlert.descripcion}</div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Municipio</label>
                    <div className="mt-1 text-sm text-gray-900">{selectedAlert.municipio}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Distrito</label>
                    <div className="mt-1 text-sm text-gray-900">{selectedAlert.distrito}</div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Diagnóstico</label>
                  <div className="mt-1 text-sm text-gray-900">{selectedAlert.diagnostico}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Fecha de Detección</label>
                  <div className="mt-1 text-sm text-gray-900">{selectedAlert.fecha_deteccion}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Coordenadas</label>
                  <div className="mt-1 text-sm text-gray-900">
                    Lat: {selectedAlert.coordenadas.lat}, Lng: {selectedAlert.coordenadas.lng}
                  </div>
                </div>
                
                {selectedAlert.acciones_tomadas && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Acciones Tomadas</label>
                    <div className="mt-1 text-sm text-gray-900">{selectedAlert.acciones_tomadas}</div>
                  </div>
                )}
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cerrar
                </button>
                {selectedAlert.estado === 'activa' && (
                  <button
                    onClick={() => {
                      resolveAlert(selectedAlert.id);
                      setSelectedAlert(null);
                    }}
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                  >
                    Marcar como Resuelta
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default AlertsManagement;