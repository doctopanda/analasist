import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon, LatLngBounds } from 'leaflet';
import { MapPin, Search, Download, Upload, Hospital, Building2, Stethoscope, Truck } from 'lucide-react';
import { ExcelService, HealthCenterData } from '../services/excelService';
import 'leaflet/dist/leaflet.css';

// Custom hook to fit map bounds to markers
const FitBounds: React.FC<{ centers: HealthCenterData[] }> = ({ centers }) => {
  const map = useMap();

  useEffect(() => {
    if (centers.length > 0) {
      const bounds = new LatLngBounds(
        centers.map(center => [center.lat, center.lng])
      );
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [centers, map]);

  return null;
};

// Custom hook to handle center selection
const CenterSelector: React.FC<{ 
  selectedCenter: HealthCenterData | null;
}> = ({ selectedCenter }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedCenter) {
      map.setView([selectedCenter.lat, selectedCenter.lng], 12);
    }
  }, [selectedCenter, map]);

  return null;
};

// Create custom icons for different types of health centers
const createCustomIcon = (tipo: string, isSelected: boolean = false) => {
  const getIconColor = (tipo: string) => {
    switch (tipo.toLowerCase()) {
      case 'hospital':
        return '#dc2626'; // red-600
      case 'centro de salud':
        return '#2563eb'; // blue-600
      case 'clínica':
        return '#16a34a'; // green-600
      case 'farmacia':
        return '#7c3aed'; // purple-600
      case 'consultorio médico':
        return '#ca8a04'; // yellow-600
      case 'consultorio dental':
        return '#ec4899'; // pink-600
      case 'unidad móvil':
        return '#ca8a04'; // yellow-600
      default:
        return '#7c3aed'; // purple-600
    }
  };

  const color = getIconColor(tipo);
  const size = isSelected ? 35 : 25;
  
  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" fill="${color}" stroke="white" stroke-width="2"/>
        <circle cx="12" cy="12" r="4" fill="white"/>
      </svg>
    `)}`,
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -size/2]
  });
};

interface HealthCentersMapProps {
  centers: HealthCenterData[];
  onFileUpload?: (centers: HealthCenterData[]) => void;
  onExportData?: () => void;
}

