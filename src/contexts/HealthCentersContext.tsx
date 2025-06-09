import React, { createContext, useState, useContext, useEffect } from 'react';
import { HealthCenterData } from '../services/excelService';

interface HealthCentersContextType {
  centers: HealthCenterData[];
  setCenters: (centers: HealthCenterData[]) => void;
  addCenters: (newCenters: HealthCenterData[]) => void;
  updateCenter: (id: string, updatedCenter: Partial<HealthCenterData>) => void;
  deleteCenter: (id: string) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

const HealthCentersContext = createContext<HealthCentersContextType | undefined>(undefined);

export const HealthCentersProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [centers, setCentersState] = useState<HealthCenterData[]>([]);
  const [loading, setLoading] = useState(false);

  // Load centers from localStorage on mount
  useEffect(() => {
    const storedCenters = localStorage.getItem('healthCenters');
    if (storedCenters) {
      try {
        const parsedCenters = JSON.parse(storedCenters);
        setCentersState(parsedCenters);
      } catch (error) {
        console.error('Error loading stored health centers:', error);
      }
    } else {
      // Load default mock data if no stored data
      loadDefaultCenters();
    }
  }, []);

  // Save centers to localStorage whenever centers change
  useEffect(() => {
    if (centers.length > 0) {
      localStorage.setItem('healthCenters', JSON.stringify(centers));
    }
  }, [centers]);

  const loadDefaultCenters = () => {
    const defaultCenters: HealthCenterData[] = [
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
        codigo_establecimiento: 'HGES001',
        clues: 'SSHES001A00'
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
        codigo_establecimiento: 'CSVS002',
        clues: 'SSHES002B00'
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
        codigo_establecimiento: 'HGC003',
        clues: 'SSHES003A00'
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
        codigo_establecimiento: 'CSN004',
        clues: 'SSHES004B00'
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
        codigo_establecimiento: 'HGSLRC005',
        clues: 'SSHES005A00'
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
        codigo_establecimiento: 'CSG006',
        clues: 'SSHES006B00'
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
        codigo_establecimiento: 'CIN007',
        clues: 'IMSS007C00'
      }
    ];
    setCentersState(defaultCenters);
  };

  const setCenters = (newCenters: HealthCenterData[]) => {
    setCentersState(newCenters);
  };

  const addCenters = (newCenters: HealthCenterData[]) => {
    setCentersState(prevCenters => {
      // Remove duplicates based on CLUES or ID
      const existingIds = new Set(prevCenters.map(c => c.clues || c.id));
      const uniqueNewCenters = newCenters.filter(c => !existingIds.has(c.clues || c.id));
      
      return [...prevCenters, ...uniqueNewCenters];
    });
  };

  const updateCenter = (id: string, updatedCenter: Partial<HealthCenterData>) => {
    setCentersState(prevCenters =>
      prevCenters.map(center =>
        center.id === id ? { ...center, ...updatedCenter } : center
      )
    );
  };

  const deleteCenter = (id: string) => {
    setCentersState(prevCenters => prevCenters.filter(center => center.id !== id));
  };

  return (
    <HealthCentersContext.Provider value={{
      centers,
      setCenters,
      addCenters,
      updateCenter,
      deleteCenter,
      loading,
      setLoading
    }}>
      {children}
    </HealthCentersContext.Provider>
  );
};

export const useHealthCenters = (): HealthCentersContextType => {
  const context = useContext(HealthCentersContext);
  if (context === undefined) {
    throw new Error('useHealthCenters must be used within a HealthCentersProvider');
  }
  return context;
};