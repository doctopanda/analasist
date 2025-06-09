export interface GeolocationResult {
  lat: number;
  lng: number;
  accuracy: 'exact' | 'approximate' | 'estimated';
  source: 'coordinates' | 'geocoded' | 'estimated';
  address?: string;
}

export interface GeolocationValidation {
  isValid: boolean;
  accuracy: number; // 0-100 score
  issues: string[];
  suggestions: string[];
}

export class GeocodingService {
  private static readonly SONORA_BOUNDS = {
    north: 32.5,
    south: 26.0,
    east: -108.0,
    west: -115.0
  };

  private static readonly MUNICIPALITY_COORDS: Record<string, { lat: number; lng: number; radius: number }> = {
    'hermosillo': { lat: 29.0729, lng: -110.9559, radius: 0.5 },
    'cajeme': { lat: 27.3833, lng: -109.9167, radius: 0.3 },
    'ciudad obregon': { lat: 27.4833, lng: -109.9333, radius: 0.3 },
    'nogales': { lat: 31.3081, lng: -110.9342, radius: 0.2 },
    'san luis río colorado': { lat: 32.4606, lng: -114.7706, radius: 0.3 },
    'san luis rio colorado': { lat: 32.4606, lng: -114.7706, radius: 0.3 },
    'navojoa': { lat: 27.0667, lng: -109.4333, radius: 0.2 },
    'guaymas': { lat: 27.9167, lng: -110.9000, radius: 0.3 },
    'agua prieta': { lat: 31.3333, lng: -109.5500, radius: 0.2 },
    'puerto peñasco': { lat: 31.3167, lng: -113.5333, radius: 0.2 },
    'puerto penasco': { lat: 31.3167, lng: -113.5333, radius: 0.2 },
    'caborca': { lat: 30.7167, lng: -112.1667, radius: 0.3 },
    'cananea': { lat: 30.9500, lng: -110.3000, radius: 0.2 },
    'empalme': { lat: 27.9667, lng: -110.8167, radius: 0.1 },
    'huatabampo': { lat: 26.8167, lng: -109.6500, radius: 0.2 },
    'magdalena': { lat: 30.6167, lng: -110.9667, radius: 0.2 },
    'santa ana': { lat: 30.5500, lng: -111.1167, radius: 0.1 },
    'altar': { lat: 30.7167, lng: -111.8333, radius: 0.2 },
    'benjamin hill': { lat: 30.2167, lng: -111.3333, radius: 0.1 },
    'pitiquito': { lat: 30.6833, lng: -112.0833, radius: 0.1 },
    'saric': { lat: 31.0833, lng: -111.2833, radius: 0.1 },
    'tubutama': { lat: 30.9333, lng: -111.6167, radius: 0.1 },
    'oquitoa': { lat: 30.7500, lng: -111.8833, radius: 0.1 },
    'atil': { lat: 30.6167, lng: -111.6500, radius: 0.1 },
    'trincheras': { lat: 30.8167, lng: -111.4167, radius: 0.1 },
    'cucurpe': { lat: 30.3833, lng: -110.7167, radius: 0.1 },
    'rayón': { lat: 29.7167, lng: -110.5500, radius: 0.1 },
    'ures': { lat: 29.4333, lng: -110.3833, radius: 0.1 },
    'villa pesqueira': { lat: 29.2167, lng: -109.8833, radius: 0.1 },
    'aconchi': { lat: 29.8000, lng: -110.2833, radius: 0.1 },
    'san felipe de jesús': { lat: 29.8833, lng: -110.4500, radius: 0.1 },
    'huépac': { lat: 29.9000, lng: -110.2167, radius: 0.1 },
    'banámichi': { lat: 29.9833, lng: -110.2333, radius: 0.1 },
    'arizpe': { lat: 30.3333, lng: -110.1667, radius: 0.1 },
    'bacoachi': { lat: 30.6167, lng: -109.8333, radius: 0.1 },
    'fronteras': { lat: 30.9000, lng: -109.6167, radius: 0.1 },
    'nacozari de garcía': { lat: 30.3833, lng: -109.6833, radius: 0.1 },
    'moctezuma': { lat: 29.7833, lng: -109.6833, radius: 0.1 },
    'cumpas': { lat: 30.0167, lng: -109.8167, radius: 0.1 },
    'villa hidalgo': { lat: 29.8167, lng: -109.4333, radius: 0.1 },
    'granados': { lat: 29.6167, lng: -109.4833, radius: 0.1 },
    'huachinera': { lat: 30.2833, lng: -109.3167, radius: 0.1 },
    'bacadéhuachi': { lat: 29.9167, lng: -109.4000, radius: 0.1 },
    'nácori chico': { lat: 29.6833, lng: -109.0833, radius: 0.1 },
    'tepache': { lat: 29.5167, lng: -109.2500, radius: 0.1 },
    'divisaderos': { lat: 29.3833, lng: -108.9833, radius: 0.1 },
    'bavispe': { lat: 30.0167, lng: -108.9167, radius: 0.1 },
    'bacerac': { lat: 30.3167, lng: -109.1833, radius: 0.1 },
    'huásabas': { lat: 30.1833, lng: -108.7833, radius: 0.1 },
    'arivechi': { lat: 28.9333, lng: -108.9167, radius: 0.1 },
    'sahuaripa': { lat: 29.0667, lng: -109.2333, radius: 0.1 },
    'yécora': { lat: 28.3667, lng: -108.9333, radius: 0.1 },
    'onavas': { lat: 28.4333, lng: -109.2833, radius: 0.1 },
    'soyopa': { lat: 28.6167, lng: -109.5833, radius: 0.1 },
    'san javier': { lat: 28.8167, lng: -109.7167, radius: 0.1 },
    'suaqui grande': { lat: 29.0833, lng: -109.5833, radius: 0.1 },
    'la colorada': { lat: 28.8833, lng: -109.5167, radius: 0.1 },
    'rosario': { lat: 27.9833, lng: -108.9167, radius: 0.1 },
    'quiriego': { lat: 27.5500, lng: -108.8833, radius: 0.1 },
    'alamos': { lat: 27.0167, lng: -108.9333, radius: 0.1 },
    'etchojoa': { lat: 26.7833, lng: -109.6167, radius: 0.1 }
  };

