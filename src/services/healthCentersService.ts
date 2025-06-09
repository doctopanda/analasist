import { HealthCenterData } from './excelService';

export interface DataSource {
  name: string;
  type: 'government' | 'opendata' | 'osm';
  url?: string;
  description: string;
  status: 'active' | 'inactive' | 'requires_key';
}

export class HealthCentersService {
  private static dataSources: DataSource[] = [
    {
      name: 'GOBI - Catálogo Maestro',
      type: 'government',
      url: 'https://datos.gob.mx/busca/dataset/establecimientos-de-salud/resource/b4b1c0e4-8b4a-4b4a-8b4a-4b4a8b4a8b4a',
      description: 'Base de datos oficial del gobierno mexicano',
      status: 'inactive'
    },
    {
      name: 'OpenStreetMap Overpass API',
      type: 'osm',
      url: 'https://overpass-api.de/api/interpreter',
      description: 'Datos de establecimientos de salud en OpenStreetMap',
      status: 'active'
    },
    {
      name: 'INEGI - Marco Geoestadístico',
      type: 'government',
      url: 'https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=889463807469',
      description: 'Instituto Nacional de Estadística y Geografía',
      status: 'inactive'
    }
  ];

  static async fetchFromOpenStreetMap(): Promise<HealthCenterData[]> {
    try {
      // Sonora bounding box coordinates - corrected format: south,west,north,east
      const bbox = '26.0,-115.0,32.5,-108.0'; // south,west,north,east
      
      const query = `
        [out:json][timeout:25];
        (
          node["amenity"~"^(hospital|clinic|doctors|dentist|pharmacy)$"](${bbox});
          node["healthcare"](${bbox});
        );
        out;
      `;

      const response = await fetch('https://overpass-api.de/api/interpreter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `data=${encodeURIComponent(query)}`
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return this.parseOSMData(data);
    } catch (error) {
      console.error('Error fetching from OpenStreetMap:', error);
      throw error;
    }
  }

  private static parseOSMData(osmData: any): HealthCenterData[] {
    const healthCenters: HealthCenterData[] = [];

    if (!osmData.elements) {
      return healthCenters;
    }

    osmData.elements.forEach((element: any, index: number) => {
      try {
        let lat: number, lng: number;

        // Get coordinates based on element type
        if (element.type === 'node') {
          lat = element.lat;
          lng = element.lon;
        } else if (element.type === 'way' && element.geometry) {
          // Use center of way
          const coords = element.geometry;
          lat = coords.reduce((sum: number, coord: any) => sum + coord.lat, 0) / coords.length;
          lng = coords.reduce((sum: number, coord: any) => sum + coord.lon, 0) / coords.length;
        } else {
          return; // Skip if no coordinates
        }

        const tags = element.tags || {};
        
        // Determine facility type
        let tipo = 'Centro de Salud';
        if (tags.amenity === 'hospital' || tags.healthcare === 'hospital') {
          tipo = 'Hospital';
        } else if (tags.amenity === 'clinic' || tags.healthcare === 'clinic') {
          tipo = 'Clínica';
        } else if (tags.amenity === 'pharmacy') {
          tipo = 'Farmacia';
        } else if (tags.amenity === 'dentist') {
          tipo = 'Consultorio Dental';
        } else if (tags.amenity === 'doctors') {
          tipo = 'Consultorio Médico';
        }

        // Estimate municipality based on coordinates
        const municipio = this.estimateMunicipality(lat, lng);

        const healthCenter: HealthCenterData = {
          id: `osm_${element.type}_${element.id}`,
          nombre: tags.name || tags['name:es'] || `${tipo} sin nombre`,
          direccion: this.buildAddress(tags),
          municipio: municipio,
          estado: 'Sonora',
          distrito: this.estimateDistrict(municipio),
          tipo: tipo,
          telefono: tags.phone || tags['contact:phone'],
          email: tags.email || tags['contact:email'],
          responsable: tags.operator || tags.owner,
          lat: lat,
          lng: lng,
          codigo_establecimiento: `OSM_${element.id}`
        };

        healthCenters.push(healthCenter);
      } catch (error) {
        console.warn(`Error parsing OSM element ${index}:`, error);
      }
    });

    return healthCenters;
  }

  private static buildAddress(tags: any): string {
    const parts = [];
    
    if (tags['addr:street']) {
      parts.push(tags['addr:street']);
    }
    if (tags['addr:housenumber']) {
      parts.push(tags['addr:housenumber']);
    }
    if (tags['addr:neighbourhood']) {
      parts.push(tags['addr:neighbourhood']);
    }
    
    return parts.length > 0 ? parts.join(' ') : 'Dirección no disponible';
  }

  private static estimateMunicipality(lat: number, lng: number): string {
    // Approximate municipality boundaries for Sonora
    const municipalities = [
      { name: 'Hermosillo', bounds: { north: 29.5, south: 28.5, east: -110.5, west: -111.5 } },
      { name: 'Cajeme', bounds: { north: 27.8, south: 27.0, east: -109.5, west: -110.5 } },
      { name: 'Nogales', bounds: { north: 31.5, south: 31.0, east: -110.5, west: -111.0 } },
      { name: 'San Luis Río Colorado', bounds: { north: 32.8, south: 32.2, east: -114.5, west: -115.0 } },
      { name: 'Navojoa', bounds: { north: 27.3, south: 26.8, east: -109.2, west: -109.8 } },
      { name: 'Guaymas', bounds: { north: 28.2, south: 27.7, east: -110.5, west: -111.2 } },
      { name: 'Puerto Peñasco', bounds: { north: 31.5, south: 31.0, east: -113.3, west: -113.8 } },
      { name: 'Agua Prieta', bounds: { north: 31.5, south: 31.2, east: -109.3, west: -109.7 } }
    ];

    for (const municipality of municipalities) {
      const { bounds } = municipality;
      if (lat >= bounds.south && lat <= bounds.north && 
          lng >= bounds.west && lng <= bounds.east) {
        return municipality.name;
      }
    }

    return 'Municipio no identificado';
  }

  private static estimateDistrict(municipio: string): string {
    const districtMap: Record<string, string> = {
      'Hermosillo': 'Distrito 1',
      'Cajeme': 'Distrito 2',
      'Navojoa': 'Distrito 2',
      'Guaymas': 'Distrito 2',
      'Nogales': 'Distrito 3',
      'Agua Prieta': 'Distrito 3',
      'San Luis Río Colorado': 'Distrito 4',
      'Puerto Peñasco': 'Distrito 4'
    };

    return districtMap[municipio] || 'Distrito no identificado';
  }

  static getAvailableDataSources(): DataSource[] {
    return this.dataSources;
  }

  static async fetchFromMultipleSources(): Promise<{
    gobi: HealthCenterData[];
    osm: HealthCenterData[];
    combined: HealthCenterData[];
  }> {
    const results = {
      gobi: [] as HealthCenterData[],
      osm: [] as HealthCenterData[],
      combined: [] as HealthCenterData[]
    };

    try {
      // Fetch from OpenStreetMap
      results.osm = await this.fetchFromOpenStreetMap();
    } catch (error) {
      console.error('Error fetching from OSM:', error);
    }

    // Combine and deduplicate
    results.combined = [...results.gobi, ...results.osm];
    
    // Remove duplicates based on proximity (within 100 meters)
    results.combined = this.removeDuplicates(results.combined);

    return results;
  }

  private static removeDuplicates(centers: HealthCenterData[]): HealthCenterData[] {
    const unique: HealthCenterData[] = [];
    
    for (const center of centers) {
      const isDuplicate = unique.some(existing => {
        const distance = this.calculateDistance(
          center.lat, center.lng,
          existing.lat, existing.lng
        );
        return distance < 0.1; // 100 meters
      });
      
      if (!isDuplicate) {
        unique.push(center);
      }
    }
    
    return unique;
  }

  private static calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }
}