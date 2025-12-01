# Overview

This is a multiplayer browser-based monster hunting game built with Python WebSocket server and HTML5 Canvas. Players can connect to a shared game world, fight monsters of varying difficulties, level up their characters, collect weapons, and defeat bosses. The game features real-time multiplayer interactions, PvP combat, weapon systems with different rarities, and a progression system with experience and gold collection.

# Recent Changes (Nov 2025)

- **Multiplayer Server**: Combined HTTP (port 5000) and WebSocket (port 8080) server in game_server.py
- **PvP Combat**: All attacks can damage other players, with 3-second respawn on death
- **Boss Loot System**: Damage contributor tracking - player with most total damage gets the loot
- **Healing Potions**: Use via inventory to restore 35 HP
- **Ancient Core Decomposition**: Boss item can be decomposed for 1000 gold
- **W Slot Flame Aura**: Fixed orbital rendering directly in client for consistent visual display

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Game Architecture Pattern
The application uses a **client-server architecture** with WebSocket-based real-time communication. The server maintains authoritative game state while clients render the game world and handle player input.

**Rationale**: This pattern ensures consistent game state across all players, prevents cheating by keeping game logic server-side, and enables real-time multiplayer interactions.

**Alternatives considered**: Peer-to-peer would reduce server costs but introduce synchronization challenges and security risks.

## Server-Side Components

### Game Server (server.py / game_server.py)
- **Purpose**: Authoritative game state management using Python asyncio and websockets
- **Key responsibilities**:
  - Player connection/disconnection handling
  - Monster spawning and AI behavior
  - Combat calculations and damage resolution
  - Experience and level progression
  - Weapon drops and inventory management
  - Boss spawning with 60-second respawn timers

**Design decision**: Single-threaded async server handles all game logic to avoid race conditions and ensure deterministic game state updates.

### Entity Management
- **Monster System**: Three standard monster types (BASIC, FAST, TANK) plus BOSS with different stats, speeds, and drop rates
- **Weapon System**: Seven weapon definitions across four rarity tiers (RARE, EPIC, LEGENDARY, MYTHIC)
  - Weapons categorized by type: E (energy beam), R (ranged attack), W (area effect)
  - Damage scales with player level using base damage + damage-per-level formula

**Rationale**: Predefined monster/weapon configurations allow easy game balancing without code changes.

## Client-Side Components

### Rendering (HTML5 Canvas)
- **index.html**: Single-player or local game mode
- **multiplayer.html**: Multi-player networked game mode
- Both use Canvas-based rendering with camera following player character

**Design decision**: Canvas chosen over DOM-based rendering for smooth 60fps performance with many entities.

### Input Handling
- Virtual joystick for mobile touch controls
- Keyboard controls for desktop (WASD movement, E/R/W skills)
- Mouse targeting for ability aiming

**Rationale**: Dual input system supports both mobile and desktop players in the same game session.

## Game State Synchronization

### Server to Client Communication
- State snapshots broadcast at regular intervals
- Event-based updates for critical actions (damage, deaths, loot drops)
- Delta compression implied by selective state updates

### Client to Server Communication  
- Player input commands (movement, skill activation)
- Inventory actions (equip, use, disassemble)
- Connection management (join, ping)

**Pros**: Authoritative server prevents cheating and ensures consistency
**Cons**: Network latency affects responsiveness; requires client-side prediction for smooth movement

## Map and World Design

### Fixed World Dimensions
- Map size: 3000x2000 pixels
- 10 predefined monster spawn points distributed across map
- 1 boss spawn location at coordinates (1500, 300)

**Design decision**: Static world layout simplifies collision detection and pathfinding while ensuring consistent player experience.

## Progression Systems

### Experience and Leveling
- Monster kills grant experience points (15-500 depending on monster type)
- Level progression affects player stats and weapon damage
- Gold drops (10-500 per monster) for economy features

### PvP Combat System
- All attacks (basic, skills, projectiles, flame aura orbitals) can damage other players
- Player kills trigger automatic respawn after 3 seconds
- Server-authoritative damage calculation prevents cheating

### Boss Competition
- Boss loot goes to the player who dealt the most total damage (damage contributor tracking)
- Boss drops include Ancient Core items and exclusive mythic weapons
- Ancient Cores can be decomposed for 1000 gold each

### Consumable Items
- Healing Potions: Restore 35 HP when used (players start with 3)
- Equipment Disassembly: Weapons can be broken down for gold (50 gold per weapon level)

### Weapon Progression
- Level-scaling damage formula enables long-term progression
- Rarity tiers create clear upgrade paths
- Boss-exclusive drops (湮滅黑洞, 創世之光) provide end-game goals

**Rationale**: Multiple progression systems (character level, weapon upgrades) maintain player engagement across different playstyles.

# External Dependencies

## Core Technologies
- **Python 3.x**: Server runtime environment
- **asyncio**: Asynchronous I/O for handling concurrent WebSocket connections
- **websockets library**: WebSocket protocol implementation for real-time client-server communication

## Client Technologies
- **HTML5 Canvas API**: 2D game rendering
- **WebSocket API**: Browser-based real-time communication
- **Touch Events API**: Mobile input handling

## Network Protocol
- **WebSocket (ws://)**: Bi-directional communication protocol
- JSON message format for all client-server messages
- No external message queue or pub/sub system detected

## Future Integration Points
The codebase structure suggests potential for:
- Database integration for persistent player data (currently in-memory only)
- RESTful API for player authentication/accounts
- Redis or similar for distributed game state if scaling to multiple server instances

**Note**: No database, authentication service, or external APIs are currently integrated. All game state is ephemeral and reset on server restart.