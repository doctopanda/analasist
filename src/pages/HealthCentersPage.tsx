import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import HealthCentersMap from '../components/HealthCentersMap';
import { ExcelService, HealthCenterData } from '../services/excelService';
import { AlertCircle, CheckCircle, Download, RefreshCw, Info } from 'lucide-react';

const HealthCentersPage: React.FC = () => {
  const [centers, setCenters] = useState<HealthCenterData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleDownloadExcel = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Updated to use HTTPS URL to avoid mixed content issues
      const excelUrl = 'https://gobi.salud.gob.mx/gobi/catalogos/catalogosmaestros/ESTABLECIMIENTO_SALUD_202504.xlsx?V=2025.05.29';
      const healthCenters = await ExcelService.downloadAndParseExcel(excelUrl);
      
      setCenters(healthCenters);
      setSuccess(`Se cargaron ${healthCenters.length} centros de salud de Sonora`);
    } catch (err) {
      setError('Error al descargar o procesar el archivo Excel. Verifique la conexión a internet o que el servidor esté disponible.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (uploadedCenters: HealthCenterData[]) => {
    setCenters(uploadedCenters);
    setSuccess(`Se cargaron ${uploadedCenters.length} centros de salud`);
  };

  const handleExportData = () => {
    if (centers.length === 0) {
      setError('No hay datos para exportar');
      return;
    }

    const csvContent = [
      // CSV headers
      'ID,Nombre,Dirección,Municipio,Estado,Distrito,Tipo,Teléfono,Email,Responsable,Código,Latitud,Longitud',
      // CSV data
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
        center.lng
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
                Visualización georreferenciada de establecimientos de salud en Sonora
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleDownloadExcel}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                ) : (
                  <Download className="h-5 w-5 mr-2" />
                )}
                Cargar desde GOBI
              </button>
              
              <button
                onClick={handleExportData}
                disabled={centers.length === 0}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="h-5 w-5 mr-2" />
                Exportar CSV
              </button>
            </div>
          </div>

          {/* Status Messages */}
          {loading && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center">
                <RefreshCw className="h-5 w-5 text-blue-600 animate-spin mr-3" />
                <div>
                  <p className="text-blue-800 font-medium">Procesando datos...</p>
                  <p className="text-blue-600 text-sm">
                    Descargando y procesando el archivo Excel desde GOBI
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
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Total Centros</p>
                <p className="text-2xl font-bold text-gray-900">{centers.length}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Municipios</p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Set(centers.map(c => c.municipio)).size}
                </p>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Hospitales</p>
                <p className="text-2xl font-bold text-gray-900">
                  {centers.filter(c => c.tipo.toLowerCase().includes('hospital')).length}
                </p>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">Centros de Salud</p>
                <p className="text-2xl font-bold text-gray-900">
                  {centers.filter(c => c.tipo.toLowerCase().includes('centro')).length}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Map Component */}
        <HealthCentersMap onFileUpload={handleFileUpload} />

        {/* Instructions */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <h3 className="text-sm font-medium text-yellow-800 mb-2">
            Instrucciones de uso:
          </h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• Haga clic en "Cargar desde GOBI" para descargar automáticamente los datos oficiales</li>
            <li>• Use los filtros para buscar centros específicos por nombre, municipio o tipo</li>
            <li>• Haga clic en los marcadores del mapa para ver información detallada</li>
            <li>• Exporte los datos en formato CSV para análisis adicional</li>
            <li>• Los colores de los marcadores indican el tipo de establecimiento</li>
          </ul>
        </div>

        {/* Map Technology Notice */}
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex items-center">
            <Info className="h-5 w-5 text-green-600 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-green-800 mb-1">
                Mapa gratuito con OpenStreetMap
              </h3>
              <p className="text-sm text-green-700">
                Este mapa utiliza OpenStreetMap y Leaflet, una alternativa gratuita y de código abierto que no requiere claves de API ni pagos.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default HealthCentersPage;