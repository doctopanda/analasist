// Mock authentication service
// In a real application, this would make API calls to your backend

interface User {
  id: number;
  username: string;
  rol: string;
  centro_salud_id?: number;
}

// Mock user database
const users = [
  { id: 1, username: 'admin', password: 'Admin123!', rol: 'admin' },
  { id: 2, username: 'analista1', password: 'Analista123!', rol: 'analista' },
  { id: 3, username: 'hospital1', password: 'Hospital123!', rol: 'centro_salud', centro_salud_id: 1 }
];

export const mockLogin = async (username: string, password: string): Promise<User> => {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const user = users.find(u => u.username === username && u.password === password);
  
  if (!user) {
    throw new Error('Credenciales incorrectas');
  }
  
  // Don't return the password
  const { password: _, ...userWithoutPassword } = user;
  return userWithoutPassword;
};

export const mockLogout = async (): Promise<void> => {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 300));
  // In a real app, this would invalidate the session/token on the server
};