
```
+------------------+       +-----------------+       +------------------+
|                  |       |                 |       |                  |
|     FRONTEND     |<----->|     BACKEND     |<----->|   IA ZERBITZUA   |
|                  |  HTTP |                 |  HTTP |                  |
| (React/Angular/  |  REST | (Flask/FastAPI) |       | (GroQ kudeatzail)|
|  Vue/Svelte)     |       |                 |       |                  |
+------------------+       +-----------------+       +------------------+
                                   ^ |                       |
                                   | v                       v
                           +----------------+        +----------------+
                           |                |        |                |
                           |    MONGODB     |        |   GROQ MODELS  |
                           |                |        |                |
                           | (Erabiltzaile, |        |    (LLMs)      |
                           |  Partidak)     |        |                |
                           +----------------+        +----------------+
```

### 11.2. Frontend-Backend Komunikazioa

```
+----------------+       HTTP Eskaera        +----------------+
|                |  ---------------------->  |                |
|    Frontend    |                           |    Backend     |
|    (Node.js)   |  <----------------------  |    (Python)    |
|                |       HTTP Erantzuna      |                |
+----------------+                           +----------------+
```

#### IA Txandaren Bistaratzeko Komunikazioa

```
+------------------+                               +------------------+
|                  |  1. POST /api/game/endTurn    |                  |
|     Frontend     |  ----------------------->     |     Backend      |
| (React/Vue/etc.) |                               |   (FastAPI)      |
|                  |  2. IA ekintzak prozesatzen   |                  |
|                  |                               |                  |
|                  |  3. Ekintzen eta egoeren      |                  |
|                  |     zerrenda sekuentziala     |                  |
|                  |     itzultzen du              |                  |
|                  |  <-----------------------     |                  |
|                  |                               |                  |
|   IA txandaren   |  4. Ekintzak sekuentzialki    |                  |
|   bistaratze     |     erreproduzitzen ditu      |                  |
|   zatitua        |     (animazioa)               |                  |
+------------------+                               +------------------+
```

#### Komunikazio fluxua:

1. **Autentikazioa eta Erabiltzaile Kudeaketa**:
   - Erabiltzaile berriaren erregistroa (POST /api/auth/register)
   - Erabiltzaile login-a (POST /api/auth/login)
   - Erabiltzaile profila lortzea (GET /api/auth/profile)
   - Profila eguneratzea (PUT /api/auth/profile)

2. **Partiden Kudeaketa**:
   - Gordetako partidak zerrendatzea (GET /api/games)
   - Partida berria sortzea (POST /api/games)
   - Uneko partida gordetzea (POST /api/games/{gameId}/save)
   - Gordetako partida kargatzea (GET /api/games/{gameId})
   - Eszenatoki erabilgarriak zerrendatzea (GET /api/scenarios)

3. **Jokalariaren txandan**:
   - Frontend-ak jokalariaren ekintzak bidaltzen ditu (POST /api/games/{gameId}/action)
   - Backend-ak ekintzak balidatzen eta prozesatzen ditu
   - Backend-ak emaitza eta egoera berria itzultzen du

4. **Jokalariaren txanda amaieran**:
   - Frontend-ak txanda amaiera eskaera bidaltzen du (POST /api/games/{gameId}/endTurn)
   - Backend-ak txanda amaiera prozesatzen du (baliabide kalkulua, etab.)
   - Backend-ak uneko egoera gordetzen du (auto-gordetzea)
   - Backend-ak IA-ren txanda hasten du

5. **Trikimailu Sistema**:
   - Frontend-ak Ctrl+Tab konbinazioa detektatzen du eta txat interfazea erakusten du
   - Frontend-ak trikimailu kodea bidaltzen du (POST /api/games/{gameId}/cheat)
   - Backend-ak kodea balidatzen du eta dagozkion efektuak aplikatzen ditu
   - Backend-ak jokoaren egoera berria itzultzen du aplikatutako aldaketekin

### 11.3. Backend-MongoDB Komunikazioa

```
+----------------+      MongoDB Driver       +----------------+
|                |  ---------------------->  |                |
|    Backend     |                           |    MongoDB     |
|    (Python)    |  <----------------------  |                |
|                |       Kontsulta Emaitzak  |                |
+----------------+                           +----------------+
```

#### Datu-basearen Egitura:

1. **Erabiltzaile Bilduma**:
   ```json
   {
     "_id": "ObjectId",
     "username": "string",
     "email": "string",
     "password_hash": "string",
     "created_at": "date",
     "last_login": "date"
   }
   ```

2. **Partida Bilduma**:
   ```json
   {
     "_id": "ObjectId",
     "user_id": "ObjectId",
     "name": "string",
     "scenario_id": "string",
     "created_at": "date",
     "last_saved": "date",
     "is_autosave": "boolean",
     "cheats_used": ["string"],
     "game_state": {
       "turn": "number",
       "player": {
         "cities": [...],
         "units": [...],
         "technologies": [...],
         "resources": {...}
       },
       "ai": {
         "cities": [...],
         "units": [...],
         "technologies": [...],
         "resources": {...}
       },
       "map": {
         "size": {"width": "number", "height": "number"},
         "tiles": [...],
         "fog_of_war": [...]
       },
       "current_player": "string"
     }
   }
   ```

3. **Eszenatoki Bilduma**:
   ```json
   {
     "_id": "ObjectId",
     "name": "string",
     "description": "string",
     "difficulty": "string",
     "map_size": {"width": "number", "height": "number"},
     "initial_state": {...}
   }
   ```

### 11.4. Backend-IA Zerbitzua Komunikazioa

```
+----------------+       API Eskaera         +----------------+
|                |  ---------------------->  |                |
|    Backend     |                           |  GroQ Models   |
|    (Python)    |  <----------------------  |                |
|                |       API Erantzuna       |                |
+----------------+                           +----------------+
```

#### Komunikazio fluxua:

1. **IA Hasieratzea**:
   - Backend-ak hasierako prompt-a bidaltzen du jokoaren deskribapena eta arauak dituena
   - Backend-ak elkarrizketa testuingurua gordetzen du

2. **IA-ren Txanda**:
   - Backend-ak IA-rentzat ikusgai den egoera prestatzen du (JSON)
   - Backend-ak egoera GroQ-ren lehen mailako modelora bidaltzen du
   - 429 errorea badago (token muga), ordezko modelora aldatzen da
   - GroQ-k IA-ren erabakiak JSON formatuan itzultzen ditu
   - Backend-ak IA-ren ekintzak balidatzen eta exekutatzen ditu
   - Backend-ak jokoaren egoera eguneratzen du
   - Backend-ak ekintzen sekuentzia bidalten dio frontend-ari bisualizaziorako

3. **Testuinguruaren Kudeaketa**:
   - Backend-ak ekintza garrantzitsuen laburpen historia mantentzen du
   - Testuingurua mugatzen da token mugak ez gainditzeko
   - Txanden artean ikasitako estrategiak gordetzen dira

4. **IA-ren Ekintzen Bistaratzea**:
   - Backend-ak egindako ekintzen zerrenda ordenatua sortzen du
   - Ekintza bakoitzak aurretiko eta ondorengo egoera barne hartzen du
   - Sekuentzia osoa frontend-ari bidaltzen zaio animaziorako

## 12. ERANSKINA: PARTIDEN DATU EGITURA

Jarraian partidak gordetzeko JSON formatuaren adibide bat erakusten da:

### 12.1 Gordetako Partidaren Formatua

```json
{
  "game_id": "65f1a2b3c4d5e6f7a8b9c0d1",
  "name": "Nire partida IA-ren aurka",
  "scenario_id": "basic_map_1",
  "created_at": "2025-04-01T18:30:22.123Z",
  "last_saved": "2025-04-01T19:45:33.456Z",
  "turn": 12,
  "current_player": "player",
  "cheats_used": ["mapa_agertu", "maila_igo"],
  "player": {
    "resources": {
      "food": 35,
      "production": 28,
      "science": 15,
      "gold": 420
    },
    "cities": [
      {
        "id": "city1",
        "name": "Bilbo",
        "position": {"x": 15, "y": 22},
        "population": 5,
        "buildings": [
          {"id": "granary", "type": "food_building"},
          {"id": "library", "type": "science_building"},
          {"id": "barracks", "type": "military_building"}
        ],
        "production": {
          "current_item": "warrior",
          "turns_remaining": 3
        }
      }
    ],
    "units": [
      {
        "id": "unit1",
        "type": "settler",
        "position": {"x": 12, "y": 18},
        "movement_points": 2,
        "movement_points_left": 1
      },
      {
        "id": "unit2",
        "type": "warrior",
        "position": {"x": 14, "y": 20},
        "movement_points": 2,
        "movement_points_left": 0,
        "strength": 5,
        "health": 100
      }
    ],
    "technologies": [
      {"id": "agriculture", "completed": true},
      {"id": "pottery", "completed": true},
      {"id": "animal_husbandry", "in_progress": true, "turns_remaining": 4}
    ]
  },
  "ai": {
    "resources": {
      "food": 40,
      "production": 22,
      "science": 10,
      "gold": 380
    },
    "cities": [
      {
        "id": "ai_city1",
        "name": "Erroma",
        "position": {"x": 42, "y": 35},
        "visible": false
      }
    ],
    "units": [
      {
        "id": "ai_unit1",
        "type": "unknown",
        "position": {"x": 45, "y": 38},
        "visible": false
      }
    ],
    "technologies": []
  },
  "map": {
    "size": {"width": 72, "height": 72},
    "explored": [
      [0, 0, 0, 0, 1, 1, 1, 0, 0],
      [0, 0, 1, 1, 1, 1, 1, 1, 0],
      [0, 1, 1, 1, 1, 1, 1, 1, 0],
      [1, 1, 1, 1, 1, 1, 1, 0, 0]
    ],
    "visible_objects": [
      {
        "type": "resource",
        "resource_type": "iron",
        "position": {"x": 14, "y": 25},
        "improved": true
      },
      {
        "type": "resource",
        "resource_type": "cattle",
        "position": {"x": 18, "y": 19},
        "improved": false
      },
      {
        "type": "barbarian_camp",
        "position": {"x": 22, "y": 28}
      }
    ]
  }
}
```

### 12.2 IA Txanda Bistaratzearen Egitura

IA-ren txandaren bistaratzea errazteko, ondorengo JSON formatua erabiliko da:

```json
{
  "ai_turn_id": "65f1a2b3c4d5e6f7a8b9c0d2",
  "game_id": "65f1a2b3c4d5e6f7a8b9c0d1",
  "turn_number": 12,
  "actions": [
    {
      "action_id": 1,
      "type": "moveUnit",
      "unitId": "ai_unit1",
      "path": [
        {"x": 42, "y": 35},
        {"x": 43, "y": 35},
        {"x": 44, "y": 36}
      ],
      "state_before": {
        "resources": { /* aurretiko egoera laburra */ },
        "units": { /* aurretiko egoera laburra */ },
        "visible_map": { /* aurretiko egoera laburra */ }
      },
      "state_after": {
        "resources": { /* ondorengo egoera laburra */ },
        "units": { /* ondorengo egoera laburra */ },
        "visible_map": { /* ondorengo egoera laburra */ }
      },
      "timestamp": "2025-04-01T19:40:15.123Z"
    },
    {
      "action_id": 2,
      "type": "buildStructure",
      "cityId": "ai_city1",
      "structureType": "library",
      "state_before": { /* aurretiko egoera laburra */ },
      "state_after": { /* ondorengo egoera laburra */ },
      "timestamp": "2025-04-01T19:40:18.456Z"
    },
    {
      "action_id": 3,
      "type": "combat",
      "attacker": {
        "unitId": "ai_unit2",
        "type": "warrior",
        "strength": 5
      },
      "defender": {
        "type": "barbarian",
        "position": {"x": 44, "y": 36},
        "strength": 4
      },
      "result": {
        "winner": "attacker",
        "casualties": {
          "attacker": {"damage": 20},
          "defender": {"killed": true}
        },
        "rewards": {
          "gold": 50
        }
      },
      "state_before": { /* aurretiko egoera laburra */ },
      "state_after": { /* ondorengo egoera laburra */ },
      "timestamp": "2025-04-01T19:40:25.789Z"
    },
    {
      "action_id": 4,
      "type": "endTurn",
      "state_before": { /* aurretiko egoera laburra */ },
      "state_after": { /* ondorengo egoera laburra */ },
      "timestamp": "2025-04-01T19:40:30.123Z"
    }
  ],
  "reasoning": "Nire unitate nagusia ekialderantz mugitzen nabil burdin mineralaren bila, aldi berean nire hiria garatzen liburutegi bat eraikiz teknologia berrien ikerketa azkartzeko."
}
```

### 12.3 Trikimailu Sistemaren Formatua

Trikimailu kodeak kudeatzeko, ondorengo eskaera eta erantzun formatua erabiliko da:

**Eskaera:**
```json
{
  "game_id": "65f1a2b3c4d5e6f7a8b9c0d1",
  "cheat_code": "maila_igo",
  "target": {
    "type": "city",
    "id": "city1"
  }
}
```

**Erantzuna:**
```json
{
  "success": true,
  "message": "Hiria maila bat igo da",
  "affected_entity": {
    "type": "city",
    "id": "city1",
    "changes": {
      "population": {"before": 5, "after": 6},
      "growth": {"before": 3, "after": 4}
    }
  },
  "game_state": {
    /* Jokoaren egoera eguneratua */
  }
}
```
