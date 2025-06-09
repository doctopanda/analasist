import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { ArrowLeft, Edit, Trash2, Building2, MapPin, Clock, User, Shield } from 'lucide-react';

interface HealthCenter {
  id: number;
  nombre: string;
  direccion: string;
  municipio: string;
  distrito: string;
  tipo: string;
  nivel_atencion: string;
  derechohabiencia: string;
  telefono?: string;
  email?: string;
  responsable?: string;
  usuario_responsable?: string;
  horario?: string;
  clues?: string;
  estado: 'activo' | 'inactivo';
  fecha_registro: string;
}

const mockHealthCenters: HealthCenter[] = [
  {
    id: 1,
    nombre: 'Hospital General del Estado de Sonora',
    direccion: 'Blvd. Luis Encinas Johnson s/n',
    municipio: 'Hermosillo',
    distrito: 'Distrito 1',
    tipo: 'Hospital',
    nivel_atencion: 'Segundo Nivel',
    derechohabiencia: 'ISSSTESON',
    telefono: '662-259-2500',
    email: 'contacto@hges.gob.mx',
    responsable: 'Dr. Juan Pérez García',
    usuario_responsable: 'hospital1',
    horario: '24 horas',
    clues: 'SSHES001A00',
    estado: 'activo',
    fecha_registro: '2024-04-05'
  },
  {
    id: 2,
    nombre: 'Centro de Salud Urbano Villa de Seris',
    direccion: 'Calle Sonora #123, Villa de Seris',
    municipio: 'Hermosillo',
    distrito: 'Distrito 1',
    tipo: 'Centro de Salud',
    nivel_atencion: 'Primer Nivel',
    derechohabiencia: 'IMSS Bienestar',
    telefono: '662-215-8900',
    email: 'villaseris@salud.gob.mx',
    responsable: 'Dra. María González López',
    usuario_responsable: 'centro_hermosillo',
    horario: 'Lunes a Viernes 8:00-16:00',
    clues: 'SSHES002B00',
    estado: 'activo',
    fecha_registro: '2024-04-12'
  },
  {
    id: 3,
    nombre: 'Hospital General de Cajeme',
    direccion: 'Calle 5 de Febrero #311',
    municipio: 'Cajeme',
    distrito: 'Distrito 2',
    tipo: 'Hospital',
    nivel_atencion: 'Segundo Nivel',
    derechohabiencia: 'ISSSTESON',
    telefono: '644-414-0050',
    email: 'hgcajeme@salud.gob.mx',
    responsable: 'Dr. Carlos Rodríguez Martínez',
    usuario_responsable: 'hospital_cajeme',
    horario: '24 horas',
    clues: 'SSHES003A00',
    estado: 'activo',
    fecha_registro: '2024-05-01'
  },
  {
    id: 4,
    nombre: 'Centro de Salud Nogales',
    direccion: 'Av. Obregón #1234',
    municipio: 'Nogales',
    distrito: 'Distrito 3',
    tipo: 'Centro de Salud',
    nivel_atencion: 'Primer Nivel',
    derechohabiencia: 'IMSS Bienestar',
    telefono: '631-311-2500',
    email: 'csnogales@salud.gob.mx',
    responsable: 'Dra. Ana López Hernández',
    usuario_responsable: 'centro_nogales',
    horario: 'Lunes a Viernes 7:00-15:00',
    clues: 'SSHES004B00',
    estado: 'activo',
    fecha_registro: '2024-05-15'
  },
  {
    id: 5,
    nombre: 'Hospital General San Luis Río Colorado',
    direccion: 'Av. Reforma #567',
    municipio: 'San Luis Río Colorado',
    distrito: 'Distrito 4',
    tipo: 'Hospital',
    nivel_atencion: 'Segundo Nivel',
    derechohabiencia: 'ISSSTESON',
    telefono: '653-534-1234',
    email: 'hgslrc@salud.gob.mx',
    responsable: 'Dr. Roberto Martínez Silva',
    usuario_responsable: 'hospital_slrc',
    horario: '24 horas',
    clues: 'SSHES005A00',
    estado: 'activo',
    fecha_registro: '2024-06-01'
  },
  {
    id: 6,
    nombre: 'Centro de Salud Guaymas',
    direccion: 'Calle 20 #456',
    municipio: 'Guaymas',
    distrito: 'Distrito 2',
    tipo: 'Centro de Salud',
    nivel_atencion: 'Primer Nivel',
    derechohabiencia: 'IMSS Bienestar',
    telefono: '622-222-3456',
    email: 'csguaymas@salud.gob.mx',
    responsable: 'Dr. Luis Hernández Castro',
    usuario_responsable: 'centro_guaymas',
    horario: 'Lunes a Viernes 8:00-16:00',
    clues: 'SSHES006B00',
    estado: 'activo',
    fecha_registro: '2024-06-15'
  },
  {
    id: 7,
    nombre: 'Clínica del IMSS Navojoa',
    direccion: 'Av. Tecnológico #789',
    municipio: 'Navojoa',
    distrito: 'Distrito 2',
    tipo: 'Clínica',
    nivel_atencion: 'Segundo Nivel',
    derechohabiencia: 'IMSS Ordinario',
    telefono: '642-422-1234',
    email: 'imssnavojoa@imss.gob.mx',
    responsable: 'Dra. Carmen Ruiz Morales',
    usuario_responsable: 'clinica_navojoa',
    horario: 'Lunes a Viernes 7:00-19:00',
    clues: 'IMSS007C00',
    estado: 'activo',
    fecha_registro: '2024-07-01'
  },
  {
    id: 8,
    nombre: 'Centro de Salud Agua Prieta',
    direccion: 'Calle Revolución #890',
    municipio: 'Agua Prieta',
    distrito: 'Distrito 3',
    tipo: 'Centro de Salud',
    nivel_atencion: 'Primer Nivel',
    derechohabiencia: 'IMSS Bienestar',
    telefono: '633-338-1234',
    email: 'csaguaprieta@salud.gob.mx',
    responsable: 'Dr. Miguel Ángel Torres',
    usuario_responsable: 'centro_agua_prieta',
    horario: 'Lunes a Viernes 8:00-16:00',
    clues: 'SSHES008B00',
    estado: 'activo',
    fecha_registro: '2024-08-15'
  },
  {
    id: 9,
    nombre: 'Hospital General Puerto Peñasco',
    direccion: 'Blvd. Benito Juárez #234',
    municipio: 'Puerto Peñasco',
    distrito: 'Distrito 4',
    tipo: 'Hospital',
    nivel_atencion: 'Segundo Nivel',
    derechohabiencia: 'ISSSTESON',
    telefono: '638-383-2345',
    email: 'hgpuertopenasco@salud.gob.mx',
    responsable: 'Dra. Patricia Moreno Vega',
    usuario_responsable: 'hospital_puerto_penasco',
    horario: '24 horas',
    clues: 'SSHES009A00',
    estado: 'activo',
    fecha_registro: '2024-09-01'
  },
  {
    id: 10,
    nombre: 'Centro de Salud Caborca',
    direccion: 'Av. Sonora #567',
    municipio: 'Caborca',
    distrito: 'Distrito 4',
    tipo: 'Centro de Salud',
    nivel_atencion: 'Primer Nivel',
    derechohabiencia: 'IMSS Bienestar',
    telefono: '637-372-4567',
    email: 'cscaborca@salud.gob.mx',
    responsable: 'Dr. Fernando Acosta Ruiz',
    usuario_responsable: 'centro_caborca',
    horario: 'Lunes a Viernes 8:00-16:00',
    clues: 'SSHES010B00',
    estado: 'activo',
    fecha_registro: '2024-09-15'
  },
  {
    id: 11,
    nombre: 'Centro de Salud Cananea',
    direccion: 'Calle Minería #123',
    municipio: 'Cananea',
    distrito: 'Distrito 5',
    tipo: 'Centro de Salud',
    nivel_atencion: 'Primer Nivel',
    derechohabiencia: 'IMSS Bienestar',
    telefono: '645-332-5678',
    email: 'cscananea@salud.gob.mx',
    responsable: 'Dra. Silvia Ramírez Flores',
    usuario_responsable: 'centro_cananea',
    horario: 'Lunes a Viernes 8:00-16:00',
    clues: 'SSHES011B00',
    estado: 'activo',
    fecha_registro: '2024-10-01'
  },
  {
    id: 12,
    nombre: 'Centro de Salud Magdalena',
    direccion: 'Av. Independencia #456',
    municipio: 'Magdalena',
    distrito: 'Distrito 3',
    tipo: 'Centro de Salud',
    nivel_atencion: 'Primer Nivel',
    derechohabiencia: 'IMSS Bienestar',
    telefono: '632-322-6789',
    email: 'csmagdalena@salud.gob.mx',
    responsable: 'Dr. Alejandro Soto Mendoza',
    usuario_responsable: 'centro_magdalena',
    horario: 'Lunes a Viernes 8:00-16:00',
    clues: 'SSHES012B00',
    estado: 'activo',
    fecha_registro: '2024-10-15'
  }
];

