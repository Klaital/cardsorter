import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LibraryServiceService } from '../generated/api';
import type { v1Library } from '../generated/api';
import './LibrariesPage.css';

export function LibrariesPage() {
  const [libraries, setLibraries] = useState<v1Library[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadLibraries();
  }, []);

  const loadLibraries = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await LibraryServiceService.libraryServiceGetLibraries();
      setLibraries(response.libraries || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load libraries');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">Loading libraries...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <header className="page-header">
        <h1>My Libraries</h1>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </header>

      {error && <div className="error-message">{error}</div>}

      {libraries.length === 0 ? (
        <div className="empty-state">
          <p>No libraries found. Create your first library to get started!</p>
        </div>
      ) : (
        <div className="libraries-grid">
          {libraries.map((library) => (
            <Link
              key={library.id}
              to={`/libraries/${library.id}`}
              className="library-card"
            >
              <h2>{library.name}</h2>
              <div className="library-stats">
                <div className="stat">
                  <span className="stat-label">Cards</span>
                  <span className="stat-value">{library.cardCount || 0}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Value</span>
                  <span className="stat-value">
                    ${((library.totalValue || 0) / 100).toFixed(2)}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
