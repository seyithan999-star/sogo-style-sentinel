# SOGO Style Sentinel

Telegram üzerinden çalışan, kadın giyim trend/ürün araştırma sistemi. Şartname belgesindeki
mimariye göre sıfırdan kurulmuştur: FastAPI + aiogram + PostgreSQL(Supabase) + APScheduler.

## ⚠️ DÜRÜST DURUM RAPORU (önce bunu oku)

Bu proje **çalışır durumda bir çekirdek** olarak teslim edilmiştir, "her şey bitti, sadece
tıkla" bir paket değildir. Şartnamenin "sahte demo/placeholder yok" ilkesine uyarak açıkça
söylüyorum:

**Gerçekten çalışan / test edilebilir kısımlar:**
- Telegram bot: `/start`, `/status`, `/report`, `/favorites`, `/search`, feedback butonları
- PostgreSQL/Supabase şeması + Alembic migration
- Duplicate engeli (URL hash + perceptual image hash)
- Kural bazlı puanlama motoru
- Öğrenen style_signals sistemi (feedback → ağırlık güncelleme)
- 08:00 Europe/Istanbul scheduler + idempotency
- Dashboard (temel, authentication korumalı)
- **Shopify tabanlı mağaza adaptörü** — bu gerçekten çalışır: birçok bağımsız/premium marka
  mağazası Shopify altyapılıdır ve `/products.json` herkese açık endpoint'ini sunar.

**Henüz bağlanmamış, dürüstçe "disabled" gösterilen kısımlar** (`app/adapters/registry.py`):
- Instagram, Pinterest, Xiaohongshu, Douyin, Weibo, Wildberries, Ozon, Lamoda, Farfetch, YOOX/Net-a-Porter
- Bunlar resmi API başvurusu, izinli 3. parti veri servisi veya iş ortaklığı gerektirir.
  Sahte "aktif" göstermek yerine sistem bunları açıkça `disabled` yapar (bkz. `/status` komutu).
- Bu kaynakları eklemek ayrı bir iş kalemidir; her biri için resmi erişim/izin sağlandıkça
  `ManualAccessAdapter` yerine gerçek bir adapter yazılabilir.

**Bu ortamda (Claude sohbeti) yapılamayanlar:**
- İnternet erişimi kapalı olduğu için `pip install` ve canlı Telegram/DB testi burada
  çalıştırılamadı. Kod **sözdizimi olarak test edildi** (`python -m py_compile` ile tüm dosyalar
  hatasız derlendi) ama runtime/entegrasyon testi mutlaka Replit/Railway/kendi bilgisayarında
  yapılmalı.

Yani: iskelet, mimari, veritabanı, bot mantığı, puanlama, dedup, öğrenme, scheduler — hepsi
gerçek ve production kalitesinde yazıldı. Eksik olan, geniş kaynak listesinin (30+ marka,
Çin/Rusya siteleri) her biri için ayrı ayrı resmi erişim/entegrasyon işi — bu tek oturumda
bitecek bir iş değil, kademeli genişletilecek bir iş.

---

## Kurulum (adım adım)

### 1. Telegram bot oluştur
1. Telegram'da `@BotFather`'a git → `/newbot` → adını ver → **API token'ı kopyala**.
2. Bota `/start` yazıp konuş, sonra kendi Telegram user ID'ni öğrenmek için `@userinfobot`'a yaz.

