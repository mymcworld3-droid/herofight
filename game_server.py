import asyncio
import json
import random
import math
import time
from typing import Dict, List, Optional
from aiohttp import web

MAP_W = 3000
MAP_H = 2000

MONSTER_TYPES = {
    'BASIC': {
        'id': 'basic',
        'level': 1,
        'hp': 30,
        'maxHp': 30,
        'speed': 70,
        'atk': 12,
        'r': 20,
        'color': '#e07b7b',
        'expDrop': 15,
        'goldMin': 1,
        'goldMax': 3,
        'respawnTime': 2
    },
    'FAST': {
        'id': 'fast',
        'level': 3,
        'hp': 40,
        'maxHp': 40,
        'speed': 120,
        'atk': 15,
        'r': 18,
        'color': '#f7d37a',
        'expDrop': 30,
        'goldMin': 2,
        'goldMax': 4,
        'respawnTime': 3
    },
    'TANK': {
        'id': 'tank',
        'level': 5,
        'hp': 150,
        'maxHp': 150,
        'speed': 50,
        'atk': 8,
        'r': 25,
        'color': '#5b8c9d',
        'expDrop': 50,
        'goldMin': 3,
        'goldMax': 5,
        'respawnTime': 4
    }
}

BOSS_TYPE = {
    'id': 'boss',
    'level': 10,
    'hp': 1500,
    'maxHp': 1500,
    'speed': 100,
    'atk': 25,
    'r': 50,
    'color': '#d30000',
    'expDrop': 500,
    'goldMin': 20,
    'goldMax': 50,
    'respawnTime': 60,
    'isBoss': True
}

MONSTER_SPAWNS = [{
    'x': 500,
    'y': 500,
    'type': 'BASIC'
}, {
    'x': 2500,
    'y': 400,
    'type': 'FAST'
}, {
    'x': 700,
    'y': 1600,
    'type': 'TANK'
}, {
    'x': 2600,
    'y': 1500,
    'type': 'BASIC'
}, {
    'x': 1500,
    'y': 100,
    'type': 'BASIC'
}, {
    'x': 100,
    'y': 1000,
    'type': 'FAST'
}, {
    'x': 2900,
    'y': 1000,
    'type': 'BASIC'
}, {
    'x': 1500,
    'y': 1900,
    'type': 'TANK'
}, {
    'x': 400,
    'y': 1200,
    'type': 'FAST'
}, {
    'x': 2000,
    'y': 1700,
    'type': 'BASIC'
}]

BOSS_SPAWN = {'x': 1500, 'y': 300, 'type': 'BOSS'}

WEAPON_DEFINITIONS = {
    'E_WEAPON_BASIC': {
        'id': 'E_WEAPON_BASIC',
        'name': '能量光束 E',
        'type': 'E',
        'rarity': 'RARE',
        'baseDmg': 30,
        'dmgPerLevel': 10
    },
    'R_WEAPON_BASIC': {
        'id': 'R_WEAPON_BASIC',
        'name': '烈焰衝擊 R',
        'type': 'R',
        'rarity': 'EPIC',
        'baseDmg': 50,
        'dmgPerLevel': 20
    },
    'W_FIRE_RING_EPIC': {
        'id': 'W_FIRE_RING_EPIC',
        'name': '烈焰光環 W',
        'type': 'W',
        'rarity': 'EPIC',
        'baseDmg': 35,
        'dmgPerLevel': 5
    },
    'E_WEAPON_LEGENDARY': {
        'id': 'E_WEAPON_LEGENDARY',
        'name': '絕對零度 E',
        'type': 'E',
        'rarity': 'LEGENDARY',
        'baseDmg': 50,
        'dmgPerLevel': 15
    },
    'R_WEAPON_LEGENDARY': {
        'id': 'R_WEAPON_LEGENDARY',
        'name': '時空裂隙 R',
        'type': 'R',
        'rarity': 'LEGENDARY',
        'baseDmg': 80,
        'dmgPerLevel': 30
    },
    'R_WEAPON_BOSS': {
        'id': 'R_WEAPON_BOSS',
        'name': '湮滅黑洞 R',
        'type': 'R',
        'rarity': 'MYTHIC',
        'baseDmg': 120,
        'dmgPerLevel': 50
    },
    'E_WEAPON_BOSS': {
        'id': 'E_WEAPON_BOSS',
        'name': '創世之光 E',
        'type': 'E',
        'rarity': 'MYTHIC',
        'baseDmg': 100,
        'dmgPerLevel': 45
    },
    # 新增位移武器
    'E_DASH_RARE': {
        'id': 'E_DASH_RARE',
        'name': '疾影突襲 E',
        'type': 'E',
        'rarity': 'RARE',
        'baseDmg': 25,
        'dmgPerLevel': 8,
        'isDash': True,
        'dashDistance': 200,
        'dashDuration': 0.2
    },
    'E_DASH_MYTHIC': {
        'id': 'E_DASH_MYTHIC',
        'name': '虛空閃現 E',
        'type': 'E',
        'rarity': 'MYTHIC',
        'baseDmg': 60,
        'dmgPerLevel': 25,
        'isDash': True,
        'dashDistance': 350,
        'dashDuration': 0.15
    }
}


