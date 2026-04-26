import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  role: string;
  balance: number;
}

interface AppState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  updateBalance: (balance: number) => void;
}

export const useStore = create<AppState>((set) => ({
  token: localStorage.getItem('token'),
  user: null, // Would fetch on load ideally
  setAuth: (token, user) => {
    localStorage.setItem('token', token);
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null });
  },
  updateBalance: (balance) => set((state) => ({ 
    user: state.user ? { ...state.user, balance } : null 
  })),
}));
