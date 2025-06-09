import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  LogOut, 
  BarChart3, 
  Users, 
  Home, 
  FileText, 
  PlusCircle,
  Activity,
  Menu,
  X,
  MapPin
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  title: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div 
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-blue-800 text-white transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-center h-16 border-b border-blue-700">
          <Activity className="h-8 w-8 mr-2" />
          <span className="text-xl font-semibold">SUIVE</span>
        </div>

        <nav className="mt-8">
          <div className="px-4 mb-6">
            <p className="text-sm text-blue-300">Bienvenido,</p>
            <p className="font-medium">{user?.username}</p>
            <p className="text-xs text-blue-300 capitalize">{user?.rol}</p>
          </div>

          <ul className="space-y-2 px-2">
            <li>
              <button 
                onClick={() => navigate('/')}
                className="flex items-center w-full px-4 py-2 text-white rounded-md hover:bg-blue-700"
              >
                <Home className="h-5 w-5 mr-3" />
                <span>Inicio</span>
              </button>
            </li>

            {user?.rol === 'admin' && (
              <li>
                <button 
                  onClick={() => navigate('/admin')}
                  className="flex items-center w-full px-4 py-2 text-white rounded-md hover:bg-blue-700"
                >
                  <Users className="h-5 w-5 mr-3" />
                  <span>Administración</span>
                </button>
              </li>
            )}

            {(user?.rol === 'analista' || user?.rol === 'admin') && (
              <>
                <li>
                  <button 
                    onClick={() => navigate('/analyst')}
                    className="flex items-center w-full px-4 py-2 text-white rounded-md hover:bg-blue-700"
                  >
                    <BarChart3 className="h-5 w-5 mr-3" />
                    <span>Análisis</span>
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => navigate('/health-centers-map')}
                    className="flex items-center w-full px-4 py-2 text-white rounded-md hover:bg-blue-700"
                  >
                    <MapPin className="h-5 w-5 mr-3" />
                    <span>Mapa de Centros</span>
                  </button>
                </li>
              </>
            )}

            {user?.rol === 'centro_salud' && (
              <>
                <li>
                  <button 
                    onClick={() => navigate('/health-center')}
                    className="flex items-center w-full px-4 py-2 text-white rounded-md hover:bg-blue-700"
                  >
                    <FileText className="h-5 w-5 mr-3" />
                    <span>Mis Reportes</span>
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => navigate('/report/new')}
                    className="flex items-center w-full px-4 py-2 text-white rounded-md hover:bg-blue-700"
                  >
                    <PlusCircle className="h-5 w-5 mr-3" />
                    <span>Nuevo Reporte</span>
                  </button>
                </li>
              </>
            )}
          </ul>
        </nav>

        <div className="absolute bottom-0 w-full border-t border-blue-700 p-4">
          <button 
            onClick={handleLogout}
            className="flex items-center w-full px-4 py-2 text-white rounded-md hover:bg-blue-700"
          >
            <LogOut className="h-5 w-5 mr-3" />
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:ml-64">
        <header className="bg-white shadow-sm z-10 relative">
          <div className="px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
            {/* Mobile menu button */}
            <div className="flex items-center lg:hidden">
              <button 
                onClick={toggleSidebar}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mr-3"
              >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
            
            <h1 className="text-2xl font-semibold text-gray-800 flex-1 lg:flex-none">{title}</h1>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-gray-50">
          {children}
        </main>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
          onClick={toggleSidebar}
        ></div>
      )}
    </div>
  );
};

export default Layout;