class Monster:

    def __init__(self, spawn_id, x, y, monster_type, is_boss=False):
        self.spawn_id = spawn_id
        self.x = x
        self.y = y
        self.spawn_x = x
        self.spawn_y = y
        self.is_boss = is_boss

        type_data = BOSS_TYPE if is_boss else MONSTER_TYPES[monster_type]
        self.type_id = type_data['id']
        self.level = type_data['level']
        self.hp = type_data['hp']
        self.maxHp = type_data['maxHp']
        self.speed = type_data['speed']
        self.atk = type_data['atk']
        self.r = type_data['r']
        self.color = type_data['color']
        self.expDrop = type_data['expDrop']
        self.goldMin = type_data['goldMin']
        self.goldMax = type_data['goldMax']
        self.respawnTime = type_data['respawnTime']

        self.alive = True
        self.respawn_timer = 0
        self.target_player = None
        self.state = 'wander'
        self.wander_dir = random.random() * math.pi * 2
        self.wander_timer = 1 + random.random() * 2
        self.attack_cooldown = 0.0
        self.skill_cooldown = 0.0
        self.skill_prepare_time = 0.0
        self.skill_type: Optional[str] = None  # 'laser' or 'meteor'
        self.skill_executed = False
        self.skill_target_x = 0.0
        self.skill_target_y = 0.0
        self.damage_contributors: Dict[str, float] = {}

    def to_dict(self):
        data = {
            'spawn_id': self.spawn_id,
            'x': self.x,
            'y': self.y,
            'hp': self.hp,
            'maxHp': self.maxHp,
            'r': self.r,
            'color': self.color,
            'level': self.level,
            'alive': self.alive,
            'isBoss': self.is_boss,
            'state': self.state
        }
        if self.is_boss and self.skill_prepare_time > 0:
            warning = {
                'type': self.skill_type,
                'progress': max(0, 1 - (self.skill_prepare_time / 1.5)),
                'x': self.x,
                'y': self.y,
                'targetX': getattr(self, 'skill_target_x', self.x),
                'targetY': getattr(self, 'skill_target_y', self.y)
            }
            data['skillWarning'] = warning
        return data


