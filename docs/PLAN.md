
RLFORGE
RL Environment Generation & Training Platform

Implementasyon Kılavuzu v5.0
Mart 2026  |  Tüm bölümler dahil



Bölüm 1: Sistem Özeti ve Kapsam

1.1 MVP Kapsamı (Kodlanacak)
Fikir giriş sistemi (NL → env spec)
Architect Agent v1 (kod üretimi + test + iteratif düzeltme)
Otomatik yayınlama (Docker + API endpoint)
Training API Mod A: Remote Step
State Viewer dashboard
5-10 hazır şablon environment (platform batch üretimi)
Python SDK
Tek sunucu hosting

1.2 Phase 2/3 (ŞİMDİ KODLANMAYACAK)

Environment Builder (Lovable modeli: AI ile iterate ederek env tasarla, GitHub’a çek) — PHASE 2
Agent Training (“Bu env’de agent eğit” butonu, SB3 ile eğitim) — PHASE 2
Paper upload (ü PDF → env spec) — PHASE 2
AI Research Lab (agent ekibi) — PHASE 3
Mod B: Agent Upload — PHASE 2
Canvas/WebGL render — PHASE 2
WebSocket/gRPC — PHASE 2
Leaderboard — PHASE 2
Kubernetes — PHASE 2

1.3 Önemli Tasarım Kararı: Tek Architect Agent

Bölüm 2: Fikir Giriş Sistemi
Kullanıcı tek metin alanına istediği RL ortamını doğal dille anlatır.
2.1 Girdi Yöntemleri
Serbest metin: “Borsa trading ortamı, 5 hisse, komisyon %0.1”
Şablon + özelleştirme: Domain seç (finans/oyun/robotik), parametreleri ayarla
Fork: Mevcut ortamı al, üzerine değişiklik yap
2.2 Doğal Dil → Environment Spec JSON
{
  "name": "stock-trading-5",
  "domain": "finance",
  "observation_space": { "type": "Box", "shape": [30] },
  "action_space": { "type": "Box", "shape": [5], "low": -1, "high": 1 },
  "reward_function": { "type": "portfolio_return", "commission": 0.001 },
  "episode": { "max_steps": 252 }
}
2.3 Akıllı Varsayılanlar
Finans: commission=0.001, episode=252, obs=OHLCV
Robotik: physics=2D, dt=0.02, max_steps=1000
Oyun: grid=10x10, vision=full, reward=sparse

Bölüm 3: Architect Agent — Tam Prompt & Skill Tanımı

3.1 Agent’ın Rolleri

3.2 System Prompt (Ana Prompt)
Architect Agent’ın her çağrıda aldığı sabit system prompt:
SYSTEM PROMPT - RLFORGE ARCHITECT AGENT
========================================

Sen RLForge platformunun Architect Agent'isin.
Gorevlerin: RL environment uretmek, test etmek, iyilestirmek,
deploy etmek ve dokumante etmek.

## TEMEL KURALLAR
1. SADECE Gymnasium v0.29+ uyumlu Python kodu uret.
2. Her environment gymnasium.Env sinifindan turetilmeli.
3. Zorunlu metodlar: __init__, step, reset, close
4. step() donusu: (observation, reward, terminated, truncated, info)
5. reset(seed=None) donusu: (observation, info)
6. observation_space ve action_space __init__'te tanimlanmali
7. Tum numerik degerler numpy float32 olmali
8. np.random.Generator kullan (eski np.random KULLANMA)
9. render() metodu opsiyonel ama tavsiye edilir

## KOD KALITE KURALLARI
1. Type hints kullan
2. Docstring yaz (sinif ve her public metod icin)
3. Magic number kullanma, sabitleri sinif seviyesinde tanimla
4. Edge case'leri handle et (NaN, Inf, out-of-bounds)
5. Seed ile deterministik olmayi garanti et

