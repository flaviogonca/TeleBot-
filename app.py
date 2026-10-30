import asyncio
import os
import re
import threading
import time
import secrets
from pathlib import Path
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, send_from_directory
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError
)
from telethon.tl.types import User
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Dlaylama_bot")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")
SESSION_NAME = os.environ.get("SESSION_NAME", "web_telegram_session")
SESSION_MINUTES = int(os.environ.get("SESSION_MINUTES", "25"))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

if not API_ID or not API_HASH or not APP_PASSWORD or not SECRET_KEY:
    raise RuntimeError(
        "Configura API_ID, API_HASH, APP_PASSWORD e SECRET_KEY no .env"
    )

if SESSION_MINUTES < 1:
    raise RuntimeError("SESSION_MINUTES deve ser pelo menos 1.")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    WTF_CSRF_TIME_LIMIT=None,
)

csrf = CSRFProtect(app)


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify(ok=False, error=f"Erro de validação CSRF: {e.description}"), 400

# O loop asyncio e o cliente Telegram vivem numa thread dedicada.
telegram_loop = asyncio.new_event_loop()
telegram_thread = None
client = None
bot_entity = None
phone_pending = None
phone_code_hash = None
login_password_needed = False
telegram_authenticated = False
expires_at = None
logout_timer = None
state_lock = threading.RLock()
messages = []
MAX_MESSAGES = 150


def add_message(item):
    with state_lock:
        for i, old in enumerate(messages):
            if old["id"] == item["id"]:
                messages[i] = item
                break
        else:
            messages.append(item)

        messages.sort(key=lambda m: m["date"])
        del messages[:-MAX_MESSAGES]


def get_messages():
    with state_lock:
        return [dict(m) for m in messages]


def require_web_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("web_authenticated"):
            return jsonify(ok=False, error="Inicia sessão na aplicação."), 401
        return fn(*args, **kwargs)
    return wrapper


def telegram_worker():
    global telegram_loop
    if telegram_loop.is_closed():
        telegram_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(telegram_loop)
    telegram_loop.run_forever()


def start_telegram_worker():
    global telegram_thread, telegram_loop
    with state_lock:
        if telegram_loop.is_closed():
            telegram_loop = asyncio.new_event_loop()
        if not telegram_loop.is_running():
            telegram_thread = threading.Thread(
                target=telegram_worker, daemon=True, name="TelegramWorker"
            )
            telegram_thread.start()


# Inicia a thread do Telegram no arranque da aplicação (funciona em Gunicorn, Render, etc.)
start_telegram_worker()


def run_telegram(coro, timeout=45):
    if not telegram_loop.is_running():
        start_telegram_worker()
        start_wait = time.time()
        while not telegram_loop.is_running() and (time.time() - start_wait < 3):
            time.sleep(0.05)

    if not telegram_loop.is_running():
        coro.close()
        raise RuntimeError("O serviço Telegram não está iniciado.")

    future = asyncio.run_coroutine_threadsafe(coro, telegram_loop)
    return future.result(timeout=timeout)


async def message_to_dict(msg):
    media_url = None

    if msg.media:
        try:
            path = await msg.download_media(file=str(MEDIA_DIR) + "/")
            if path:
                media_url = "/media/" + Path(path).name
        except Exception as exc:
            print("Erro ao descarregar media:", exc)

    buttons = []
    if msg.buttons:
        for ri, row in enumerate(msg.buttons):
            converted = []
            for ci, button in enumerate(row):
                obj = getattr(button, "button", None)
                url = (
                    getattr(button, "url", None)
                    or getattr(obj, "url", None)
                )
                converted.append({
                    "text": str(button.text),
                    "row": ri,
                    "col": ci,
                    "url": url
                })
            buttons.append(converted)

    return {
        "id": msg.id,
        "date": msg.date.timestamp() if msg.date else time.time(),
        "text": msg.raw_text or "",
        "outgoing": bool(msg.out),
        "media": media_url,
        "buttons": buttons
    }


async def record_message(msg):
    add_message(await message_to_dict(msg))


def cancel_logout_timer():
    global logout_timer
    if logout_timer:
        logout_timer.cancel()
        logout_timer = None


