# RLForge Python SDK

RLForge uzak RL ortamları ile etkileşim kurmak için Gymnasium uyumlu Python SDK.

## Kurulum

```bash
pip install rlforge
```

Geliştirme modunda (local):

```bash
cd sdk/
pip install -e .
```

## Hızlı Başlangıç

```python
import rlforge

# API anahtarı ile yapılandır
rlforge.configure(api_url="https://rlforge.ai", api_key="YOUR_KEY")

# Katalogdaki ortamları listele
envs = rlforge.list_envs(domain="finance", limit=5)
for env in envs["items"]:
    print(f"{env['slug']}  —  {env['description']}")

# Ortam oluştur ve eğitim döngüsü çalıştır
env = rlforge.make("gridworld-maze-v1")
obs, info = env.reset(seed=42)

for step in range(1000):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()

env.close()
```

## Doğal Dilden Ortam Üretimi

```python
import rlforge

rlforge.configure(api_key="YOUR_KEY")

# Doğal dil açıklaması ile yeni ortam üret
result = rlforge.generate(
    description="5 hisseli borsa trading ortamı, komisyon %0.1",
    domain="finance",
    difficulty="medium",
)
print(f"Ortam üretildi: {result['slug']} (id={result['id']})")

# Üretilen ortamı hemen kullan
env = rlforge.make(result["id"])
obs, info = env.reset()

for step in range(500):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()

env.close()
```

## API Referansı

### `rlforge.configure(api_url, api_key)`
Varsayılan istemciyi yapılandırır. Diğer fonksiyonlardan önce çağrılmalıdır.

### `rlforge.list_envs(domain, difficulty, search, limit) -> dict`
Yayınlanmış ortamları listeler. `{"items": [...], "total": int}` döner.

| Parametre    | Tip   | Varsayılan | Açıklama                            |
|-------------|-------|-----------|-------------------------------------|
| `domain`    | str   | None      | Filtre: finance, game, robotics ... |
| `difficulty`| str   | None      | Filtre: easy, medium, hard          |
| `search`    | str   | None      | İsim/açıklama içinde arama          |
| `limit`     | int   | 20        | Dönen maksimum sonuç sayısı         |

### `rlforge.get_env(slug_or_id) -> dict`
Tekil ortam detayını döner (slug veya id ile).

### `rlforge.generate(description, domain, difficulty) -> dict`
Doğal dil açıklamasından yeni ortam üretir. Üretim sonucu:
```json
{"id": 42, "slug": "stock-trading-5", "name": "...", "test_results": {...}}
```

### `rlforge.make(env_slug_or_id, **kwargs) -> RemoteEnv`
Uzak ortam oturumu oluşturur ve Gymnasium uyumlu `RemoteEnv` nesnesi döner.

### `RemoteEnv` (gymnasium.Env)

| Metod                         | Açıklama                          |
|-------------------------------|-----------------------------------|
| `step(action)`                | `(obs, reward, terminated, truncated, info)` |
| `reset(seed=None)`           | `(obs, info)`                     |
| `close()`                     | Oturumu sonlandırır               |
| `observation_space`           | `gymnasium.Space`                 |
| `action_space`                | `gymnasium.Space`                 |

### `RLForgeClient`

Düşük seviye istemci — birden fazla bağlantı veya farklı API anahtarları gerektiğinde doğrudan kullanılır:

```python
from rlforge.client import RLForgeClient

client = RLForgeClient(api_url="https://rlforge.ai", api_key="KEY")
catalog = client.list_envs(domain="game")
env = client.make("gridworld-maze-v1")
```

## Lisans

Kualia AI © 2026