const HealthCentersManagement: React.FC = () => {
  const navigate = useNavigate();
  const [centers] = useState<HealthCenter[]>(mockHealthCenters);
  const [filteredCenters, setFilteredCenters] = useState<HealthCenter[]>(mockHealthCenters);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterDistrict, setFilterDistrict] = useState('');
  const [filterDerechohabiencia, setFilterDerechohabiencia] = useState('');

  React.useEffect(() => {
    let filtered = centers;

    if (searchTerm) {
      filtered = filtered.filter(center =>
        center.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.direccion.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.responsable?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.clues?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterType) {
      filtered = filtered.filter(center => center.tipo === filterType);
    }

    if (filterDistrict) {
      filtered = filtered.filter(center => center.distrito === filterDistrict);
    }

    if (filterDerechohabiencia) {
      filtered = filtered.filter(center => center.derechohabiencia === filterDerechohabiencia);
    }

    setFilteredCenters(filtered);
  }, [centers, searchTerm, filterType, filterDistrict, filterDerechohabiencia]);

  const getTypeBadge = (tipo: string) => {
    const colors = {
      'Hospital': 'bg-red-100 text-red-800',
      'Centro de Salud': 'bg-blue-100 text-blue-800',
      'Clínica': 'bg-green-100 text-green-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[tipo as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {tipo}
      </span>
    );
  };

  const getDerechohabienciaBadge = (derechohabiencia: string) => {
    const colors = {
      'IMSS Ordinario': 'bg-blue-100 text-blue-800',
      'IMSS Bienestar': 'bg-green-100 text-green-800',
      'ISSSTE': 'bg-purple-100 text-purple-800',
      'ISSSTESON': 'bg-orange-100 text-orange-800',
      'Privado': 'bg-gray-100 text-gray-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[derechohabiencia as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {derechohabiencia}
      </span>
    );
  };

  const editCenter = (centerId: number) => {
    console.log(`Edit center ${centerId}`);
  };

  const deleteCenter = (centerId: number) => {
    if (confirm('¿Está seguro de que desea eliminar este centro de salud?')) {
      console.log(`Delete center ${centerId}`);
    }
  };

  const stats = {
    total: centers.length,
    hospitales: centers.filter(c => c.tipo === 'Hospital').length,
    centros: centers.filter(c => c.tipo === 'Centro de Salud').length,
    clinicas: centers.filter(c => c.tipo === 'Clínica').length,
    activos: centers.filter(c => c.estado === 'activo').length
  };

  const districts = [...new Set(centers.map(c => c.distrito))].sort();
  const types = [...new Set(centers.map(c => c.tipo))].sort();
  const derechohabiencias = [...new Set(centers.map(c => c.derechohabiencia))].sort();

  return (
    <Layout title="Gestión de Centros de Salud">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/admin')}
              className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Volver al Panel
            </button>
            <h2 className="text-2xl font-bold text-gray-900">Gestión de Centros de Salud</h2>
          </div>
          
          <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            <Building2 className="h-5 w-5 mr-2" />
            Nuevo Centro
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">Total Centros</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-red-600">{stats.hospitales}</div>
            <div className="text-sm text-gray-600">Hospitales</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-blue-600">{stats.centros}</div>
            <div className="text-sm text-gray-600">Centros de Salud</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-green-600">{stats.clinicas}</div>
            <div className="text-sm text-gray-600">Clínicas</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="text-2xl font-bold text-green-600">{stats.activos}</div>
            <div className="text-sm text-gray-600">Activos</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Buscar Centro
              </label>
              <input
                type="text"
                placeholder="Buscar por nombre, dirección, responsable o CLUES..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los tipos</option>
                {types.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Distrito
              </label>
              <select
                value={filterDistrict}
                onChange={(e) => setFilterDistrict(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los distritos</option>
                {districts.map(district => (
                  <option key={district} value={district}>{district}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Derechohabiencia
              </label>
              <select
                value={filterDerechohabiencia}
                onChange={(e) => setFilterDerechohabiencia(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todas las derechohabiencias</option>
                {derechohabiencias.map(derecho => (
                  <option key={derecho} value={derecho}>{derecho}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Centers Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Centro de Salud
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ubicación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo / Nivel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Derechohabiencia
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Responsable
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario Sistema
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Horario
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCenters.map((center) => (
                  <tr key={center.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{center.nombre}</div>
                        <div className="text-sm text-gray-500">CLUES: {center.clues}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm text-gray-900 flex items-center">
                          <MapPin className="h-4 w-4 mr-1 text-gray-400" />
                          {center.municipio}
                        </div>
                        <div className="text-sm text-gray-500">{center.distrito}</div>
                        <div className="text-sm text-gray-500">{center.direccion}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        {getTypeBadge(center.tipo)}
                        <div className="text-sm text-gray-500 mt-1">{center.nivel_atencion}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getDerechohabienciaBadge(center.derechohabiencia)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <User className="h-4 w-4 mr-1 text-gray-400" />
                        {center.responsable}
                      </div>
                      {center.telefono && (
                        <div className="text-sm text-gray-500">{center.telefono}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <Shield className="h-4 w-4 mr-1 text-gray-400" />
                        {center.usuario_responsable}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 flex items-center">
                        <Clock className="h-4 w-4 mr-1 text-gray-400" />
                        {center.horario}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => editCenter(center.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Editar centro"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => deleteCenter(center.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Eliminar centro"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredCenters.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-500">No se encontraron centros de salud que coincidan con los filtros.</div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default HealthCentersManagement;