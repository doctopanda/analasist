export interface GeolocationResult {
  lat: number;
  lng: number;
  accuracy: 'exact' | 'approximate' | 'estimated';
  source: 'coordinates' | 'geocoded' | 'estimated';
  address?: string;
  confidence: number; // 0-100 confidence score
}

export interface GeolocationValidation {
  isValid: boolean;
  accuracy: number; // 0-100 score
  issues: string[];
  suggestions: string[];
  distanceFromCenter: number; // km from municipality center
}

export class GeocodingService {
  private static readonly SONORA_BOUNDS = {
    north: 32.5,
    south: 26.0,
    east: -108.0,
    west: -115.0
  };

  private static readonly MUNICIPALITY_COORDS: Record<string, { lat: number; lng: number; radius: number }> = {
    'hermosillo': { lat: 29.0729, lng: -110.9559, radius: 0.8 },
    'cajeme': { lat: 27.3833, lng: -109.9167, radius: 0.5 },
    'ciudad obregon': { lat: 27.4833, lng: -109.9333, radius: 0.5 },
    'nogales': { lat: 31.3081, lng: -110.9342, radius: 0.3 },
    'san luis río colorado': { lat: 32.4606, lng: -114.7706, radius: 0.4 },
    'san luis rio colorado': { lat: 32.4606, lng: -114.7706, radius: 0.4 },
    'navojoa': { lat: 27.0667, lng: -109.4333, radius: 0.3 },
    'guaymas': { lat: 27.9167, lng: -110.9000, radius: 0.4 },
    'agua prieta': { lat: 31.3333, lng: -109.5500, radius: 0.2 },
    'puerto peñasco': { lat: 31.3167, lng: -113.5333, radius: 0.3 },
    'puerto penasco': { lat: 31.3167, lng: -113.5333, radius: 0.3 },
    'caborca': { lat: 30.7167, lng: -112.1667, radius: 0.4 },
    'cananea': { lat: 30.9500, lng: -110.3000, radius: 0.3 },
    'empalme': { lat: 27.9667, lng: -110.8167, radius: 0.2 },
    'huatabampo': { lat: 26.8167, lng: -109.6500, radius: 0.3 },
    'magdalena': { lat: 30.6167, lng: -110.9667, radius: 0.2 },
    'santa ana': { lat: 30.5500, lng: -111.1167, radius: 0.2 },
    'altar': { lat: 30.7167, lng: -111.8333, radius: 0.3 },
    'benjamin hill': { lat: 30.2167, lng: -111.3333, radius: 0.2 },
    'pitiquito': { lat: 30.6833, lng: -112.0833, radius: 0.2 },
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
   * Validates coordinates against municipality bounds and address information
   */
  static validateCoordinatesWithAddress(
    lat: number, 
    lng: number, 
    municipio: string, 
    direccion?: string
  ): GeolocationValidation {
    const normalizedMunicipio = municipio.toLowerCase().trim();
    const municipalityData = this.MUNICIPALITY_COORDS[normalizedMunicipio];
    
    const validation: GeolocationValidation = {
      isValid: true,
      accuracy: 100,
      issues: [],
      suggestions: [],
      distanceFromCenter: 0
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
      validation.distanceFromCenter = distance;
      
      if (distance > municipalityData.radius) {
        validation.isValid = false;
        validation.accuracy = Math.max(0, 100 - (distance * 50));
        validation.issues.push(`Las coordenadas están a ${distance.toFixed(2)}km del centro de ${municipio}`);
        validation.suggestions.push(`Verificar que la ubicación esté dentro del municipio de ${municipio}`);
        
        // If we have an address, suggest geocoding
        if (direccion) {
          validation.suggestions.push('Intentar geocodificar usando la dirección proporcionada');
        }
      } else {
        // Calculate accuracy based on distance from center
        validation.accuracy = Math.max(60, 100 - (distance * 40));
        
        if (distance > municipalityData.radius * 0.7) {
          validation.issues.push(`Ubicación en el límite del municipio (${distance.toFixed(2)}km del centro)`);
        }
      }
    } else {
      validation.accuracy = 50; // Lower accuracy for unknown municipalities
      validation.issues.push(`Municipio "${municipio}" no reconocido en la base de datos`);
      validation.suggestions.push('Verificar la ortografía del nombre del municipio');
    }

    // Additional validation based on address patterns
    if (direccion) {
      const addressValidation = this.validateAddressPattern(direccion, municipio);
      if (!addressValidation.isValid) {
        validation.issues.push(...addressValidation.issues);
        validation.suggestions.push(...addressValidation.suggestions);
        validation.accuracy = Math.min(validation.accuracy, addressValidation.accuracy);
      }
    }

    return validation;
  }

  /**
   * Validates address patterns for consistency
   */
  private static validateAddressPattern(direccion: string, municipio: string): GeolocationValidation {
    const validation: GeolocationValidation = {
      isValid: true,
      accuracy: 100,
      issues: [],
      suggestions: [],
      distanceFromCenter: 0
    };

    const normalizedAddress = direccion.toLowerCase();
    const normalizedMunicipio = municipio.toLowerCase();

    // Check if address contains municipality name (common inconsistency)
    if (normalizedAddress.includes(normalizedMunicipio)) {
      validation.accuracy = 90; // Slightly lower accuracy but still good
    }

    // Check for common address patterns
    const hasStreetNumber = /\d+/.test(direccion);
    const hasStreetType = /(calle|avenida|boulevard|blvd|av\.|c\.)/.test(normalizedAddress);
    
    if (!hasStreetNumber && !hasStreetType) {
      validation.accuracy = 70;
      validation.issues.push('Dirección incompleta - falta número o tipo de vialidad');
      validation.suggestions.push('Verificar que la dirección incluya número y tipo de calle');
    }

    // Check for postal code
    const hasPostalCode = /\d{5}/.test(direccion);
    if (!hasPostalCode) {
      validation.accuracy = Math.min(validation.accuracy, 80);
      validation.suggestions.push('Considerar agregar código postal para mayor precisión');
    }

    return validation;
  }

  /**
   * Attempts to improve coordinates using address geocoding and validation
   */
  static async improveCoordinatesWithAddress(
    currentLat: number,
    currentLng: number,
    municipio: string,
    direccion?: string
  ): Promise<GeolocationResult> {
    // First, validate current coordinates with address
    const validation = this.validateCoordinatesWithAddress(currentLat, currentLng, municipio, direccion);
    
    if (validation.isValid && validation.accuracy > 85) {
      return {
        lat: currentLat,
        lng: currentLng,
        accuracy: 'exact',
        source: 'coordinates',
        confidence: validation.accuracy
      };
    }

    // Try to geocode the address if available
    if (direccion) {
      try {
        const geocoded = await this.geocodeAddressAdvanced(direccion, municipio);
        if (geocoded) {
          const geocodedValidation = this.validateCoordinatesWithAddress(
            geocoded.lat, 
            geocoded.lng, 
            municipio, 
            direccion
          );
          
          if (geocodedValidation.isValid && geocodedValidation.accuracy > validation.accuracy) {
            return {
              lat: geocoded.lat,
              lng: geocoded.lng,
              accuracy: 'approximate',
              source: 'geocoded',
              address: `${direccion}, ${municipio}, Sonora, México`,
              confidence: geocodedValidation.accuracy
            };
          }
        }
      } catch (error) {
        console.warn('Advanced geocoding failed:', error);
      }
    }

    // Try to improve using nearby landmarks or known locations
    const improved = this.improveUsingLandmarks(currentLat, currentLng, municipio, direccion);
    if (improved) {
      const improvedValidation = this.validateCoordinatesWithAddress(
        improved.lat, 
        improved.lng, 
        municipio, 
        direccion
      );
      
      if (improvedValidation.accuracy > validation.accuracy) {
        return {
          lat: improved.lat,
          lng: improved.lng,
          accuracy: 'approximate',
          source: 'geocoded',
          confidence: improvedValidation.accuracy
        };
      }
    }

    // Fall back to municipality center with offset based on address
    const municipalityCoords = this.getMunicipalityCenter(municipio);
    const offset = this.calculateAddressOffset(direccion);
    
    return {
      lat: municipalityCoords.lat + offset.lat,
      lng: municipalityCoords.lng + offset.lng,
      accuracy: 'estimated',
      source: 'estimated',
      confidence: 50
    };
  }

  /**
   * Advanced geocoding using address components and patterns
   */
  static async geocodeAddressAdvanced(direccion: string, municipio: string): Promise<{ lat: number; lng: number } | null> {
    // Parse address components
    const addressComponents = this.parseAddressComponents(direccion);
    const municipalityCoords = this.getMunicipalityCenter(municipio);
    
    // Calculate offset based on address components
    let offsetLat = 0;
    let offsetLng = 0;
    
    // Use street name patterns to estimate location within municipality
    if (addressComponents.streetName) {
      const streetOffset = this.getStreetOffset(addressComponents.streetName, municipio);
      offsetLat += streetOffset.lat;
      offsetLng += streetOffset.lng;
    }
    
    // Use street number to estimate position along street
    if (addressComponents.streetNumber) {
      const numberOffset = this.getNumberOffset(addressComponents.streetNumber);
      offsetLat += numberOffset.lat;
      offsetLng += numberOffset.lng;
    }
    
    // Use neighborhood/colony information if available
    if (addressComponents.neighborhood) {
      const neighborhoodOffset = this.getNeighborhoodOffset(addressComponents.neighborhood, municipio);
      offsetLat += neighborhoodOffset.lat;
      offsetLng += neighborhoodOffset.lng;
    }
    
    return {
      lat: municipalityCoords.lat + offsetLat,
      lng: municipalityCoords.lng + offsetLng
    };
  }

  /**
   * Parses address into components
   */
  private static parseAddressComponents(direccion: string): {
    streetType?: string;
    streetName?: string;
    streetNumber?: number;
    neighborhood?: string;
    postalCode?: string;
  } {
    const components: any = {};
    
    // Extract street number
    const numberMatch = direccion.match(/\b(\d+)\b/);
    if (numberMatch) {
      components.streetNumber = parseInt(numberMatch[1]);
    }
    
    // Extract street type
    const streetTypeMatch = direccion.match(/(calle|avenida|boulevard|blvd|av\.|c\.)\s+([^,\d]+)/i);
    if (streetTypeMatch) {
      components.streetType = streetTypeMatch[1];
      components.streetName = streetTypeMatch[2].trim();
    }
    
    // Extract neighborhood/colony
    const neighborhoodMatch = direccion.match(/(?:col\.|colonia|fracc\.|fraccionamiento)\s+([^,]+)/i);
    if (neighborhoodMatch) {
      components.neighborhood = neighborhoodMatch[1].trim();
    }
    
    // Extract postal code
    const postalMatch = direccion.match(/\b(\d{5})\b/);
    if (postalMatch) {
      components.postalCode = postalMatch[1];
    }
    
    return components;
  }

  /**
   * Gets offset based on street name patterns
   */
  private static getStreetOffset(streetName: string, municipio: string): { lat: number; lng: number } {
    const normalizedStreet = streetName.toLowerCase();
    
    // Common street patterns and their typical locations
    const streetPatterns = {
      'centro': { lat: 0, lng: 0 },
      'norte': { lat: 0.01, lng: 0 },
      'sur': { lat: -0.01, lng: 0 },
      'oriente': { lat: 0, lng: 0.01 },
      'poniente': { lat: 0, lng: -0.01 },
      'industrial': { lat: -0.005, lng: 0.005 },
      'residencial': { lat: 0.005, lng: 0.005 },
      'popular': { lat: -0.003, lng: -0.003 }
    };
    
    for (const [pattern, offset] of Object.entries(streetPatterns)) {
      if (normalizedStreet.includes(pattern)) {
        return offset;
      }
    }
    
    return { lat: 0, lng: 0 };
  }

  /**
   * Gets offset based on street number
   */
  private static getNumberOffset(streetNumber: number): { lat: number; lng: number } {
    // Estimate position based on street number
    // Lower numbers typically closer to center, higher numbers further out
    const factor = Math.min(streetNumber / 1000, 1) * 0.005;
    
    return {
      lat: (Math.random() - 0.5) * factor,
      lng: (Math.random() - 0.5) * factor
    };
  }

  /**
   * Gets offset based on neighborhood
   */
  private static getNeighborhoodOffset(neighborhood: string, municipio: string): { lat: number; lng: number } {
    // Known neighborhoods and their approximate locations relative to city center
    const neighborhoodOffsets: Record<string, { lat: number; lng: number }> = {
      'centro': { lat: 0, lng: 0 },
      'villa de seris': { lat: 0.02, lng: 0.01 },
      'san benito': { lat: -0.01, lng: 0.02 },
      'pitic': { lat: 0.01, lng: -0.01 },
      'modelo': { lat: 0.015, lng: 0.005 }
    };
    
    const normalizedNeighborhood = neighborhood.toLowerCase();
    
    for (const [name, offset] of Object.entries(neighborhoodOffsets)) {
      if (normalizedNeighborhood.includes(name)) {
        return offset;
      }
    }
    
    return { lat: 0, lng: 0 };
  }

  /**
   * Improves coordinates using known landmarks
   */
  private static improveUsingLandmarks(
    lat: number, 
    lng: number, 
    municipio: string, 
    direccion?: string
  ): { lat: number; lng: number } | null {
    if (!direccion) return null;
    
    const normalizedAddress = direccion.toLowerCase();
    
    // Known landmarks and their coordinates
    const landmarks = {
      'hospital general': { lat: 29.0729, lng: -110.9559 },
      'palacio municipal': { lat: 29.0892, lng: -110.9618 },
      'universidad de sonora': { lat: 29.0729, lng: -110.9559 },
      'aeropuerto': { lat: 29.0959, lng: -111.0478 },
      'plaza zaragoza': { lat: 29.0892, lng: -110.9618 }
    };
    
    for (const [landmark, coords] of Object.entries(landmarks)) {
      if (normalizedAddress.includes(landmark)) {
        // Add small random offset to avoid exact duplication
        return {
          lat: coords.lat + (Math.random() - 0.5) * 0.002,
          lng: coords.lng + (Math.random() - 0.5) * 0.002
        };
      }
    }
    
    return null;
  }

  /**
   * Calculates address-based offset for municipality center
   */
  private static calculateAddressOffset(direccion?: string): { lat: number; lng: number } {
    if (!direccion) {
      return { lat: 0, lng: 0 };
    }
    
    // Generate deterministic but varied offset based on address
    const hash = this.simpleHash(direccion);
    const factor = 0.01; // ~1km max offset
    
    return {
      lat: ((hash % 200) - 100) / 100 * factor,
      lng: (((hash * 7) % 200) - 100) / 100 * factor
    };
  }

  /**
   * Simple hash function for consistent offsets
   */
  private static simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
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
   * Validates and corrects a batch of health centers using address information
   */
  static async validateHealthCentersWithAddresses(centers: any[]): Promise<{
    validated: any[];
    issues: { centerId: string; issues: string[]; suggestions: string[] }[];
    statistics: {
      total: number;
      valid: number;
      corrected: number;
      estimated: number;
      averageAccuracy: number;
    };
  }> {
    const validated = [];
    const issues = [];
    let correctedCount = 0;
    let estimatedCount = 0;
    let totalAccuracy = 0;

    for (const center of centers) {
      const validation = this.validateCoordinatesWithAddress(
        center.lat, 
        center.lng, 
        center.municipio, 
        center.direccion
      );
      
      if (!validation.isValid || validation.accuracy < 70) {
        try {
          const improved = await this.improveCoordinatesWithAddress(
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
            geolocation_source: improved.source,
            geolocation_confidence: improved.confidence,
            original_lat: center.lat,
            original_lng: center.lng
          };

          validated.push(updatedCenter);
          totalAccuracy += improved.confidence;

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
            geolocation_source: 'original',
            geolocation_confidence: validation.accuracy
          });
          
          totalAccuracy += validation.accuracy;
          
          issues.push({
            centerId: center.id,
            issues: ['No se pudieron mejorar las coordenadas'],
            suggestions: ['Verificar manualmente la ubicación y dirección']
          });
        }
      } else {
        validated.push({
          ...center,
          geolocation_accuracy: validation.accuracy > 90 ? 'exact' : 'approximate',
          geolocation_source: 'validated',
          geolocation_confidence: validation.accuracy
        });
        totalAccuracy += validation.accuracy;
      }
    }