class Player:

    def __init__(self, player_id, name):
        self.id = player_id
        self.name = name
        self.x = MAP_W / 2 + random.randint(-100, 100)
        self.y = MAP_H / 2 + random.randint(-100, 100)
        self.r = 24
        self.hp = 100.0
        self.maxHp = 100
        self.speed = 300
        self.level = 1
        self.exp = 0
        self.expToNextLevel = 100
        self.baseAttack = 10
        self.gold = 500
        self.color = f'hsl({random.randint(0, 360)}, 70%, 60%)'
        self.dirX = 0.0
        self.dirY = 0.0
        self.faceX = 1.0
        self.faceY = 0.0
        self.inventory: List[dict] = []
        self.equipment: Dict[str, dict | None] = {
            'E': None,
            'R': None,
            'W': None
        }  # E = Skill 2, R = Skill 3, W = passive
        self.skill_cooldowns = {1: 0.0, 2: 0.0, 3: 0.0}
        self.attack_cooldown = 0.0
        self.respawn_timer = 0.0
        self.alive = True
        self.orb_hit_times: Dict[str, float] = {}
        self.ws: Optional[web.WebSocketResponse] = None

        # 新增：位移狀態
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_dir_x = 0.0
        self.dash_dir_y = 0.0
        self.dash_speed = 0.0
        self.dash_damage = 0.0
        self.dash_hit_entities = set()

        self.inventory.append({
            'id': 'healing_potion',
            'name': '治療藥水',
            'icon': 'HP',
            'color': '#ff4d4d',
            'count': 3,
            'isWeapon': False
        })

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'r': self.r,
            'hp': self.hp,
            'maxHp': self.maxHp,
            'level': self.level,
            'exp': self.exp,
            'expToNextLevel': self.expToNextLevel,
            'baseAttack': self.baseAttack,
            'gold': self.gold,
            'color': self.color,
            'faceX': self.faceX,
            'faceY': self.faceY,
            'alive': self.alive,
            'inventory': self.inventory,
            'equipment': self.equipment,
            # 新增位移狀態同步
            'is_dashing': self.is_dashing,
            'dash_dir_x': self.dash_dir_x if self.is_dashing else 0,
            'dash_dir_y': self.dash_dir_y if self.is_dashing else 0
        }

    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.expToNextLevel:
            self.exp -= self.expToNextLevel
            self.level += 1
            self.expToNextLevel = int(self.expToNextLevel * 1.5)
            self.maxHp += 10
            self.hp = self.maxHp
            self.baseAttack += 2

    def add_gold(self, amount):
        self.gold += amount

    def add_to_inventory(self, item):
        if len(self.inventory) < 12:
            for existing in self.inventory:
                if existing.get('id') == item.get(
                        'id') and not item.get('isWeapon'):
                    existing['count'] = existing.get('count', 1) + item.get(
                        'count', 1)
                    return True
            self.inventory.append(item)
            return True
        return False


class GameState:

    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.monsters: List[Monster] = []
        self.projectiles: List[dict] = []
        self.lasers: List[dict] = []
        self.meteors: List[dict] = []
        self.last_update = time.time()

        for i, spawn in enumerate(MONSTER_SPAWNS):
            monster = Monster(f'monster_{i}', spawn['x'], spawn['y'],
                              spawn['type'])
            self.monsters.append(monster)

        boss = Monster('boss_0',
                       BOSS_SPAWN['x'],
                       BOSS_SPAWN['y'],
                       'BOSS',
                       is_boss=True)
        self.monsters.append(boss)

    def get_state_for_player(self, player_id):
        player = self.players.get(player_id)
        if not player:
            return None

        return {
            'type':
            'state',
            'you':
            player.to_dict(),
            'players': [
                p.to_dict() for pid, p in self.players.items()
                if pid != player_id
            ],
            'monsters': [m.to_dict() for m in self.monsters],
            'projectiles':
            self.projectiles,
            'lasers':
            self.lasers,
            'meteors':
            self.meteors
        }


game = GameState()


def hyp(dx, dy):
    return math.sqrt(dx * dx + dy * dy)


def generate_weapon_drop(is_boss=False):
    rand = random.random()

    if is_boss:
        if rand < 1 / 3:
            weapon_id = random.choice(
                ['R_WEAPON_BOSS', 'E_WEAPON_BOSS', 'E_DASH_MYTHIC'])
        else:
            return None
    else:
        if rand < 0.05:
            weapon_id = random.choice(
                ['E_WEAPON_LEGENDARY', 'R_WEAPON_LEGENDARY'])
        elif rand < 0.10:
            weapon_id = random.choice(['R_WEAPON_BASIC', 'W_FIRE_RING_EPIC'])
        elif rand < 0.15:
            weapon_id = random.choice(['E_WEAPON_BASIC', 'E_DASH_RARE'])
        else:
            return None

    weapon_def = WEAPON_DEFINITIONS[weapon_id]
    rarity_colors = {
        'COMMON':
        '#666',
        'RARE':
        '#4d88ff',
        'EPIC':
        '#8e44ad',
        'LEGENDARY':
        '#e74c3c',
        'MYTHIC':
        'linear-gradient(90deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3)'
    }

    return {
        'id': weapon_id,
        'name': weapon_def['name'],
        'icon': weapon_def['type'],
        'color': rarity_colors.get(weapon_def['rarity'], '#666'),
        'isWeapon': True,
        'level': 1,
        'type': weapon_def['type'],
        'count': 1
    }


