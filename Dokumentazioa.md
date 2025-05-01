# Backend API-aren Dokumentazioa

## Sarrera

Dokumentu honek backend zerbitzariaren API deiak deskribatzen ditu. Hemen azalduko da nola deitu endpoint desberdinak, hauek zer erantzuten duten, eta baita zein endpoint dauden jadanik inplementatuta.

## Oinarrizko URL-a

```
http://localhost:5000
```

## Autentifikazioa

API deietan autentifikatzeko, eskaera gorputzean erabiltzaile izena eta pasahitza bidali behar dira:

```json
{
    "username": "erabiltzailea",
    "password": "pasahitza"
}
```

## API Endpoints-ak

### Proba Endpoint-a

- **Metodoa:** GET
- **Bidea:** `/proba`
- **Deskribapena:** Proba sinple bat egiteko erabiltzen den endpoint-a
- **Inplementazioa:** Bai
- **Erantzuna:**
```
Kaixoooo
```

### Erabiltzaile Endpoints-ak

#### Erabiltzaile berria sortu

- **Metodoa:** POST
- **Bidea:** `/api/users`
- **Deskribapena:** Erabiltzaile berri bat erregistratzen du sisteman
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "username": "erabiltzailea",
    "password": "pasahitza"
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "User created successfully"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Username already exists"
}
```
edo
```json
{
    "error": "Username and password are required"
}
```

#### Erabiltzailea saioa hasteko

- **Metodoa:** POST
- **Bidea:** `/api/login`
- **Deskribapena:** Erabiltzaile baten saioa hasten du
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "username": "erabiltzailea",
    "password": "pasahitza"
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Login successful",
    "user": {
        "username": "erabiltzailea",
        "score": 0,
        "level": 1
    }
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Invalid username or password"
}
```
edo
```json
{
    "error": "Username and password are required"
}
```

#### Erabiltzaile bat lortu

- **Metodoa:** GET
- **Bidea:** `/api/users/{username}`
- **Deskribapena:** Erabiltzaile baten informazioa itzultzen du
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
{
    "username": "erabiltzailea",
    "score": 0,
    "level": 1
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "User not found"
}
```

#### Erabiltzaile guztiak lortu

- **Metodoa:** GET
- **Bidea:** `/api/users/`
- **Deskribapena:** Erabiltzaile guztien informazioa itzultzen du
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
[
{
    "username": "erabiltzailea",
    "score": 0,
    "level": 1
},
{
    "username": "erabiltzailea2",
    "score": 0,
    "level": 1
}
]
```
- **Erantzuna (erroreekin):**
```json
{
    "message": "No users found"
}
```
edo
```json
{
    "error": "Internal server error"
}
```

#### Erabiltzaile baten puntuazioa eguneratu

- **Metodoa:** PUT
- **Bidea:** `/api/users/{username}/score`
- **Deskribapena:** Erabiltzaile baten puntuazioa eguneratzen du
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "score": 100
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Score updated successfully"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "User not found"
}
```
edo
```json
{
    "error": "Score is required"
}
```

#### Saioa amaitu

- **Metodoa:** POST
- **Bidea:** `/api/logout`
- **Deskribapena:** Erabiltzailearen saioa ixten du
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Logged out successfully"
}
```

#### Saioaren egoera egiaztatu

- **Metodoa:** GET
- **Bidea:** `/api/session`
- **Deskribapena:** Egiaztatu erabiltzailea saioan dagoen ala ez
- **Inplementazioa:** Bai
- **Erantzuna (saio aktiboarekin):**
```json
{
    "authenticated": true,
    "user": {
        "username": "erabiltzailea",
        "score": 0,
        "level": 1
    }
}
```
- **Erantzuna (saiorik gabe):**
```json
{
    "authenticated": false
}
```

### Mapen Kudeaketarako

#### Mapa berri bat sortu

