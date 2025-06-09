import React, { createContext, useState, useContext, useEffect } from 'react';
import { HealthCenterData } from '../services/excelService';
import { getPermanentHealthCenters, getPermanentDatabaseStats } from '../data/permanentHealthCenters';

interface User {
  id: number;
  username: string;
  rol: string;
  centro_salud_id?: number;
  centro_salud_nombre?: string;
  distrito?: string;
  fecha_registro: string;
  ultima_participacion: string;
  estado: 'activo' | 'inactivo';
}

interface Report {
  id: number;
  folio: string;
  fecha_subida: string;
  fecha_consulta: string;
  centro_salud: string;
  municipio: string;
  distrito: string;
  diagnostico: string;
  edad_paciente: number;
  sexo: string;
  usuario_subida: string;
  estado: 'procesado' | 'pendiente' | 'revision';
}

interface Alert {
  id: number;
  tipo: 'brote' | 'incremento' | 'cluster' | 'anomalia';
  titulo: string;
  descripcion: string;
  municipio: string;
  distrito: string;
  diagnostico: string;
  casos_detectados: number;
  fecha_deteccion: string;
  coordenadas: { lat: number; lng: number };
  severidad: 'baja' | 'media' | 'alta' | 'critica';
  estado: 'activa' | 'investigando' | 'resuelta' | 'descartada';
  acciones_tomadas?: string;
}

interface DataContextType {
  // Health Centers
  healthCenters: HealthCenterData[];
  setHealthCenters: (centers: HealthCenterData[]) => void;
  addHealthCenters: (newCenters: HealthCenterData[]) => void;
  updateHealthCenter: (id: string, updatedCenter: Partial<HealthCenterData>) => void;
  deleteHealthCenter: (id: string) => void;
  loadPermanentHealthCenters: () => void;
  
  // Users
  users: User[];
  setUsers: (users: User[]) => void;
  addUser: (user: User) => void;
  updateUser: (id: number, updatedUser: Partial<User>) => void;
  deleteUser: (id: number) => void;
  
  // Reports
  reports: Report[];
  setReports: (reports: Report[]) => void;
  addReport: (report: Report) => void;
  updateReport: (id: number, updatedReport: Partial<Report>) => void;
  deleteReport: (id: number) => void;
  
  // Alerts
  alerts: Alert[];
  setAlerts: (alerts: Alert[]) => void;
  addAlert: (alert: Alert) => void;
  updateAlert: (id: number, updatedAlert: Partial<Alert>) => void;
  deleteAlert: (id: number) => void;
  
  // Statistics
  getStatistics: () => {
    totalUsers: number;
    activeUsers: number;
    totalHealthCenters: number;
    totalReports: number;
    pendingReports: number;
    totalAlerts: number;
    activeAlerts: number;
    criticalAlerts: number;
  };
  
  // Database info
  getDatabaseInfo: () => {
    isPermanentLoaded: boolean;
    permanentStats: any;
    lastUpdated: string;
  };
  
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [healthCenters, setHealthCentersState] = useState<HealthCenterData[]>([]);
  const [users, setUsersState] = useState<User[]>([]);
  const [reports, setReportsState] = useState<Report[]>([]);
  const [alerts, setAlertsState] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [isPermanentLoaded, setIsPermanentLoaded] = useState(false);

  // Load data from localStorage on mount, with permanent database fallback
  useEffect(() => {
    loadStoredData();
  }, []);

  // Save data to localStorage whenever any data changes
  useEffect(() => {
    saveDataToStorage();
  }, [healthCenters, users, reports, alerts]);

  const loadStoredData = () => {
    try {
      // Load health centers - check localStorage first, then permanent database
      const storedCenters = localStorage.getItem('healthCenters');
      if (storedCenters) {
        const parsedCenters = JSON.parse(storedCenters);
        setHealthCentersState(parsedCenters);
        console.log(`Loaded ${parsedCenters.length} health centers from localStorage`);
      } else {
        // Load permanent database if no localStorage data
        loadPermanentHealthCenters();
      }

      // Load users
      const storedUsers = localStorage.getItem('users');
      if (storedUsers) {
        setUsersState(JSON.parse(storedUsers));
      } else {
        loadDefaultUsers();
      }

      // Load reports
      const storedReports = localStorage.getItem('reports');
      if (storedReports) {
        setReportsState(JSON.parse(storedReports));
      } else {
        loadDefaultReports();
      }

      // Load alerts
      const storedAlerts = localStorage.getItem('alerts');
      if (storedAlerts) {
        setAlertsState(JSON.parse(storedAlerts));
      } else {
        loadDefaultAlerts();
      }
    } catch (error) {
      console.error('Error loading stored data:', error);
      loadDefaultData();
    }
  };

