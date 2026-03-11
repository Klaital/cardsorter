import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LibraryServiceService, CardsService } from '../generated/api';
import type { v1Library } from '../generated/api';
import './LibrariesPage.css';

export function LibrariesPage() {
  const [libraries, setLibraries] = useState<v1Library[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newLibraryName, setNewLibraryName] = useState('');
  const [creating, setCreating] = useState(false);
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

  const handleCreateLibrary = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLibraryName.trim()) return;

    try {
      setCreating(true);
      setError('');
      await CardsService.libraryServiceCreateLibrary({ name: newLibraryName });
      setNewLibraryName('');
      setShowCreateModal(false);
      await loadLibraries();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create library');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteLibrary = async (libraryId: string, libraryName: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm(`Are you sure you want to delete "${libraryName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setError('');
      await LibraryServiceService.libraryServiceDeleteLibrary(libraryId);
      await loadLibraries();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete library');
    }
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
        <div className="header-actions">
          <button onClick={() => setShowCreateModal(true)} className="create-button">
            Create Library
          </button>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}

      {libraries.length === 0 ? (
        <div className="empty-state">
          <p>No libraries found. Create your first library to get started!</p>
        </div>
      ) : (
        <div className="libraries-grid">
          {libraries.map((library) => (
            <div key={library.id} className="library-card-wrapper">
              <Link
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
              <button
                onClick={(e) => handleDeleteLibrary(library.id!, library.name!, e)}
                className="delete-button"
                title="Delete library"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Library</h2>
            <form onSubmit={handleCreateLibrary}>
              <div className="form-group">
                <label htmlFor="libraryName">Library Name</label>
                <input
                  id="libraryName"
                  type="text"
                  value={newLibraryName}
                  onChange={(e) => setNewLibraryName(e.target.value)}
                  placeholder="Enter library name"
                  autoFocus
                  disabled={creating}
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="cancel-button"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-button"
                  disabled={creating || !newLibraryName.trim()}
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
