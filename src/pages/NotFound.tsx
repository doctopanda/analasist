import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home } from 'lucide-react';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-blue-600">404</h1>
        <h2 className="text-2xl font-semibold text-gray-800 mt-4">Página no encontrada</h2>
        <p className="text-gray-600 mt-2 mb-6">
          Lo sentimos, la página que estás buscando no existe.
        </p>
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Home className="h-5 w-5 mr-2" />
          Volver al inicio
        </button>
      </div>
    </div>
  );
};

export default NotFound;