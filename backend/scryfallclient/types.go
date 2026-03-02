package scryfallclient

import "github.com/google/uuid"

type ImageUris struct {
	Small      string `json:"small"`
	Normal     string `json:"normal"`
	Large      string `json:"large"`
	Png        string `json:"png"`
	ArtCrop    string `json:"art_crop"`
	BorderCrop string `json:"border_crop"`
}

type CardData struct {
	Object        string    `json:"object"`
	ID            uuid.UUID `json:"id"`
	OracleID      uuid.UUID `json:"oracle_id"`
	MultiverseIds []any     `json:"multiverse_ids"`
	TcgplayerID   int       `json:"tcgplayer_id"`
	Name          string    `json:"name"`
	Lang          string    `json:"lang"`
	ReleasedAt    string    `json:"released_at"`
	URI           string    `json:"uri"`
	ScryfallURI   string    `json:"scryfall_uri"`
	Layout        string    `json:"layout"`
	HighresImage  bool      `json:"highres_image"`
	ImageStatus   string    `json:"image_status"`
	ImageUris     ImageUris `json:"image_uris"`
	ManaCost      string    `json:"mana_cost"`
	Cmc           float64   `json:"cmc"`
	TypeLine      string    `json:"type_line"`
	OracleText    string    `json:"oracle_text"`
	Power         string    `json:"power"`
	Toughness     string    `json:"toughness"`
	Colors        []string  `json:"colors"`
	ColorIdentity []string  `json:"color_identity"`
	Keywords      []any     `json:"keywords"`
	AllParts      []struct {
		Object    string    `json:"object"`
		ID        uuid.UUID `json:"id"`
		Component string    `json:"component"`
		Name      string    `json:"name"`
		TypeLine  string    `json:"type_line"`
		URI       string    `json:"uri"`
	} `json:"all_parts"`
	Legalities struct {
		Standard        string `json:"standard"`
		Future          string `json:"future"`
		Historic        string `json:"historic"`
		Timeless        string `json:"timeless"`
		Gladiator       string `json:"gladiator"`
		Pioneer         string `json:"pioneer"`
		Modern          string `json:"modern"`
		Legacy          string `json:"legacy"`
		Pauper          string `json:"pauper"`
		Vintage         string `json:"vintage"`
		Penny           string `json:"penny"`
		Commander       string `json:"commander"`
		Oathbreaker     string `json:"oathbreaker"`
		Standardbrawl   string `json:"standardbrawl"`
		Brawl           string `json:"brawl"`
		Alchemy         string `json:"alchemy"`
		Paupercommander string `json:"paupercommander"`
		Duel            string `json:"duel"`
		Oldschool       string `json:"oldschool"`
		Premodern       string `json:"premodern"`
		Predh           string `json:"predh"`
	} `json:"legalities"`
	Games           []string  `json:"games"`
	Reserved        bool      `json:"reserved"`
	GameChanger     bool      `json:"game_changer"`
	Foil            bool      `json:"foil"`
	Nonfoil         bool      `json:"nonfoil"`
	Finishes        []string  `json:"finishes"`
	Oversized       bool      `json:"oversized"`
	Promo           bool      `json:"promo"`
	Reprint         bool      `json:"reprint"`
	Variation       bool      `json:"variation"`
	SetID           uuid.UUID `json:"set_id"`
	Set             string    `json:"set"`
	SetName         string    `json:"set_name"`
	SetType         string    `json:"set_type"`
	SetURI          string    `json:"set_uri"`
	SetSearchURI    string    `json:"set_search_uri"`
	ScryfallSetURI  string    `json:"scryfall_set_uri"`
	RulingsURI      string    `json:"rulings_uri"`
	PrintsSearchURI string    `json:"prints_search_uri"`
	CollectorNumber string    `json:"collector_number"`
	Digital         bool      `json:"digital"`
	Rarity          string    `json:"rarity"`
	CardBackID      uuid.UUID `json:"card_back_id"`
	Artist          string    `json:"artist"`
	ArtistIds       []string  `json:"artist_ids"`
	IllustrationID  uuid.UUID `json:"illustration_id"`
	BorderColor     string    `json:"border_color"`
	Frame           string    `json:"frame"`
	FullArt         bool      `json:"full_art"`
	Textless        bool      `json:"textless"`
	Booster         bool      `json:"booster"`
	StorySpotlight  bool      `json:"story_spotlight"`
	PromoTypes      []string  `json:"promo_types"`
	Prices          struct {
		Usd       string `json:"usd"`
		UsdFoil   any    `json:"usd_foil"`
		UsdEtched any    `json:"usd_etched"`
		Eur       any    `json:"eur"`
		EurFoil   any    `json:"eur_foil"`
		Tix       any    `json:"tix"`
	} `json:"prices"`
	RelatedUris struct {
		TcgplayerInfiniteArticles string `json:"tcgplayer_infinite_articles"`
		TcgplayerInfiniteDecks    string `json:"tcgplayer_infinite_decks"`
		Edhrec                    string `json:"edhrec"`
	} `json:"related_uris"`
	PurchaseUris struct {
		Tcgplayer   string `json:"tcgplayer"`
		Cardmarket  string `json:"cardmarket"`
		Cardhoarder string `json:"cardhoarder"`
	} `json:"purchase_uris"`
	CardFaces []CardFace `json:"card_faces"`
}

type CardFace struct {
	Object         string    `json:"object"`
	Name           string    `json:"name"`
	ManaCost       string    `json:"mana_cost"`
	TypeLine       string    `json:"type_line"`
	OracleText     string    `json:"oracle_text"`
	Colors         []string  `json:"colors"`
	Artist         string    `json:"artist"`
	ArtistID       uuid.UUID `json:"artist_id"`
	IllustrationID uuid.UUID `json:"illustration_id"`
	ImageUris      ImageUris `json:"image_uris"`
}

func (c CardData) GetCardFaces() []CardFace {
	if len(c.CardFaces) == 0 {
		return []CardFace{CardFace{
			Name:           c.Name,
			ManaCost:       c.ManaCost,
			TypeLine:       c.TypeLine,
			Colors:         c.Colors,
			Artist:         c.Artist,
			IllustrationID: c.IllustrationID,
			ImageUris:      c.ImageUris,
		}}
	}
	return c.CardFaces
}
