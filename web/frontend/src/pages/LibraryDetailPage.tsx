import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { CardsService, LibraryServiceService } from '../generated/api';
import type { v1Card, v1Library } from '../generated/api';
import './LibraryDetailPage.css';

export function LibraryDetailPage() {
  const { libraryId } = useParams<{ libraryId: string }>();
  const [library, setLibrary] = useState<v1Library | null>(null);
  const [cards, setCards] = useState<v1Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedPrices, setExpandedPrices] = useState<Set<string>>(new Set());
  const [editingComment, setEditingComment] = useState<string | null>(null);
  const [commentText, setCommentText] = useState<string>('');
  const [sortColumn, setSortColumn] = useState<string>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (libraryId) {
      loadLibraryData();
    }
  }, [libraryId]);

  const loadLibraryData = async () => {
    if (!libraryId) return;

    try {
      setLoading(true);
      setError('');

      console.log('Fetching library:', libraryId);

      const [libraryResponse, cardsResponse] = await Promise.all([
        LibraryServiceService.libraryServiceGetLibrary(libraryId),
        CardsService.cardServiceGetCards(libraryId),
      ]);

      console.log('Library response:', libraryResponse);
      console.log('Cards response:', cardsResponse);

      setLibrary(libraryResponse.library || null);
      setCards(cardsResponse.cards || []);
    } catch (err) {
      console.error('Error loading library:', err);
      setError(err instanceof Error ? err.message : 'Failed to load library');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatPrice = (cents: number | undefined) => {
    if (cents === undefined || cents === null) return 'N/A';
    return `$${(cents / 100).toFixed(2)}`;
  };

  const togglePriceExpanded = (cardId: string) => {
    setExpandedPrices(prev => {
      const next = new Set(prev);
      if (next.has(cardId)) {
        next.delete(cardId);
      } else {
        next.add(cardId);
      }
      return next;
    });
  };

  const startEditingComment = (cardId: string, currentComment: string) => {
    setEditingComment(cardId);
    setCommentText(currentComment || '');
  };

  const cancelEditingComment = () => {
    setEditingComment(null);
    setCommentText('');
  };

  const saveComment = async (cardId: string) => {
    if (!libraryId) return;

    try {
      await CardsService.cardServiceUpdateCard(libraryId, cardId, { comment: commentText });
      // Reload cards to get updated data
      await loadLibraryData();
      setEditingComment(null);
      setCommentText('');
    } catch (err) {
      console.error('Error updating comment:', err);
      setError(err instanceof Error ? err.message : 'Failed to update comment');
    }
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      // Toggle direction if same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column, default to ascending (except for created_at which defaults to descending)
      setSortColumn(column);
      setSortDirection(column === 'created_at' ? 'desc' : 'asc');
    }
  };

  const getSortedCards = () => {
    return [...cards].sort((a, b) => {
      let aVal: any;
      let bVal: any;

      switch (sortColumn) {
        case 'name':
          aVal = a.name?.toLowerCase() || '';
          bVal = b.name?.toLowerCase() || '';
          break;
        case 'set':
          aVal = a.setId?.toLowerCase() || '';
          bVal = b.setId?.toLowerCase() || '';
          break;
        case 'collector_number':
          aVal = a.collectorNumber || '';
          bVal = b.collectorNumber || '';
          break;
        case 'rarity':
          aVal = a.rarity?.toLowerCase() || '';
          bVal = b.rarity?.toLowerCase() || '';
          break;
        case 'foil':
          aVal = a.foil ? 1 : 0;
          bVal = b.foil ? 1 : 0;
          break;
        case 'qty':
          aVal = a.qty || 0;
          bVal = b.qty || 0;
          break;
        case 'price':
          aVal = (a.currentUsdPrice || a.usdPrice || 0) * (a.qty || 1);
          bVal = (b.currentUsdPrice || b.usdPrice || 0) * (b.qty || 1);
          break;
        case 'comment':
          aVal = a.comment?.toLowerCase() || '';
          bVal = b.comment?.toLowerCase() || '';
          break;
        case 'created_at':
          aVal = a.createdAt ? new Date(a.createdAt).getTime() : 0;
          bVal = b.createdAt ? new Date(b.createdAt).getTime() : 0;
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const getSortIndicator = (column: string) => {
    if (sortColumn !== column) return null;
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">Loading library...</div>
      </div>
    );
  }

  if (!library) {
    return (
      <div className="page-container">
        <div className="error-message">Library not found</div>
        <Link to="/libraries" className="back-link">
          ← Back to Libraries
        </Link>
      </div>
    );
  }

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <Link to="/libraries" className="back-link">
            ← Back to Libraries
          </Link>
          <h1>{library.name}</h1>
          <div className="library-summary">
            <span>{cards.length} unique cards</span>
            <span>•</span>
            <span>{cards.reduce((sum, card) => sum + (card.qty || 1), 0)} total copies</span>
            <span>•</span>
            <span>Total Value: {formatPrice(library.totalValue)}</span>
          </div>
        </div>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </header>

      {error && <div className="error-message">{error}</div>}

      {cards.length === 0 ? (
        <div className="empty-state">
          <p>No cards in this library yet.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="cards-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('name')} className="sortable">
                  Name{getSortIndicator('name')}
                </th>
                <th onClick={() => handleSort('set')} className="sortable">
                  Set{getSortIndicator('set')}
                </th>
                <th onClick={() => handleSort('collector_number')} className="sortable">
                  Collector #{getSortIndicator('collector_number')}
                </th>
                <th onClick={() => handleSort('rarity')} className="sortable">
                  Rarity{getSortIndicator('rarity')}
                </th>
                <th onClick={() => handleSort('foil')} className="sortable">
                  Foil{getSortIndicator('foil')}
                </th>
                <th onClick={() => handleSort('qty')} className="text-center sortable">
                  Qty{getSortIndicator('qty')}
                </th>
                <th onClick={() => handleSort('price')} className="text-right sortable">
                  Price (USD){getSortIndicator('price')}
                </th>
                <th onClick={() => handleSort('comment')} className="sortable">
                  Comment{getSortIndicator('comment')}
                </th>
                <th onClick={() => handleSort('created_at')} className="sortable">
                  Added{getSortIndicator('created_at')}
                </th>
              </tr>
            </thead>
            <tbody>
              {getSortedCards().map((card) => {
                const unitPrice = card.currentUsdPrice || card.usdPrice || 0;
                const qty = card.qty || 1;
                const totalPrice = unitPrice * qty;
                const isExpanded = expandedPrices.has(card.id || '');
                const createdDate = card.createdAt ? new Date(card.createdAt) : null;

                return (
                  <tr key={card.id}>
                    <td className="card-name">{card.name || 'Unknown'}</td>
                    <td>{card.setId || 'N/A'}</td>
                    <td>{card.collectorNumber || 'N/A'}</td>
                    <td>
                      <span className={`rarity rarity-${card.rarity?.toLowerCase()}`}>
                        {card.rarity || 'N/A'}
                      </span>
                    </td>
                    <td>{card.foil ? '✨ Yes' : 'No'}</td>
                    <td className="text-center">{qty}</td>
                    <td
                      className="text-right price-cell"
                      onClick={() => togglePriceExpanded(card.id || '')}
                      title="Click to show per-card price"
                    >
                      {formatPrice(totalPrice)}
                      {isExpanded && qty > 1 && (
                        <span className="per-card-price"> ({formatPrice(unitPrice)} ea)</span>
                      )}
                    </td>
                    <td className="comment-cell">
                      {editingComment === card.id ? (
                        <div className="comment-edit">
                          <input
                            type="text"
                            value={commentText}
                            onChange={(e) => setCommentText(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                saveComment(card.id || '');
                              } else if (e.key === 'Escape') {
                                cancelEditingComment();
                              }
                            }}
                            autoFocus
                            placeholder="Add a comment..."
                          />
                          <div className="comment-actions">
                            <button
                              onClick={() => saveComment(card.id || '')}
                              className="save-button"
                              title="Save (Enter)"
                            >
                              ✓
                            </button>
                            <button
                              onClick={cancelEditingComment}
                              className="cancel-button"
                              title="Cancel (Esc)"
                            >
                              ✗
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div
                          className="comment-display"
                          onClick={() => startEditingComment(card.id || '', card.comment || '')}
                          title="Click to edit"
                        >
                          {card.comment || <span className="comment-placeholder">Add comment...</span>}
                        </div>
                      )}
                    </td>
                    <td className="date-cell">
                      {createdDate ? (
                        <span title={createdDate.toLocaleString()}>
                          {createdDate.toLocaleDateString()}
                        </span>
                      ) : (
                        'N/A'
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
