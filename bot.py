import discord
import asyncio
import aiohttp
import os
from datetime import datetime

TOKEN = os.environ["DISCORD_TOKEN"]
CANAL_ID = 1514471338042065038

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def buscar_stock():
    urls = [
        "https://blox-fruits-api.onrender.com/api/bloxfruits/stock",
        "https://api.bloxfruits.app/stock",
    ]
    try:
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # Verifica se tem dados úteis
                            if data and data != {"stock": {}}:
                                return data
                except Exception:
                    continue
    except Exception:
        pass
    return None

async def montar_mensagem(data):
    if not data:
        # Fallback: posta o link direto
        return (
            "🍎 **STOCK DO BLOX FRUITS**\n\n"
            "Veja as frutas disponíveis agora:\n"
            "🔗 https://fruityblox.com/stock\n\n"
            f"_Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}_"
        )

    linhas = ["🍎 **STOCK DO BLOX FRUITS**\n"]

    normal = data.get("normal") or data.get("stock", {}).get("normal")
    mirage = data.get("mirage") or data.get("stock", {}).get("mirage")

    if normal:
        linhas.append("**NORMAL STOCK:**")
        for fruta in normal:
            nome = fruta.get("name", "?")
            preco = fruta.get("price", 0)
            linhas.append(f"🍈 {nome} — $ {preco:,}".replace(",", "."))

    if mirage:
        linhas.append("\n**MIRAGE STOCK:**")
        for fruta in mirage:
            nome = fruta.get("name", "?")
            preco = fruta.get("price", 0)
            linhas.append(f"🌊 {nome} — $ {preco:,}".replace(",", "."))

    linhas.append(f"\n_Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}_")
    return "\n".join(linhas)

async def loop_4h():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)

    while not client.is_closed():
        data = await buscar_stock()
        mensagem = await montar_mensagem(data)
        if canal:
            await canal.send(mensagem)
        await asyncio.sleep(4 * 60 * 60)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    client.loop.create_task(loop_4h())

client.run(TOKEN)