async def update_game(dt):
    current_time = time.time()

    for monster in game.monsters:
        if not monster.alive:
            monster.respawn_timer -= dt
            if monster.respawn_timer <= 0:
                monster.alive = True
                monster.hp = monster.maxHp
                monster.x = monster.spawn_x
                monster.y = monster.spawn_y
                monster.damage_contributors = {}
            continue

        if monster.attack_cooldown > 0:
            monster.attack_cooldown -= dt
        if monster.skill_cooldown > 0:
            monster.skill_cooldown -= dt
        if monster.skill_prepare_time > 0:
            monster.skill_prepare_time -= dt

        if monster.target_player and monster.target_player in game.players:
            target = game.players[monster.target_player]
            if not target.alive:
                monster.target_player = None
                monster.state = 'wander'
            else:
                dx = target.x - monster.x
                dy = target.y - monster.y
                dist = hyp(dx, dy)

                # 在追踪范围内（<= 400）
                if monster.is_boss and dist < 400:
                    # 找最近的玩家
                    closest_player = target
                    closest_dist = dist
                    for player_id, player in game.players.items():
                        if player.alive:
                            p_dx = player.x - monster.x
                            p_dy = player.y - monster.y
                            p_dist = hyp(p_dx, p_dy)
                            if p_dist < closest_dist:
                                closest_player = player
                                closest_dist = p_dist

                    # Boss技能邏輯：準備階段 -> 執行階段
                    if monster.skill_prepare_time > 0:
                        # 準備階段：Boss停頓，顯示警示區域
                        monster.skill_prepare_time -= dt

                        # 準備階段結束，執行技能
                        if monster.skill_prepare_time <= 0 and not monster.skill_executed:
                            if monster.skill_type == 'laser':
                                # 激光技能：向最近玩家方向發射持續激光
                                closest_dx = closest_player.x - monster.x
                                closest_dy = closest_player.y - monster.y
                                closest_dist_calc = hyp(closest_dx, closest_dy)
                                if closest_dist_calc > 0:
                                    laser_dir_x = closest_dx / closest_dist_calc
                                    laser_dir_y = closest_dy / closest_dist_calc
                                    game.lasers.append({
                                        'x': monster.x,
                                        'y': monster.y,
                                        'dirX': laser_dir_x,
                                        'dirY': laser_dir_y,
                                        'dmg': monster.atk * 0.8,  # 每0.1秒造成傷害
                                        'life': 2.5,
                                        'owner': f'monster_{monster.spawn_id}',
                                        'color': '#ff00ff'
                                    })

                            elif monster.skill_type == 'meteor':
                                # 隕石技能：在目標位置召喚3顆隕石
                                target_x = monster.skill_target_x
                                target_y = monster.skill_target_y
                                for offset in [0]:
                                    game.meteors.append({
                                        'x': target_x + offset,
                                        'y': target_y - 400,  # 從上方落下
                                        'targetX': target_x + offset,
                                        'targetY': target_y,
                                        'dmg': monster.atk * 2.5,
                                        'life': 1.5,  # 1.5秒後落地
                                        'r': 20,
                                        'owner': f'monster_{monster.spawn_id}',
                                        'color': '#ff8800'
                                    })

                            monster.skill_executed = True
                            monster.skill_cooldown = 6.0 + random.random(
                            ) * 2  # 6-8秒冷卻

                    elif monster.skill_cooldown > 0:
                        # 冷卻中
                        monster.skill_cooldown -= dt

                    else:
                        # 冷卻結束，開始新的技能準備
                        monster.skill_prepare_time = 1.5
                        monster.skill_executed = False
                        rand = random.random()
                        monster.skill_type = 'laser' if rand < 0.5 else 'meteor'
                        monster.skill_target_x = closest_player.x
                        monster.skill_target_y = closest_player.y

                if dist > monster.r + target.r:
                    # 继续追踪（除非在施放激光）
                    if not (monster.is_boss and monster.skill_type == 'laser'
                            and 1.5 >= monster.skill_cooldown > 0.5):
                        monster.x += (dx / dist) * monster.speed * dt
                        monster.y += (dy / dist) * monster.speed * dt
                elif monster.attack_cooldown <= 0:
                    # 接近到可以攻击的距离
                    if not monster.is_boss or monster.skill_cooldown > 1.5 or monster.skill_prepare_time > 0:
                        # 非Boss或者技能冷却中或准备中：普通近距离攻击
                        target.hp -= monster.atk
                    monster.attack_cooldown = 1.2

                    if target.hp <= 0:
                        target.hp = 0
                        target.alive = False
                        target.respawn_timer = 3
        else:
            monster.wander_timer -= dt
            if monster.wander_timer <= 0:
                monster.wander_dir = random.random() * math.pi * 2
                monster.wander_timer = 1 + random.random() * 2

            speed = monster.speed * 0.3
            monster.x += math.cos(monster.wander_dir) * speed * dt
            monster.y += math.sin(monster.wander_dir) * speed * dt

        monster.x = max(monster.r, min(MAP_W - monster.r, monster.x))
        monster.y = max(monster.r, min(MAP_H - monster.r, monster.y))

    # 激光伤害处理
    for laser in game.lasers[:]:
        laser['life'] -= dt
        if laser['life'] <= 0:
            game.lasers.remove(laser)
            continue

        

    # 隕石伤害处理
    for meteor in game.meteors[:]:
        meteor['life'] -= dt
        if meteor['life'] <= 0:
            for player in game.players.values():
                if not player.alive:
                    continue
                dist = hyp(meteor['targetX'] - player.x,
                           meteor['targetY'] - player.y)
                if dist < 100:
                    player.hp -= meteor['dmg']
                    if player.hp <= 0:
                        player.hp = 0
                        player.alive = False
                        player.respawn_timer = 3
            game.meteors.remove(meteor)
            continue

        meteor['y'] += (meteor['targetY'] - meteor['y']) * dt / meteor['life']

    for player in game.players.values():
        if not player.alive:
            player.respawn_timer -= dt
            if player.respawn_timer <= 0:
                player.alive = True
                player.hp = player.maxHp
                player.x = MAP_W / 2 + random.randint(-100, 100)
                player.y = MAP_H / 2 + random.randint(-100, 100)
            continue
        if player.is_dashing:
            player.dash_timer -= dt

            if player.dash_timer > 0:
                old_x, old_y = player.x, player.y
                player.x += player.dash_dir_x * player.dash_speed * dt
                player.y += player.dash_dir_y * player.dash_speed * dt

                # 限制在地圖範圍內
                player.x = max(player.r, min(MAP_W - player.r, player.x))
                player.y = max(player.r, min(MAP_H - player.r, player.y))

                # 路徑傷害判定 - 怪物
                for monster in game.monsters:
                    if not monster.alive or id(monster) in player.dash_hit_entities:
                        continue
                    dist = hyp(monster.x - player.x, monster.y - player.y)
                    if dist < monster.r + player.r:
                        monster.hp -= player.dash_damage
                        monster.damage_contributors[player.id] = monster.damage_contributors.get(player.id, 0) + player.dash_damage
                        monster.target_player = player.id
                        monster.state = 'chase'
                        player.dash_hit_entities.add(id(monster))

                # 路徑傷害判定 - 其他玩家
                for other_player in game.players.values():
                    if other_player.id == player.id or not other_player.alive or id(other_player) in player.dash_hit_entities:
                        continue
                    dist = hyp(other_player.x - player.x, other_player.y - player.y)
                    if dist < other_player.r + player.r:
                        other_player.hp -= player.dash_damage
                        player.dash_hit_entities.add(id(other_player))
                        if other_player.hp <= 0:
                            other_player.hp = 0
                            other_player.alive = False
                            other_player.respawn_timer = 3
            else:
                # 位移結束
                player.is_dashing = False
                player.dash_hit_entities = set()

            # 位移期間跳過正常移動
            continue


        if player.attack_cooldown > 0:
            player.attack_cooldown -= dt

        for skill_id in player.skill_cooldowns:
            if player.skill_cooldowns[skill_id] > 0:
                player.skill_cooldowns[skill_id] -= dt

        if player.dirX != 0 or player.dirY != 0:
            player.x += player.dirX * player.speed * dt
            player.y += player.dirY * player.speed * dt
            player.x = max(player.r, min(MAP_W - player.r, player.x))
            player.y = max(player.r, min(MAP_H - player.r, player.y))

            dist = hyp(player.dirX, player.dirY)
            if dist > 0:
                player.faceX = player.dirX / dist
                player.faceY = player.dirY / dist

        weapon = player.equipment.get('W')
        if weapon is not None:
            weapon_def = WEAPON_DEFINITIONS.get(weapon['id'])
            if weapon_def:
                num_orbs = weapon.get('level', 1)
                orb_damage = weapon_def['baseDmg'] + (
                    weapon.get('level', 1) - 1) * weapon_def['dmgPerLevel']
                orbit_distance = 80
                orbit_speed = 2

                for i in range(num_orbs):
                    angle = (current_time * orbit_speed +
                             (i / num_orbs) * math.pi * 2) % (math.pi * 2)
                    orb_x = player.x + orbit_distance * math.cos(angle)
                    orb_y = player.y + orbit_distance * math.sin(angle)

                    for monster in game.monsters:
                        if not monster.alive:
                            continue
                        dist = hyp(orb_x - monster.x, orb_y - monster.y)
                        if dist < monster.r + 10:
                            hit_key = f"{player.id}_{monster.spawn_id}_{i}"
                            last_hit = player.orb_hit_times.get(hit_key, 0)
                            if current_time - last_hit > 0.5:
                                monster.hp -= orb_damage
                                monster.damage_contributors[
                                    player.
                                    id] = monster.damage_contributors.get(
                                        player.id, 0) + orb_damage
                                monster.target_player = player.id
                                monster.state = 'chase'
                                player.orb_hit_times[hit_key] = current_time

                    for other_player in game.players.values():
                        if other_player.id == player.id or not other_player.alive:
                            continue
                        dist = hyp(orb_x - other_player.x,
                                   orb_y - other_player.y)
                        if dist < other_player.r + 10:
                            hit_key = f"{player.id}_{other_player.id}_{i}"
                            last_hit = player.orb_hit_times.get(hit_key, 0)
                            if current_time - last_hit > 0.5:
                                other_player.hp -= orb_damage
                                player.orb_hit_times[hit_key] = current_time
                                if other_player.hp <= 0:
                                    other_player.hp = 0
                                    other_player.alive = False
                                    other_player.respawn_timer = 3

    new_projectiles = []
    for proj in game.projectiles:
        proj['x'] += proj['vx'] * dt
        proj['y'] += proj['vy'] * dt
        proj['life'] -= dt

        if proj['life'] <= 0:
            continue

        hit = False

        if proj.get('targetType') in ['monster', 'all']:
            for monster in game.monsters:
                if not monster.alive:
                    continue
                dist = hyp(proj['x'] - monster.x, proj['y'] - monster.y)
                if dist < monster.r + proj['r']:
                    monster.hp -= proj['dmg']
                    monster.damage_contributors[
                        proj['owner']] = monster.damage_contributors.get(
                            proj['owner'], 0) + proj['dmg']
                    monster.target_player = proj['owner']
                    monster.state = 'chase'
                    hit = True
                    break

        if not hit and proj.get('targetType') in ['player', 'all']:
            for other_player in game.players.values():
                if other_player.id == proj['owner'] or not other_player.alive:
                    continue
                dist = hyp(proj['x'] - other_player.x,
                           proj['y'] - other_player.y)
                if dist < other_player.r + proj['r']:
                    other_player.hp -= proj['dmg']
                    if other_player.hp <= 0:
                        other_player.hp = 0
                        other_player.alive = False
                        other_player.respawn_timer = 3
                    hit = True
                    break

        if not hit:
            new_projectiles.append(proj)

    game.projectiles = new_projectiles

    for monster in game.monsters:
        if monster.alive and monster.hp <= 0:
            monster.alive = False
            monster.respawn_timer = monster.respawnTime

            top_contributor = None
            top_damage = 0
            for pid, dmg in monster.damage_contributors.items():
                if dmg > top_damage:
                    top_damage = dmg
                    top_contributor = pid

            if top_contributor and top_contributor in game.players:
                killer = game.players[top_contributor]
                killer.add_exp(monster.expDrop)
                gold_drop = random.randint(monster.goldMin,
                                           monster.goldMax) * 10
                killer.add_gold(gold_drop)

                weapon = generate_weapon_drop(monster.is_boss)
                if weapon:
                    killer.add_to_inventory(weapon)

                if monster.is_boss:
                    boss_item = {
                        'id': 'boss_item',
                        'name': '遠古核心',
                        'icon': 'CORE',
                        'color': '#ff00ff',
                        'count': 1,
                        'isWeapon': False
                    }
                    killer.add_to_inventory(boss_item)

            monster.damage_contributors = {}


