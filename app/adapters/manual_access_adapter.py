"""
Şartname Bölüm 23/28: Instagram, Xiaohongshu, Douyin, Weibo, TSUM, VK gibi kaynaklar
resmi API / izinli servis / güvenilir browser-automation gerektirir. Bu adapter, kullanıcıyı
yanıltmamak için bu kaynakları HER ZAMAN "disabled" olarak raporlar; sahte "healthy" görünmez.

Gerçek entegrasyon için:
- Instagram: Meta Graph API (Instagram Content Publishing / Business Discovery) resmi erişim başvurusu gerekir.
- Xiaohongshu/Douyin/Weibo: resmi açık API'leri kısıtlıdır; üçüncü taraf veri sağlayıcı veya
  yasal browser-automation servisi (ör. Bright Data benzeri) ile entegre edilmesi gerekir.
Bu adapter o entegrasyon yapılana kadar "disabled" statüsünde durur.
"""
from app.adapters.base import BaseSourceAdapter
from app.schemas import RawProduct, SourceHealthResult


class ManualAccessAdapter(BaseSourceAdapter):
    requires_manual_access_setup = True

    def __init__(self, source_name: str, reason: str):
        self.source_name = source_name
        self.reason = reason

    async def health_check(self) -> SourceHealthResult:
        return SourceHealthResult(source_name=self.source_name, status="disabled", detail=self.reason)

    async def fetch_new_products(self, limit: int = 100) -> list[RawProduct]:
        return []
