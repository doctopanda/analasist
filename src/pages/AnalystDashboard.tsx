import React, { useState } from 'react';
import Layout from '../components/Layout';
import ChartCard from '../components/ChartCard';
import { format } from 'date-fns';

// Mock data
const diagnosisData = [
  { name: 'Dengue', value: 35 },
  { name: 'COVID-19', value: 40 },
  { name: 'Influenza', value: 25 },
  { name: 'Zika', value: 15 },
  { name: 'Chikungunya', value: 10 }
];

const timeSeriesData = [
  { name: '01/01', value: 12 },
  { name: '02/01', value: 15 },
  { name: '03/01', value: 18 },
  { name: '04/01', value: 14 },
  { name: '05/01', value: 10 },
  { name: '06/01', value: 8 },
  { name: '07/01', value: 9 },
  { name: '08/01', value: 11 },
  { name: '09/01', value: 13 },
  { name: '10/01', value: 15 },
  { name: '11/01', value: 17 },
  { name: '12/01', value: 19 },
  { name: '13/01', value: 21 },
  { name: '14/01', value: 22 },
];

const riskFactorsData = [
  { name: 'Diabetes', value: 28 },
  { name: 'Obesidad', value: 35 },
  { name: 'Hipertensión', value: 42 },
  { name: 'Embarazo', value: 12 }
];

const municipalityData = [
  { name: 'Neza', value: 45 },
  { name: 'Ecatepec', value: 38 },
  { name: 'Toluca', value: 32 },
  { name: 'Cuautitlán', value: 25 },
  { name: 'Naucalpan', value: 30 }
];

const AnalystDashboard: React.FC = () => {
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-06-15');
  const [healthCenter, setHealthCenter] = useState('all');

  return (
    <Layout title="Panel de Análisis">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Filtros de Análisis</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Inicio
            </label>
            <input
              type="date"
              id="startDate"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Fin
            </label>
            <input
              type="date"
              id="endDate"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label htmlFor="healthCenter" className="block text-sm font-medium text-gray-700 mb-1">
              Centro de Salud
            </label>
            <select
              id="healthCenter"
              value={healthCenter}
              onChange={(e) => setHealthCenter(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Todos</option>
              <option value="1">Hospital General de la Ciudad</option>
              <option value="2">Centro de Salud Urbano</option>
            </select>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Aplicar Filtros
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ChartCard 
          title="Distribución por Diagnóstico" 
          type="pie" 
          data={diagnosisData} 
        />
        <ChartCard 
          title="Tendencia Temporal de Casos" 
          type="line" 
          data={timeSeriesData} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ChartCard 
          title="Factores de Riesgo en Pacientes" 
          type="bar" 
          data={riskFactorsData} 
        />
        <ChartCard 
          title="Casos por Municipio" 
          type="bar" 
          data={municipalityData} 
        />
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Estadísticas Descriptivas</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Edad</h4>
            <ul className="space-y-2">
              <li className="flex justify-between">
                <span className="text-gray-600">Media:</span>
                <span className="font-medium">42.3 años</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Mediana:</span>
                <span className="font-medium">39 años</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Moda:</span>
                <span className="font-medium">35 años</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Desv. Estándar:</span>
                <span className="font-medium">12.7 años</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Distribución por Sexo</h4>
            <ul className="space-y-2">
              <li className="flex justify-between">
                <span className="text-gray-600">Masculino:</span>
                <span className="font-medium">43% (54)</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Femenino:</span>
                <span className="font-medium">57% (71)</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Indicadores</h4>
            <ul className="space-y-2">
              <li className="flex justify-between">
                <span className="text-gray-600">Incidencia:</span>
                <span className="font-medium">23.5 por 100,000</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Prevalencia:</span>
                <span className="font-medium">42.1 por 100,000</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Razón de Morbilidad:</span>
                <span className="font-medium">3.2 por 1,000</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AnalystDashboard;