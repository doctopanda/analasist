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
  horario?: string;
  clues?: string;
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

    console.log('Headers found:', headers);
    console.log('Total rows:', rows.length);
    console.log('Sample row:', rows[0]);

    // Create column mapping based on exact GOBI column names
    const columnMap = this.createGOBIColumnMap(headers);
    console.log('Column mapping:', columnMap);

    const healthCenters: HealthCenterData[] = [];

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i] as any[];
      
      // Skip empty rows
      if (!row || row.length === 0 || !row.some(cell => cell !== null && cell !== undefined && cell !== '')) {
        continue;
      }

      try {
        const entidad = this.getCellValue(row, columnMap.entidad);
        
        // Filter only Sonora health centers (clave 26 or name contains Sonora)
        if (!entidad || (!entidad.toString().toLowerCase().includes('sonora') && entidad.toString() !== '26')) {
          continue;
        }

        const lat = this.parseCoordinate(this.getCellValue(row, columnMap.latitud));
        const lng = this.parseCoordinate(this.getCellValue(row, columnMap.longitud));
        const municipio = this.getCellValue(row, columnMap.municipio) || 'Sin municipio';
        const clues = this.getCellValue(row, columnMap.clues);
        const nombreUnidad = this.getCellValue(row, columnMap.nombreUnidad);
        const nombreInstitucion = this.getCellValue(row, columnMap.nombreInstitucion);

        // Use the most appropriate name
        const nombre = nombreUnidad || nombreInstitucion || 'Sin nombre';

        // Build address from available components
        const direccion = this.buildAddress(row, columnMap);

        const healthCenter: HealthCenterData = {
          id: clues || `HC_${i}`,
          nombre: nombre,
          direccion: direccion,
          municipio: municipio,
          estado: 'Sonora',
          distrito: this.getCellValue(row, columnMap.jurisdiccion) || this.estimateDistrict(municipio),
          tipo: this.getCellValue(row, columnMap.tipoEstablecimiento) || this.getCellValue(row, columnMap.tipologia) || 'Centro de Salud',
          telefono: this.getCellValue(row, columnMap.telefono1) || this.getCellValue(row, columnMap.telefono2),
          responsable: this.getCellValue(row, columnMap.nombreInstitucion),
          codigo_establecimiento: clues || this.getCellValue(row, columnMap.claveInstitucion) || `EST_${i}`,
          clues: clues,
          lat: lat || this.estimateCoordinates(municipio).lat,
          lng: lng || this.estimateCoordinates(municipio).lng
        };

        // Only add if we have valid coordinates or can estimate them
        if ((lat && lng) || municipio !== 'Sin municipio') {
          healthCenters.push(healthCenter);
        }
      } catch (error) {
        console.warn(`Error parsing row ${i}:`, error, row);
        continue;
      }
    }

    console.log(`Parsed ${healthCenters.length} health centers from Excel`);
    return healthCenters;
  }

  private static createGOBIColumnMap(headers: string[]): Record<string, number> {
    const map: Record<string, number> = {};
    
    headers.forEach((header, index) => {
      const normalizedHeader = header.toString().toLowerCase().trim();
      
      // Map exact GOBI column names
      if (normalizedHeader === 'clues') {
        map.clues = index;
      } else if (normalizedHeader === 'clave de la institucion') {
        map.claveInstitucion = index;
      } else if (normalizedHeader === 'nombre de la institucion') {
        map.nombreInstitucion = index;
      } else if (normalizedHeader === 'clave de la entidad') {
        map.claveEntidad = index;
      } else if (normalizedHeader === 'entidad') {
        map.entidad = index;
      } else if (normalizedHeader === 'clave del municipio') {
        map.claveMunicipio = index;
      } else if (normalizedHeader === 'municipio') {
        map.municipio = index;
      } else if (normalizedHeader === 'clave de la localidad') {
        map.claveLocalidad = index;
      } else if (normalizedHeader === 'localidad') {
        map.localidad = index;
      } else if (normalizedHeader === 'clave de la jurisdiccion') {
        map.claveJurisdiccion = index;
      } else if (normalizedHeader === 'jurisdiccion') {
        map.jurisdiccion = index;
      } else if (normalizedHeader === 'clave del tipo establecimiento') {
        map.claveTipoEstablecimiento = index;
      } else if (normalizedHeader === 'nombre tipo establecimiento') {
        map.tipoEstablecimiento = index;
      } else if (normalizedHeader === 'clave de tipologia') {
        map.claveTipologia = index;
      } else if (normalizedHeader === 'nombre de tipologia') {
        map.tipologia = index;
      } else if (normalizedHeader === 'clave de subtipologia') {
        map.claveSubtipologia = index;
      } else if (normalizedHeader === 'nombre de subtipologia') {
        map.subtipologia = index;
      } else if (normalizedHeader === 'nombre de la unidad') {
        map.nombreUnidad = index;
      } else if (normalizedHeader === 'nombre comercial') {
        map.nombreComercial = index;
      } else if (normalizedHeader === 'clave tipo de vialidad') {
        map.claveTipoVialidad = index;
      } else if (normalizedHeader === 'tipo de vialidad') {
        map.tipoVialidad = index;
      } else if (normalizedHeader === 'vialidad') {
        map.vialidad = index;
      } else if (normalizedHeader === 'numero exterior') {
        map.numeroExterior = index;
      } else if (normalizedHeader === 'numero interior') {
        map.numeroInterior = index;
      } else if (normalizedHeader === 'clave tipo de asentamiento') {
        map.claveTipoAsentamiento = index;
      } else if (normalizedHeader === 'tipo de asentamiento') {
        map.tipoAsentamiento = index;
      } else if (normalizedHeader === 'asentamiento') {
        map.asentamiento = index;
      } else if (normalizedHeader === 'codigo postal') {
        map.codigoPostal = index;
      } else if (normalizedHeader === 'telefono 1 del establecimiento') {
        map.telefono1 = index;
      } else if (normalizedHeader === 'telefono 2 del establecimiento') {
        map.telefono2 = index;
      } else if (normalizedHeader === 'latitud') {
        map.latitud = index;
      } else if (normalizedHeader === 'longitud') {
        map.longitud = index;
      } else if (normalizedHeader === 'nivel atencion') {
        map.nivelAtencion = index;
      } else if (normalizedHeader === 'estatus de operacion') {
        map.estatusOperacion = index;
      }
    });

    return map;
  }

  private static buildAddress(row: any[], columnMap: Record<string, number>): string {
    const addressParts = [];
    
    const tipoVialidad = this.getCellValue(row, columnMap.tipoVialidad);
    const vialidad = this.getCellValue(row, columnMap.vialidad);
    const numeroExterior = this.getCellValue(row, columnMap.numeroExterior);
    const numeroInterior = this.getCellValue(row, columnMap.numeroInterior);
    const tipoAsentamiento = this.getCellValue(row, columnMap.tipoAsentamiento);
    const asentamiento = this.getCellValue(row, columnMap.asentamiento);
    const codigoPostal = this.getCellValue(row, columnMap.codigoPostal);

    // Build street address
    if (tipoVialidad && vialidad) {
      addressParts.push(`${tipoVialidad} ${vialidad}`);
    } else if (vialidad) {
      addressParts.push(vialidad);
    }

    if (numeroExterior) {
      addressParts.push(`#${numeroExterior}`);
    }

    if (numeroInterior) {
      addressParts.push(`Int. ${numeroInterior}`);
    }

    // Add neighborhood/settlement
    if (tipoAsentamiento && asentamiento) {
      addressParts.push(`${tipoAsentamiento} ${asentamiento}`);
    } else if (asentamiento) {
      addressParts.push(asentamiento);
    }

    // Add postal code
    if (codigoPostal) {
      addressParts.push(`CP ${codigoPostal}`);
    }

    return addressParts.length > 0 ? addressParts.join(', ') : 'Sin dirección';
  }

  private static getCellValue(row: any[], index: number): string | undefined {
    if (index === undefined || index < 0 || index >= row.length) {
      return undefined;
    }
    
    const value = row[index];
    if (value === null || value === undefined || value === '') {
      return undefined;
    }
    
    return value.toString().trim();
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
      'san luis rio colorado': { lat: 32.4606, lng: -114.7706 },
      'navojoa': { lat: 27.0667, lng: -109.4333 },
      'guaymas': { lat: 27.9167, lng: -110.9000 },
      'agua prieta': { lat: 31.3333, lng: -109.5500 },
      'puerto peñasco': { lat: 31.3167, lng: -113.5333 },
      'puerto penasco': { lat: 31.3167, lng: -113.5333 },
      'caborca': { lat: 30.7167, lng: -112.1667 },
      'cananea': { lat: 30.9500, lng: -110.3000 },
      'obregon': { lat: 27.4833, lng: -109.9333 },
      'ciudad obregon': { lat: 27.4833, lng: -109.9333 },
      'empalme': { lat: 27.9667, lng: -110.8167 },
      'huatabampo': { lat: 26.8167, lng: -109.6500 },
      'magdalena': { lat: 30.6167, lng: -110.9667 },
      'santa ana': { lat: 30.5500, lng: -111.1167 },
      'altar': { lat: 30.7167, lng: -111.8333 },
      'benjamin hill': { lat: 30.2167, lng: -111.3333 },
      'pitiquito': { lat: 30.6833, lng: -112.0833 },
      'saric': { lat: 31.0833, lng: -111.2833 },
      'tubutama': { lat: 30.9333, lng: -111.6167 },
      'oquitoa': { lat: 30.7500, lng: -111.8833 },
      'atil': { lat: 30.6167, lng: -111.6500 },
      'trincheras': { lat: 30.8167, lng: -111.4167 },
      'cucurpe': { lat: 30.3833, lng: -110.7167 },
      'rayón': { lat: 29.7167, lng: -110.5500 },
      'ures': { lat: 29.4333, lng: -110.3833 },
      'villa pesqueira': { lat: 29.2167, lng: -109.8833 },
      'aconchi': { lat: 29.8000, lng: -110.2833 },
      'san felipe de jesús': { lat: 29.8833, lng: -110.4500 },
      'huépac': { lat: 29.9000, lng: -110.2167 },
      'banámichi': { lat: 29.9833, lng: -110.2333 },
      'arizpe': { lat: 30.3333, lng: -110.1667 },
      'bacoachi': { lat: 30.6167, lng: -109.8333 },
      'fronteras': { lat: 30.9000, lng: -109.6167 },
      'nacozari de garcía': { lat: 30.3833, lng: -109.6833 },
      'moctezuma': { lat: 29.7833, lng: -109.6833 },
      'cumpas': { lat: 30.0167, lng: -109.8167 },
      'villa hidalgo': { lat: 29.8167, lng: -109.4333 },
      'granados': { lat: 29.6167, lng: -109.4833 },
      'huachinera': { lat: 30.2833, lng: -109.3167 },
      'bacadéhuachi': { lat: 29.9167, lng: -109.4000 },
      'nácori chico': { lat: 29.6833, lng: -109.0833 },
      'tepache': { lat: 29.5167, lng: -109.2500 },
      'divisaderos': { lat: 29.3833, lng: -108.9833 },
      'bavispe': { lat: 30.0167, lng: -108.9167 },
      'bacerac': { lat: 30.3167, lng: -109.1833 },
      'huásabas': { lat: 30.1833, lng: -108.7833 },
      'arivechi': { lat: 28.9333, lng: -108.9167 },
      'sahuaripa': { lat: 29.0667, lng: -109.2333 },
      'yécora': { lat: 28.3667, lng: -108.9333 },
      'onavas': { lat: 28.4333, lng: -109.2833 },
      'soyopa': { lat: 28.6167, lng: -109.5833 },
      'san javier': { lat: 28.8167, lng: -109.7167 },
      'suaqui grande': { lat: 29.0833, lng: -109.5833 },
      'la colorada': { lat: 28.8833, lng: -109.5167 },
      'rosario': { lat: 27.9833, lng: -108.9167 },
      'quiriego': { lat: 27.5500, lng: -108.8833 },
      'alamos': { lat: 27.0167, lng: -108.9333 },
      'etchojoa': { lat: 26.7833, lng: -109.6167 }
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

  private static estimateDistrict(municipio: string): string {
    const districtMap: Record<string, string> = {
      'hermosillo': 'Distrito 1',
      'cajeme': 'Distrito 2',
      'navojoa': 'Distrito 2',
      'guaymas': 'Distrito 2',
      'empalme': 'Distrito 2',
      'huatabampo': 'Distrito 2',
      'etchojoa': 'Distrito 2',
      'nogales': 'Distrito 3',
      'agua prieta': 'Distrito 3',
      'magdalena': 'Distrito 3',
      'santa ana': 'Distrito 3',
      'fronteras': 'Distrito 3',
      'nacozari de garcía': 'Distrito 3',
      'cananea': 'Distrito 3',
      'san luis río colorado': 'Distrito 4',
      'san luis rio colorado': 'Distrito 4',
      'puerto peñasco': 'Distrito 4',
      'caborca': 'Distrito 4',
      'altar': 'Distrito 4',
      'pitiquito': 'Distrito 4',
      'obregon': 'Distrito 2',
      'ciudad obregon': 'Distrito 2'
    };

    const normalizedMunicipio = municipio.toLowerCase().trim();
    
    for (const [key, district] of Object.entries(districtMap)) {
      if (normalizedMunicipio.includes(key)) {
        return district;
      }
    }

    return 'Distrito no identificado';
  }
}