- **Metodoa:** POST
- **Bidea:** `/api/maps`
- **Deskribapena:** Mapa berri bat sortzen du jokoan erabiltzeko
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "width": 10,
    "height": 10,
    "startPoint": [5, 5],
    "difficulty": "easy"
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Map created successfully",
    "map_id": "60a1b2c3d4e5f6g7h8i9j0"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Width, height, startPoint, and difficulty are required"
}
```
edo
```json
{
    "error": "Width and height must be integers"
}
```
edo
```json
{
    "error": "StartPoint must be a list of two integers"
}
```
edo
```json
{
    "error": "Difficulty must be 'easy', 'medium', or 'hard'"
}
```

#### Lehenengo mapa lortu

- **Metodoa:** GET
- **Bidea:** `/api/maps/first`
- **Deskribapena:** Datu-baseko lehenengo mapa itzultzen du
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
{
    "width": 30,
    "height": 15,
    "grid": [[0,0,0,...],[0,1,0,...],...],
    "startPoint": [15, 7]
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "No maps found"
}
```
edo
```json
{
    "error": "Internal server error: [error message]"
}
```

### Partiden Kudeaketarako

#### Partida berri bat sortu

- **Metodoa:** POST
- **Bidea:** `/api/game`
- **Deskribapena:** Partida berri bat sortzen du
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "map": "maparen_datuak",
    "difficulty": "zailtasun_maila"
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Game added successfully"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "User not logged in"
}
```

#### Uneko partida lortu

- **Metodoa:** GET
- **Bidea:** `/api/game`
- **Deskribapena:** Uneko partida itzultzen du
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
{
    // Partidaren datu guztiak
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "No game found"
}
```

#### Partida gorde

- **Metodoa:** POST
- **Bidea:** `/api/game/save`
- **Deskribapena:** Uneko partida gordetzen du datu-basean
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Game saved successfully"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Failed to save game"
}
```

### Tropen Kudeaketarako

#### Talde militarren motak lortu

- **Metodoa:** GET
- **Bidea:** `/api/troops/types`
- **Deskribapena:** Eskuragarri dauden tropa mota guztiak itzultzen ditu
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
[
    {
        "type_id": "warrior",
        "name": "Warrior",
        "category": "infantry",
        "health": 100,
        "attack": 10,
        "defense": 10,
        "movement": 2,
        "cost": {
            "food": 50,
            "gold": 10
        },
        "abilities": ["basic_attack"],
        "description": "Basic infantry unit"
    },
    // Beste tropa motak...
]
```

#### Talde militar mota zehatz bat lortu

- **Metodoa:** GET
- **Bidea:** `/api/troops/types/{type_id}`
- **Deskribapena:** Tropa mota zehatz baten informazioa itzultzen du
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
{
    "type_id": "warrior",
    "name": "Warrior",
    "category": "infantry",
    "health": 100,
    "attack": 10,
    "defense": 10,
    "movement": 2,
    "cost": {
        "food": 50,
        "gold": 10
    },
    "abilities": ["basic_attack"],
    "description": "Basic infantry unit"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Troop type not found"
}
```

#### Tropa berri bat sortu

- **Metodoa:** POST
- **Bidea:** `/api/troops`
- **Deskribapena:** Jokalariaren armadara tropa berri bat gehitzen du
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "type_id": "warrior",
    "position": [10, 5]
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Troop added successfully",
    "troop": {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "type_id": "warrior",
        "name": "Warrior",
        "health": 100,
        "attack": 10,
        "defense": 10,
        "movement": 2,
        "position": [10, 5],
        "status": "ready",
        "created_at": "2023-05-12T14:20:30.456Z"
    }
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Type ID and position are required"
}
```
edo
```json
{
    "error": "Invalid troop type"
}
```
edo
```json
{
    "error": "Position is out of map bounds"
}
```

#### Jokalariaren tropa guztiak lortu

