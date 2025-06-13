# config/settings.py の【最終解決・完成版】フルコード！

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
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-YOUR-DEFAULT-KEY')

# ✨✨ DEBUG設定を、元の安全な形に戻したよ！ ✨✨
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
else:
    # 開発中はローカルホストを許可
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# --- アプリケーション定義 ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'accounts.apps.AccountsConfig',
    'calendar_app.apps.CalendarAppConfig',
    'ai_assistant_app.apps.AiAssistantAppConfig',
    'notifications_app.apps.NotificationsAppConfig',
    'main_app.apps.MainAppConfig',
    'schedule_requests_app.apps.ScheduleRequestsAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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

# --- ✨✨ データベース設定を、より確実な形に修正したよ！ ✨✨ ---
if IS_RENDER:
    # 本番環境(Render)では、DATABASE_URLを使ってPostgreSQLに接続する
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # 開発環境(ひろとくんのPC)では、今まで通りSQLite3を使う
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- パスワード検証 ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- 国際化 ---
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# --- ファイルストレージ設定 ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
if IS_RENDER:
    MEDIA_ROOT = '/var/data/media'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}

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
        
