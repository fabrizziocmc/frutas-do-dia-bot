import discord
import asyncio
import os
import re
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright

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
    "diamond":"💎","barrier":"🛡️","kilo":"⚖️","spring":"🌿",
}

async def buscar_stock_playwright():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-setuid-sandbox"])
            page = await browser.new_page()
            await page.goto("https://fruityblox.com/stock", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            content = await page.content()
            await browser.close()

            # Extrai seções Normal e Mirage
            normal_frutas = []
            mirage_frutas = []

            # Padrão para capturar frutas: nome + preço em Beli
            # O site mostra: NomeNomeTipo5.000R 50 (nome repetido + tipo + preço)
            # Vamos usar uma abordagem mais simples: pegar texto das seções
            
            # Tenta extrair via regex do HTML renderizado
            # Frutas aparecem como links: /items/nome com preço próximo
            frutas_raw = re.findall(
                r'href="/items/([^"]+)"[^>]*>.*?(\d[\d,.]+)\s*R\s*\d',
                content, re.DOTALL
            )

            # Determina se é normal ou mirage pela posição no HTML
            normal_idx = content.find("Normal")
            mirage_idx = content.find("Mirage")

            for match in re.finditer(
                r'href="/items/([^"]+)".*?(\d[\d,.]+)\s*R\s*\d',
                content, re.DOTALL
            ):
                nome_slug = match.group(1)
                preco_str = match.group(2).replace(".", "").replace(",", "")
                nome = nome_slug.capitalize()
                try:
                    preco = int(preco_str)
                except:
                    preco = 0
                pos = match.start()
                if pos < mirage_idx or mirage_idx == -1:
                    normal_frutas.append({"name": nome, "price": preco})
                else:
                    mirage_frutas.append({"name": nome, "price": preco})

            return normal_frutas, mirage_frutas

    except Exception as e:
        print(f"Erro Playwright: {e}")
        return [], []

def segundos_ate_proximo_reset():
    agora = datetime.now(timezone.utc)
    for h in RESET_HOURS_UTC:
        if h > agora.hour:
            proximo = agora.replace(hour=h, minute=0, second=15, microsecond=0)
            return max((proximo - agora).total_seconds(), 1)
    proximo = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=15, microsecond=0)
    return max((proximo - agora).total_seconds(), 1)

def montar_mensagem(normal, mirage):
    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    linhas = [f"🍎 **STOCK DO BLOX FRUITS** — {agora}\n"]

    if normal:
        linhas.append("**NORMAL STOCK:**")
        for f in normal:
            nome = f["name"]
            preco = f["price"]
            emoji = EMOJIS.get(nome.lower(), "🍈")
            linhas.append(f"{emoji} {nome} — $ {preco:,}".replace(",", "."))

    if mirage:
        linhas.append("\n**MIRAGE STOCK:**")
        for f in mirage:
            nome = f["name"]
            preco = f["price"]
            emoji = EMOJIS.get(nome.lower(), "🍈")
            linhas.append(f"{emoji} {nome} — $ {preco:,}".replace(",", "."))

    if not normal and not mirage:
        linhas.append("Veja as frutas disponíveis agora:")
        linhas.append("🔗 https://fruityblox.com/stock")
    else:
        linhas.append("\n🔗 fruityblox.com/stock")

    return "\n".join(linhas)

async def postar_stock(canal):
    normal, mirage = await buscar_stock_playwright()
    msg = montar_mensagem(normal, mirage)
    await canal.send(msg)
    print(f"✅ Postado: {len(normal)} normal, {len(mirage)} mirage")

async def loop_stock():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)
    await postar_stock(canal)

    while not client.is_closed():
        espera = segundos_ate_proximo_reset()
        print(f"⏳ Próximo post em {int(espera)}s")
        await asyncio.sleep(espera)
        await postar_stock(canal)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    client.loop.create_task(loop_stock())

client.run(TOKEN)
