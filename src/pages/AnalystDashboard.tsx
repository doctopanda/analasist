import React, { useState } from 'react';
import Layout from '../components/Layout';
import ChartCard from '../components/ChartCard';
import { format } from 'date-fns';

// Mock data for different diagnoses over time
const timeSeriesByDiagnosis = {
  'Dengue': [
    { name: 'Semana 1', value: 12 },
    { name: 'Semana 2', value: 15 },
    { name: 'Semana 3', value: 18 },
    { name: 'Semana 4', value: 14 }
  ],
  'COVID-19': [
    { name: 'Semana 1', value: 25 },
    { name: 'Semana 2', value: 30 },
    { name: 'Semana 3', value: 28 },
    { name: 'Semana 4', value: 22 }
  ],
  'Influenza': [
    { name: 'Semana 1', value: 8 },
    { name: 'Semana 2', value: 10 },
    { name: 'Semana 3', value: 12 },
    { name: 'Semana 4', value: 9 }
  ]
};

const municipalityData = [
  { id: 1, name: 'Hermosillo' },
  { id: 2, name: 'Cajeme' },
  { id: 3, name: 'Nogales' },
  { id: 4, name: 'San Luis Río Colorado' },
  { id: 5, name: 'Navojoa' }
];

const districtData = [
  { id: 1, name: 'Distrito 1' },
  { id: 2, name: 'Distrito 2' },
  { id: 3, name: 'Distrito 3' },
  { id: 4, name: 'Distrito 4' },
  { id: 5, name: 'Distrito 5' }
];

const AnalystDashboard: React.FC = () => {
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-06-15');
  const [selectedDiagnosis, setSelectedDiagnosis] = useState('all');
  const [selectedMunicipality, setSelectedMunicipality] = useState('all');
  const [selectedDistrict, setSelectedDistrict] = useState('all');
  const [viewType, setViewType] = useState('state'); // state, municipality, district

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
            <label htmlFor="diagnosis" className="block text-sm font-medium text-gray-700 mb-1">
              Diagnóstico
            </label>
            <select
              id="diagnosis"
              value={selectedDiagnosis}
              onChange={(e) => setSelectedDiagnosis(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Todos los diagnósticos</option>
              <option value="Dengue">Dengue</option>
              <option value="COVID-19">COVID-19</option>
              <option value="Influenza">Influenza</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div>
            <label htmlFor="viewType" className="block text-sm font-medium text-gray-700 mb-1">
              Nivel de Análisis
            </label>
            <select
              id="viewType"
              value={viewType}
              onChange={(e) => setViewType(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="state">Estatal</option>
              <option value="municipality">Municipal</option>
              <option value="district">Distrital</option>
            </select>
          </div>

          {viewType === 'municipality' && (
            <div>
              <label htmlFor="municipality" className="block text-sm font-medium text-gray-700 mb-1">
                Municipio
              </label>
              <select
                id="municipality"
                value={selectedMunicipality}
                onChange={(e) => setSelectedMunicipality(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">Todos los municipios</option>
                {municipalityData.map(municipality => (
                  <option key={municipality.id} value={municipality.id}>
                    {municipality.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {viewType === 'district' && (
            <div>
              <label htmlFor="district" className="block text-sm font-medium text-gray-700 mb-1">
                Distrito
              </label>
              <select
                id="district"
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">Todos los distritos</option>
                {districtData.map(district => (
                  <option key={district.id} value={district.id}>
                    {district.name}
                  </option>
                ))}
              </select>
            </div>
          )}
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

      <div className="grid grid-cols-1 gap-6 mb-6">
        <ChartCard 
          title="Tendencia Temporal por Semana Epidemiológica" 
          type="line" 
          data={timeSeriesByDiagnosis[selectedDiagnosis] || timeSeriesByDiagnosis['Dengue']} 
        />
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Estadísticas Descriptivas</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Casos por Semana</h4>
            <ul className="space-y-2">
              <li className="flex justify-between">
                <span className="text-gray-600">Promedio:</span>
                <span className="font-medium">14.8 casos</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Máximo:</span>
                <span className="font-medium">25 casos</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Mínimo:</span>
                <span className="font-medium">8 casos</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Distribución Geográfica</h4>
            <ul className="space-y-2">
              <li className="flex justify-between">
                <span className="text-gray-600">Municipio más afectado:</span>
                <span className="font-medium">Hermosillo</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Distrito más afectado:</span>
                <span className="font-medium">Distrito 2</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Indicadores</h4>
            <ul className="space-y-2">
              <li className="flex justify-between">
                <span className="text-gray-600">Tasa de crecimiento:</span>
                <span className="font-medium">+5.2%</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-600">Variación semanal:</span>
                <span className="font-medium">±3.8 casos</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AnalystDashboard;