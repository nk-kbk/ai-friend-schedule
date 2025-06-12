# config/settings.py の【最終決定版】フルコード！

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# --- 基本設定 ---
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# --- 環境判定 ---
# Renderのサーバー上ならTrue、ひろとくんのPCならFalseになるよ
IS_RENDER = 'RENDER' in os.environ

# --- セキュリティ設定 ---
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-YOUR-DEFAULT-KEY') # デフォルトキーは自分のものに合わせたままでOK

# DEBUGは、本番(Render)では必ずFalseに！
if IS_RENDER:
    DEBUG = False
else:
    DEBUG = True

# ALLOWED_HOSTSの設定
ALLOWED_HOSTS = []
if IS_RENDER:
    RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
# 開発中はローカルホストも許可
if not IS_RENDER:
    ALLOWED_HOSTS.append('localhost')
    ALLOWED_HOSTS.append('127.0.0.1')


# --- アプリケーション定義 ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # whitenoise を'django.contrib.staticfiles'のすぐ下に追加！
    'whitenoise.runserver_nostatic', 
    # 自作アプリたち
    'accounts.apps.AccountsConfig',
    'calendar_app.apps.CalendarAppConfig',
    'ai_assistant_app.apps.AiAssistantAppConfig',
    'notifications_app.apps.NotificationsAppConfig',
    'main_app.apps.MainAppConfig',
    'schedule_requests_app.apps.ScheduleRequestsAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # whitenoise のためのミドルウェアを追加！
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications_app.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- データベース設定 ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )


# --- パスワード検証 ---
AUTH_PASSWORD_VALIDATORS = [
    # ... (ここは省略するね、ひろとくんの元のままでOK！)
]


# --- 国際化 ---
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True


# --- ファイルストレージ設定【エラー修正箇所！】 ---
# 静的ファイル (CSS, JavaScript) の設定
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# メディアファイル (User uploads) の設定
MEDIA_URL = '/media/'
if IS_RENDER:
    # Renderでは永続ディスクを使うのがおすすめ (今は一時ディスク)
    MEDIA_ROOT = '/var/data/media' 
else:
    # 開発中はプロジェクトフォルダ内のmediaフォルダ
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ✨✨ ここがエラー修正の重要ポイントだよ！ ✨✨
STORAGES = {
    # 静的ファイル（CSSやJS）の扱い方を指定
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    # デフォルトのファイル（画像など）の扱い方を指定
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}
# --- ✨✨ エラー修正はここまで！ ✨✨ ---


# --- その他の設定 ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

# --- APIキーの設定 ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NIJIVOICE_API_KEY = os.getenv('NIJIVOICE_API_KEY')
NIJIVOICE_VOICE_ACTOR_ID = os.getenv('NIJIVOICE_VOICE_ACTOR_ID')


# --- 本番環境用の追加セキュリティ設定 ---
if IS_RENDER:
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
    if RENDER_EXTERNAL_URL:
        CSRF_TRUSTED_ORIGINS = [RENDER_EXTERNAL_URL]
    # SECURE_SSL_REDIRECT = True # Renderがやってくれるので基本的には不要
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True