async def disconnect_telegram(log_out=True):
    """Termina a sessão Telegram e invalida o ficheiro de sessão."""
    global client, bot_entity, telegram_authenticated
    global expires_at, phone_pending, phone_code_hash
    global login_password_needed

    cancel_logout_timer()

    old_client = client
    client = None
    bot_entity = None
    telegram_authenticated = False
    expires_at = None
    phone_pending = None
    phone_code_hash = None
    login_password_needed = False

    if old_client is not None:
        try:
            if old_client.is_connected():
                if log_out:
                    await old_client.log_out()
                else:
                    await old_client.disconnect()
        except Exception as exc:
            print("Aviso ao terminar sessão:", exc)
            try:
                await old_client.disconnect()
            except Exception:
                pass


def schedule_auto_logout():
    global logout_timer, expires_at

    cancel_logout_timer()
    expires_at = time.time() + SESSION_MINUTES * 60

    def expire():
        asyncio.create_task(disconnect_telegram(log_out=True))

    logout_timer = telegram_loop.call_later(
        SESSION_MINUTES * 60, expire
    )


async def attach_bot_handlers():
    global bot_entity

    bot_entity = await client.get_entity(BOT_USERNAME)

    @client.on(events.NewMessage(chats=bot_entity))
    async def on_new_message(event):
        await record_message(event.message)

    @client.on(events.MessageEdited(chats=bot_entity))
    async def on_edit(event):
        await record_message(event.message)

    history = await client.get_messages(bot_entity, limit=40)
    for msg in reversed(history):
        await record_message(msg)


async def begin_phone_login(phone):
    global client, phone_pending, phone_code_hash
    global login_password_needed, telegram_authenticated

    if client is not None:
        await disconnect_telegram(log_out=False)

    phone_pending = phone
    phone_code_hash = None
    login_password_needed = False
    telegram_authenticated = False

    client = TelegramClient(
        str(BASE_DIR / SESSION_NAME), API_ID, API_HASH
    )

    await client.connect()

    if await client.is_user_authorized():
        await finish_login()
        return {"status": "authenticated"}

    result = await client.send_code_request(phone)
    phone_code_hash = result.phone_code_hash
    return {"status": "code_sent"}


async def finish_login():
    global telegram_authenticated

    await attach_bot_handlers()
    telegram_authenticated = True
    schedule_auto_logout()


async def verify_phone_code(code):
    global login_password_needed

    if client is None or not phone_pending or not phone_code_hash:
        raise ValueError("Solicita primeiro um código de acesso.")

    try:
        await client.sign_in(
            phone=phone_pending,
            code=code,
            phone_code_hash=phone_code_hash
        )
    except SessionPasswordNeededError:
        login_password_needed = True
        return {"status": "password_required"}

    await finish_login()
    return {"status": "authenticated"}


async def verify_2fa(password):
    global login_password_needed

    if client is None or not login_password_needed:
        raise ValueError("A verificação por palavra-passe não está pendente.")

    await client.sign_in(password=password)
    login_password_needed = False
    await finish_login()
    return {"status": "authenticated"}




# =====================================================
# PÁGINAS
# =====================================================

@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/access")
def app_access():
    data = request.get_json(silent=True) or {}
    password = str(data.get("password", ""))

    if not secrets.compare_digest(password, APP_PASSWORD):
        return jsonify(ok=False, error="Palavra-passe incorreta."), 401

    csrf_token = session.get("csrf_token")
    session.clear()
    if csrf_token:
        session["csrf_token"] = csrf_token
    session["web_authenticated"] = True
    session.permanent = True
    return jsonify(ok=True)


@app.post("/api/telegram/phone")
@require_web_login
def telegram_phone():
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    phone = re.sub(r"[\s\-\(\)]", "", phone)

    if not phone.startswith("+") or not phone[1:].isdigit():
        return jsonify(
            ok=False,
            error="Usa o formato internacional, por exemplo +244923456789."
        ), 400

    try:
        result = run_telegram(begin_phone_login(phone))
        return jsonify(ok=True, **result)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/telegram/code")