const HealthCentersMap: React.FC<HealthCentersMapProps> = ({ 
  centers = [], 
  onFileUpload,
  onExportData 
}) => {
  const [filteredCenters, setFilteredCenters] = useState<HealthCenterData[]>(centers);
  const [selectedCenter, setSelectedCenter] = useState<HealthCenterData | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMunicipality, setFilterMunicipality] = useState('');
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(false);

  // Update filtered centers when centers prop changes
  useEffect(() => {
    setFilteredCenters(centers);
  }, [centers]);

  // Filter centers based on search and filters
  useEffect(() => {
    let filtered = centers;

    if (searchTerm) {
      filtered = filtered.filter(center =>
        center.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.direccion.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.responsable?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.clues?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterMunicipality) {
      filtered = filtered.filter(center => center.municipio === filterMunicipality);
    }

    if (filterType) {
      filtered = filtered.filter(center => center.tipo === filterType);
    }

    setFilteredCenters(filtered);
  }, [centers, searchTerm, filterMunicipality, filterType]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const healthCenters = await ExcelService.parseFileUpload(file);
      onFileUpload?.(healthCenters);
    } catch (error) {
      console.error('Error processing file:', error);
      alert('Error al procesar el archivo Excel. Verifique que el formato sea correcto.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = () => {
    onExportData?.();
  };

  const getTypeIcon = (tipo: string) => {
    switch (tipo.toLowerCase()) {
      case 'hospital':
        return <Hospital className="h-4 w-4 text-red-600" />;
      case 'centro de salud':
        return <Building2 className="h-4 w-4 text-blue-600" />;
      case 'clínica':
        return <Stethoscope className="h-4 w-4 text-green-600" />;
      case 'farmacia':
        return <MapPin className="h-4 w-4 text-purple-600" />;
      case 'consultorio médico':
        return <Stethoscope className="h-4 w-4 text-yellow-600" />;
      case 'consultorio dental':
        return <Stethoscope className="h-4 w-4 text-pink-600" />;
      case 'unidad móvil':
        return <Truck className="h-4 w-4 text-yellow-600" />;
      default:
        return <MapPin className="h-4 w-4 text-purple-600" />;
    }
  };

  const municipalities = [...new Set(centers.map(c => c.municipio))].sort();
  const types = [...new Set(centers.map(c => c.tipo))].sort();

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <h3 className="text-lg font-medium text-gray-800">
            Centros de Salud de Sonora
          </h3>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <label className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer">
              <Upload className="h-5 w-5 mr-2" />
              Cargar Excel
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
            
            <button 
              onClick={handleExportData}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              <Download className="h-5 w-5 mr-2" />
              Exportar Datos
            </button>
          </div>
        </div>

        {loading && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-blue-500 mr-3"></div>
              <span className="text-blue-700">Procesando archivo Excel...</span>
            </div>
          </div>
        )}

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar centros de salud..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <select
            value={filterMunicipality}
            onChange={(e) => setFilterMunicipality(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Todos los municipios</option>
            {municipalities.map(municipality => (
              <option key={municipality} value={municipality}>
                {municipality}
              </option>
            ))}
          </select>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Todos los tipos</option>
            {types.map(type => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-4 flex items-center gap-4 text-sm text-gray-600">
          <span>Total: {filteredCenters.length} centros</span>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>Hospitales</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Centros de Salud</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Clínicas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span>Otros</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
        <div className="lg:col-span-2 h-96 lg:h-[600px]">
          <MapContainer
            center={[29.0729, -110.9559]} // Hermosillo, Sonora
            zoom={7}
            style={{ height: '100%', width: '100%' }}
            className="z-0"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            <FitBounds centers={filteredCenters} />
            <CenterSelector selectedCenter={selectedCenter} />
            
            {filteredCenters.map(center => (
              <Marker
                key={center.id}
                position={[center.lat, center.lng]}
                icon={createCustomIcon(center.tipo, selectedCenter?.id === center.id)}
                eventHandlers={{
                  click: () => setSelectedCenter(center)
                }}
              >
                <Popup>
                  <div className="p-2 max-w-sm">
                    <h3 className="font-bold text-lg text-blue-800 mb-2">{center.nombre}</h3>
                    <div className="flex items-center gap-2 mb-2">
                      {getTypeIcon(center.tipo)}
                      <span className="text-sm text-gray-600">{center.tipo}</span>
                    </div>
                    <p className="text-sm mb-1"><strong>Dirección:</strong> {center.direccion}</p>
                    <p className="text-sm mb-1"><strong>Municipio:</strong> {center.municipio}</p>
                    <p className="text-sm mb-1"><strong>Distrito:</strong> {center.distrito}</p>
                    {center.clues && (
                      <p className="text-sm mb-1"><strong>CLUES:</strong> {center.clues}</p>
                    )}
                    {center.telefono && (
                      <p className="text-sm mb-1"><strong>Teléfono:</strong> {center.telefono}</p>
                    )}
                    {center.horario && (
                      <p className="text-sm mb-1"><strong>Horario:</strong> {center.horario}</p>
                    )}
                    {center.responsable && (
                      <p className="text-sm"><strong>Responsable:</strong> {center.responsable}</p>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>

        <div className="bg-gray-50 p-4 overflow-y-auto max-h-96 lg:max-h-[600px]">
          <h4 className="font-medium text-gray-800 mb-3">Lista de Centros</h4>
          <div className="space-y-3">
            {filteredCenters.map(center => (
              <div
                key={center.id}
                className={`p-3 bg-white rounded-md shadow-sm cursor-pointer transition-colors ${
                  selectedCenter?.id === center.id ? 'ring-2 ring-blue-500' : 'hover:bg-blue-50'
                }`}
                onClick={() => setSelectedCenter(center)}
              >
                <div className="flex items-start gap-2">
                  {getTypeIcon(center.tipo)}
                  <div className="min-w-0 flex-1">
                    <h5 className="font-medium text-sm text-gray-900 truncate">
                      {center.nombre}
                    </h5>
                    <p className="text-xs text-gray-600">{center.tipo}</p>
                    <p className="text-xs text-gray-500">{center.municipio}</p>
                    {center.clues && (
                      <p className="text-xs text-gray-500">CLUES: {center.clues}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedCenter && (
        <div className="p-6 border-t border-gray-200 bg-blue-50">
          <h4 className="font-medium text-gray-800 mb-3">Información Detallada</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm"><strong>Nombre:</strong> {selectedCenter.nombre}</p>
              <p className="text-sm"><strong>Tipo:</strong> {selectedCenter.tipo}</p>
              <p className="text-sm"><strong>Dirección:</strong> {selectedCenter.direccion}</p>
              <p className="text-sm"><strong>Municipio:</strong> {selectedCenter.municipio}</p>
              {selectedCenter.clues && (
                <p className="text-sm"><strong>CLUES:</strong> {selectedCenter.clues}</p>
              )}
            </div>
            <div>
              <p className="text-sm"><strong>Distrito:</strong> {selectedCenter.distrito}</p>
              <p className="text-sm"><strong>Código:</strong> {selectedCenter.codigo_establecimiento}</p>
              {selectedCenter.telefono && (
                <p className="text-sm"><strong>Teléfono:</strong> {selectedCenter.telefono}</p>
              )}
              {selectedCenter.horario && (
                <p className="text-sm"><strong>Horario:</strong> {selectedCenter.horario}</p>
              )}
              {selectedCenter.responsable && (
                <p className="text-sm"><strong>Responsable:</strong> {selectedCenter.responsable}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthCentersMap;