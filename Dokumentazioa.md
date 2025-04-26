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