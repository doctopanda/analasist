import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon, LatLngBounds } from 'leaflet';
import { MapPin, Search, Download, Upload, Hospital, Building2, Stethoscope, Truck } from 'lucide-react';
import { ExcelService, HealthCenterData } from '../services/excelService';
import 'leaflet/dist/leaflet.css';

interface HealthCenter {
  id: string;
  nombre: string;
  direccion: string;
  municipio: string;
  estado: string;
  distrito: string;
  tipo: string;
  telefono?: string;
  email?: string;
  responsable?: string;
  lat: number;
  lng: number;
  codigo_establecimiento: string;
  horario?: string;
  clues?: string;
}

// Custom hook to fit map bounds to markers
const FitBounds: React.FC<{ centers: HealthCenter[] }> = ({ centers }) => {
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
  selectedCenter: HealthCenter | null;
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
  centers?: HealthCenter[];
  onFileUpload?: (centers: HealthCenter[]) => void;
  onExportData?: () => void;
}

const HealthCentersMap: React.FC<HealthCentersMapProps> = ({ 
  centers: externalCenters = [], 
  onFileUpload,
  onExportData 
}) => {
  const [centers, setCenters] = useState<HealthCenter[]>([]);
  const [filteredCenters, setFilteredCenters] = useState<HealthCenter[]>([]);
  const [selectedCenter, setSelectedCenter] = useState<HealthCenter | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMunicipality, setFilterMunicipality] = useState('');
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(false);

  // Use external centers if provided, otherwise use mock data
  useEffect(() => {
    if (externalCenters.length > 0) {
      setCenters(externalCenters);
      setFilteredCenters(externalCenters);
    } else {
      // Mock data for Sonora health centers
      const mockCenters: HealthCenter[] = [
        {
          id: '1',
          nombre: 'Hospital General del Estado de Sonora',
          direccion: 'Blvd. Luis Encinas Johnson s/n',
          municipio: 'Hermosillo',
          estado: 'Sonora',
          distrito: 'Distrito 1',
          tipo: 'Hospital',
          telefono: '662-259-2500',
          responsable: 'Dr. Juan Pérez',
          lat: 29.0729,
          lng: -110.9559,
          codigo_establecimiento: 'HGES001'
        },
        {
          id: '2',
          nombre: 'Centro de Salud Urbano Villa de Seris',
          direccion: 'Calle Sonora #123, Villa de Seris',
          municipio: 'Hermosillo',
          estado: 'Sonora',
          distrito: 'Distrito 1',
          tipo: 'Centro de Salud',
          telefono: '662-215-8900',
          responsable: 'Dra. María González',
          lat: 29.0892,
          lng: -110.9618,
          codigo_establecimiento: 'CSVS002'
        },
        {
          id: '3',
          nombre: 'Hospital General de Cajeme',
          direccion: 'Calle 5 de Febrero #311',
          municipio: 'Cajeme',
          estado: 'Sonora',
          distrito: 'Distrito 2',
          tipo: 'Hospital',
          telefono: '644-414-0050',
          responsable: 'Dr. Carlos Rodríguez',
          lat: 27.3833,
          lng: -109.9167,
          codigo_establecimiento: 'HGC003'
        },
        {
          id: '4',
          nombre: 'Centro de Salud Nogales',
          direccion: 'Av. Obregón #1234',
          municipio: 'Nogales',
          estado: 'Sonora',
          distrito: 'Distrito 3',
          tipo: 'Centro de Salud',
          telefono: '631-311-2500',
          responsable: 'Dra. Ana López',
          lat: 31.3081,
          lng: -110.9342,
          codigo_establecimiento: 'CSN004'
        },
        {
          id: '5',
          nombre: 'Hospital General San Luis Río Colorado',
          direccion: 'Av. Reforma #567',
          municipio: 'San Luis Río Colorado',
          estado: 'Sonora',
          distrito: 'Distrito 4',
          tipo: 'Hospital',
          telefono: '653-534-1234',
          responsable: 'Dr. Roberto Martínez',
          lat: 32.4606,
          lng: -114.7706,
          codigo_establecimiento: 'HGSLRC005'
        },
        {
          id: '6',
          nombre: 'Centro de Salud Guaymas',
          direccion: 'Calle 20 #456',
          municipio: 'Guaymas',
          estado: 'Sonora',
          distrito: 'Distrito 2',
          tipo: 'Centro de Salud',
          telefono: '622-222-3456',
          responsable: 'Dr. Luis Hernández',
          lat: 27.9167,
          lng: -110.9000,
          codigo_establecimiento: 'CSG006'
        },
        {
          id: '7',
          nombre: 'Clínica del IMSS Navojoa',
          direccion: 'Av. Tecnológico #789',
          municipio: 'Navojoa',
          estado: 'Sonora',
          distrito: 'Distrito 2',
          tipo: 'Clínica',
          telefono: '642-422-1234',
          responsable: 'Dra. Carmen Ruiz',
          lat: 27.0667,
          lng: -109.4500,
          codigo_establecimiento: 'CIN007'
        }
      ];
      setCenters(mockCenters);
      setFilteredCenters(mockCenters);
    }
  }, [externalCenters]);

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
      setCenters(healthCenters);
      setFilteredCenters(healthCenters);
      onFileUpload?.(healthCenters);
    } catch (error) {
      console.error('Error processing file:', error);
      alert('Error al procesar el archivo Excel. Verifique que el formato sea correcto.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = () => {
    if (centers.length === 0) {
      alert('No hay datos para exportar');
      return;
    }

    // Create CSV content
    const csvContent = [
      'ID,Nombre,Dirección,Municipio,Estado,Distrito,Tipo,Teléfono,Email,Responsable,Código,CLUES,Horario,Latitud,Longitud',
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
        center.clues || '',
        `"${center.horario || ''}"`,
        center.lat,
        center.lng
      ].join(','))
    ].join('\n');

    // Create and download file
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

    // Call external export handler if provided
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
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Unidades Móviles</span>
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