  const loadPermanentHealthCenters = () => {
    try {
      const permanentCenters = getPermanentHealthCenters();
      setHealthCentersState(permanentCenters);
      setIsPermanentLoaded(true);
      
      // Save to localStorage for future use
      localStorage.setItem('healthCenters', JSON.stringify(permanentCenters));
      localStorage.setItem('healthCentersSource', 'permanent');
      localStorage.setItem('healthCentersLoadedAt', new Date().toISOString());
      
      console.log(`Loaded ${permanentCenters.length} health centers from permanent database`);
    } catch (error) {
      console.error('Error loading permanent health centers:', error);
      loadDefaultHealthCenters();
    }
  };

  const saveDataToStorage = () => {
    try {
      localStorage.setItem('healthCenters', JSON.stringify(healthCenters));
      localStorage.setItem('users', JSON.stringify(users));
      localStorage.setItem('reports', JSON.stringify(reports));
      localStorage.setItem('alerts', JSON.stringify(alerts));
      localStorage.setItem('lastSaved', new Date().toISOString());
    } catch (error) {
      console.error('Error saving data to storage:', error);
    }
  };

  const loadDefaultData = () => {
    loadPermanentHealthCenters(); // Use permanent database as default
    loadDefaultUsers();
    loadDefaultReports();
    loadDefaultAlerts();
  };