## REWARD FONKSIYONU KURALLARI
1. Reward degerlerini [-10, 10] araliginda tut (clipping)
2. Dense reward tercih et (sparse sadece zorunluysa)
3. Negative reward, positive ile orantili olmali
4. Reward hacking'e karsi koruma ekle
5. info dict'ine reward bilesenleri ayri ayri yaz (debug icin)

## OBSERVATION SPACE KURALLARI
1. Tum degerleri [-1, 1] veya [0, 1] araligina normalize et
2. Sadece karar icin gerekli bilgiyi dahil et
3. Gymnasium standart tiplerini kullan: Box, Discrete, MultiDiscrete

## ACTION SPACE KURALLARI
1. Discrete: sonlu secenekler (al/sat/bekle)
2. Box: surekli degerler (portfoy agirliklari)
3. Gecersiz aksiyonlari icsel olarak handle et

## CIKTI FORMATI
Sadece Python kodu uret. Aciklama, markdown, yorum blogu YAZMA.
Kod calisir durumda olmali - import'lar dahil.

3.3 Skill Sistemi (İki Katmanlı: Hazır + Dinamik)

3.3.1 Skill Seçim Akışı
SKILL SECIM AKISI:

1. Kullanici istegi gelir: 'havalimani bagaj bandi optimizasyonu'

2. Domain classifier calisir:
   - Bilinen domain mi? (finans, grid, kontrol, optimizasyon, oyun)
   - EVET -> Hazir skill prompt'u kullan (Katman 1)
   - HAYIR -> Dinamik skill generation (Katman 2)

3. Katman 2 - Dinamik Skill Generation:
   LLM'e sor: 'Havalimani bagaj bandi optimizasyonu icin
   bir RL environment yazarken dikkat edilmesi gereken
   domain-spesifik kurallar nelerdir?'

   LLM cevabi (ornek):
   - Observation: bant hizi, kuyruk uzunlugu, bagaj boyutlari
   - Action: bant hizi ayarla, yonlendirme kapisi ac/kapa
   - Reward: throughput - bekleme_suresi - hasar_orani
   - Constraints: max bant hizi, kapasite limiti
   - Termination: tum bagajlar islendi veya timeout

4. Bu dinamik skill, system prompt'a eklenir
5. Kod uretimi bu enriched context ile yapilir

3.3.2 Katman 1: Hazır Skill Prompt’ları
Sık kullanılan domain’ler için önceden test edilmiş, optimize edilmiş prompt ekleri. Bu skill’ler daha yüksek kalite garantisi verir çünkü domain-spesifik kurallar ve edge case’ler önceden tanımlanmıştır.


Bu skill’ler başlangıç seti. Platform büyüdükçe yeni hazır skill’ler eklenir: sağlık, enerji, telekom, NLP, robotik navigasyon, supply chain vb. Dinamik skill’lerden en sık kullanılanlar zaman içinde hazır skill’e promote edilir.

3.3.3 Katman 2: Dinamik Skill Generation
Kullanıcı bilinmeyen bir domain istediğinde, Architect Agent otomatik olarak o domain için geçici bir skill prompt üretir:
DINAMIK SKILL GENERATION PROMPT:

Sen bir RL environment tasarim uzmansin.
Kullanici su domain icin bir environment istiyor:

DOMAIN: {user_description}

Bu domain icin bir RL environment yazarken dikkat edilmesi
gereken domain-spesifik kurallari listele:

1. OBSERVATION SPACE: Bu domain'de agent ne gormeli?
   Hangi degerler/metrikler karar icin kritik?

2. ACTION SPACE: Agent ne yapabilmeli?
   Discrete mi continuous mu? Kac boyutlu?

3. REWARD FUNCTION: Basari nasil olculur?
   Hangi metrikler odullendirilmeli, hangisi cezalandirilmali?

4. TRANSITION DYNAMICS: Fizik/kurallar nasil calisir?
   Deterministik mi stokastik mi?

5. TERMINATION CONDITIONS: Episode ne zaman biter?
   Basari kosulu? Basarisizlik kosulu? Zaman asimi?

6. EDGE CASES: Bu domain'e ozel dikkat edilmesi
   gereken sinir durumlar neler?