  /**
   * Validates if coordinates are within Sonora state bounds
   */
  static isWithinSonora(lat: number, lng: number): boolean {
    return lat >= this.SONORA_BOUNDS.south &&
           lat <= this.SONORA_BOUNDS.north &&
           lng >= this.SONORA_BOUNDS.west &&
           lng <= this.SONORA_BOUNDS.east;
  }

  /**
   * Validates coordinates against municipality bounds
   */
  static validateMunicipalityCoordinates(lat: number, lng: number, municipio: string): GeolocationValidation {
    const normalizedMunicipio = municipio.toLowerCase().trim();
    const municipalityData = this.MUNICIPALITY_COORDS[normalizedMunicipio];
    
    const validation: GeolocationValidation = {
      isValid: true,
      accuracy: 100,
      issues: [],
      suggestions: []
    };

    // Check if coordinates are within Sonora
    if (!this.isWithinSonora(lat, lng)) {
      validation.isValid = false;
      validation.accuracy = 0;
      validation.issues.push('Las coordenadas están fuera del estado de Sonora');
      validation.suggestions.push('Verificar que las coordenadas correspondan a una ubicación en Sonora');
      return validation;
    }

    // Check municipality-specific validation
    if (municipalityData) {
      const distance = this.calculateDistance(lat, lng, municipalityData.lat, municipalityData.lng);
      
      if (distance > municipalityData.radius) {
        validation.isValid = false;
        validation.accuracy = Math.max(0, 100 - (distance * 100));
        validation.issues.push(`Las coordenadas están a ${distance.toFixed(2)}km del centro de ${municipio}`);
        validation.suggestions.push(`Verificar que la ubicación esté dentro del municipio de ${municipio}`);
      } else {
        validation.accuracy = Math.max(50, 100 - (distance * 50));
      }
    } else {
      validation.accuracy = 70; // Lower accuracy for unknown municipalities
      validation.issues.push(`Municipio "${municipio}" no reconocido en la base de datos`);
      validation.suggestions.push('Verificar la ortografía del nombre del municipio');
    }

    return validation;
  }