async def game_loop():
    while True:
        current_time = time.time()
        dt = current_time - game.last_update
        game.last_update = current_time

        await update_game(min(dt, 0.1))

        for player_id, player in list(game.players.items()):
            if player.ws and not player.ws.closed:
                try:
                    state = game.get_state_for_player(player_id)
                    if state:
                        await player.ws.send_json(state)
                except Exception:
                    pass

        await asyncio.sleep(1 / 30)


async def handle_message(player_id, data):
    try:
        msg_type = data.get('type')

        player = game.players.get(player_id)
        if not player:
            return

        if msg_type == 'move':
            player.dirX = float(data.get('dirX', 0))
            player.dirY = float(data.get('dirY', 0))

        elif msg_type == 'attack':
            if player.attack_cooldown > 0 or not player.alive:
                return

            player.attack_cooldown = 0.3
            dirX = float(data.get('dirX', player.faceX))
            dirY = float(data.get('dirY', player.faceY))

            game.projectiles.append({
                'x': player.x + dirX * player.r,
                'y': player.y + dirY * player.r,
                'vx': dirX * 700,
                'vy': dirY * 700,
                'r': 8,
                'dmg': player.baseAttack * 1.5,
                'life': 2,
                'owner': player_id,
                'targetType': 'all',
                'color': player.color
            })

        elif msg_type == 'skill':
            skill_id = data.get('skillId')
            if skill_id not in [1, 2, 3]:
                return

            cooldowns = {1: 0.5, 2: 6, 3: 8}
            if player.skill_cooldowns.get(skill_id, 0) > 0 or not player.alive:
                return

            player.skill_cooldowns[skill_id] = cooldowns[skill_id]
            dirX = float(data.get('dirX', player.faceX))
            dirY = float(data.get('dirY', player.faceY))

            if skill_id == 1:
                game.projectiles.append({
                    'x': player.x + dirX * player.r,
                    'y': player.y + dirY * player.r,
                    'vx': dirX * 600,
                    'vy': dirY * 600,
                    'r': 8,
                    'dmg': player.baseAttack * 2,
                    'life': 2,
                    'owner': player_id,
                    'targetType': 'all',
                    'color': '#ffd166'
                })

            elif skill_id == 2:
                equipped = player.equipment.get('E')
                if equipped:
                    weapon_def = WEAPON_DEFINITIONS.get(equipped['id'])
                    if weapon_def:
                        dmg = player.baseAttack + weapon_def['baseDmg'] + (
                            equipped.get('level', 1) -
                            1) * weapon_def['dmgPerLevel']

                        # 檢查是否為位移武器
                        if weapon_def.get('isDash'):
                            # 位移武器邏輯
                            player.is_dashing = True
                            player.dash_timer = weapon_def['dashDuration']
                            player.dash_dir_x = dirX
                            player.dash_dir_y = dirY
                            player.dash_speed = weapon_def[
                                'dashDistance'] / weapon_def['dashDuration']
                            player.dash_damage = dmg
                            player.dash_hit_entities = set()
                        else:
                            # 原有的能量光束邏輯
                            game.projectiles.append({
                                'x':
                                player.x + dirX * player.r,
                                'y':
                                player.y + dirY * player.r,
                                'vx':
                                dirX * 750,
                                'vy':
                                dirY * 750,
                                'r':
                                10,
                                'dmg':
                                dmg,
                                'life':
                                2,
                                'owner':
                                player_id,
                                'targetType':
                                'all',
                                'color':
                                '#00ffff'
                            })
                else:
                    # 未裝備 E 武器：治療
                    player.hp = min(player.maxHp, player.hp + 35)

            elif skill_id == 3:
                equipped = player.equipment.get('R')
                weapon_def = WEAPON_DEFINITIONS.get(
                    equipped['id']) if equipped else None
                R = 180 if equipped else 140
                dmg = (player.baseAttack * 0.5 + weapon_def['baseDmg'] +
                       (equipped.get('level', 1) - 1) *
                       weapon_def['dmgPerLevel']) if (weapon_def and equipped) else (
                           40 + player.baseAttack * 1.5)

                for monster in game.monsters:
                    if not monster.alive:
                        continue
                    dist = hyp(monster.x - player.x, monster.y - player.y)
                    if dist < R:
                        monster.hp -= dmg
                        monster.damage_contributors[
                            player_id] = monster.damage_contributors.get(
                                player_id, 0) + dmg
                        monster.target_player = player_id

                for other_player in game.players.values():
                    if other_player.id == player_id or not other_player.alive:
                        continue
                    dist = hyp(other_player.x - player.x,
                               other_player.y - player.y)
                    if dist < R:
                        other_player.hp -= dmg
                        if other_player.hp <= 0:
                            other_player.hp = 0
                            other_player.alive = False
                            other_player.respawn_timer = 3

        elif msg_type == 'equip':
            index = data.get('index')
            if 0 <= index < len(player.inventory):
                item = player.inventory[index]
                if item.get('isWeapon'):
                    weapon_type = item.get('type')
                    # 创建一个新的装备副本，确保引用正确
                    player.equipment[weapon_type] = dict(item)

        elif msg_type == 'unequip':
            weapon_type = data.get('weaponType')
            if weapon_type in player.equipment:
                player.equipment[weapon_type] = None

        elif msg_type == 'use_item':
            index = data.get('index')
            if 0 <= index < len(player.inventory):
                item = player.inventory[index]
                if item.get('id') == 'healing_potion':
                    player.hp = min(player.maxHp, player.hp + 35)
                    item['count'] -= 1
                    if item['count'] <= 0:
                        player.inventory.pop(index)

        elif msg_type == 'upgrade':
            index = data.get('index')
            if 0 <= index < len(player.inventory):
                item = player.inventory[index]
                if item.get('isWeapon'):
                    upgrade_cost = item.get('level', 1) * 100
                    if player.gold >= upgrade_cost:
                        player.gold -= upgrade_cost
                        item['level'] = item.get('level', 1) + 1

        elif msg_type == 'disassemble':
            index = data.get('index')
            if 0 <= index < len(player.inventory):
                item = player.inventory[index]
                if item.get('id') == 'boss_item':
                    player.gold += 1000 * item.get('count', 1)
                    player.inventory.pop(index)
                elif item.get('isWeapon'):
                    weapon_type = item.get('type')
                    if player.equipment.get(weapon_type) == item:
                        player.equipment[weapon_type] = None
                    player.gold += 50 * item.get('level', 1)
                    player.inventory.pop(index)

    except Exception as e:
        print(f"Error handling message: {e}")


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player_id = f"player_{id(ws)}"
    player_name = f"玩家{len(game.players) + 1}"

    player = Player(player_id, player_name)
    player.ws = ws
    game.players[player_id] = player

    print(f"Player connected: {player_name} ({player_id})")

    try:
        await ws.send_json({
            'type': 'connected',
            'playerId': player_id,
            'playerName': player_name
        })

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    await handle_message(player_id, data)
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"Error processing message: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
            elif msg.type == web.WSMsgType.CLOSE:
                print('WebSocket closed')
                break

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"WebSocket handler error: {e}")
    finally:
        if player_id in game.players:
            del game.players[player_id]
        if not ws.closed:
            await ws.close()
        print(f"Player disconnected: {player_name}")

    return ws


async def index_handler(request):
    with open('index.html', 'r', encoding='utf-8') as f:
        return web.Response(text=f.read(),
                            content_type='text/html',
                            charset='utf-8')


async def start_background_loop():
    await game_loop()


async def main():
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/index.html', index_handler)
    app.router.add_get('/ws', websocket_handler)

    asyncio.create_task(game_loop())

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8888)
    await site.start()

    print("Server started on port8888")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