    return {
      validated,
      issues,
      statistics: {
        total: centers.length,
        valid: centers.length - issues.length,
        corrected: correctedCount,
        estimated: estimatedCount,
        averageAccuracy: Math.round(totalAccuracy / centers.length)
      }
    };
  }

  /**
   * Generates a comprehensive geolocation quality report with address analysis
   */
  static generateDetailedQualityReport(centers: any[]): {
    overall: {
      total: number;
      withinSonora: number;
      accurateCoordinates: number;
      estimatedCoordinates: number;
      withAddresses: number;
      averageAccuracy: number;
      qualityScore: number;
    };
    byMunicipality: Record<string, {
      total: number;
      accurate: number;
      estimated: number;
      withAddresses: number;
      averageDistance: number;
      qualityScore: number;
    }>;
    addressAnalysis: {
      completeAddresses: number;
      partialAddresses: number;
      noAddresses: number;
      addressQualityScore: number;
    };
    recommendations: string[];
  } {
    const overall = {
      total: centers.length,
      withinSonora: 0,
      accurateCoordinates: 0,
      estimatedCoordinates: 0,
      withAddresses: 0,
      averageAccuracy: 0,
      qualityScore: 0
    };

    const byMunicipality: Record<string, any> = {};
    const addressAnalysis = {
      completeAddresses: 0,
      partialAddresses: 0,
      noAddresses: 0,
      addressQualityScore: 0
    };
    const recommendations: string[] = [];
    let totalAccuracy = 0;

    for (const center of centers) {
      // Check if within Sonora
      if (this.isWithinSonora(center.lat, center.lng)) {
        overall.withinSonora++;
      }

      // Validate coordinates with address
      const validation = this.validateCoordinatesWithAddress(
        center.lat, 
        center.lng, 
        center.municipio, 
        center.direccion
      );
      
      totalAccuracy += validation.accuracy;
      
      if (validation.accuracy > 80) {
        overall.accurateCoordinates++;
      } else if (validation.accuracy < 50) {
        overall.estimatedCoordinates++;
      }

      // Address analysis
      if (center.direccion) {
        overall.withAddresses++;
        const addressComponents = this.parseAddressComponents(center.direccion);
        
        if (addressComponents.streetName && addressComponents.streetNumber) {
          addressAnalysis.completeAddresses++;
        } else if (addressComponents.streetName || addressComponents.streetNumber) {
          addressAnalysis.partialAddresses++;
        }
      } else {
        addressAnalysis.noAddresses++;
      }

      // Track by municipality
      if (!byMunicipality[center.municipio]) {
        byMunicipality[center.municipio] = {
          total: 0,
          accurate: 0,
          estimated: 0,
          withAddresses: 0,
          totalDistance: 0,
          averageDistance: 0,
          qualityScore: 0
        };
      }

      const municipalityData = byMunicipality[center.municipio];
      municipalityData.total++;
      municipalityData.totalDistance += validation.distanceFromCenter;
      
      if (validation.accuracy > 80) {
        municipalityData.accurate++;
      } else if (validation.accuracy < 50) {
        municipalityData.estimated++;
      }
      
      if (center.direccion) {
        municipalityData.withAddresses++;
      }
    }

    // Calculate averages and scores
    overall.averageAccuracy = Math.round(totalAccuracy / overall.total);
    overall.qualityScore = Math.round((overall.accurateCoordinates / overall.total) * 100);

    addressAnalysis.addressQualityScore = Math.round(
      ((addressAnalysis.completeAddresses * 100) + (addressAnalysis.partialAddresses * 50)) / 
      overall.total
    );

    for (const municipality in byMunicipality) {
      const data = byMunicipality[municipality];
      data.averageDistance = Math.round((data.totalDistance / data.total) * 100) / 100;
      data.qualityScore = Math.round((data.accurate / data.total) * 100);
      delete data.totalDistance; // Remove intermediate calculation
    }

    // Generate recommendations
    if (overall.qualityScore < 70) {
      recommendations.push('Se recomienda validar y corregir las coordenadas de los centros de salud');
    }

    if (overall.estimatedCoordinates > overall.total * 0.3) {
      recommendations.push('Más del 30% de las coordenadas son estimadas - considerar geocodificación con direcciones');
    }

    if (overall.withinSonora < overall.total) {
      recommendations.push(`${overall.total - overall.withinSonora} centros tienen coordenadas fuera de Sonora`);
    }

    if (addressAnalysis.noAddresses > overall.total * 0.2) {
      recommendations.push('Más del 20% de los centros no tienen dirección - agregar direcciones mejorará la precisión');
    }

    if (addressAnalysis.addressQualityScore < 60) {
      recommendations.push('Mejorar la calidad de las direcciones (agregar números y tipos de vialidad)');
    }

    if (overall.averageAccuracy < 75) {
      recommendations.push('La precisión promedio es baja - considerar validación manual de ubicaciones');
    }

    return {
      overall,
      byMunicipality,
      addressAnalysis,
      recommendations
    };
  }
}