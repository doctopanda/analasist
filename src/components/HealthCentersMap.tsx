import React, { useState, useEffect, useCallback } from 'react';
import { Wrapper, Status } from '@googlemaps/react-wrapper';
import { MapPin, Search, Filter, Download, Upload } from 'lucide-react';

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
}

interface MapProps {
  centers: HealthCenter[];
  selectedCenter: HealthCenter | null;
  onCenterSelect: (center: HealthCenter | null) => void;
}

const Map: React.FC<MapProps> = ({ centers, selectedCenter, onCenterSelect }) => {
  const [map, setMap] = useState<google.maps.Map>();
  const [markers, setMarkers] = useState<google.maps.Marker[]>([]);

  const ref = useCallback((node: HTMLDivElement | null) => {
    if (node !== null) {
      const newMap = new google.maps.Map(node, {
        center: { lat: 29.0729, lng: -110.9559 }, // Hermosillo, Sonora
        zoom: 7,
        mapTypeId: 'roadmap',
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ]
      });
      setMap(newMap);
    }
  }, []);

  useEffect(() => {
    if (!map) return;

    // Clear existing markers
    markers.forEach(marker => marker.setMap(null));

    // Create new markers
    const newMarkers = centers.map(center => {
      const marker = new google.maps.Marker({
        position: { lat: center.lat, lng: center.lng },
        map,
        title: center.nombre,
        icon: {
          url: getMarkerIcon(center.tipo),
          scaledSize: new google.maps.Size(32, 32)
        }
      });

      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div class="p-3 max-w-sm">
            <h3 class="font-bold text-lg text-blue-800">${center.nombre}</h3>
            <p class="text-sm text-gray-600 mb-2">${center.tipo}</p>
            <p class="text-sm"><strong>Dirección:</strong> ${center.direccion}</p>
            <p class="text-sm"><strong>Municipio:</strong> ${center.municipio}</p>
            <p class="text-sm"><strong>Distrito:</strong> ${center.distrito}</p>
            ${center.telefono ? `<p class="text-sm"><strong>Teléfono:</strong> ${center.telefono}</p>` : ''}
            ${center.responsable ? `<p class="text-sm"><strong>Responsable:</strong> ${center.responsable}</p>` : ''}
          </div>
        `
      });

      marker.addListener('click', () => {
        onCenterSelect(center);
        infoWindow.open(map, marker);
      });

      return marker;
    });

    setMarkers(newMarkers);

    // Adjust map bounds to show all markers
    if (centers.length > 0) {
      const bounds = new google.maps.LatLngBounds();
      centers.forEach(center => {
        bounds.extend({ lat: center.lat, lng: center.lng });
      });
      map.fitBounds(bounds);
    }
  }, [map, centers, onCenterSelect]);

  // Highlight selected center
  useEffect(() => {
    if (!selectedCenter || !map) return;

    const selectedMarker = markers.find(marker => 
      marker.getTitle() === selectedCenter.nombre
    );

    if (selectedMarker) {
      map.panTo({ lat: selectedCenter.lat, lng: selectedCenter.lng });
      map.setZoom(12);
    }
  }, [selectedCenter, map, markers]);

  return <div ref={ref} className="w-full h-full" />;
};

const getMarkerIcon = (tipo: string): string => {
  const baseUrl = 'https://maps.google.com/mapfiles/ms/icons/';
  switch (tipo.toLowerCase()) {
    case 'hospital':
      return `${baseUrl}red-dot.png`;
    case 'centro de salud':
      return `${baseUrl}blue-dot.png`;
    case 'clínica':
      return `${baseUrl}green-dot.png`;
    case 'unidad móvil':
      return `${baseUrl}yellow-dot.png`;
    default:
      return `${baseUrl}purple-dot.png`;
  }
};

const render = (status: Status) => {
  switch (status) {
    case Status.LOADING:
      return (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    case Status.FAILURE:
      return (
        <div className="flex items-center justify-center h-96 bg-red-50">
          <div className="text-center">
            <p className="text-red-600 font-medium">Error al cargar Google Maps</p>
            <p className="text-red-500 text-sm">Verifique la clave de API</p>
          </div>
        </div>
      );
    default:
      return null;
  }
};

interface HealthCentersMapProps {
  onFileUpload?: (centers: HealthCenter[]) => void;
}

const HealthCentersMap: React.FC<HealthCentersMapProps> = ({ onFileUpload }) => {
  const [centers, setCenters] = useState<HealthCenter[]>([]);
  const [filteredCenters, setFilteredCenters] = useState<HealthCenter[]>([]);
  const [selectedCenter, setSelectedCenter] = useState<HealthCenter | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMunicipality, setFilterMunicipality] = useState('');
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(false);

  // Mock data for Sonora health centers (you would replace this with actual Excel data)
  useEffect(() => {
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
      }
    ];
    setCenters(mockCenters);
    setFilteredCenters(mockCenters);
  }, []);

  // Filter centers based on search and filters
  useEffect(() => {
    let filtered = centers;

    if (searchTerm) {
      filtered = filtered.filter(center =>
        center.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.direccion.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.responsable?.toLowerCase().includes(searchTerm.toLowerCase())
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
      // Here you would process the Excel file
      // For now, we'll simulate the process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // In a real implementation, you would:
      // 1. Read the Excel file using the xlsx library
      // 2. Parse the data and extract health centers for Sonora
      // 3. Geocode addresses to get lat/lng coordinates
      // 4. Update the centers state
      
      console.log('File uploaded:', file.name);
      // onFileUpload?.(parsedCenters);
    } catch (error) {
      console.error('Error processing file:', error);
    } finally {
      setLoading(false);
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
            
            <button className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
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
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
        <div className="lg:col-span-2 h-96 lg:h-[600px]">
          <Wrapper
            apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "YOUR_GOOGLE_MAPS_API_KEY"}
            render={render}
          >
            <Map
              centers={filteredCenters}
              selectedCenter={selectedCenter}
              onCenterSelect={setSelectedCenter}
            />
          </Wrapper>
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
                  <MapPin className="h-4 w-4 text-blue-600 mt-1 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h5 className="font-medium text-sm text-gray-900 truncate">
                      {center.nombre}
                    </h5>
                    <p className="text-xs text-gray-600">{center.tipo}</p>
                    <p className="text-xs text-gray-500">{center.municipio}</p>
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
            </div>
            <div>
              <p className="text-sm"><strong>Distrito:</strong> {selectedCenter.distrito}</p>
              <p className="text-sm"><strong>Código:</strong> {selectedCenter.codigo_establecimiento}</p>
              {selectedCenter.telefono && (
                <p className="text-sm"><strong>Teléfono:</strong> {selectedCenter.telefono}</p>
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