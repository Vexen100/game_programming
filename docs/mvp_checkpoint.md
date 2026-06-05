# Crown Reclaim - MVP checkpoint

## 1. Что уже работает

### Core loop

- Game loop + dt.
- SceneManager.
- InputManager.
- MainMenu / Pause / WorldMap / Region / CastleAssault.
- EventBus для gameplay-событий.
- GameState с регионами, influence, assault unlock, liberation и unlock next region.
- In-session cache `RegionScene` по `region_id`.
- Возврат Pause -> WorldMap -> gameplay без потери текущей gameplay-сцены.
- SaveManager / Continue MVP.
- Single-slot disk persistence для world progress.

### Region loop

- Вход в регион из карты мира.
- Движение игрока.
- Враги в обычном регионе.
- Patrol + LOS + A*.
- Outpost progress через удержание `E`.
- NPC report progress через удержание `E`.
- Influence в HUD обычного региона.
- Assault unlock после ослабления влияния врага.
- Повторный вход в тот же регион в рамках текущего запуска не сбрасывает runtime progress.
- Minimal `RegionScene` runtime snapshot для Continue.

### Castle loop

- Вход в штурм после unlock.
- Capture points.
- Waves после захвата не финальной точки.
- Liberation event.
- Unlock next region после liberation.
- Возврат на карту мира.

### Algorithms already implemented

- Game loop + deltaTime.
- AABB hitbox.
- Patrol + LOS + last seen/hysteresis.
- A* pathfinding.
- Flood fill / BFS validation.
- UniformGrid / SpatialIndex.

## 2. Что ещё НЕ является готовой игрой

- Full multi-slot save system не реализован.
- CastleAssaultScene runtime save не реализован.
- Partial region resurgence / reinforcements while away не реализованы.
- SettingsScene / SettingsManager не реализованы.
- Behavior Tree не реализован.
- BSP generation не реализован.
- SpatialHashing не реализован.
- Lightmap / Perlin не реализованы.
- Enemy attack имеет AABB telegraph и windup, но полноценные animations/sound/hit effects ещё не реализованы.
- Нет спрайтов, анимаций и звука.
- Регионы пока используют один прототип `RegionScene`.
- Квесты пока прототипные, без диалогов и вариативности.
- Баланс влияния пока тестовый.

## 3. Почему количество шагов выросло

Исходный план был картой крупных вех, а не реальным production backlog.

Каждый пункт плана на практике распался на реализацию, тесты, интеграцию, UX, фиксы и документацию. Это нормальная часть разработки, потому что рабочий игровой цикл держится не только на наличии систем, но и на том, что они согласованы между собой.

QA-фиксы не являются отклонением от плана. Они защищают архитектуру от скрытых регрессий и не дают новым системам менять старую gameplay-семантику.

Дальше полезнее считать не номера шагов, а закрытые milestones: что реально работает, что проверено тестами, и что нужно для следующего playable slice.

## 4. Новый ближайший маршрут

### Milestone A - закрыть playable vertical slice

1. Acceptance tests текущего цикла.
2. SettingsManager / SettingsScene минимально.
3. Минимальная ручная проверка vertical slice после SaveManager / Continue MVP.

### Milestone B - алгоритмическое развитие

1. Behavior Tree для enemy decisions.
2. SpatialHashing backend.
3. BSP castle generation.

### Milestone C - presentation

1. ResourceManager.
2. Простые sprites.
3. Attack/death animations.
4. Sound/hit feedback.
5. Lightmap.

## 5. Definition of Done для vertical slice

Вертикальный срез считается закрытым, когда:

- новая игра открывает карту регионов;
- игрок входит в enemy region;
- игрок ослабляет регион через enemy/outpost/NPC;
- assault unlock виден в HUD и WorldMap;
- игрок входит в CastleAssaultScene;
- capture points освобождают регион;
- WorldMap показывает liberated region и unlocked next region;
- после перезапуска через SaveManager это состояние можно продолжить.