7. TIPIK PARAMETRELER: Varsayilan degerler ne olmali?

SADECE kurallari listele. Kod yazma.

LLM’in ürettiği domain kuralları, system prompt’a eklenir ve kod üretimi bu zenginleştirilmiş context ile yapılır. Bu dinamik skill prompt’lar cached edilir — aynı domain tekrar istenirse yeniden üretilmez.

3.3.4 Skill Gelişim Döngüsü
SKILL YASAM DONGUSU:

Bilinmeyen domain istegi
    |
    v
Dinamik skill uretilir (Katman 2)
    |
    v
Env uretilir, test edilir, deploy edilir
    |
    v
Skill cache'e kaydedilir (ayni domain icin reuse)
    |
    v
[Eger bu domain 10+ kez istenirse]
    |
    v
Admin review -> Hazir skill'e promote et (Katman 1)
    |
    v
Skill prompt optimize edilir, edge case'ler eklenir


3.4 Araçlar (Tools)

3.5 Karar Matrisi

3.6 Hata Düzeltme Prompt’u
Test fail ettiğinde agent’a gönderilen ikinci prompt:
HATA DUZELTME PROMPT:

Onceki kodun asagidaki testleri GECEMEDI:

FAIL: {test_name}
HATA: {error_message}
DETAY: {error_details}

Orijinal spec: {env_spec_json}
Onceki kod: {previous_code}

HATALI BOLUMU DUZELT ve TUM KODU tekrar uret.
Sadece Python kodu uret. Aciklama yazma.

3.7 Batch vs On-Demand Üretim

Bölüm 4: Data Meselesi


Bölüm 5: Görselleştirme

Bölüm 6: Hosting
Her env = bir Docker container. MVP: Hetzner CPX31 ($18/ay) tek sunucu.
Cloudflare -> Nginx -> FastAPI Gateway -> Docker Engine
                                        -> PostgreSQL + Redis

Cold start: 2-5 sn. Idle timeout: 15 dk. LRU eviction.
Güvenlik: Container izolasyonu, no egress, resource limits, kod tarama.

Bölüm 7: Training API (Mod A: Remote Step)


import rlforge

env = rlforge.make('gridworld-10x10', api_key='KEY')
obs, info = env.reset(seed=42)
for step in range(10000):
    action = my_agent.act(obs)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()

Bölüm 8: Fizibilite


Bölüm 9: Maliyet


Bölüm 10: Fiyatlandırma

Bölüm 11: Environment Builder [Phase 2]


11.1 Akış
ENVIRONMENT BUILDER AKISI:

=== PHASE 1: ENV TASARLA (Lovable modeli) ===

Kullanici: 'Drone navigasyon ortami istiyorum,
            10x10 grid, rastgele engeller'
    |
    v
Architect Agent: Env uretir (30 sn)
    |
    v
Dashboard: Env ozellikleri gosterilir
  - Observation space: Box(shape=[104])
  - Action space: Discrete(4)
  - Reward: distance_to_goal - collision_penalty
  - Episode: max 200 step
  - State Viewer: agent pozisyonu, engeller, hedef
    |
    v
Kullanici AI ile iterate eder (sohbet):
  'Engel sayisini %30'a cikar'  -> Agent gunceller
  'Reward'a yakit tuketimi ekle' -> Agent gunceller
  'Observation'a ruzgar yonu ekle' -> Agent gunceller
  'Difficulty artir'             -> Agent gunceller
  Her degisiklik aninda dashboard'da gorulur.
    |
    v
Kullanici begendi -> 'GitHub'a cek' butonu
  -> Otomatik private repo olusturulur:
     /env/drone_nav_env.py    (Gymnasium kodu)
     /env/env_config.json     (parametreler)
     /README.md               (dokumantasyon)
     /requirements.txt        (bagimliliklar)
     /examples/test_env.py    (test kodu)

=== PHASE 2: AGENT EGIT (opsiyonel buton) ===

Kullanici: 'Bu env'de agent egit' butonuna basar
    |
    v