- **Metodoa:** GET
- **Bidea:** `/api/troops`
- **Deskribapena:** Jokalariaren tropa guztiak itzultzen ditu
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
[
    {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "type_id": "warrior",
        "name": "Warrior",
        "health": 100,
        "attack": 10,
        "defense": 10,
        "movement": 2,
        "position": [10, 5],
        "status": "ready",
        "created_at": "2023-05-12T14:20:30.456Z"
    },
    // Beste tropak...
]
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "User not logged in"
}
```

#### Tropa mugitu

- **Metodoa:** PUT
- **Bidea:** `/api/troops/{troop_id}/move`
- **Deskribapena:** Tropa posizio berri batera mugitzen du
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "position": [12, 6]
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Troop position updated"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Position is required"
}
```
edo
```json
{
    "error": "Position is out of map bounds"
}
```
edo
```json
{
    "error": "Troop not found"
}
```

#### Tropa egoera eguneratu

- **Metodoa:** PUT
- **Bidea:** `/api/troops/{troop_id}/status`
- **Deskribapena:** Tropa baten egoera eguneratzen du
- **Inplementazioa:** Bai
- **Eskaera Gorputza:**
```json
{
    "status": "attacked"
}
```
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "Troop status updated"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "Status is required"
}
```
edo
```json
{
    "error": "Invalid status"
}
```
edo
```json
{
    "error": "Troop not found"
}
```

#### Tropa guztien egoera berrabiarazi

- **Metodoa:** POST
- **Bidea:** `/api/troops/reset`
- **Deskribapena:** Tropa guztien egoera "ready" gisa ezartzen du, txanda berriaren hasieran
- **Inplementazioa:** Bai
- **Erantzuna (arrakastarekin):**
```json
{
    "message": "All troops reset to ready status"
}
```
- **Erantzuna (erroreekin):**
```json
{
    "error": "No troops found for player"
}
```

## Erroreen Kudeaketa

Erroreen kasuan, API-ak ondorengo egiturako erantzunak bueltatzen ditu:

```json
{
    "error": "Errorearen mezua"
}
```

Ohiko errore kodeak:
- `400` - Eskaera okerra (Bad Request)
- `401` - Autentifikatu gabe (Unauthorized)
- `404` - Ez da aurkitu (Not Found)
- `409` - Gatazka (Conflict)
- `500` - Zerbitzariaren barne errorea (Internal Server Error)

## Etorkizuneko Garapenerako Endpoints-ak

Ondorengo endpoints-ak etorkizunean inplementatzeko planifikaturik daude:

### Partiden Kudeaketarako

#### Partida berri bat sortu

- **Metodoa:** POST
- **Bidea:** `/api/games`
- **Deskribapena:** Partida berri bat sortzen du
- **Inplementazioa:** Ez
- **Eskaera Gorputza:**
```json
{
    "username": "erabiltzailea",
    "scenario": "basic_scenario"
}
```
- **Erantzuna:**
```json
{
    "game_id": "12345678",
    "message": "Game created successfully",
    "initial_state": {
        // Jokoaren hasierako egoera
    }
}
```

#### Partida bat gorde

- **Metodoa:** POST
- **Bidea:** `/api/games/{game_id}/save`
- **Deskribapena:** Jokoaren uneko egoera gordetzen du
- **Inplementazioa:** Ez
- **Eskaera Gorputza:**
```json
{
    "game_state": {
        // Jokoaren egoera osoa
    }
}
```
- **Erantzuna:**
```json
{
    "message": "Game saved successfully",
    "saved_at": "2025-04-01T19:45:33.456Z"
}
```

#### Txanda amaitu

- **Metodoa:** POST
- **Bidea:** `/api/games/{game_id}/endTurn`
- **Deskribapena:** Jokalariaren txanda amaitu eta IA-ren txanda hasten du
- **Inplementazioa:** Ez
- **Erantzuna:**
```json
{
    "message": "Turn ended successfully",
    "ai_actions": [
        // IA-k egindako ekintzen zerrenda
    ],
    "updated_state": {
        // Jokoaren egoera eguneratua
    }
}
```

Dokumentazio hau proiektuaren aurrerapen eta aldaketekin batera eguneratuko da.