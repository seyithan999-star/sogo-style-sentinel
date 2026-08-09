"""
Şartname Bölüm 18/21: mobil uyumlu, authentication korumalı yönetim paneli.
Basit HTTP Basic Auth kullanır (private erişim şartı için yeterli minimum önlem).
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select, desc, func

from app.config import settings
from app.database import async_session
from app.models import Product, SourceRun, TelegramDelivery, Feedback

router = APIRouter()
security = HTTPBasic()


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, settings.dashboard_username)
    correct_pass = secrets.compare_digest(credentials.password, settings.dashboard_password)
    if not (correct_user and correct_pass):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Basic"})
    return True


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(_: bool = Depends(check_auth)):
    async with async_session() as session:
        total_products = (await session.execute(select(func.count(Product.id)))).scalar_one()
        total_sent = (await session.execute(
            select(func.count(TelegramDelivery.id)).where(TelegramDelivery.status == "sent")
        )).scalar_one()
        total_failed = (await session.execute(
            select(func.count(TelegramDelivery.id)).where(TelegramDelivery.status == "failed")
        )).scalar_one()
        feedback_counts = await session.execute(
            select(Feedback.action, func.count(Feedback.id)).group_by(Feedback.action)
        )
        runs = (await session.execute(
            select(SourceRun).order_by(desc(SourceRun.started_at)).limit(30)
        )).scalars().all()

    fb_rows = "".join(f"<tr><td>{a}</td><td>{c}</td></tr>" for a, c in feedback_counts)
    run_rows = "".join(
        f"<tr><td>{r.source_name}</td><td class='status-{r.status}'>{r.status}</td>"
        f"<td>{r.items_found}</td><td>{r.items_new}</td>"
        f"<td>{r.started_at.strftime('%d.%m %H:%M') if r.started_at else '-'}</td></tr>"
        for r in runs
    )

    html = f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SOGO Style Sentinel Dashboard</title>
    <style>
      body {{ font-family: -apple-system, sans-serif; background:#111; color:#eee; padding:16px; }}
      .cards {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:24px; }}
      .card {{ background:#1c1c1c; border-radius:12px; padding:16px; min-width:140px; }}
      .card b {{ font-size:24px; display:block; }}
      table {{ width:100%; border-collapse:collapse; margin-bottom:24px; }}
      td, th {{ padding:8px; border-bottom:1px solid #333; text-align:left; font-size:14px; }}
      .status-healthy {{ color:#4ade80; }}
      .status-degraded {{ color:#facc15; }}
      .status-blocked, .status-disabled {{ color:#f87171; }}
      h2 {{ margin-top:0; }}
    </style></head>
    <body>
      <h2>SOGO Style Sentinel</h2>
      <div class="cards">
        <div class="card">Toplam Ürün<b>{total_products}</b></div>
        <div class="card">Gönderilen<b>{total_sent}</b></div>
        <div class="card">Başarısız<b>{total_failed}</b></div>
      </div>
      <h3>Son Kaynak Taramaları</h3>
      <table><tr><th>Kaynak</th><th>Durum</th><th>Bulunan</th><th>Yeni</th><th>Zaman</th></tr>{run_rows}</table>
      <h3>Feedback Dağılımı</h3>
      <table><tr><th>Aksiyon</th><th>Adet</th></tr>{fb_rows}</table>
    </body></html>
    """
    return HTMLResponse(content=html)
