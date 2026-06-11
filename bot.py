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
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://blox-fruits-api.onrender.com/api/bloxfruits/stock", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        pass
    return None

async def montar_mensagem(data):
    if not data:
        return "⚠️ Não foi possível buscar o stock agora. Tente mais tarde."

    linhas = ["🍎 **STOCK DO BLOX FRUITS**\n"]

    if "normal" in data:
        linhas.append("**NORMAL STOCK:**")
        for fruta in data["normal"]:
            nome = fruta.get("name", "?")
            preco = fruta.get("price", 0)
            linhas.append(f"🍈 {nome} — $ {preco:,}".replace(",", "."))

    if "mirage" in data:
        linhas.append("\n**MIRAGE STOCK:**")
        for fruta in data["mirage"]:
            nome = fruta.get("name", "?")
            preco = fruta.get("price", 0)
            linhas.append(f"🌊 {nome} — $ {preco:,}".replace(",", "."))

    linhas.append(f"\n_Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}_")
    return "\n".join(linhas)

async def loop_diario():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)
    ultimo_envio = ""

    while not client.is_closed():
        agora = datetime.now().strftime("%H:%M")
        if agora == "08:00" and agora != ultimo_envio:
            data = await buscar_stock()
            mensagem = await montar_mensagem(data)
            if canal:
                await canal.send(mensagem)
            ultimo_envio = agora
        await asyncio.sleep(30)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    client.loop.create_task(loop_diario())

client.run(TOKEN)
