package models

type CreateUserRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type CreateLibraryRequest struct {
	Name string `json:"name"`
}

type CreateCardRequest struct {
	Name            string `json:"name"`
	SetName         string `json:"set_name"`
	Condition       string `json:"condition"`
	Foil            bool   `json:"foil"`
	CollectorNumber string `json:"collector_number"`
	USDPrice        int32  `json:"usd_price"`
}

type MoveCardRequest struct {
	NewLibraryID int64 `json:"new_library_id"`
}
