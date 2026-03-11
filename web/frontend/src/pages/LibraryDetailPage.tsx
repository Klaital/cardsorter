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
                <th>Name</th>
                <th>Set</th>
                <th>Collector #</th>
                <th>Rarity</th>
                <th>Foil</th>
                <th className="text-center">Qty</th>
                <th className="text-right">Price (USD)</th>
              </tr>
            </thead>
            <tbody>
              {cards.map((card) => {
                const unitPrice = card.currentUsdPrice || card.usdPrice || 0;
                const qty = card.qty || 1;
                const totalPrice = unitPrice * qty;
                const isExpanded = expandedPrices.has(card.id || '');

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
