import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { useData } from '../contexts/DataContext';
import { ArrowLeft, Eye, Download, Calendar, MapPin, User, FileText } from 'lucide-react';

const ReportsManagement: React.FC = () => {
  const navigate = useNavigate();
  const { reports } = useData();
  const [filteredReports, setFilteredReports] = useState(reports);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDiagnosis, setFilterDiagnosis] = useState('');
  const [filterDistrict, setFilterDistrict] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  React.useEffect(() => {
    setFilteredReports(reports);
  }, [reports]);

  React.useEffect(() => {
    let filtered = reports;

    if (searchTerm) {
      filtered = filtered.filter(report =>
        report.folio.toLowerCase().includes(searchTerm.toLowerCase()) ||
        report.centro_salud.toLowerCase().includes(searchTerm.toLowerCase()) ||
        report.municipio.toLowerCase().includes(searchTerm.toLowerCase()) ||
        report.usuario_subida.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterDiagnosis) {
      filtered = filtered.filter(report => report.diagnostico === filterDiagnosis);
    }

    if (filterDistrict) {
      filtered = filtered.filter(report => report.distrito === filterDistrict);
    }

    if (filterStatus) {
      filtered = filtered.filter(report => report.estado === filterStatus);
    }

    if (dateRange.start) {
      filtered = filtered.filter(report => report.fecha_subida >= dateRange.start);
    }

    if (dateRange.end) {
      filtered = filtered.filter(report => report.fecha_subida <= dateRange.end + ' 23:59:59');
    }

    setFilteredReports(filtered);
  }, [reports, searchTerm, filterDiagnosis, filterDistrict, filterStatus, dateRange]);

  const getStatusBadge = (estado: string) => {
    const colors = {
      'procesado': 'bg-green-100 text-green-800',
      'pendiente': 'bg-yellow-100 text-yellow-800',
      'revision': 'bg-blue-100 text-blue-800'
    };

    const labels = {
      'procesado': 'Procesado',
      'pendiente': 'Pendiente',
      'revision': 'En Revisión'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[estado as keyof typeof colors]}`}>
        {labels[estado as keyof typeof labels]}
      </span>
    );
  };

  const getDiagnosisBadge = (diagnostico: string) => {
    const colors = {
      'Dengue': 'bg-red-100 text-red-800',
      'COVID-19': 'bg-purple-100 text-purple-800',
      'Influenza': 'bg-blue-100 text-blue-800',
      'Zika': 'bg-orange-100 text-orange-800',
      'Chikungunya': 'bg-pink-100 text-pink-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[diagnostico as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {diagnostico}
      </span>
    );
  };

  const viewReport = (reportId: number) => {
    console.log(`View report ${reportId}`);
  };

  const exportReports = () => {
    const csvContent = [
      'Folio,Fecha Subida,Fecha Consulta,Centro de Salud,Municipio,Distrito,Diagnóstico,Edad,Sexo,Usuario,Estado',
      ...filteredReports.map(report => [
        report.folio,
        report.fecha_subida,
        report.fecha_consulta,
        `"${report.centro_salud}"`,
        report.municipio,
        report.distrito,
        report.diagnostico,
        report.edad_paciente,
        report.sexo,
        report.usuario_subida,
        report.estado
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `reportes_suive_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const stats = {
    total: reports.length,
    procesados: reports.filter(r => r.estado === 'procesado').length,
    pendientes: reports.filter(r => r.estado === 'pendiente').length,
    revision: reports.filter(r => r.estado === 'revision').length,
    hoy: reports.filter(r => r.fecha_subida.startsWith(new Date().toISOString().split('T')[0])).length
  };

  const districts = [...new Set(reports.map(r => r.distrito))].sort();
  const diagnoses = [...new Set(reports.map(r => r.diagnostico))].sort();

  return (
    <Layout title="Gestión de Reportes">
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
            <h2 className="text-2xl font-bold text-gray-900">Gestión de Reportes SUIVE</h2>
          </div>
          
          <button 
            onClick={exportReports}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            <Download className="h-5 w-5 mr-2" />
            Exportar Reportes
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">Total Reportes</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-green-600">{stats.procesados}</div>
            <div className="text-sm text-gray-600">Procesados</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-yellow-600">{stats.pendientes}</div>
            <div className="text-sm text-gray-600">Pendientes</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-blue-600">{stats.revision}</div>
            <div className="text-sm text-gray-600">En Revisión</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-purple-600">{stats.hoy}</div>
            <div className="text-sm text-gray-600">Hoy</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Buscar Reporte
              </label>
              <input
                type="text"
                placeholder="Buscar por folio, centro, municipio o usuario..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Diagnóstico
              </label>
              <select
                value={filterDiagnosis}
                onChange={(e) => setFilterDiagnosis(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los diagnósticos</option>
                {diagnoses.map(diagnosis => (
                  <option key={diagnosis} value={diagnosis}>{diagnosis}</option>
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
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                <option value="procesado">Procesado</option>
                <option value="pendiente">Pendiente</option>
                <option value="revision">En Revisión</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fecha Inicio
              </label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fecha Fin
              </label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Reports Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Folio
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha Subida
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Centro de Salud
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ubicación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Diagnóstico
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Paciente
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario
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
                {filteredReports.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 flex items-center">
                        <FileText className="h-4 w-4 mr-2 text-gray-400" />
                        {report.folio}
                      </div>
                      <div className="text-sm text-gray-500">{report.fecha_consulta}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <Calendar className="h-4 w-4 mr-1 text-gray-400" />
                        {new Date(report.fecha_subida).toLocaleDateString()}
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(report.fecha_subida).toLocaleTimeString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{report.centro_salud}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <MapPin className="h-4 w-4 mr-1 text-gray-400" />
                        {report.municipio}
                      </div>
                      <div className="text-sm text-gray-500">{report.distrito}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getDiagnosisBadge(report.diagnostico)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {report.sexo === 'M' ? 'Masculino' : 'Femenino'}, {report.edad_paciente} años
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <User className="h-4 w-4 mr-1 text-gray-400" />
                        {report.usuario_subida}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(report.estado)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => viewReport(report.id)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Ver reporte completo"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredReports.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-500">No se encontraron reportes que coincidan con los filtros.</div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default ReportsManagement;