### 2. Supabase (PostgreSQL) oluştur
1. [supabase.com](https://supabase.com) → yeni proje oluştur (ücretsiz plan yeterli, başlangıç için).
2. Project Settings → Database → Connection string → **URI** kopyala (Session pooler önerilir).
3. İki farklı formatta lazım olacak (`.env.example`'a bak):
   - `DATABASE_URL` → `postgresql+asyncpg://...`
   - `DATABASE_URL_SYNC` → `postgresql+psycopg2://...` (alembic için)

### 3. Ortam değişkenlerini ayarla
`.env.example` dosyasını `.env` olarak kopyala, tüm değerleri doldur.

### 4. Yerelde test (opsiyonel ama önerilir)
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head       # veritabanı tablolarını oluşturur
pytest                     # gerçek unit testleri çalıştırır
uvicorn app.main:app --reload
```
Çalışırsa: Telegram'da botuna `/start` yaz, birkaç saniye içinde cevap gelmeli.

### 5. Deploy (Railway önerilir — sabit fiyat, kredi kaygısı yok)
1. Bu klasörü GitHub'a push et.
2. [railway.app](https://railway.app) → New Project → GitHub repo'yu bağla.
3. Environment Variables kısmına `.env` içeriğini tek tek gir.
4. Railway otomatik olarak `Procfile`'ı kullanıp deploy eder.
5. `USE_WEBHOOK=true` yapıp `WEBHOOK_BASE_URL`'i Railway'in verdiği public URL ile doldurmanı öneririm (polling yerine webhook, production için daha stabil).

**Alternatif: Replit** — `Dockerfile` üzerinden Replit'te de deploy edilebilir, ama sürekli
çalışan servisler için Railway/Render genelde daha öngörülebilir maliyetlidir.

### 6. Kaynak ekleme
`app/adapters/registry.py` içindeki `SHOPIFY_SOURCES` listesine gerçek, doğruladığın Shopify
mağaza domain'lerini ekle:
```python
ShopifyAdapter("Marka Adi", "https://gercek-magaza-domaini.com"),
```
Domain'in gerçekten Shopify olup olmadığını `https://domain.com/products.json` adresine
tarayıcıdan girerek kontrol edebilirsin — JSON dönerse çalışır.

---

## Mimari özeti
```
app/
  main.py          FastAPI giriş noktası, webhook/polling yönetimi
  config.py        Tüm ayarlar (.env'den okunur)
  database.py      Async SQLAlchemy engine/session
  models.py        Tüm tablolar (products, feedback, style_signals, source_runs, ...)
  schemas.py       Kaynak adaptör ortak veri sözleşmesi (RawProduct)
  filters.py       Kalıcı hariç marka/kategori filtreleri
  dedup.py         URL + perceptual image hash duplicate engeli
  scoring.py       Kural bazlı puanlama motoru
  learning.py      Feedback'ten style_signals ağırlık güncelleme
  ingestion.py     Tara → filtrele → dedup → puanla → kaydet pipeline'ı
  reporting.py     08:00 raporu, idempotency
  scheduler.py     APScheduler cron job
  dashboard.py     Basit auth korumalı web paneli
  adapters/
    base.py                  Adaptör sözleşmesi (health_check + fetch_new_products)
    shopify_adapter.py       GERÇEK ÇALIŞAN adapter
    manual_access_adapter.py Resmi izin gerektiren kaynaklar için dürüst "disabled" adapter
    registry.py               Aktif kaynak listesi
  bot/
    instance.py      Bot + Dispatcher
    handlers.py       /start /status /report /favorites /search + feedback callback
    keyboards.py       Inline butonlar
    product_card.py    3 görsel + caption + link gönderimi
migrations/          Alembic migration dosyaları
tests/                Gerçek unit testler (pytest)
```

## Bilinen sınırlar
- Instagram/Pinterest/Çin-Rusya kaynakları henüz bağlı değil (yukarıda açıklandı).
- Çince arama kelimeleri ve hashtag havuzu şartnamede var ama henüz kod tarafında
  kullanılan bir kaynak yok — bağlanacak ilk Çin kaynağı ile birlikte eklenmeli.
- AI vision/LLM destekli görsel analiz (Faz 2) `scoring.py` içinde bilinçli olarak stub
  bırakıldı, sahte skor üretmiyor.
- Tek worker process varsayılıyor; birden fazla instance çalıştırılacaksa scheduler için
  Postgres advisory lock eklenmesi gerekir (`app/scheduler.py` içine not düşüldü).

## Aylık tahmini maliyet (Ağustos 2026 referans fiyatları, şartnamedeki gibi)
- Railway: kullanım bazlı, küçük bir bot için ~$5-10/ay
- Supabase Free: $0 (üretim için Pro önerilir, $25/ay)
- Ek kaynak entegrasyonları (proxy/3. parti veri servisi): kaynağa göre değişir, henüz dahil değil