  /**
   * Attempts to improve coordinates using various methods
   */
  static async improveCoordinates(
    currentLat: number,
    currentLng: number,
    municipio: string,
    direccion?: string
  ): Promise<GeolocationResult> {
    // First, validate current coordinates
    const validation = this.validateMunicipalityCoordinates(currentLat, currentLng, municipio);
    
    if (validation.isValid && validation.accuracy > 80) {
      return {
        lat: currentLat,
        lng: currentLng,
        accuracy: 'exact',
        source: 'coordinates'
      };
    }

    // Try to geocode the address if available
    if (direccion) {
      try {
        const geocoded = await this.geocodeAddress(direccion, municipio);
        if (geocoded) {
          const geocodedValidation = this.validateMunicipalityCoordinates(geocoded.lat, geocoded.lng, municipio);
          if (geocodedValidation.isValid) {
            return {
              lat: geocoded.lat,
              lng: geocoded.lng,
              accuracy: 'approximate',
              source: 'geocoded',
              address: `${direccion}, ${municipio}, Sonora, México`
            };
          }
        }
      } catch (error) {
        console.warn('Geocoding failed:', error);
      }
    }

    // Fall back to municipality center
    const municipalityCoords = this.getMunicipalityCenter(municipio);
    return {
      lat: municipalityCoords.lat,
      lng: municipalityCoords.lng,
      accuracy: 'estimated',
      source: 'estimated'
    };
  }

  /**
   * Geocodes an address using a mock geocoding service
   * In a real application, this would use Google Maps Geocoding API or similar
   */
  static async geocodeAddress(direccion: string, municipio: string): Promise<{ lat: number; lng: number } | null> {
    // Mock geocoding - in a real app, use actual geocoding service
    const fullAddress = `${direccion}, ${municipio}, Sonora, México`;
    
    // For demonstration, we'll use a simple pattern matching approach
    const municipalityCoords = this.getMunicipalityCenter(municipio);
    
    // Add some random offset to simulate address-specific coordinates
    const offsetLat = (Math.random() - 0.5) * 0.02; // ~1km max offset
    const offsetLng = (Math.random() - 0.5) * 0.02;
    
    return {
      lat: municipalityCoords.lat + offsetLat,
      lng: municipalityCoords.lng + offsetLng
    };
  }

  /**
   * Gets the center coordinates for a municipality
   */
  static getMunicipalityCenter(municipio: string): { lat: number; lng: number } {
    const normalizedMunicipio = municipio.toLowerCase().trim();
    const municipalityData = this.MUNICIPALITY_COORDS[normalizedMunicipio];
    
    if (municipalityData) {
      return { lat: municipalityData.lat, lng: municipalityData.lng };
    }

    // Default to Hermosillo if municipality not found
    return { lat: 29.0729, lng: -110.9559 };
  }

