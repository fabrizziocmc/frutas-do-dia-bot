import discord
import asyncio
import aiohttp
import os
import re
from datetime import datetime

TOKEN = os.environ["DISCORD_TOKEN"]
CANAL_ID = 1514471338042065038

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Emojis por fruta
EMOJIS = {
    "rocket": "🚀", "spin": "🌀", "blade": "🗡️", "bomb": "💣",
    "smoke": "💨", "spike": "🌵", "chop": "🪓", "spring": "🌿",
    "kilo": "⚖️", "ice": "❄️", "sand": "🏜️", "dark": "🌑",
    "diamond": "💎", "light": "✨", "love": "💕", "rubber": "🪃",
    "barrier": "🛡️", "magma": "🌋", "quake": "💥", "buddha": "☯️",
    "phoenix": "🔥", "rumble": "⚡", "pain": "😈", "gravity": "🌀",
    "dough": "🍞", "shadow": "🌙", "venom": "🐍", "control": "🎮",
    "soul": "👻", "dragon": "🐉", "leopard": "🐆", "kitsune": "🦊",
    "gas": "☁️", "ghost": "👻", "sound": "🎵", "mammoth": "🦣",
    "t-rex": "🦕", "portal": "🌀",
}

def get_emoji(nome):
    return EMOJIS.get(nome.lower(), "🍈")

async def buscar_stock_e_timer():
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get("https://fruityblox.com/stock", headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None, None, None

                html = await resp.text()

                # Extrai frutas do Normal stock
                normal_match = re.search(r'## Normal.*?Next reset([\d:]+)(.*?)## Mirage', html, re.DOTALL)
                mirage_match = re.search(r'## Mirage.*?Next reset([\d:]+)(.*?)(?:\[FruityBlox\]|$)', html, re.DOTALL)

                normal_timer = normal_match.group(1).strip() if normal_match else None
                mirage_timer = mirage_match.group(1).strip() if mirage_match else None

                # Extrai nomes e preços das frutas
                fruta_pattern = re.compile(r'\[(\w[\w\s-]*?)\1[\w\s]*?(\d[\d,]*?)R\s*[\d,]+\]', re.IGNORECASE)

                normal_frutas = fruta_pattern.findall(normal_match.group(2)) if normal_match else []
                mirage_frutas = fruta_pattern.findall(mirage_match.group(2)) if mirage_match else []

                return normal_frutas, mirage_frutas, (normal_timer, mirage_timer)
    except Exception as e:
        print(f"Erro: {e}")
        return None, None, None

def timer_para_segundos(timer_str):
    """Converte HH:MM:SS para segundos"""
    try:
        partes = timer_str.strip().split(":")
        if len(partes) == 3:
            h, m, s = int(partes[0]), int(partes[1]), int(partes[2])
            return h * 3600 + m * 60 + s
        elif len(partes) == 2:
            m, s = int(partes[0]), int(partes[1])
            return m * 60 + s
    except:
        pass
    return 4 * 3600  # fallback 4h

def montar_mensagem(normal_frutas, mirage_frutas):
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    linhas = [f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n"]

    if normal_frutas:
        linhas.append("**NORMAL STOCK:**")
        for nome, preco in normal_frutas:
            emoji = get_emoji(nome)
            preco_fmt = f"{int(preco.replace(',', '')):,}".replace(",", ".")
            linhas.append(f"{emoji} {nome} — $ {preco_fmt}")

    if mirage_frutas:
        linhas.append("\n**MIRAGE STOCK:**")
        for nome, preco in mirage_frutas:
            emoji = get_emoji(nome)
            preco_fmt = f"{int(preco.replace(',', '')):,}".replace(",", ".")
            linhas.append(f"{emoji} {nome} — $ {preco_fmt}")

    if not normal_frutas and not mirage_frutas:
        return (
            f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n\n"
            "Veja as frutas disponíveis agora:\n"
            "🔗 https://fruityblox.com/stock"
        )

    linhas.append("\n🔗 fruityblox.com/stock")
    return "\n".join(linhas)

async def loop_stock():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)

    while not client.is_closed():
        normal, mirage, timers = await buscar_stock_e_timer()
        mensagem = montar_mensagem(normal or [], mirage or [])
        if canal:
            await canal.send(mensagem)

        # Aguarda até o próximo reset do Normal stock
        if timers and timers[0]:
            segundos = timer_para_segundos(timers[0])
            print(f"✅ Stock postado. Próximo em {segundos}s ({timers[0]})")
            await asyncio.sleep(segundos + 10)  # +10s para garantir que o stock já atualizou
        else:
            await asyncio.sleep(4 * 3600)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    client.loop.create_task(loop_stock())

client.run(TOKEN)
