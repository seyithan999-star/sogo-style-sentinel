"""
Kaynak kayıt defteri. Buraya yeni Shopify tabanlı mağaza eklemek = 1 satır.
Gerçek domain'leri sen (kullanıcı) doğrulayıp eklemelisin - varsayım/tahmini domain
eklemek şartnamenin "sahte kaynak yok" ilkesine aykırı olur, bu yüzden liste kasıtlı
olarak boş/örnek bırakılmıştır. README'de nasıl kaynak ekleneceği anlatılmıştır.
"""
from app.adapters.shopify_adapter import ShopifyAdapter
from app.adapters.manual_access_adapter import ManualAccessAdapter
from app.adapters.base import BaseSourceAdapter

# ÖRNEK: gerçek, doğrulanmış Shopify domain'lerini buraya ekle.
# ShopifyAdapter("Marka Adi", "https://gercek-magaza-domaini.com"),
SHOPIFY_SOURCES: list[BaseSourceAdapter] = [
    # ShopifyAdapter("Ornek Marka", "https://ornek-magaza.myshopify.com"),
]

# Dürüstçe "disabled" olarak işaretlenen, resmi izin gerektiren kaynaklar.
MANUAL_ACCESS_SOURCES: list[BaseSourceAdapter] = [
    ManualAccessAdapter("instagram", "Meta Graph API resmi izni gerekir - henüz bağlanmadı"),
    ManualAccessAdapter("pinterest", "Pinterest API resmi izni gerekir - henüz bağlanmadı"),
    ManualAccessAdapter("xiaohongshu_red", "Resmi API yok, izinli 3. parti veri servisi gerekir"),
    ManualAccessAdapter("douyin", "Resmi API yok, izinli 3. parti veri servisi gerekir"),
    ManualAccessAdapter("weibo", "Resmi API izni gerekir - henüz bağlanmadı"),
    ManualAccessAdapter("wildberries", "Resmi API/izinli erişim doğrulanmadı"),
    ManualAccessAdapter("ozon", "Resmi API/izinli erişim doğrulanmadı"),
    ManualAccessAdapter("lamoda", "Resmi API/izinli erişim doğrulanmadı"),
    ManualAccessAdapter("farfetch", "Resmi partner API'si gerekir - henüz bağlanmadı"),
    ManualAccessAdapter("yoox_net_a_porter", "Resmi partner API'si gerekir - henüz bağlanmadı"),
]


def get_all_sources() -> list[BaseSourceAdapter]:
    return SHOPIFY_SOURCES + MANUAL_ACCESS_SOURCES
