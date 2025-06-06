import * as XLSX from 'xlsx';

export interface HealthCenterData {
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

export class ExcelService {
  static async downloadAndParseExcel(url: string): Promise<HealthCenterData[]> {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const arrayBuffer = await response.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: 'array' });
      
      // Get the first worksheet
      const worksheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[worksheetName];
      
      // Convert to JSON
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
      
      return this.parseHealthCenters(jsonData);
    } catch (error) {
      console.error('Error downloading or parsing Excel file:', error);
      throw error;
    }
  }

  static async parseFileUpload(file: File): Promise<HealthCenterData[]> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: 'array' });
          
          const worksheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[worksheetName];
          
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
          const healthCenters = this.parseHealthCenters(jsonData);
          
          resolve(healthCenters);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Error reading file'));
      reader.readAsArrayBuffer(file);
    });
  }

  private static parseHealthCenters(jsonData: any[]): HealthCenterData[] {
    if (!jsonData || jsonData.length < 2) {
      throw new Error('Invalid data format');
    }

    const headers = jsonData[0] as string[];
    const rows = jsonData.slice(1);

    // Map column indices (adjust these based on actual Excel structure)
    const columnMap = this.createColumnMap(headers);

    const healthCenters: HealthCenterData[] = [];

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i] as any[];
      
      // Skip empty rows
      if (!row || row.length === 0) continue;

      try {
        const estado = this.getCellValue(row, columnMap.estado);
        
        // Filter only Sonora health centers
        if (!estado || !estado.toString().toLowerCase().includes('sonora')) {
          continue;
        }

        const healthCenter: HealthCenterData = {
          id: this.getCellValue(row, columnMap.id) || `HC_${i}`,
          nombre: this.getCellValue(row, columnMap.nombre) || 'Sin nombre',
          direccion: this.getCellValue(row, columnMap.direccion) || 'Sin dirección',
          municipio: this.getCellValue(row, columnMap.municipio) || 'Sin municipio',
          estado: 'Sonora',
          distrito: this.getCellValue(row, columnMap.distrito) || 'Sin distrito',
          tipo: this.getCellValue(row, columnMap.tipo) || 'Centro de Salud',
          telefono: this.getCellValue(row, columnMap.telefono),
          email: this.getCellValue(row, columnMap.email),
          responsable: this.getCellValue(row, columnMap.responsable),
          codigo_establecimiento: this.getCellValue(row, columnMap.codigo) || `EST_${i}`,
          lat: this.parseCoordinate(this.getCellValue(row, columnMap.latitud)) || 29.0729,
          lng: this.parseCoordinate(this.getCellValue(row, columnMap.longitud)) || -110.9559
        };

        // Geocode if coordinates are missing
        if (healthCenter.lat === 29.0729 && healthCenter.lng === -110.9559) {
          // In a real implementation, you would geocode the address
          const coords = this.estimateCoordinates(healthCenter.municipio);
          healthCenter.lat = coords.lat;
          healthCenter.lng = coords.lng;
        }

        healthCenters.push(healthCenter);
      } catch (error) {
        console.warn(`Error parsing row ${i}:`, error);
        continue;
      }
    }

    return healthCenters;
  }

  private static createColumnMap(headers: string[]): Record<string, number> {
    const map: Record<string, number> = {};
    
    headers.forEach((header, index) => {
      const normalizedHeader = header.toString().toLowerCase().trim();
      
      // Map common column names (adjust based on actual Excel structure)
      if (normalizedHeader.includes('id') || normalizedHeader.includes('clave')) {
        map.id = index;
      } else if (normalizedHeader.includes('nombre') || normalizedHeader.includes('denominacion')) {
        map.nombre = index;
      } else if (normalizedHeader.includes('direccion') || normalizedHeader.includes('domicilio')) {
        map.direccion = index;
      } else if (normalizedHeader.includes('municipio')) {
        map.municipio = index;
      } else if (normalizedHeader.includes('estado') || normalizedHeader.includes('entidad')) {
        map.estado = index;
      } else if (normalizedHeader.includes('distrito')) {
        map.distrito = index;
      } else if (normalizedHeader.includes('tipo') || normalizedHeader.includes('categoria')) {
        map.tipo = index;
      } else if (normalizedHeader.includes('telefono') || normalizedHeader.includes('tel')) {
        map.telefono = index;
      } else if (normalizedHeader.includes('email') || normalizedHeader.includes('correo')) {
        map.email = index;
      } else if (normalizedHeader.includes('responsable') || normalizedHeader.includes('director')) {
        map.responsable = index;
      } else if (normalizedHeader.includes('codigo') || normalizedHeader.includes('establecimiento')) {
        map.codigo = index;
      } else if (normalizedHeader.includes('latitud') || normalizedHeader.includes('lat')) {
        map.latitud = index;
      } else if (normalizedHeader.includes('longitud') || normalizedHeader.includes('lng') || normalizedHeader.includes('lon')) {
        map.longitud = index;
      }
    });

    return map;
  }

  private static getCellValue(row: any[], index: number): string | undefined {
    if (index === undefined || index < 0 || index >= row.length) {
      return undefined;
    }
    
    const value = row[index];
    return value !== null && value !== undefined ? value.toString().trim() : undefined;
  }

  private static parseCoordinate(value: string | undefined): number | undefined {
    if (!value) return undefined;
    
    const num = parseFloat(value);
    return isNaN(num) ? undefined : num;
  }

  private static estimateCoordinates(municipio: string): { lat: number; lng: number } {
    // Approximate coordinates for major municipalities in Sonora
    const municipalityCoords: Record<string, { lat: number; lng: number }> = {
      'hermosillo': { lat: 29.0729, lng: -110.9559 },
      'cajeme': { lat: 27.3833, lng: -109.9167 },
      'nogales': { lat: 31.3081, lng: -110.9342 },
      'san luis río colorado': { lat: 32.4606, lng: -114.7706 },
      'navojoa': { lat: 27.0667, lng: -109.4333 },
      'guaymas': { lat: 27.9167, lng: -110.9000 },
      'agua prieta': { lat: 31.3333, lng: -109.5500 },
      'puerto peñasco': { lat: 31.3167, lng: -113.5333 },
      'caborca': { lat: 30.7167, lng: -112.1667 },
      'cananea': { lat: 30.9500, lng: -110.3000 }
    };

    const normalizedMunicipio = municipio.toLowerCase().trim();
    
    for (const [key, coords] of Object.entries(municipalityCoords)) {
      if (normalizedMunicipio.includes(key)) {
        return coords;
      }
    }

    // Default to Hermosillo if municipality not found
    return { lat: 29.0729, lng: -110.9559 };
  }

  static async geocodeAddress(address: string, municipio: string, estado: string): Promise<{ lat: number; lng: number } | null> {
    try {
      const fullAddress = `${address}, ${municipio}, ${estado}, México`;
      const geocoder = new google.maps.Geocoder();
      
      return new Promise((resolve) => {
        geocoder.geocode({ address: fullAddress }, (results, status) => {
          if (status === 'OK' && results && results[0]) {
            const location = results[0].geometry.location;
            resolve({
              lat: location.lat(),
              lng: location.lng()
            });
          } else {
            resolve(null);
          }
        });
      });
    } catch (error) {
      console.error('Geocoding error:', error);
      return null;
    }
  }
}