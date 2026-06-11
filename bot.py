import discord
import asyncio
import aiohttp
import os
import json
from datetime import datetime, timezone, timedelta

TOKEN = os.environ["DISCORD_TOKEN"]
CANAL_ID = 1514471338042065038

intents = discord.Intents.default()
client = discord.Client(intents=intents)

RESET_HOURS_UTC = [0, 4, 8, 12, 16, 20]

EMOJIS = {
    "rocket":"🚀","spin":"🌀","blade":"🗡️","bomb":"💣","smoke":"💨",
    "spike":"🌵","chop":"🪓","spring":"🌿","ice":"❄️","sand":"🏜️",
    "dark":"🌑","light":"✨","love":"💕","rubber":"🪃","magma":"🌋",
    "quake":"💥","buddha":"☯️","phoenix":"🔥","rumble":"⚡","dough":"🍞",
    "shadow":"🌙","venom":"🐍","dragon":"🐉","leopard":"🐆","kitsune":"🦊",
    "ghost":"👻","sound":"🎵","gravity":"🌀","pain":"😈","control":"🎮",
    "mammoth":"🦣","gas":"☁️","portal":"🌀","soul":"👻",
    "diamond":"💎","barrier":"🛡️","kilo":"⚖️",
}

async def buscar_stock():
    """Busca o stock via API interna do FruityBlox (Next.js)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://fruityblox.com/stock",
    }
    
    # Tenta a API interna do Next.js
    urls = [
        "https://fruityblox.com/api/stock",
        "https://fruityblox.com/api/fruits/stock",
        "https://fruityblox.com/api/dealer/stock",
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    print(f"Tentando {url} -> {resp.status}")
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"Resposta: {text[:300]}")
                        data = json.loads(text)
                        if data:
                            return data
            except Exception as e:
                print(f"Erro em {url}: {e}")
        
        # Tenta pegar o build ID do Next.js para montar a URL correta
        try:
            async with session.get("https://fruityblox.com/stock", headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                html = await resp.text()
                print(f"HTML length: {len(html)}")
                print(f"HTML preview: {html[:500]}")
        except Exception as e:
            print(f"Erro HTML: {e}")
    
    return None

def segundos_ate_proximo_reset():
    agora = datetime.now(timezone.utc)
    for h in RESET_HOURS_UTC:
        if h > agora.hour:
            proximo = agora.replace(hour=h, minute=0, second=15, microsecond=0)
            return max((proximo - agora).total_seconds(), 1)
    proximo = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=15, microsecond=0)
    return max((proximo - agora).total_seconds(), 1)

async def postar_stock(canal):
    print("Buscando stock...")
    data = await buscar_stock()
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    if data:
        print(f"Dados recebidos: {str(data)[:200]}")
    
    msg = (
        f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n\n"
        "O stock acabou de atualizar!\n"
        "🔗 https://fruityblox.com/stock"
    )
    await canal.send(msg)

async def loop_stock():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)
    await postar_stock(canal)

    while not client.is_closed():
        espera = segundos_ate_proximo_reset()
        print(f"Próximo post em {int(espera)}s")
        await asyncio.sleep(espera)
        await postar_stock(canal)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    client.loop.create_task(loop_stock())

client.run(TOKEN)
