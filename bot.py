import discord
import asyncio
import aiohttp
import os
from datetime import datetime, timezone, timedelta

TOKEN = os.environ["DISCORD_TOKEN"]
CANAL_ID = 1514471338042065038

intents = discord.Intents.default()
client = discord.Client(intents=intents)

RESET_HOURS_UTC = [0, 4, 8, 12, 16, 20]

def segundos_ate_proximo_reset():
    agora = datetime.now(timezone.utc)
    for h in RESET_HOURS_UTC:
        if h > agora.hour:
            proximo = agora.replace(hour=h, minute=0, second=15, microsecond=0)
            return max((proximo - agora).total_seconds(), 1)
    proximo = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=15, microsecond=0)
    return max((proximo - agora).total_seconds(), 1)

def montar_mensagem():
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    proximo_reset_utc = datetime.now(timezone.utc)
    for h in RESET_HOURS_UTC:
        if h > proximo_reset_utc.hour:
            proximo_reset_utc = proximo_reset_utc.replace(hour=h, minute=0, second=0)
            break
    else:
        proximo_reset_utc = (proximo_reset_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    
    # Converte para horário de Brasília (UTC-3)
    proximo_brt = proximo_reset_utc - timedelta(hours=3)
    proximo_str = proximo_brt.strftime('%H:%M')

    return (
        f"🍎 **STOCK DO BLOX FRUITS ACABOU DE ATUALIZAR!**\n"
        f"📅 {agora}\n\n"
        f"Confira agora as frutas disponíveis na loja:\n"
        f"🔗 **https://fruityblox.com/stock**\n\n"
        f"⏰ Próxima atualização às **{proximo_str}** (horário de Brasília)"
    )

async def loop_stock():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)

    # Posta ao iniciar
    await canal.send(montar_mensagem())

    while not client.is_closed():
        espera = segundos_ate_proximo_reset()
        print(f"Próximo post em {int(espera)}s")
        await asyncio.sleep(espera)
        await canal.send(montar_mensagem())

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    client.loop.create_task(loop_stock())

client.run(TOKEN)