Platform: Algoritma secer (PPO/SAC/DQN)
  -> SB3 ile egitir (5dk - 2 saat)
  -> Sonuclari dashboard'da gosterir
    |
    v
Egitilmis model GitHub repo'ya eklenir:
  /model/best_model.zip
  /logs/training_curve.json
  /examples/run_agent.py

11.2 Iterate / Konuşma Sistemi
Environment Builder’ın temel farkı: tek seferlik üretim değil, çok turlu sohbet ile iteratif tasarım.
11.2.1 Conversation Agent Prompt
Kullanıcı environment üretildikten sonra sohbet ile değişiklik istediğinde, Architect Agent’a ek prompt eklenir:
CONVERSATION MODE PROMPT (system prompt'a eklenir):

Kullanici mevcut bir environment'i degistirmek istiyor.

MEVCUT ENVIRONMENT KODU:
{current_env_code}

MEVCUT ENVIRONMENT SPEC:
{current_env_spec_json}

KULLANICI ISTEGI:
{user_message}

KURALLAR:
1. Sadece istenen degisikligi yap. Gereksiz degisiklik YAPMA.
2. Mevcut observation/action space'i KORUMA - ekle veya degistir.
3. Degisiklik sonrasi TUM testlerin gecmesi gerekir.
4. Degisikligi acikla: ne degisti, neden, etkisi ne.
5. Breaking change varsa (obs/action space boyutu degisti)
   kullaniciyi UYAR.

CIKTI FORMATI:
1. DEGISIKLIK_OZETI: Tek cumle ne degisti
2. GUNCEL_KOD: Tum environment kodu (tam, calisir)
3. GUNCEL_SPEC: Guncellenmis spec JSON

11.2.2 Desteklenen Değişiklik Tipleri

11.2.3 Dashboard Canlı Görünüm
Her değişiklik sonrası dashboard anında güncellenir:
ENVIRONMENT BUILDER DASHBOARD:
+================================================================+
| RLFORGE Environment Builder           [GitHub'a Cek] [Egit]   |
+================================================================+
|                                                                |
| +-- SOHBET (sol panel) ---+  +-- ENV DETAY (sag panel) -----+ |
| | Kullanici: Drone nav    |  | Ad: drone-nav-v3             | |
| |   ortami istiyorum      |  | Obs: Box(104) float32        | |
| |                         |  | Act: Discrete(8)             | |
| | AI: Urettim! 10x10      |  | Reward: goal - fuel - coll   | |
| |   grid, 4 yonlu hareket |  | Episode: max 200 step        | |
| |                         |  | Versiyon: v3 (2 degisiklik)  | |
| | Kullanici: Capraz       |  +------------------------------+ |
| |   hareket de ekle       |  |                                |
| |                         |  | +-- STATE VIEWER -------------+|
| | AI: Eklendi! Discrete(4)|  | | Obs degerler tablosu        ||
| |   -> Discrete(8) oldu.  |  | | Reward grafik               ||
| |   Test gecti.           |  | | Son 10 step action log      ||
| |                         |  | +-----------------------------+|
| | Kullanici: Reward'a     |  |                                |
| |   yakit tuketimi ekle   |  | +-- VERSIYON GECMISI --------+|
| |                         |  | | v1: ilk uretim             ||
| | AI: Eklendi! Her step   |  | | v2: engel %30              ||
| |   -0.01 fuel cost.      |  | | v3: capraz hareket eklendi ||
| |   Test gecti.           |  | +-----------------------------+|
| +-------------------------+                                    |
+================================================================+

11.3 GitHub Export
Kullanıcı “GitHub’a çek” butonuna bastığında:
Private repo oluşturulur: rlforge-envs/{kullanici}/{env-adi}
Tüm versiyonlar commit edilir: v1, v2, v3... her iterate bir commit
README otomatik üretilir: Env özellikleri, kurulum, kullanım kodu
ZIP download da mümkün: GitHub hesabı yoksa

11.4 Agent Eğitim Butonu (Opsiyonel)
Dashboard’da “Bu env’de agent eğit” butonu. Tıklayınca:
Algoritma otomatik seçilir: Discrete action → DQN/PPO, Continuous → SAC
SB3 ile eğitim başlar: Progress bar, anlık reward grafik
Sonuçlar dashboard’da: Mean reward, başarı%, training curve
Model repo’ya eklenir: /model/best_model.zip + /examples/run_agent.py + /logs/

EGITIM SONRASI GITHUB REPO YAPISI:

rlforge-envs/user/drone-nav/
|-- env/
|   |-- drone_nav_env.py      # Gymnasium kodu (iterate edilmis)
|   |-- env_config.json       # Parametreler
|-- model/                    # (egitim yapildiysa)
|   |-- best_model.zip        # Egitilmis SB3 model
|   |-- checkpoints/          # Ara checkpoint'ler
|-- logs/                     # (egitim yapildiysa)
|   |-- training_curve.json
|   |-- eval_results.json
|-- examples/
|   |-- test_env.py           # Env'i test et
|   |-- run_agent.py          # (egitim yapildiysa) Modeli calistir
|   |-- continue_training.py  # (egitim yapildiysa) Egitimi devam ettir
|-- README.md                 # Otomatik uretilmis dokumantasyon
|-- requirements.txt

11.5 Architect Agent Ek Prompt’ları (Environment Builder Modu)
Architect Agent’ın Environment Builder modunda kullandığı ek skill’ler:
Skill: Iterate / Değişiklik Yönetimi
ITERATE SKILL PROMPT:

Environment degisiklik yonetimi kurallari:
1. Her degisiklik MINIMAL olmali - sadece istenen seyi degistir
2. Degisiklik sonrasi BUTUN testleri tekrar calistir
3. Breaking change (obs/action boyut degisimi) varsa:
   - Kullaniciyi uyar: 'Action space 4'ten 8'e cikti,
     mevcut agent'lar calismaz'
   - Kullanicidan onay iste
4. Her degisiklik icin version bump yap (v1 -> v2 -> v3)
5. Degisiklik ozeti yaz: ne degisti, neden, etkisi
6. Geri alma destekle: 'geri al' -> onceki versiyona don
7. Degisiklikler ATOMIK olmali - ya tamami uygulanir ya hic

Skill: Dashboard Sync
DASHBOARD SYNC SKILL PROMPT:

Her degisiklik sonrasi dashboard'a su bilgileri gonder:
1. SPEC_UPDATE: Guncellenmis env spec JSON
2. CODE_UPDATE: Guncellenmis Python kodu
3. CHANGE_SUMMARY: Tek cumle degisiklik ozeti
4. VERSION: Yeni versiyon numarasi
5. TEST_RESULTS: 8 testin sonuclari (pass/fail)
6. BREAKING_CHANGE: bool - obs/action space degisti mi?
7. WARNINGS: Kullaniciya gosterilecek uyarilar

11.6 Fiyatlandırma (Environment Builder)

Bölüm 12: AI Research Lab [Phase 3]

12.1 Konsept
RLForge sadece araç değil, araştırma ortağı olur. Platformun içinde AI agent’lardan oluşan bir araştırma ekibi bulunur.
12.2 Agent Ekibi

12.3 Kullanıcı Senaryosu
KULLANICI: 'Multi-agent cooperation konusunda ne var?'

LITERATURE AGENT:
  -> Son 20 paper'i tarar
  -> Kullanilan env'leri, algoritmalari, metrikleri cikarir
  -> Ozet tablo sunar

KULLANICI: 'Su paper'daki setup'i replike et' (PDF yukler)

REPLICATION AGENT:
  -> Paper'i okur, env spec cikarir
  -> Architect Agent ile env uretir
  -> Paper'daki algoritma ile egitir
  -> Sonuclari paper'daki baseline ile karsilastirir

KULLANICI: 'Reward fonksiyonunu degistirip dene'

EXPERIMENT AGENT:
  -> Orijinal ve degistirilmis reward ile iki egitim calistirir
  -> Reward curve'leri ust uste koyar
  -> Istatistiksel karsilastirma sunar

ANALYSIS AGENT:
  -> 'Reward hacking var gibi gorunuyor, step 200K'de agent
     exploit buluyor. Reward fonksiyonuna anti-exploit eklenmeli.'

Bölüm 13: MVP Yol Haritası
Faz 1 (Hafta 1-3): Mod A Foundation
Architect Agent v1 (tüm prompt/skill/tool bu dokümandaki gibi)
REST API + Python SDK
5 hazır env + custom env generation
Tek sunucu + State Viewer
Faz 2 (Hafta 4-6): Mod A Olgunlaşma
Vectorized API + ödeme (Stripe) + dashboard
Architect Agent v2: otonom iyileştirme
Faz 3 (Hafta 7-9): Environment Builder
Builder UI: sohbet + env detay + state viewer + iterate + GitHub export + agent eğitim butonu
Faz 4 (Hafta 10-12): Growth
20+ env şablonu + fork + CLI + Fly.io geçiş
Faz 5 (Ay 4-6): Research Lab
Paper upload + Literature Agent + Replication Agent

Bölüm 14: Riskler

EK A: Landing Page Metinleri

A.1 — Hazır RL Environment API

Başlık: Production-Ready RL Environments. Tek API Call Uzaklığında.

Alt başlık: Haftalar süren environment geliştirmeyi unutun. RLForge’un hazır, test edilmiş, Gymnasium-uyumlu ortamlarını API üzerinden anında kullanmaya başlayın.

Nedir?
RLForge, farklı domain’lerde (finans, oyun, lojistik, robotik, optimizasyon) hazır RL environment’ları sunan bir platformdur. Her environment, Gymnasium v0.29+ standardında üretilmiş, 8 farklı testten geçmiş ve Docker container içinde izole olarak çalışır.
Nasıl Çalışır?
Kayıt ol, API key al. 30 saniye.
Environment seç, katalogdan domain ve zorluk seviyesine göre filtrele.
SDK ile bağlan: rlforge.make('trading-5stock') — tek satır.
Agent’ını eğit: env.step(action) — Stable-Baselines3, RLlib, CleanRL, herhangi bir framework.
Ne Sunar?
Sıfır kurulum: Docker, Kubernetes, GPU — hiçbiriyle uğraşma. pip install rlforge, başla.
Gymnasium uyumlu: Mevcut RL kodun değişmeden çalışır.
Test edilmiş: Her env 8 otomatik testten geçmiş: syntax, API uyumu, reward sanity, determinism, performance, memory.
Sürekli iyileşen: Architect Agent her ortamı sürekli izler, reward hacking yakalar, bug’ları fix’ler, difficulty’yi ayarlar.
Free tier: 3 environment, 30K step/ay. Kredi kartı gerekmez.

# 3 satirda baslat
import rlforge
env = rlforge.make('gridworld-maze-v1', api_key='YOUR_KEY')
obs, info = env.reset()


A.2 — Custom RL Environment Generation

Başlık: Hayalindeki RL Ortamını Anlat. 30 Saniyede Hazır.

Alt başlık: Kod yazmadan, Gymnasium bilmeden, Docker kurmadan — sadece ne istediğini yaz. RLForge’un AI Architect Agent’ı environment’ını saniyeler içinde üretir, test eder ve API olarak yayınlar.

Nedir?
RLForge’un Architect Agent’ı, doğal dil açıklamanızı çalışır bir RL environment’a dönüştüren bir AI’dır. “5 hisseli borsa trading ortamı, komisyon %0.1” yazın — 30 saniye sonra test edilmiş, deploy edilmiş, API’si açık bir Gymnasium environment’ınız olsun.
Nasıl Çalışır?
Anlat: “Drone engelden kaçsın, 10x10 grid, rastgele engeller” — sadece yaz.
Architect Agent üretir: AI, doğal dilinizi analiz eder. Domain’a uygun observation space, action space, reward function ve fizik kurallarını belirler. Gymnasium-uyumlu Python kodu yazar.
Otomatik test: 8 farklı test (syntax, API uyumu, reward sanity, determinism, performance, memory) otomatik çalışır. Başarısızsa agent kodu düzeltir ve tekrar test eder.
Anında yayınla: Test geçen environment Docker container’a paketlenir ve API endpoint’i anında açılır. rlforge.make(’senin-env’) ile kullanmaya başla.
Ne Sunar?
Kod yazmadan environment: Gymnasium syntaxı, reward engineering, observation normalization — hiçbirini bilmene gerek yok.
5 domain desteği: Finans, oyun, robotik, lojistik, optimizasyon — her domain için uzmanlaşmış AI skill’leri.
Kendini iyileştiren ortamlar: Architect Agent, ortamı yaratmakla kalmaz — sürekli izler. Reward hacking yakalar, bug fix’ler, difficulty ayarlar.
Fork & özelleştir: Mevcut bir ortamı al, üzerine değişiklik yap. “Trading ortamını al ama kripto için uyarla.”
NVIDIA Eureka tabanlı: Akademik olarak kanıtlanmış LLM-based environment generation. %83 oranında insan uzmanları geçen kalite.

# Custom env olustur ve kullan
import rlforge

# 1. Env'ini tanimla
env_id = rlforge.generate(
  description='Drone engelden kacsin, 10x10 grid, rastgele engeller',
  domain='robotics'
)

# 2. Kullanmaya basla
env = rlforge.make(env_id, api_key='YOUR_KEY')
obs, info = env.reset()


A.3 — Auto Research Lab [Phase 3]

Başlık: RL Araştırmanız İçin AI Ekibiniz. Paper’dan Deneyime, Dakikalar İçinde.

Alt başlık: Paper okumak, repo bulmak, dataset indirmek, environment kurmak için saatler harcamayı bırakın. RLForge’un AI araştırma ekibi, paper’ınızı yükleyin, deneylerinizi çalıştırsın, sonuçları karşılaştırsın.

Nedir?
RLForge Research Lab, platformun içinde çalışan bir AI araştırma ekibidir. Beş uzman agent’tan oluşur: literür tarama, paper replikasyonu, deney yönetimi, sonuç analizi ve benchmark. Her biri otonom çalışır, birbirleriyle koordine olur.
Nasıl Çalışır?
Paper yükle: PDF’i sürükle-bırak. Literature Agent paper’ı okur: environment, algoritma, metrikler, baseline sonuçları çıkarır.
Replike et: Replication Agent, paper’daki setup’ı otomatik oluşturur. Architect Agent environment’ı üretir, SB3 ile eğitir, sonuçları paper’ın baseline’ıyla karşılaştırır.
Dene: “Reward fonksiyonunu değiştir” de. Experiment Agent orijinal ve değiştirilmiş versiyonla iki eğitim çalıştırır, sonuçları üst üste koyar.
Analiz al: Analysis Agent: “Step 200K’de reward hacking var, agent exploit buluyor. Anti-exploit eklenmeli.” — somut, uygulanabilir öneriler.
Ne Sunar?
Paper’dan deneyime 15 dakikada: PDF yükle, bekle, sonuçları gör. Repo bulmak, dataset indirmek, environment kurmak yok.
Otomatik literür tarama: “Multi-agent cooperation’da son 20 paper ne kullanmış?” — env, algoritma, metrik tablosu anında.
A/B deneyleri tek tıkla: “Reward’ı değiştir ve karşılaştır” — iki eğitim paralel çalışır, grafik üst üste gelir.
Akıllı analiz: Neden takıldın, ne değiştirmelisin, hangi hiperparametre önemli — AI tabanlı öneriler.
Tüm sonuçlar GitHub’da: Her deney otomatik repo olur. Tekrarlanabilir, paylaşılabilir, yayınlanabilir.



MVP kapsamına SADIK KAL. Phase 2/3’ü kodlama. Önce çalışan MVP.
