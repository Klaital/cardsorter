package server

import (
	"context"
	"database/sql"
	"errors"
	pb "github.com/klaital/cardsorter/backend/gen/protos"
	carddb "github.com/klaital/cardsorter/backend/internal/db"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"
	"log/slog"
)

type CardServer struct {
	pb.UnimplementedCardServiceServer
	db *sql.DB
}

func NewCardServer(db *sql.DB) *CardServer {
	return &CardServer{db: db}
}

func (s *CardServer) CreateCard(ctx context.Context, req *pb.CreateCardRequest) (*pb.CreateCardResponse, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, err
	}

	queries := carddb.New(s.db)

	// Verify library ownership
	_, err = queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "library not found")
		}
		return nil, status.Error(codes.Internal, "failed to verify library ownership")
	}

	resp, err := queries.CreateCard(ctx, carddb.CreateCardParams{
		LibraryID:    req.LibraryId,
		Name:         req.Name,
		SetName:      req.SetName,
		//TODO: add Cnd:           req.Condition,
		Foil:         sql.NullBool{Bool: req.Foil, Valid: true},
		CollectorNum: req.CollectorNumber,
		Usd:          req.UsdPrice,
		Comment:      req.Comment,
	})
	if err != nil {
		slog.Error("Failed to create card", "err", err.Error())
		return nil, status.Error(codes.Internal, "failed to create card")
	}
	cardId, err := resp.LastInsertId()
	if err != nil {
		slog.Error("Failed to get new card id", "err", err)
		return nil, status.Error(codes.Internal, "Failed to fetch new card id")
	}
	newCard, err := queries.GetCard(ctx, cardId)
	if err != nil {
		slog.Error("Failed to fetch new card", "err", err)
		return nil, status.Error(codes.Internal, "Failed to fetch new card")
	}

	return &pb.CreateCardResponse{
		Card: toProtoCard(newCard),
	}, nil
}

func (s *CardServer) GetCards(ctx context.Context, req *pb.GetCardsRequest) (*pb.GetCardsResponse, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, err
	}

	queries := carddb.New(s.db)

	// Verify library ownership
	_, err = queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, status.Error(codes.NotFound, "library not found")
		}
		return nil, status.Error(codes.Internal, "failed to verify library ownership")
	}

	cards, err := queries.GetCards(ctx, req.LibraryId)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to fetch cards")
	}

	response := &pb.GetCardsResponse{
		Cards: make([]*pb.Card, 0, len(cards)),
	}
	for _, card := range cards {
		response.Cards = append(response.Cards, toProtoCardFromCardsRow(card))
	}

	return response, nil
}

func (s *CardServer) GetCard(ctx context.Context, req *pb.GetCardRequest) (*pb.GetCardResponse, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, err
	}

	queries := carddb.New(s.db)

	// Verify library ownership
	// TODO: verify ownership in the same query as fetching the card data.
	_, err = queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "library not found")
		}
		return nil, status.Error(codes.Internal, "failed to verify library ownership")
	}

	card, err := queries.GetCard(ctx, req.CardId)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "card not found")
		}
		return nil, status.Error(codes.Internal, "failed to fetch card")
	}

	return &pb.GetCardResponse{
		Card: toProtoCard(card),
	}, nil
}

func (s *CardServer) MoveCard(ctx context.Context, req *pb.MoveCardRequest) (*emptypb.Empty, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, err
	}

	queries := carddb.New(s.db)

	// Verify source library ownership
	_, err = queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "source library not found")
		}
		return nil, status.Error(codes.Internal, "failed to verify source library ownership")
	}

	// Verify destination library ownership
	_, err = queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "destination library not found")
		}
		return nil, status.Error(codes.Internal, "failed to verify destination library ownership")
	}

	err = queries.MoveCard(ctx, carddb.MoveCardParams{
		ID:        req.CardId,
		LibraryID: req.LibraryId,
	})
	if err != nil {
		slog.Error("failed to move card", "err", err, "card", req.CardId, "library", req.LibraryId, "user", userID)
		return nil, status.Error(codes.Internal, "failed to move card")
	}

	return &emptypb.Empty{}, nil
}

