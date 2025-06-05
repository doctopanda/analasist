// Mock data for the application
// In a real application, this would be fetched from the API

export const mockCentrosSalud = [
  {
    id: 1,
    nombre: 'Hospital General de la Ciudad',
    direccion: 'Av. Salud 123',
    codigo_establecimiento: 'HGC001'
  },
  {
    id: 2,
    nombre: 'Centro de Salud Urbano',
    direccion: 'Calle Bienestar 456',
    codigo_establecimiento: 'CSU002'
  }
];

export const mockReportes = Array.from({ length: 50 }, (_, i) => {
  const diagnosticos = ['Dengue', 'COVID-19', 'Influenza', 'Zika', 'Chikungunya'];
  const municipios = ['Neza', 'Ecatepec', 'Toluca', 'Cuautitlán', 'Naucalpan'];
  const randomDate = new Date();
  randomDate.setDate(randomDate.getDate() - Math.floor(Math.random() * 30));
  
  return {
    id: i + 1,
    centro_salud_id: Math.random() > 0.5 ? 1 : 2,
    fecha_reporte: randomDate.toISOString().split('T')[0],
    datos: {
      datos_generales: {
        folio: `FOL-${i+1000}`,
        fecha_consulta: randomDate.toISOString().split('T')[0],
        unidad_notificante: Math.random() > 0.5 ? 'Hospital' : 'Centro Salud',
        clave_unidad: Math.random() > 0.5 ? 'HGC001' : 'CSU002'
      },
      datos_paciente: {
        curp: `CURP${i.toString().padStart(4, '0')}`,
        edad: Math.floor(Math.random() * 80) + 1,
        sexo: Math.random() > 0.5 ? 'H' : 'M',
        entidad_residencia: 'Estado de México',
        municipio_residencia: municipios[Math.floor(Math.random() * municipios.length)]
      },
      datos_clinicos: {
        fecha_inicio_sintomas: new Date(randomDate.getTime() - Math.floor(Math.random() * 15) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        diagnostico: diagnosticos[Math.floor(Math.random() * diagnosticos.length)],
        codigo_cie10: 'A90',
        tratamiento: 'Sintomático'
      },
      factores_riesgo: {
        embarazo: Math.random() > 0.8,
        diabetes: Math.random() > 0.8,
        obesidad: Math.random() > 0.7,
        hipertension: Math.random() > 0.75
      }
    }
  };
});