import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import HealthCentersMap from '../components/HealthCentersMap';
import GeolocationValidator from '../components/GeolocationValidator';
import { ExcelService, HealthCenterData } from '../services/excelService';
import { HealthCentersService, DataSource } from '../services/healthCentersService';
import { useData } from '../contexts/DataContext';
import { AlertCircle, CheckCircle, Download, RefreshCw, Info, Database, Globe, Building2, MapPin, HardDrive } from 'lucide-react';

const HealthCentersPage: React.FC = () => {
  const { healthCenters, addHealthCenters, setHealthCenters, loading, setLoading, loadPermanentHealthCenters, getDatabaseInfo } = useData();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [activeTab, setActiveTab] = useState<'map' | 'validation'>('map');
  const [dataStats, setDataStats] = useState<{
    gobi: number;
    osm: number;
    total: number;
  }>({ gobi: 0, osm: 0, total: healthCenters.length });

  const databaseInfo = getDatabaseInfo();

  useEffect(() => {
    setDataSources(HealthCentersService.getAvailableDataSources());
    setDataStats(prev => ({ ...prev, total: healthCenters.length }));
  }, [healthCenters.length]);

  const handleLoadPermanentDatabase = () => {
    setLoading(true);
    try {
      loadPermanentHealthCenters();
      setSuccess(`Se cargaron ${databaseInfo.permanentStats.total} centros de salud desde la base de datos permanente`);
    } catch (error) {
      setError('Error al cargar la base de datos permanente');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFromGOBI = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Get the correct GOBI URL from data sources
      const gobiDataSource = dataSources.find(source => source.name === 'GOBI - Catálogo Maestro');
      if (!gobiDataSource) {
        throw new Error('No se encontró la fuente de datos GOBI');
      }
      
      const healthCenters = await ExcelService.downloadAndParseExcel(gobiDataSource.url);
      
      // Replace all centers with GOBI data
      setHealthCenters(healthCenters);
      setDataStats(prev => ({ ...prev, gobi: healthCenters.length, total: healthCenters.length }));
      setSuccess(`Se cargaron ${healthCenters.length} centros de salud desde GOBI y se guardaron en el sistema`);
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
      
      // Replace all centers with OSM data
      setHealthCenters(osmCenters);
      setDataStats(prev => ({ ...prev, osm: osmCenters.length, total: osmCenters.length }));
      setSuccess(`Se cargaron ${osmCenters.length} establecimientos desde OpenStreetMap y se guardaron en el sistema`);
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
        const gobiDataSource = dataSources.find(source => source.name === 'GOBI - Catálogo Maestro');
        if (gobiDataSource) {
          results.gobi = await ExcelService.downloadAndParseExcel(gobiDataSource.url);
        }
      } catch (gobiError) {
        console.warn('GOBI data not available:', gobiError);
      }

      // Combine all sources
      const allCenters = [...results.gobi, ...results.osm];
      const uniqueCenters = HealthCentersService.removeDuplicates ? 
        await HealthCentersService.removeDuplicates(allCenters) : allCenters;

      // Replace all centers with combined data
      setHealthCenters(uniqueCenters);
      setDataStats({
        gobi: results.gobi.length,
        osm: results.osm.length,
        total: uniqueCenters.length
      });
      
      setSuccess(`Se combinaron datos de múltiples fuentes: ${results.gobi.length} de GOBI + ${results.osm.length} de OSM = ${uniqueCenters.length} únicos y se guardaron en el sistema`);
    } catch (err) {
      setError('Error al combinar datos de múltiples fuentes.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (uploadedCenters: HealthCenterData[]) => {
    // Add uploaded centers to existing ones
    addHealthCenters(uploadedCenters);
    setDataStats(prev => ({ ...prev, total: healthCenters.length + uploadedCenters.length }));
    setSuccess(`Se cargaron ${uploadedCenters.length} centros de salud desde Excel y se guardaron en el sistema`);
  };

  const handleExportData = () => {
    if (healthCenters.length === 0) {
      setError('No hay datos para exportar');
      return;
    }

    const csvContent = [
      'ID,Nombre,Dirección,Municipio,Estado,Distrito,Tipo,Teléfono,Email,Responsable,Código,CLUES,Latitud,Longitud,Precisión,Fuente',
      ...healthCenters.map(center => [
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
        center.clues || '',
        center.lat,
        center.lng,
        (center as any).geolocation_accuracy || 'unknown',
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

  const handleCentersUpdated = (updatedCenters: HealthCenterData[]) => {
    setHealthCenters(updatedCenters);
    setSuccess('Coordenadas actualizadas correctamente');
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
                onClick={handleLoadPermanentDatabase}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                ) : (
                  <HardDrive className="h-5 w-5 mr-2" />
                )}
                Base Permanente
              </button>
              
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
                className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
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
                disabled={healthCenters.length === 0}
                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="h-5 w-5 mr-2" />
                Exportar CSV
              </button>
            </div>
          </div>

          {/* Database Status */}
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center gap-2 mb-2">
              <HardDrive className="h-5 w-5 text-blue-600" />
              <h4 className="font-medium text-blue-800">Estado de la Base de Datos</h4>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-blue-600">Centros Cargados:</span>
                <span className="font-medium text-blue-900 ml-2">{databaseInfo.currentCount}</span>
              </div>
              <div>
                <span className="text-blue-600">Fuente:</span>
                <span className="font-medium text-blue-900 ml-2 capitalize">{databaseInfo.source}</span>
              </div>
              <div>
                <span className="text-blue-600">Base Permanente:</span>
                <span className="font-medium text-blue-900 ml-2">{databaseInfo.permanentStats.total} disponibles</span>
              </div>
              <div>
                <span className="text-blue-600">Última Actualización:</span>
                <span className="font-medium text-blue-900 ml-2">
                  {databaseInfo.lastUpdated !== 'unknown' ? 
                    new Date(databaseInfo.lastUpdated).toLocaleDateString() : 
                    'No disponible'
                  }
                </span>
              </div>
            </div>
          </div>

          {/* Data Sources Information */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-purple-50 p-3 rounded-md">
              <div className="flex items-center gap-2 mb-1">
                <HardDrive className="h-4 w-4 text-purple-600" />
                <h4 className="font-medium text-sm text-purple-800">Base Permanente</h4>
              </div>
              <p className="text-xs text-purple-600">Datos guardados permanentemente en el código</p>
            </div>
            
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
          {healthCenters.length > 0 && (
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
                  {new Set(healthCenters.map(c => c.municipio)).size}
                </p>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Tipos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Set(healthCenters.map(c => c.tipo)).size}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              <button
                onClick={() => setActiveTab('map')}
                className={`py-4 px-6 text-sm font-medium border-b-2 ${
                  activeTab === 'map'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <Building2 className="h-5 w-5 mr-2" />
                  Mapa de Centros
                </div>
              </button>
              <button
                onClick={() => setActiveTab('validation')}
                className={`py-4 px-6 text-sm font-medium border-b-2 ${
                  activeTab === 'validation'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <MapPin className="h-5 w-5 mr-2" />
                  Validación de Coordenadas
                </div>
              </button>
            </nav>
          </div>

          <div className="p-0">
            {activeTab === 'map' && (
              <HealthCentersMap 
                centers={healthCenters} 
                onFileUpload={handleFileUpload}
                onExportData={handleExportData}
              />
            )}
            
            {activeTab === 'validation' && (
              <div className="p-6">
                <GeolocationValidator 
                  centers={healthCenters}
                  onCentersUpdated={handleCentersUpdated}
                />
              </div>
            )}
          </div>
        </div>

        {/* Information Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Data Sources Information */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-medium text-blue-800 mb-2">
              Fuentes de Datos Disponibles:
            </h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• <strong>Base Permanente:</strong> {databaseInfo.permanentStats.total} centros guardados permanentemente en el código</li>
              <li>• <strong>GOBI:</strong> Base de datos oficial del gobierno mexicano con establecimientos registrados</li>
              <li>• <strong>OpenStreetMap:</strong> Datos colaborativos que incluyen establecimientos públicos y privados</li>
              <li>• <strong>Combinar Fuentes:</strong> Integra ambas fuentes eliminando duplicados por proximidad geográfica</li>
              <li>• <strong>Validación de Coordenadas:</strong> Verifica la precisión geográfica y corrige ubicaciones incorrectas</li>
              <li>• Los datos de OSM pueden incluir consultorios privados, farmacias y clínicas no registradas oficialmente</li>
            </ul>
          </div>

          {/* Instructions */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <h3 className="text-sm font-medium text-yellow-800 mb-2">
              Instrucciones de uso:
            </h3>
            <ul className="text-sm text-yellow-700 space-y-1">
              <li>• <strong>Base Permanente:</strong> Carga los {databaseInfo.permanentStats.total} centros guardados permanentemente (recomendado)</li>
              <li>• <strong>GOBI Oficial:</strong> Carga solo datos del gobierno (más confiables pero pueden estar incompletos)</li>
              <li>• <strong>OpenStreetMap:</strong> Incluye establecimientos privados y datos colaborativos</li>
              <li>• <strong>Combinar Fuentes:</strong> Obtiene la vista más completa eliminando duplicados</li>
              <li>• <strong>Cargar Excel:</strong> Sube archivos Excel locales que se agregan a la base de datos</li>
              <li>• <strong>Validación:</strong> Use la pestaña de validación para verificar y corregir coordenadas</li>
              <li>• <strong>Persistencia:</strong> Todos los datos se guardan automáticamente en el navegador</li>
              <li>• Use los filtros para buscar centros específicos por nombre, municipio o tipo</li>
              <li>• Exporte los datos combinados para análisis adicional</li>
            </ul>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default HealthCentersPage;