func (s *CardServer) UpdateCard(ctx context.Context, req *pb.UpdateCardRequest) (*pb.UpdateCardResponse, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, err
	}

	queries := carddb.New(s.db)

	// Verify library ownership
	_, err = queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "library not found")
		}
		return nil, status.Error(codes.Internal, "failed to verify library ownership")
	}

	// Get current card to preserve existing data
	card, err := queries.GetCard(ctx, req.CardId)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "card not found")
		}
		return nil, status.Error(codes.Internal, "failed to fetch card")
	}

	// Update the card
	err = queries.UpdateCard(ctx, carddb.UpdateCardParams{
		ID:      req.CardId,
		Name:    card.Name,
		Usd:     card.Usd,
		Comment: req.Comment,
	})
	if err != nil {
		slog.Error("Failed to update card", "err", err.Error())
		return nil, status.Error(codes.Internal, "failed to update card")
	}

	// Fetch updated card
	updatedCard, err := queries.GetCard(ctx, req.CardId)
	if err != nil {
		slog.Error("Failed to fetch updated card", "err", err)
		return nil, status.Error(codes.Internal, "failed to fetch updated card")
	}

	return &pb.UpdateCardResponse{
		Card: toProtoCard(updatedCard),
	}, nil
}

func (s *CardServer) DeleteCard(ctx context.Context, req *pb.DeleteCardRequest) (*emptypb.Empty, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, err
	}

	queries := carddb.New(s.db)

	// Verify library ownership
	_, err = queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, status.Error(codes.NotFound, "library not found")
		}
		return nil, status.Error(codes.Internal, "failed to verify library ownership")
	}

	err = queries.DeleteCard(ctx, req.CardId)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "card not found")
		}
		return nil, status.Error(codes.Internal, "failed to delete card")
	}

	return &emptypb.Empty{}, nil
}

// Helper function to convert database card row to proto card
func toProtoCard(card carddb.GetCardRow) *pb.Card {
	// Use scryfall name if available, fallback to user-entered name
	name := card.Name
	if card.ScryfallName.Valid && card.ScryfallName.String != "" {
		name = card.ScryfallName.String
	}

	// Use calculated current price if available, fallback to stored price
	price := card.Usd
	if card.CurrentUsdPrice != nil {
		if priceInt, ok := card.CurrentUsdPrice.(int32); ok {
			price = priceInt
		} else if priceInt64, ok := card.CurrentUsdPrice.(int64); ok {
			price = int32(priceInt64)
		}
	}

	pbCard := &pb.Card{
		Id:              card.ID,
		LibraryId:       card.LibraryID,
		Name:            name,
		SetId:           card.SetName,
		CollectorNumber: card.CollectorNum,
		Foil:            card.Foil.Bool,
		UsdPrice:        price,
		CurrentUsdPrice: price,
		Qty:             int32(card.Qty),
		Comment:         card.Comment,
	}

	// Add rarity if available
	if card.Rarity.Valid {
		pbCard.Rarity = card.Rarity.String
	}

	// Add created_at timestamp
	if card.CreatedAt.Valid {
		pbCard.CreatedAt = timestamppb.New(card.CreatedAt.Time)
	}

	return pbCard
}

// Helper function to convert GetCardsRow to proto card
func toProtoCardFromCardsRow(card carddb.GetCardsRow) *pb.Card {
	// Use scryfall name if available, fallback to user-entered name
	name := card.Name
	if card.ScryfallName.Valid && card.ScryfallName.String != "" {
		name = card.ScryfallName.String
	}

	// Use calculated current price if available, fallback to stored price
	price := card.Usd
	if card.CurrentUsdPrice != nil {
		if priceInt, ok := card.CurrentUsdPrice.(int32); ok {
			price = priceInt
		} else if priceInt64, ok := card.CurrentUsdPrice.(int64); ok {
			price = int32(priceInt64)
		}
	}

	pbCard := &pb.Card{
		Id:              card.ID,
		LibraryId:       card.LibraryID,
		Name:            name,
		SetId:           card.SetName,
		CollectorNumber: card.CollectorNum,
		Foil:            card.Foil.Bool,
		UsdPrice:        price,
		CurrentUsdPrice: price,
		Qty:             int32(card.Qty),
		Comment:         card.Comment,
	}

	// Add rarity if available
	if card.Rarity.Valid {
		pbCard.Rarity = card.Rarity.String
	}

	// Add created_at timestamp
	if card.CreatedAt.Valid {
		pbCard.CreatedAt = timestamppb.New(card.CreatedAt.Time)
	}

	return pbCard
}