  const loadDefaultHealthCenters = () => {
    // Fallback to basic centers if permanent database fails
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
      }
    ];
    setHealthCentersState(defaultCenters);
  };

  const loadDefaultUsers = () => {
    const defaultUsers: User[] = [
      {
        id: 1,
        username: 'admin',
        rol: 'admin',
        fecha_registro: '2024-01-15',
        ultima_participacion: '2025-01-15',
        estado: 'activo'
      },
      {
        id: 2,
        username: 'analista1',
        rol: 'analista',
        fecha_registro: '2024-02-20',
        ultima_participacion: '2025-01-14',
        estado: 'activo'
      },
      {
        id: 3,
        username: 'hospital1',
        rol: 'centro_salud',
        centro_salud_id: 1,
        centro_salud_nombre: 'Hospital General del Estado de Sonora',
        distrito: 'Distrito 1',
        fecha_registro: '2024-04-05',
        ultima_participacion: '2025-01-15',
        estado: 'activo'
      }
    ];
    setUsersState(defaultUsers);
  };

  const loadDefaultReports = () => {
    const defaultReports: Report[] = [
      {
        id: 1,
        folio: 'FOL-1045',
        fecha_subida: '2025-01-15 14:30:00',
        fecha_consulta: '2025-01-15',
        centro_salud: 'Hospital General del Estado de Sonora',
        municipio: 'Hermosillo',
        distrito: 'Distrito 1',
        diagnostico: 'Dengue',
        edad_paciente: 34,
        sexo: 'M',
        usuario_subida: 'hospital1',
        estado: 'procesado'
      },
      {
        id: 2,
        folio: 'FOL-1044',
        fecha_subida: '2025-01-14 16:45:00',
        fecha_consulta: '2025-01-14',
        centro_salud: 'Centro de Salud Urbano Villa de Seris',
        municipio: 'Hermosillo',
        distrito: 'Distrito 1',
        diagnostico: 'COVID-19',
        edad_paciente: 28,
        sexo: 'F',
        usuario_subida: 'centro_hermosillo',
        estado: 'pendiente'
      }
    ];
    setReportsState(defaultReports);
  };

  const loadDefaultAlerts = () => {
    const defaultAlerts: Alert[] = [
      {
        id: 1,
        tipo: 'brote',
        titulo: 'Posible brote de Dengue en Hermosillo',
        descripcion: 'Se han detectado 8 casos de dengue en un radio de 2km en la colonia Villa de Seris en los últimos 7 días.',
        municipio: 'Hermosillo',
        distrito: 'Distrito 1',
        diagnostico: 'Dengue',
        casos_detectados: 8,
        fecha_deteccion: '2025-01-15',
        coordenadas: { lat: 29.0892, lng: -110.9618 },
        severidad: 'alta',
        estado: 'activa',
        acciones_tomadas: 'Equipo de epidemiología enviado para investigación de campo'
      },
      {
        id: 2,
        tipo: 'incremento',
        titulo: 'Incremento de casos de COVID-19 en Cajeme',
        descripcion: 'Aumento del 40% en casos de COVID-19 comparado con la semana anterior.',
        municipio: 'Cajeme',
        distrito: 'Distrito 2',
        diagnostico: 'COVID-19',
        casos_detectados: 12,
        fecha_deteccion: '2025-01-14',
        coordenadas: { lat: 27.3833, lng: -109.9167 },
        severidad: 'critica',
        estado: 'activa'
      }
    ];
    setAlertsState(defaultAlerts);
  };

  // Health Centers methods
  const setHealthCenters = (centers: HealthCenterData[]) => {
    setHealthCentersState(centers);
    localStorage.setItem('healthCentersSource', 'manual');
    localStorage.setItem('healthCentersLoadedAt', new Date().toISOString());
  };

  const addHealthCenters = (newCenters: HealthCenterData[]) => {
    setHealthCentersState(prevCenters => {
      const existingIds = new Set(prevCenters.map(c => c.clues || c.id));
      const uniqueNewCenters = newCenters.filter(c => !existingIds.has(c.clues || c.id));
      const combined = [...prevCenters, ...uniqueNewCenters];
      
      localStorage.setItem('healthCentersSource', 'combined');
      localStorage.setItem('healthCentersLoadedAt', new Date().toISOString());
      
      return combined;
    });
  };

  const updateHealthCenter = (id: string, updatedCenter: Partial<HealthCenterData>) => {
    setHealthCentersState(prevCenters =>
      prevCenters.map(center =>
        center.id === id ? { ...center, ...updatedCenter } : center
      )
    );
  };

  const deleteHealthCenter = (id: string) => {
    setHealthCentersState(prevCenters => prevCenters.filter(center => center.id !== id));
  };

  // Users methods
  const setUsers = (newUsers: User[]) => {
    setUsersState(newUsers);
  };

  const addUser = (user: User) => {
    setUsersState(prevUsers => [...prevUsers, user]);
  };

  const updateUser = (id: number, updatedUser: Partial<User>) => {
    setUsersState(prevUsers =>
      prevUsers.map(user =>
        user.id === id ? { ...user, ...updatedUser } : user
      )
    );
  };

  const deleteUser = (id: number) => {
    setUsersState(prevUsers => prevUsers.filter(user => user.id !== id));
  };

  // Reports methods
  const setReports = (newReports: Report[]) => {
    setReportsState(newReports);
  };

  const addReport = (report: Report) => {
    setReportsState(prevReports => [...prevReports, report]);
  };

  const updateReport = (id: number, updatedReport: Partial<Report>) => {
    setReportsState(prevReports =>
      prevReports.map(report =>
        report.id === id ? { ...report, ...updatedReport } : report
      )
    );
  };

  const deleteReport = (id: number) => {
    setReportsState(prevReports => prevReports.filter(report => report.id !== id));
  };

  // Alerts methods
  const setAlerts = (newAlerts: Alert[]) => {
    setAlertsState(newAlerts);
  };

  const addAlert = (alert: Alert) => {
    setAlertsState(prevAlerts => [...prevAlerts, alert]);
  };

  const updateAlert = (id: number, updatedAlert: Partial<Alert>) => {
    setAlertsState(prevAlerts =>
      prevAlerts.map(alert =>
        alert.id === id ? { ...alert, ...updatedAlert } : alert
      )
    );
  };

  const deleteAlert = (id: number) => {
    setAlertsState(prevAlerts => prevAlerts.filter(alert => alert.id !== id));
  };

  // Statistics calculation
  const getStatistics = () => {
    return {
      totalUsers: users.length,
      activeUsers: users.filter(u => u.estado === 'activo').length,
      totalHealthCenters: healthCenters.length,
      totalReports: reports.length,
      pendingReports: reports.filter(r => r.estado === 'pendiente').length,
      totalAlerts: alerts.length,
      activeAlerts: alerts.filter(a => a.estado === 'activa').length,
      criticalAlerts: alerts.filter(a => a.severidad === 'critica').length
    };
  };

  // Database information
  const getDatabaseInfo = () => {
    const source = localStorage.getItem('healthCentersSource') || 'unknown';
    const loadedAt = localStorage.getItem('healthCentersLoadedAt') || 'unknown';
    const permanentStats = getPermanentDatabaseStats();
    
    return {
      isPermanentLoaded: source === 'permanent' || isPermanentLoaded,
      permanentStats,
      lastUpdated: loadedAt,
      source,
      currentCount: healthCenters.length
    };
  };

  return (
    <DataContext.Provider value={{
      healthCenters,
      setHealthCenters,
      addHealthCenters,
      updateHealthCenter,
      deleteHealthCenter,
      loadPermanentHealthCenters,
      users,
      setUsers,
      addUser,
      updateUser,
      deleteUser,
      reports,
      setReports,
      addReport,
      updateReport,
      deleteReport,
      alerts,
      setAlerts,
      addAlert,
      updateAlert,
      deleteAlert,
      getStatistics,
      getDatabaseInfo,
      loading,
      setLoading
    }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = (): DataContextType => {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};