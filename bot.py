import discord
import asyncio
import aiohttp
import os
from datetime import datetime, timezone

TOKEN = os.environ["DISCORD_TOKEN"]
CANAL_ID = 1514471338042065038

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# O stock reseta a cada 4h nos horários fixos UTC: 00, 04, 08, 12, 16, 20
RESET_HOURS_UTC = [0, 4, 8, 12, 16, 20]

async def buscar_stock():
    """Tenta buscar o stock da API. Retorna lista de frutas ou None."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://blox-fruits-api.onrender.com/api/bloxfruits/stock",
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # A API retorna string JSON dentro do JSON
                    if isinstance(data, str):
                        import json
                        data = json.loads(data)
                    stock = data.get("stock", data)
                    if stock and stock != {}:
                        return stock
    except Exception as e:
        print(f"Erro API: {e}")
    return None

def segundos_ate_proximo_reset():
    """Calcula quantos segundos faltam para o próximo reset."""
    agora = datetime.now(timezone.utc)
    hora_atual = agora.hour

    # Encontra o próximo horário de reset
    for h in RESET_HOURS_UTC:
        if h > hora_atual:
            proximo = agora.replace(hour=h, minute=0, second=10, microsecond=0)
            return (proximo - agora).total_seconds()

    # Se passou de 20h, próximo reset é meia-noite
    proximo = agora.replace(hour=0, minute=0, second=10, microsecond=0)
    proximo = proximo.replace(day=agora.day + 1)
    return (proximo - agora).total_seconds()

def montar_mensagem(stock):
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')

    if not stock:
        return (
            f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n\n"
            "**NORMAL STOCK:**\n"
            "🚀 Rocket — $ 0\n"
            "🌀 Spin — $ 7.500\n"
            "_(+ outras frutas)_\n\n"
            "🔗 Veja a lista completa: https://fruityblox.com/stock"
        )

    emojis = {
        "rocket":"🚀","spin":"🌀","blade":"🗡️","bomb":"💣","smoke":"💨",
        "spike":"🌵","chop":"🪓","spring":"🌿","ice":"❄️","sand":"🏜️",
        "dark":"🌑","light":"✨","love":"💕","rubber":"🪃","magma":"🌋",
        "quake":"💥","buddha":"☯️","phoenix":"🔥","rumble":"⚡","dough":"🍞",
        "shadow":"🌙","venom":"🐍","dragon":"🐉","leopard":"🐆","kitsune":"🦊",
        "ghost":"👻","sound":"🎵","gravity":"🌀","pain":"😈","control":"🎮",
    }

    linhas = [f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n"]

    normal = stock.get("normal", [])
    mirage = stock.get("mirage", [])

    if normal:
        linhas.append("**NORMAL STOCK:**")
        for f in normal:
            nome = f.get("name", "?")
            preco = f.get("price", 0)
            emoji = emojis.get(nome.lower(), "🍈")
            linhas.append(f"{emoji} {nome} — $ {preco:,}".replace(",", "."))

    if mirage:
        linhas.append("\n**MIRAGE STOCK:**")
        for f in mirage:
            nome = f.get("name", "?")
            preco = f.get("price", 0)
            emoji = emojis.get(nome.lower(), "🍈")
            linhas.append(f"{emoji} {nome} — $ {preco:,}".replace(",", "."))

    linhas.append("\n🔗 fruityblox.com/stock")
    return "\n".join(linhas)

async def loop_stock():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)

    # Posta imediatamente ao iniciar
    stock = await buscar_stock()
    msg = montar_mensagem(stock)
    if canal:
        await canal.send(msg)

    while not client.is_closed():
        # Espera até o próximo reset exato
        espera = segundos_ate_proximo_reset()
        print(f"⏳ Próximo post em {int(espera)}s")
        await asyncio.sleep(espera)

        stock = await buscar_stock()
        msg = montar_mensagem(stock)
        if canal:
            await canal.send(msg)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    client.loop.create_task(loop_stock())

client.run(TOKEN)
