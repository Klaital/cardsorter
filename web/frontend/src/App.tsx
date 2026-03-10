import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { LibrariesPage } from './pages/LibrariesPage';
import { LibraryDetailPage } from './pages/LibraryDetailPage';
import './App.css';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return !isAuthenticated ? <>{children}</> : <Navigate to="/libraries" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/libraries"
        element={
          <ProtectedRoute>
            <LibrariesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/libraries/:libraryId"
        element={
          <ProtectedRoute>
            <LibraryDetailPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/libraries" replace />} />
      <Route path="*" element={<Navigate to="/libraries" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
