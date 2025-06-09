import React, { useState, useEffect } from 'react';
import { GeocodingService } from '../services/geocodingService';
import { HealthCenterData } from '../services/excelService';
import { MapPin, CheckCircle, AlertTriangle, XCircle, RefreshCw, Eye, Download, Map, BarChart3 } from 'lucide-react';

interface GeolocationValidatorProps {
  centers: HealthCenterData[];
  onCentersUpdated: (updatedCenters: HealthCenterData[]) => void;
}

const GeolocationValidator: React.FC<GeolocationValidatorProps> = ({ centers, onCentersUpdated }) => {
  const [validationResults, setValidationResults] = useState<any[]>([]);
  const [qualityReport, setQualityReport] = useState<any>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [selectedCenter, setSelectedCenter] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'list' | 'report' | 'map'>('list');

  useEffect(() => {
    if (centers.length > 0) {
      validateCenters();
    }
  }, [centers]);

  const validateCenters = async () => {
    setIsValidating(true);
    try {
      const results = await GeocodingService.validateHealthCentersWithAddresses(centers);
      setValidationResults(results.validated);
      
      const report = GeocodingService.generateDetailedQualityReport(results.validated);
      setQualityReport(report);
    } catch (error) {
      console.error('Error validating centers:', error);
    } finally {
      setIsValidating(false);
    }
  };

  const improveAllCoordinates = async () => {
    setIsValidating(true);
    try {
      const improved = [];
      
      for (const center of centers) {
        const result = await GeocodingService.improveCoordinatesWithAddress(
          center.lat,
          center.lng,
          center.municipio,
          center.direccion
        );
        
        improved.push({
          ...center,
          lat: result.lat,
          lng: result.lng,
          geolocation_accuracy: result.accuracy,
          geolocation_source: result.source,
          geolocation_confidence: result.confidence,
          original_lat: center.lat,
          original_lng: center.lng
        });
      }
      
      onCentersUpdated(improved);
      setValidationResults(improved);
      
      const report = GeocodingService.generateDetailedQualityReport(improved);
      setQualityReport(report);
    } catch (error) {
      console.error('Error improving coordinates:', error);
    } finally {
      setIsValidating(false);
    }
  };

  const getAccuracyBadge = (accuracy: string, confidence?: number) => {
    const colors = {
      'exact': 'bg-green-100 text-green-800',
      'approximate': 'bg-yellow-100 text-yellow-800',
      'estimated': 'bg-red-100 text-red-800',
      'unknown': 'bg-gray-100 text-gray-800'
    };

    const labels = {
      'exact': 'Exacta',
      'approximate': 'Aproximada',
      'estimated': 'Estimada',
      'unknown': 'Desconocida'
    };

    return (
      <div className="flex flex-col">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[accuracy as keyof typeof colors] || colors.unknown}`}>
          {labels[accuracy as keyof typeof labels] || 'Desconocida'}
        </span>
        {confidence && (
          <span className="text-xs text-gray-500 mt-1">
            {confidence}% confianza
          </span>
        )}
      </div>
    );
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'coordinates':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'geocoded':
        return <MapPin className="h-4 w-4 text-blue-600" />;
      case 'estimated':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      default:
        return <XCircle className="h-4 w-4 text-red-600" />;
    }
  };

  const exportValidationReport = () => {
    if (!qualityReport) return;

    const reportData = [
      'REPORTE DETALLADO DE CALIDAD DE GEOLOCALIZACIÓN',
      `Generado: ${new Date().toLocaleString()}`,
      '',
      'RESUMEN GENERAL:',
      `Total de centros: ${qualityReport.overall.total}`,
      `Dentro de Sonora: ${qualityReport.overall.withinSonora}`,
      `Coordenadas precisas: ${qualityReport.overall.accurateCoordinates}`,
      `Coordenadas estimadas: ${qualityReport.overall.estimatedCoordinates}`,
      `Con direcciones: ${qualityReport.overall.withAddresses}`,
      `Precisión promedio: ${qualityReport.overall.averageAccuracy}%`,
      `Puntuación de calidad: ${qualityReport.overall.qualityScore}%`,
      '',
      'ANÁLISIS DE DIRECCIONES:',
      `Direcciones completas: ${qualityReport.addressAnalysis.completeAddresses}`,
      `Direcciones parciales: ${qualityReport.addressAnalysis.partialAddresses}`,
      `Sin dirección: ${qualityReport.addressAnalysis.noAddresses}`,
      `Calidad de direcciones: ${qualityReport.addressAnalysis.addressQualityScore}%`,
      '',
      'CALIDAD POR MUNICIPIO:',
      ...Object.entries(qualityReport.byMunicipality).map(([municipality, data]: [string, any]) =>
        `${municipality}: ${data.accurate}/${data.total} precisas (${data.qualityScore}%) - Distancia promedio: ${data.averageDistance}km`
      ),
      '',
      'RECOMENDACIONES:',
      ...qualityReport.recommendations,
      '',
      'DETALLE POR CENTRO:',
      'Nombre,Municipio,Dirección,Latitud,Longitud,Lat_Original,Lng_Original,Precisión,Fuente,Confianza,Dentro_Sonora',
      ...validationResults.map(center => {
        const withinSonora = GeocodingService.isWithinSonora(center.lat, center.lng);
        return [
          `"${center.nombre}"`,
          `"${center.municipio}"`,
          `"${center.direccion || 'Sin dirección'}"`,
          center.lat,
          center.lng,
          center.original_lat || center.lat,
          center.original_lng || center.lng,
          `"${center.geolocation_accuracy || 'unknown'}"`,
          `"${center.geolocation_source || 'unknown'}"`,
          center.geolocation_confidence || 'N/A',
          withinSonora ? 'Sí' : 'No'
        ].join(',');
      })
    ].join('\n');

    const blob = new Blob([reportData], { type: 'text/plain;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `reporte_geolocalizacion_detallado_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (centers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500">
          No hay centros de salud para validar. Cargue datos primero.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-800">
            Validación Avanzada de Geolocalización
          </h3>
          <div className="flex space-x-3">
            <button
              onClick={improveAllCoordinates}
              disabled={isValidating}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {isValidating ? (
                <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
              ) : (
                <MapPin className="h-5 w-5 mr-2" />
              )}
              Mejorar con Direcciones
            </button>
            <button
              onClick={exportValidationReport}
              disabled={!qualityReport}
              className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
            >
              <Download className="h-5 w-5 mr-2" />
              Exportar Reporte
            </button>
          </div>
        </div>

        {isValidating && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center">
              <RefreshCw className="h-5 w-5 text-blue-600 animate-spin mr-3" />
              <span className="text-blue-700">Validando coordenadas con información de direcciones...</span>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('list')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'list'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <Eye className="h-4 w-4 mr-2" />
                Lista de Validación
              </div>
            </button>
            <button
              onClick={() => setActiveTab('report')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'report'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <BarChart3 className="h-4 w-4 mr-2" />
                Reporte de Calidad
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Quality Report Tab */}
      {activeTab === 'report' && qualityReport && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-lg font-medium text-gray-800 mb-6">Reporte Detallado de Calidad</h4>
          
          {/* Overall Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-900">{qualityReport.overall.total}</div>
              <div className="text-sm text-blue-600">Total Centros</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-900">{qualityReport.overall.accurateCoordinates}</div>
              <div className="text-sm text-green-600">Coordenadas Precisas</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-900">{qualityReport.overall.averageAccuracy}%</div>
              <div className="text-sm text-yellow-600">Precisión Promedio</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-900">{qualityReport.overall.qualityScore}%</div>
              <div className="text-sm text-purple-600">Puntuación General</div>
            </div>
          </div>

          {/* Address Analysis */}
          <div className="mb-8">
            <h5 className="font-medium text-gray-800 mb-4">Análisis de Direcciones</h5>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-xl font-bold text-gray-900">{qualityReport.addressAnalysis.completeAddresses}</div>
                <div className="text-sm text-gray-600">Direcciones Completas</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-xl font-bold text-gray-900">{qualityReport.addressAnalysis.partialAddresses}</div>
                <div className="text-sm text-gray-600">Direcciones Parciales</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-xl font-bold text-gray-900">{qualityReport.addressAnalysis.noAddresses}</div>
                <div className="text-sm text-gray-600">Sin Dirección</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-xl font-bold text-gray-900">{qualityReport.addressAnalysis.addressQualityScore}%</div>
                <div className="text-sm text-gray-600">Calidad de Direcciones</div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {qualityReport.recommendations.length > 0 && (
            <div className="mb-8">
              <h5 className="font-medium text-gray-800 mb-3">Recomendaciones:</h5>
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <ul className="list-disc list-inside space-y-2 text-sm text-yellow-800">
                  {qualityReport.recommendations.map((rec: string, index: number) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Municipality Analysis */}
          <div>
            <h5 className="font-medium text-gray-800 mb-4">Análisis por Municipio</h5>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Municipio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Precisas
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Con Direcciones
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Distancia Promedio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Calidad
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(qualityReport.byMunicipality).map(([municipality, data]: [string, any]) => (
                    <tr key={municipality}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {municipality}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {data.total}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {data.accurate}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {data.withAddresses}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {data.averageDistance} km
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          data.qualityScore >= 80 ? 'bg-green-100 text-green-800' :
                          data.qualityScore >= 60 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {data.qualityScore}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Validation Results List Tab */}
      {activeTab === 'list' && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-lg font-medium text-gray-800">Resultados de Validación con Direcciones</h4>
          </div>
          
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
                    Dirección
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Coordenadas
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Precisión
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fuente
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
                {validationResults.map((center) => {
                  const withinSonora = GeocodingService.isWithinSonora(center.lat, center.lng);
                  const validation = GeocodingService.validateCoordinatesWithAddress(
                    center.lat, 
                    center.lng, 
                    center.municipio, 
                    center.direccion
                  );
                  
                  return (
                    <tr key={center.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{center.nombre}</div>
                        <div className="text-sm text-gray-500">CLUES: {center.clues || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{center.municipio}</div>
                        <div className="text-sm text-gray-500">{center.distrito}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 max-w-xs truncate">
                          {center.direccion || 'Sin dirección'}
                        </div>
                        {center.direccion && (
                          <div className="text-xs text-gray-500 mt-1">
                            {GeocodingService['parseAddressComponents'](center.direccion).streetNumber ? '📍' : '⚠️'} 
                            {GeocodingService['parseAddressComponents'](center.direccion).streetName ? ' 🛣️' : ''}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {center.lat.toFixed(6)}, {center.lng.toFixed(6)}
                        </div>
                        {center.original_lat && (
                          <div className="text-xs text-gray-500">
                            Original: {center.original_lat.toFixed(4)}, {center.original_lng.toFixed(4)}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getAccuracyBadge(center.geolocation_accuracy || 'unknown', center.geolocation_confidence)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getSourceIcon(center.geolocation_source || 'unknown')}
                          <span className="ml-2 text-sm text-gray-900 capitalize">
                            {center.geolocation_source || 'Desconocida'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {withinSonora ? (
                            <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600 mr-2" />
                          )}
                          <span className={`text-sm ${withinSonora ? 'text-green-600' : 'text-red-600'}`}>
                            {withinSonora ? 'En Sonora' : 'Fuera de Sonora'}
                          </span>
                        </div>
                        {validation.distanceFromCenter > 0 && (
                          <div className="text-xs text-gray-500 mt-1">
                            {validation.distanceFromCenter.toFixed(2)}km del centro
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => setSelectedCenter(center)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Ver detalles"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedCenter && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-medium text-gray-900">{selectedCenter.nombre}</h3>
              <button
                onClick={() => setSelectedCenter(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Municipio</label>
                  <div className="mt-1 text-sm text-gray-900">{selectedCenter.municipio}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Distrito</label>
                  <div className="mt-1 text-sm text-gray-900">{selectedCenter.distrito}</div>
                </div>
              </div>
              
              {/* Address Information */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Dirección Completa</label>
                <div className="mt-1 text-sm text-gray-900 p-3 bg-gray-50 rounded-md">
                  {selectedCenter.direccion || 'Sin dirección registrada'}
                </div>
                {selectedCenter.direccion && (
                  <div className="mt-2">
                    <h6 className="text-sm font-medium text-gray-700">Componentes de la Dirección:</h6>
                    <div className="mt-1 text-xs text-gray-600">
                      {(() => {
                        const components = GeocodingService['parseAddressComponents'](selectedCenter.direccion);
                        return (
                          <ul className="list-disc list-inside space-y-1">
                            {components.streetType && <li>Tipo de vía: {components.streetType}</li>}
                            {components.streetName && <li>Nombre de calle: {components.streetName}</li>}
                            {components.streetNumber && <li>Número: {components.streetNumber}</li>}
                            {components.neighborhood && <li>Colonia: {components.neighborhood}</li>}
                            {components.postalCode && <li>Código postal: {components.postalCode}</li>}
                          </ul>
                        );
                      })()}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Coordinate Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Coordenadas Actuales</label>
                  <div className="mt-1 text-sm text-gray-900 font-mono">
                    {selectedCenter.lat.toFixed(6)}, {selectedCenter.lng.toFixed(6)}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Coordenadas Originales</label>
                  <div className="mt-1 text-sm text-gray-500 font-mono">
                    {selectedCenter.original_lat ? 
                      `${selectedCenter.original_lat.toFixed(6)}, ${selectedCenter.original_lng.toFixed(6)}` :
                      'Sin cambios'
                    }
                  </div>
                </div>
              </div>
              
              {/* Quality Information */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Precisión</label>
                  <div className="mt-1">{getAccuracyBadge(selectedCenter.geolocation_accuracy || 'unknown', selectedCenter.geolocation_confidence)}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Fuente</label>
                  <div className="mt-1 flex items-center">
                    {getSourceIcon(selectedCenter.geolocation_source || 'unknown')}
                    <span className="ml-2 text-sm text-gray-900 capitalize">
                      {selectedCenter.geolocation_source || 'Desconocida'}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Confianza</label>
                  <div className="mt-1 text-sm text-gray-900">
                    {selectedCenter.geolocation_confidence ? `${selectedCenter.geolocation_confidence}%` : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Validation Results */}
              {(() => {
                const validation = GeocodingService.validateCoordinatesWithAddress(
                  selectedCenter.lat, 
                  selectedCenter.lng, 
                  selectedCenter.municipio,
                  selectedCenter.direccion
                );
                
                return (
                  <div>
                    <h6 className="text-sm font-medium text-gray-700 mb-3">Resultado de Validación</h6>
                    {validation.issues.length > 0 ? (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                        <h6 className="text-sm font-medium text-yellow-800 mb-2">Problemas Detectados:</h6>
                        <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                          {validation.issues.map((issue, index) => (
                            <li key={index}>{issue}</li>
                          ))}
                        </ul>
                        
                        {validation.suggestions.length > 0 && (
                          <>
                            <h6 className="text-sm font-medium text-yellow-800 mt-3 mb-2">Sugerencias:</h6>
                            <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                              {validation.suggestions.map((suggestion, index) => (
                                <li key={index}>{suggestion}</li>
                              ))}
                            </ul>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="bg-green-50 border border-green-200 rounded-md p-4">
                        <div className="flex items-center">
                          <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                          <span className="text-sm text-green-700">
                            Las coordenadas y dirección son válidas (Precisión: {validation.accuracy}%)
                          </span>
                        </div>
                        {validation.distanceFromCenter > 0 && (
                          <div className="text-sm text-green-600 mt-2">
                            Distancia del centro municipal: {validation.distanceFromCenter.toFixed(2)} km
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedCenter(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeolocationValidator;