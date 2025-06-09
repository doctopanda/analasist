import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import HealthCentersMap from '../components/HealthCentersMap';
import { ExcelService, HealthCenterData } from '../services/excelService';
import { HealthCentersService, DataSource } from '../services/healthCentersService';
import { AlertCircle, CheckCircle, Download, RefreshCw, Info, Database, Globe, Building2 } from 'lucide-react';

const HealthCentersPage: React.FC = () => {
  const [centers, setCenters] = useState<HealthCenterData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>(['GOBI']);
  const [dataStats, setDataStats] = useState<{
    gobi: number;
    osm: number;
    total: number;
  }>({ gobi: 0, osm: 0, total: 0 });

  useEffect(() => {
    setDataSources(HealthCentersService.getAvailableDataSources());
  }, []);

  const handleDownloadFromGOBI = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const excelUrl = '/gobi/catalogos/catalogosmaestros/ESTABLECIMIENTO_SALUD_202504.xlsx?V=2025.05.29';
      const healthCenters = await ExcelService.downloadAndParseExcel(excelUrl);
      
      setCenters(healthCenters);
      setDataStats(prev => ({ ...prev, gobi: healthCenters.length, total: healthCenters.length }));
      setSuccess(`Se cargaron ${healthCenters.length} centros de salud desde GOBI`);
    } catch (err) {
      setError('Error al descargar datos de GOBI. Verifique la conexión a internet.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFromOSM = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const osmCenters = await HealthCentersService.fetchFromOpenStreetMap();
      
      setCenters(osmCenters);
      setDataStats(prev => ({ ...prev, osm: osmCenters.length, total: osmCenters.length }));
      setSuccess(`Se cargaron ${osmCenters.length} establecimientos desde OpenStreetMap`);
    } catch (err) {
      setError('Error al obtener datos de OpenStreetMap. El servicio puede estar temporalmente no disponible.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFromMultipleSources = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const results = await HealthCentersService.fetchFromMultipleSources();
      
      // First try to get GOBI data
      try {
        const excelUrl = '/gobi/catalogos/catalogosmaestros/ESTABLECIMIENTO_SALUD_202504.xlsx?V=2025.05.29';
        results.gobi = await ExcelService.downloadAndParseExcel(excelUrl);
      } catch (gobiError) {
        console.warn('GOBI data not available:', gobiError);
      }

      // Combine all sources
      const allCenters = [...results.gobi, ...results.osm];
      const uniqueCenters = HealthCentersService.removeDuplicates ? 
        await HealthCentersService.removeDuplicates(allCenters) : allCenters;

      setCenters(uniqueCenters);
      setDataStats({
        gobi: results.gobi.length,
        osm: results.osm.length,
        total: uniqueCenters.length
      });
      
      setSuccess(`Se combinaron datos de múltiples fuentes: ${results.gobi.length} de GOBI + ${results.osm.length} de OSM = ${uniqueCenters.length} únicos`);
    } catch (err) {
      setError('Error al combinar datos de múltiples fuentes.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (uploadedCenters: HealthCenterData[]) => {
    setCenters(uploadedCenters);
    setDataStats(prev => ({ ...prev, total: uploadedCenters.length }));
    setSuccess(`Se cargaron ${uploadedCenters.length} centros de salud`);
  };

  const handleExportData = () => {
    if (centers.length === 0) {
      setError('No hay datos para exportar');
      return;
    }

    const csvContent = [
      'ID,Nombre,Dirección,Municipio,Estado,Distrito,Tipo,Teléfono,Email,Responsable,Código,Latitud,Longitud,Fuente',
      ...centers.map(center => [
        center.id,
        `"${center.nombre}"`,
        `"${center.direccion}"`,
        center.municipio,
        center.estado,
        center.distrito,
        center.tipo,
        center.telefono || '',
        center.email || '',
        `"${center.responsable || ''}"`,
        center.codigo_establecimiento,
        center.lat,
        center.lng,
        center.id.startsWith('osm_') ? 'OpenStreetMap' : 'GOBI'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `centros_salud_sonora_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setSuccess('Datos exportados correctamente');
  };

  return (
    <Layout title="Centros de Salud - Mapa de Sonora">
      <div className="space-y-6">
        {/* Control Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">
                Gestión de Centros de Salud
              </h2>
              <p className="text-gray-600 text-sm mt-1">
                Datos georeferenciados de establecimientos públicos y privados en Sonora
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleDownloadFromGOBI}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                ) : (
                  <Database className="h-5 w-5 mr-2" />
                )}
                GOBI Oficial
              </button>
              
              <button
                onClick={handleDownloadFromOSM}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                ) : (
                  <Globe className="h-5 w-5 mr-2" />
                )}
                OpenStreetMap
              </button>

              <button
                onClick={handleDownloadFromMultipleSources}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                ) : (
                  <Building2 className="h-5 w-5 mr-2" />
                )}
                Combinar Fuentes
              </button>
              
              <button
                onClick={handleExportData}
                disabled={centers.length === 0}
                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="h-5 w-5 mr-2" />
                Exportar CSV
              </button>
            </div>
          </div>

          {/* Data Sources Information */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            {dataSources.filter(source => source.status === 'active').map((source, index) => (
              <div key={index} className="bg-gray-50 p-3 rounded-md">
                <div className="flex items-center gap-2 mb-1">
                  {source.type === 'government' && <Database className="h-4 w-4 text-blue-600" />}
                  {source.type === 'osm' && <Globe className="h-4 w-4 text-green-600" />}
                  <h4 className="font-medium text-sm text-gray-800">{source.name}</h4>
                </div>
                <p className="text-xs text-gray-600">{source.description}</p>
              </div>
            ))}
          </div>

          {/* Status Messages */}
          {loading && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center">
                <RefreshCw className="h-5 w-5 text-blue-600 animate-spin mr-3" />
                <div>
                  <p className="text-blue-800 font-medium">Procesando datos...</p>
                  <p className="text-blue-600 text-sm">
                    Obteniendo establecimientos de salud georeferenciados
                  </p>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-600 mr-3" />
                <div>
                  <p className="text-red-800 font-medium">Error</p>
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}

          {success && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                <div>
                  <p className="text-green-800 font-medium">Éxito</p>
                  <p className="text-green-600 text-sm">{success}</p>
                </div>
              </div>
            </div>
          )}

          {/* Statistics */}
          {centers.length > 0 && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Total Centros</p>
                <p className="text-2xl font-bold text-gray-900">{dataStats.total}</p>
              </div>
              {dataStats.gobi > 0 && (
                <div className="bg-blue-50 p-3 rounded-md">
                  <p className="text-sm text-blue-600">GOBI</p>
                  <p className="text-2xl font-bold text-blue-900">{dataStats.gobi}</p>
                </div>
              )}
              {dataStats.osm > 0 && (
                <div className="bg-green-50 p-3 rounded-md">
                  <p className="text-sm text-green-600">OpenStreetMap</p>
                  <p className="text-2xl font-bold text-green-900">{dataStats.osm}</p>
                </div>
              )}
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Municipios</p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Set(centers.map(c => c.municipio)).size}
                </p>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Tipos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Set(centers.map(c => c.tipo)).size}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Map Component */}
        <HealthCentersMap 
          centers={centers} 
          onFileUpload={handleFileUpload}
          onExportData={handleExportData}
        />

        {/* Data Sources Information */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h3 className="text-sm font-medium text-blue-800 mb-2">
            Fuentes de Datos Disponibles:
          </h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• <strong>GOBI:</strong> Base de datos oficial del gobierno mexicano con establecimientos registrados</li>
            <li>• <strong>OpenStreetMap:</strong> Datos colaborativos que incluyen establecimientos públicos y privados</li>
            <li>• <strong>Combinar Fuentes:</strong> Integra ambas fuentes eliminando duplicados por proximidad geográfica</li>
            <li>• Los datos de OSM pueden incluir consultorios privados, farmacias y clínicas no registradas oficialmente</li>
          </ul>
        </div>

        {/* Instructions */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <h3 className="text-sm font-medium text-yellow-800 mb-2">
            Instrucciones de uso:
          </h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• <strong>GOBI Oficial:</strong> Carga solo datos del gobierno (más confiables pero pueden estar incompletos)</li>
            <li>• <strong>OpenStreetMap:</strong> Incluye establecimientos privados y datos colaborativos</li>
            <li>• <strong>Combinar Fuentes:</strong> Obtiene la vista más completa eliminando duplicados</li>
            <li>• Use los filtros para buscar centros específicos por nombre, municipio o tipo</li>
            <li>• Exporte los datos combinados para análisis adicional</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
};

export default HealthCentersPage;