"""
Şartname Bölüm 22: Kaynak Adaptör Standardı.
Her kaynak bu sözleşmeye uymalı ve ortak RawProduct çıktısı üretmelidir.
health_check() 403/429/yapı değişikliğini "0 ürün" diye gizlemez, gerçek durumu raporlar.
"""
from abc import ABC, abstractmethod
from app.schemas import RawProduct, SourceHealthResult


class BaseSourceAdapter(ABC):
    source_name: str = "base"
    # Bu kaynağın gerçekten resmi/izinli/erişilebilir olup olmadığı - dürüstlük ilkesi (bkz. bölüm 23/28)
    requires_manual_access_setup: bool = False

    @abstractmethod
    async def health_check(self) -> SourceHealthResult:
        """Kaynağa gerçek bir istek atarak erişilebilir olup olmadığını kontrol eder."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_new_products(self, limit: int = 100) -> list[RawProduct]:
        """Kaynaktan en yeni ürünleri çeker. Hata durumunda exception fırlatır (worker yakalar)."""
        raise NotImplementedError
