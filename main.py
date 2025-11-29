import aiobale
from flask import Response
import httpx
from aiobale import Client
from aiobale.client.session import aiohttp
import aiobale.types as types
import quart
from quart import Quart, jsonify
import toml
import json


def toml_to_json(toml_str):
    data = toml.loads(toml_str)
    return json.dumps(data, ensure_ascii=False, indent=2)


def toml_file_to_json(toml_file_path, json_file_path=None):
    with open(toml_file_path, 'r', encoding='utf-8') as f:
        data = toml.load(f)

    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    if json_file_path:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)

    return json_str


client = Client()
app = Quart(__name__)


async def get_user_name(username):
    s = await client.search_username(username)
    s = s.dict()
    if s.get("group"):
        return str(s.get("group").get("id"))
    elif s.get("user"):
        return "0"
    else:
        return "0"


async def get_latest_message(chat_id):
    try:
        s = await client.load_history(chat_id, aiobale.enums.ChatType.CHANNEL)
    except BaseException:
        return ""

    l = s[0]

    if l.text:
        h = str(l.text)
    elif l.document.caption:
        h = l.document.caption
    return h.content


async def get_img(chat_id):
    try:
        s = await client.load_history(chat_id, aiobale.enums.ChatType.CHANNEL)
    except BaseException:
        return ""
    try:
        doc = s[0].document
        file = await client.get_file(file_id=doc.file_id, access_hash=doc.access_hash)
        return file
    except BaseException:
        return "no profile"


@app.route("/")
async def index():
    return await quart.render_template("index.html")


@app.route("/logo.png")
async def logo():
    return await quart.send_file("fosp.png")


@app.route("/docs")
async def docs():
    return await quart.render_template("docs.html")


@app.route("/Arad.ttf")
async def font():
    with open("Arad.ttf", "rb") as r:
        return Response(r.read(), mimetype="ttf")


@app.route("/favicon.ico")
async def favicon():
    return await quart.send_file("fosp.png")


@app.route("/generate")
async def generate():
    return await quart.render_template("generate.html")


@app.route("/<user>")
async def get_user(user):
    result = await get_user_name(user)
    res2 = await get_latest_message(int(result))

    try:
        print(res2)
        data = json.loads(toml_to_json(res2))
        return await quart.render_template("template.html", json_data=data, image=f"/getimage/{user}")
    except Exception as e:
        print(e)
        return await quart.render_template("404.html", username=user)


@app.route("/getimage/<user>")
async def get_image(user):
    result = await get_user_name(user)

    try:
        url = await get_img(result)
        async with httpx.AsyncClient() as client:
            response = await client.get(url.url)
            content = response.content
            return quart.Response(content, mimetype="jpg")
    except Exception as e:
        if f"{e}" == "'str' object has no attribute 'url'":
            with open("defaultprofile.png", "rb") as r:
                return Response(r.read(), mimetype="png")

if __name__ == "__main__":
    app.run()