@require_web_login
def telegram_code():
    data = request.get_json(silent=True) or {}
    code = str(data.get("code", "")).strip()

    if not code:
        return jsonify(ok=False, error="Introduz o código recebido."), 400

    try:
        result = run_telegram(verify_phone_code(code))
        return jsonify(ok=True, **result)
    except (PhoneCodeInvalidError, PhoneCodeExpiredError) as exc:
        return jsonify(ok=False, error="Código inválido ou expirado."), 400
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/telegram/password")
@require_web_login
def telegram_password():
    data = request.get_json(silent=True) or {}
    password = str(data.get("password", ""))

    try:
        result = run_telegram(verify_2fa(password))
        return jsonify(ok=True, **result)
    except PasswordHashInvalidError:
        return jsonify(ok=False, error="Palavra-passe Telegram incorreta."), 400
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.get("/api/state")
@require_web_login
def api_state():
    with state_lock:
        authenticated = telegram_authenticated
        expiry = expires_at

    remaining = max(0, int(expiry - time.time())) if expiry else 0

    return jsonify(
        ok=True,
        authenticated=authenticated,
        password_required=login_password_needed,
        remaining_seconds=remaining,
        bot=BOT_USERNAME
    )


@app.get("/api/messages")
@require_web_login
def api_messages():
    if not telegram_authenticated:
        return jsonify(ok=False, error="Inicia sessão no Telegram."), 401
    return jsonify(ok=True, messages=get_messages())


@app.post("/api/send")
@require_web_login
def api_send():
    if not telegram_authenticated or bot_entity is None:
        return jsonify(ok=False, error="Sessão Telegram inativa."), 401

    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()

    if not text:
        return jsonify(ok=False, error="A mensagem está vazia."), 400

    async def send():
        msg = await client.send_message(bot_entity, text)
        await record_message(msg)

    try:
        run_telegram(send())
        return jsonify(ok=True)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/click")
@require_web_login
def api_click():
    if not telegram_authenticated or bot_entity is None:
        return jsonify(ok=False, error="Sessão Telegram inativa."), 401

    data = request.get_json(silent=True) or {}

    try:
        message_id = int(data["message_id"])
        row = int(data["row"])
        col = int(data["col"])

        if min(message_id, row, col) < 0:
            raise ValueError("Índices inválidos.")

        async def click():
            msg = await client.get_messages(bot_entity, ids=message_id)
            if not msg or not msg.buttons:
                raise ValueError("Os botões já não estão disponíveis.")
            await msg.click(row, col)

        run_telegram(click())
        return jsonify(ok=True)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/upload")
@require_web_login
def api_upload():
    if not telegram_authenticated or bot_entity is None:
        return jsonify(ok=False, error="Sessão Telegram inativa."), 401

    file = request.files.get("image")
    caption = request.form.get("caption", "").strip()

    if not file or not file.filename:
        return jsonify(ok=False, error="Escolhe um ficheiro."), 400

    name = secure_filename(file.filename)
    if not name:
        return jsonify(ok=False, error="Nome de ficheiro inválido."), 400

    path = MEDIA_DIR / name
    stem, suffix = path.stem, path.suffix
    i = 1
    while path.exists():
        path = MEDIA_DIR / f"{stem}_{i}{suffix}"
        i += 1

    file.save(path)

    async def send_file():
        msg = await client.send_file(
            bot_entity, str(path), caption=caption or None
        )
        await record_message(msg)

    try:
        run_telegram(send_file())
        return jsonify(ok=True)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/logout")
@require_web_login
def telegram_logout():
    try:
        run_telegram(disconnect_telegram(log_out=True))
        return jsonify(ok=True)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/access/logout")
def web_logout():
    csrf_token = session.get("csrf_token")
    session.clear()
    if csrf_token:
        session["csrf_token"] = csrf_token
    return jsonify(ok=True)


@app.get("/media/<path:name>")
@require_web_login
def media(name):
    return send_from_directory(MEDIA_DIR, name)


# CSRF é verificado também nos pedidos fetch da interface.
# O token é disponibilizado no HTML e enviado no cabeçalho X-CSRFToken.


if __name__ == "__main__":
    start_telegram_worker()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
