from flask import Flask, request, send_file, jsonify
import threading
import discord
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

def draw_bold_text(draw, position, text, font, fill):
    x, y = position
    draw.text((x, y), text, font=font, fill=fill)
    draw.text((x+1, y), text, font=font, fill=fill)
    draw.text((x, y+1), text, font=font, fill=fill)

async def gerar_imagem_com_dados(token):
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = True

    client = discord.Client(intents=intents)

    stats = {}

    @client.event
    async def on_ready():
        try:
            guild = client.guilds[0]  # Pega o primeiro servidor
            stats["nome"] = guild.name
            stats["id"] = guild.id
            stats["membros"] = guild.member_count
            stats["entradas"] = 0
            stats["saidas"] = 0
            stats["mensagens"] = 0
        finally:
            await client.close()

    try:
        await client.start(token)
    except discord.LoginFailure:
        return None, "Token inválido"
    except Exception as e:
        return None, f"Erro ao conectar: {str(e)}"

    # Geração da imagem com base nos dados coletados
    img = Image.new("RGB", (800, 400), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw_bold_text(draw, (40, 40), stats["nome"], font, fill=(255, 255, 255))
    draw_bold_text(draw, (40, 90), f"ID: {stats['id']}", font, fill=(180, 180, 180))

    stat_data = [
        ("icons/membros.png", "Membros", str(stats["membros"])),
        ("icons/entradas.png", "Entradas recentes", str(stats["entradas"])),
        ("icons/saidas.png", "Saídas recentes", str(stats["saidas"])),
        ("icons/mensagens.png", "Mensagens", str(stats["mensagens"])),
    ]

    y = 150
    for icon_path, label, value in stat_data:
        if os.path.exists(icon_path):
            icon = Image.open(icon_path).resize((32, 32))
            img.paste(icon, (40, y), mask=icon.convert("RGBA"))
        draw_bold_text(draw, (90, y), label, font, fill=(255, 255, 255))
        draw_bold_text(draw, (90, y + 20), value, font, fill=(255, 255, 255))
        y += 60

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer, None

def rodar_asyncio(func, *args):
    return asyncio.run(func(*args))

@app.route('/stats', methods=['POST'])
def stats_api():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"erro": "Token não fornecido"}), 400

    img_buffer, error = rodar_asyncio(gerar_imagem_com_dados, token)

    if error:
        return jsonify({"erro": error}), 400

    return send_file(img_buffer, mimetype='image/png')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
