import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useStore } from './store';
import Login from './pages/Login';
import DashboardLayout from './components/DashboardLayout';
import EditorPage from './pages/EditorPage';
import JobsList from './pages/JobsList';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useStore((state) => state.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/editor" replace />} />
          <Route path="editor" element={<EditorPage />} />
          <Route path="jobs" element={<JobsList />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
