import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { CheckCircle } from 'lucide-react';

const ReportForm: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [submitted, setSubmitted] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    // General data
    folio: `FOL-${Math.floor(1000 + Math.random() * 9000)}`,
    fecha_consulta: new Date().toISOString().split('T')[0],
    
    // Patient data
    curp: '',
    edad: '',
    sexo: '',
    entidad_residencia: 'Estado de México',
    municipio_residencia: '',
    
    // Clinical data
    fecha_inicio_sintomas: '',
    diagnostico: '',
    codigo_cie10: '',
    tratamiento: '',
    
    // Risk factors
    embarazo: false,
    diabetes: false,
    obesidad: false,
    hipertension: false
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const nextStep = () => {
    setCurrentStep(prev => prev + 1);
  };

  const prevStep = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would send the data to the server
    console.log('Form submitted:', formData);
    setSubmitted(true);
    
    // After 2 seconds, redirect to the dashboard
    setTimeout(() => {
      navigate('/health-center');
    }, 2000);
  };

  // Render different form sections based on current step
  const renderFormStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Datos Generales</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="folio" className="block text-sm font-medium text-gray-700">
                  Folio
                </label>
                <input
                  type="text"
                  id="folio"
                  name="folio"
                  value={formData.folio}
                  readOnly
                  className="mt-1 block w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">Generado automáticamente</p>
              </div>
              
              <div>
                <label htmlFor="fecha_consulta" className="block text-sm font-medium text-gray-700">
                  Fecha de Consulta
                </label>
                <input
                  type="date"
                  id="fecha_consulta"
                  name="fecha_consulta"
                  value={formData.fecha_consulta}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        );
      
      case 2:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Datos del Paciente</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="curp" className="block text-sm font-medium text-gray-700">
                  CURP
                </label>
                <input
                  type="text"
                  id="curp"
                  name="curp"
                  value={formData.curp}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label htmlFor="edad" className="block text-sm font-medium text-gray-700">
                  Edad
                </label>
                <input
                  type="number"
                  id="edad"
                  name="edad"
                  value={formData.edad}
                  onChange={handleChange}
                  min="0"
                  max="120"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label htmlFor="sexo" className="block text-sm font-medium text-gray-700">
                  Sexo
                </label>
                <select
                  id="sexo"
                  name="sexo"
                  value={formData.sexo}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Seleccionar</option>
                  <option value="H">Hombre</option>
                  <option value="M">Mujer</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="entidad_residencia" className="block text-sm font-medium text-gray-700">
                  Entidad de Residencia
                </label>
                <input
                  type="text"
                  id="entidad_residencia"
                  name="entidad_residencia"
                  value={formData.entidad_residencia}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div className="md:col-span-2">
                <label htmlFor="municipio_residencia" className="block text-sm font-medium text-gray-700">
                  Municipio de Residencia
                </label>
                <select
                  id="municipio_residencia"
                  name="municipio_residencia"
                  value={formData.municipio_residencia}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Seleccionar</option>
                  <option value="Neza">Nezahualcóyotl</option>
                  <option value="Ecatepec">Ecatepec</option>
                  <option value="Toluca">Toluca</option>
                  <option value="Cuautitlán">Cuautitlán</option>
                  <option value="Naucalpan">Naucalpan</option>
                </select>
              </div>
            </div>
          </div>
        );
      
      case 3:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Datos Clínicos</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="fecha_inicio_sintomas" className="block text-sm font-medium text-gray-700">
                  Fecha de Inicio de Síntomas
                </label>
                <input
                  type="date"
                  id="fecha_inicio_sintomas"
                  name="fecha_inicio_sintomas"
                  value={formData.fecha_inicio_sintomas}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label htmlFor="diagnostico" className="block text-sm font-medium text-gray-700">
                  Diagnóstico
                </label>
                <select
                  id="diagnostico"
                  name="diagnostico"
                  value={formData.diagnostico}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Seleccionar</option>
                  <option value="Dengue">Dengue</option>
                  <option value="COVID-19">COVID-19</option>
                  <option value="Influenza">Influenza</option>
                  <option value="Zika">Zika</option>
                  <option value="Chikungunya">Chikungunya</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="codigo_cie10" className="block text-sm font-medium text-gray-700">
                  Código CIE-10
                </label>
                <input
                  type="text"
                  id="codigo_cie10"
                  name="codigo_cie10"
                  value={formData.codigo_cie10}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div className="md:col-span-2">
                <label htmlFor="tratamiento" className="block text-sm font-medium text-gray-700">
                  Tratamiento
                </label>
                <textarea
                  id="tratamiento"
                  name="tratamiento"
                  rows={3}
                  value={formData.tratamiento}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                ></textarea>
              </div>
            </div>
          </div>
        );
      
      case 4:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Factores de Riesgo</h3>
            
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="embarazo"
                    name="embarazo"
                    type="checkbox"
                    checked={formData.embarazo}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="embarazo" className="font-medium text-gray-700">Embarazo</label>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="diabetes"
                    name="diabetes"
                    type="checkbox"
                    checked={formData.diabetes}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="diabetes" className="font-medium text-gray-700">Diabetes</label>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="obesidad"
                    name="obesidad"
                    type="checkbox"
                    checked={formData.obesidad}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="obesidad" className="font-medium text-gray-700">Obesidad</label>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="hipertension"
                    name="hipertension"
                    type="checkbox"
                    checked={formData.hipertension}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="hipertension" className="font-medium text-gray-700">Hipertensión</label>
                </div>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  // If form is submitted, show success message
  if (submitted) {
    return (
      <Layout title="Nuevo Reporte">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <div className="flex justify-center mb-4">
              <CheckCircle className="h-16 w-16 text-green-500" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">¡Reporte Enviado!</h2>
            <p className="text-gray-600 mb-6">
              Su reporte ha sido enviado correctamente con el folio <strong>{formData.folio}</strong>.
            </p>
            <p className="text-sm text-gray-500">
              Redirigiendo al panel de control...
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Nuevo Reporte">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          {/* Progress bar */}
          <div className="bg-gray-50 px-6 py-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-medium text-gray-900">Nuevo Reporte SUIVE</h2>
              <span className="text-sm text-gray-500">Paso {currentStep} de 4</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full" 
                style={{ width: `${(currentStep / 4) * 100}%` }}
              ></div>
            </div>
          </div>
          
          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="p-6">
              {renderFormStep()}
            </div>
            
            {/* Navigation buttons */}
            <div className="bg-gray-50 px-6 py-4 flex justify-between">
              <button
                type="button"
                onClick={prevStep}
                disabled={currentStep === 1}
                className={`px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                  currentStep === 1 ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Anterior
              </button>
              
              {currentStep < 4 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Siguiente
                </button>
              ) : (
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  Enviar Reporte
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};

export default ReportForm;