  /**
   * Calculates distance between two points in kilometers
   */
  static calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }

  /**
   * Validates and corrects a batch of health centers
   */
  static async validateHealthCenters(centers: any[]): Promise<{
    validated: any[];
    issues: { centerId: string; issues: string[]; suggestions: string[] }[];
    statistics: {
      total: number;
      valid: number;
      corrected: number;
      estimated: number;
    };
  }> {
    const validated = [];
    const issues = [];
    let correctedCount = 0;
    let estimatedCount = 0;

    for (const center of centers) {
      const validation = this.validateMunicipalityCoordinates(center.lat, center.lng, center.municipio);
      
      if (!validation.isValid || validation.accuracy < 70) {
        try {
          const improved = await this.improveCoordinates(
            center.lat,
            center.lng,
            center.municipio,
            center.direccion
          );

          const updatedCenter = {
            ...center,
            lat: improved.lat,
            lng: improved.lng,
            geolocation_accuracy: improved.accuracy,
            geolocation_source: improved.source
          };

          validated.push(updatedCenter);

          if (improved.source === 'geocoded') {
            correctedCount++;
          } else if (improved.source === 'estimated') {
            estimatedCount++;
          }

          if (validation.issues.length > 0) {
            issues.push({
              centerId: center.id,
              issues: validation.issues,
              suggestions: validation.suggestions
            });
          }
        } catch (error) {
          // Keep original coordinates if improvement fails
          validated.push({
            ...center,
            geolocation_accuracy: 'unknown',
            geolocation_source: 'original'
          });
          
          issues.push({
            centerId: center.id,
            issues: ['No se pudieron mejorar las coordenadas'],
            suggestions: ['Verificar manualmente la ubicación']
          });
        }
      } else {
        validated.push({
          ...center,
          geolocation_accuracy: validation.accuracy > 90 ? 'exact' : 'approximate',
          geolocation_source: 'validated'
        });
      }
    }

    return {
      validated,
      issues,
      statistics: {
        total: centers.length,
        valid: centers.length - issues.length,
        corrected: correctedCount,
        estimated: estimatedCount
      }
    };
  }

  /**
   * Generates a geolocation quality report
   */
  static generateQualityReport(centers: any[]): {
    overall: {
      total: number;
      withinSonora: number;
      accurateCoordinates: number;
      estimatedCoordinates: number;
      qualityScore: number;
    };
    byMunicipality: Record<string, {
      total: number;
      accurate: number;
      estimated: number;
      qualityScore: number;
    }>;
    recommendations: string[];
  } {
    const overall = {
      total: centers.length,
      withinSonora: 0,
      accurateCoordinates: 0,
      estimatedCoordinates: 0,
      qualityScore: 0
    };

    const byMunicipality: Record<string, any> = {};
    const recommendations: string[] = [];

    for (const center of centers) {
      // Check if within Sonora
      if (this.isWithinSonora(center.lat, center.lng)) {
        overall.withinSonora++;
      }

      // Validate coordinates
      const validation = this.validateMunicipalityCoordinates(center.lat, center.lng, center.municipio);
      
      if (validation.accuracy > 80) {
        overall.accurateCoordinates++;
      } else if (validation.accuracy < 50) {
        overall.estimatedCoordinates++;
      }

      // Track by municipality
      if (!byMunicipality[center.municipio]) {
        byMunicipality[center.municipio] = {
          total: 0,
          accurate: 0,
          estimated: 0,
          qualityScore: 0
        };
      }

      byMunicipality[center.municipio].total++;
      
      if (validation.accuracy > 80) {
        byMunicipality[center.municipio].accurate++;
      } else if (validation.accuracy < 50) {
        byMunicipality[center.municipio].estimated++;
      }
    }

    // Calculate quality scores
    overall.qualityScore = Math.round((overall.accurateCoordinates / overall.total) * 100);

    for (const municipality in byMunicipality) {
      const data = byMunicipality[municipality];
      data.qualityScore = Math.round((data.accurate / data.total) * 100);
    }

    // Generate recommendations
    if (overall.qualityScore < 70) {
      recommendations.push('Se recomienda validar y corregir las coordenadas de los centros de salud');
    }

    if (overall.estimatedCoordinates > overall.total * 0.3) {
      recommendations.push('Más del 30% de las coordenadas son estimadas - considerar geocodificación manual');
    }

    if (overall.withinSonora < overall.total) {
      recommendations.push(`${overall.total - overall.withinSonora} centros tienen coordenadas fuera de Sonora`);
    }

    return {
      overall,
      byMunicipality,
      recommendations
    };
  }
}