import discord
import asyncio
import aiohttp
import os
import json
from datetime import datetime, timezone

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
    "mammoth":"🦣","gas":"☁️","t-rex":"🦕","portal":"🌀","soul":"👻",
    "diamond":"💎","barrier":"🛡️","kilo":"⚖️",
}

PRECOS = {
    "Rocket": 5000, "Spin": 7500, "Blade": 30000, "Bomb": 80000,
    "Smoke": 100000, "Spike": 180000, "Chop": 30000, "Spring": 60000,
    "Kilo": 5000, "Ice": 350000, "Sand": 420000, "Dark": 500000,
    "Diamond": 600000, "Light": 650000, "Love": 1300000, "Rubber": 750000,
    "Barrier": 800000, "Magma": 850000, "Quake": 1000000, "Buddha": 1200000,
    "Phoenix": 1400000, "Rumble": 2100000, "Pain": 2400000, "Gravity": 2500000,
    "Dough": 2800000, "Shadow": 2900000, "Venom": 3000000, "Control": 3200000,
    "Soul": 3400000, "Dragon": 3500000, "Leopard": 5000000, "Kitsune": 8000000,
    "Gas": 600000, "Ghost": 940000, "Sound": 1700000, "Mammoth": 2000000,
}

async def buscar_stock_bloxverse():
    """Tenta buscar stock da API do Blox Stock bot (Blox Verse)."""
    apis = [
        "https://blox-fruits-api.onrender.com/api/bloxfruits/stock",
        "https://api.blox-verse.xyz/stock",
        "https://bloxfruits.app/api/stock",
    ]
    for url in apis:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        data = json.loads(text)
                        # Tenta diferentes formatos
                        for key in ["normal", "stock", "fruits", "data"]:
                            if key in data and data[key]:
                                return data
        except Exception:
            continue
    return None

def segundos_ate_proximo_reset():
    agora = datetime.now(timezone.utc)
    hora_atual = agora.hour
    for h in RESET_HOURS_UTC:
        if h > hora_atual:
            proximo = agora.replace(hour=h, minute=0, second=15, microsecond=0)
            return max((proximo - agora).total_seconds(), 1)
    from datetime import timedelta
    proximo = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=15, microsecond=0)
    return max((proximo - agora).total_seconds(), 1)

def montar_mensagem_com_dados(normal, mirage):
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    linhas = [f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n"]

    if normal:
        linhas.append("**NORMAL STOCK:**")
        for f in normal:
            nome = f.get("name", "?")
            preco = f.get("price", PRECOS.get(nome, 0))
            emoji = EMOJIS.get(nome.lower(), "🍈")
            linhas.append(f"{emoji} {nome} — $ {preco:,}".replace(",", "."))

    if mirage:
        linhas.append("\n**MIRAGE STOCK:**")
        for f in mirage:
            nome = f.get("name", "?")
            preco = f.get("price", PRECOS.get(nome, 0))
            emoji = EMOJIS.get(nome.lower(), "🍈")
            linhas.append(f"{emoji} {nome} — $ {preco:,}".replace(",", "."))

    linhas.append("\n🔗 fruityblox.com/stock")
    return "\n".join(linhas)

def montar_mensagem_fallback():
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return (
        f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n\n"
        "O stock acabou de atualizar!\n"
        "Veja as frutas disponíveis agora:\n"
        "🔗 https://fruityblox.com/stock"
    )

async def postar_stock(canal):
    data = await buscar_stock_bloxverse()

    if data:
        normal = data.get("normal") or data.get("stock", {}).get("normal") or []
        mirage = data.get("mirage") or data.get("stock", {}).get("mirage") or []
        if normal or mirage:
            msg = montar_mensagem_com_dados(normal, mirage)
            await canal.send(msg)
            return

    await canal.send(montar_mensagem_fallback())

async def loop_stock():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)
    await postar_stock(canal)

    while not client.is_closed():
        espera = segundos_ate_proximo_reset()
        print(f"⏳ Próximo post em {int(espera)}s ({int(espera/60)} min)")
        await asyncio.sleep(espera)
        await postar_stock(canal)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    client.loop.create_task(loop_stock())

client.run(TOKEN)
