# cardsorter
Robot for sorting CCG cards

# Databases

## Remote

The backend webservices store data about players' collections.

## Local

The local database stores data about the cards themselves, including hashes of the card images and the local path where the images have been downloaded.

### Schema

Cards

| Field            | Type   |
|------------------|--------|
| id               | int    |
| scryfall_id      | string |
| set_id           | string |
| collector_number | string |
| name             | string |
| value            | int    |

Faces

| Field       | Type   |
|-------------|--------|
| id          | int    |
| card_id     | int    |
| image_url   | string |
| image_path  | string |
| hash        | string |

# The Robot

The purpose of the robot is to take a stack of cards, identify them, and add them to a collection. 
Valuable cards and unidentifiable cards are sorted into a separate piles.

## Components

### Cardsorter

The cardsorter is the main component of the robot. It takes a stack of cards and identifies them.

On startup, it prompts the user to login to the backend, and fetches the list of collections from the API.

Next it loads the local database, and prepares the image hashes for searching.

### Downloader

The downloader fetches the All Cards bulk data from Scryfall, and downloads the best image for each card face.

It is responsible for maintaining the local database. On each run, it checks for updated bulk data, and updates the local database with the new cards. 
It then downloads the images for any cards that don't have them.
