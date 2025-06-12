# config/settings.py の Renderデプロイ用フルコード！

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url # 👈 これが追加されたimportだよ！

BASE_DIR = Path(__file__).resolve().parent.parent

# --- .env ファイルを読み込む設定 ---
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# 🚀 Renderが本番環境かどうかを判断するための大事なフラグ！
# Renderの環境には自動で`RENDER`っていう環境変数が設定されるんだ。
IS_RENDER = 'RENDER' in os.environ

# --- セキュリティ設定 ---
# 秘密のキーは.envファイルから読み込むのが安全だよ！
# もし.envにSECRET_KEYがなかったら、Djangoが作ったキーを使うようになってる
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-+fejb5m()eqrb@#e@ipb_u0vw%h)^z6ov')

# 🚀 DEBUGは、本番環境(Render)では必ずFalseにする！
if IS_RENDER:
    DEBUG = False
else:
    DEBUG = True

# 🚀 ALLOWED_HOSTSの設定！これが超重要！
ALLOWED_HOSTS = []

if IS_RENDER:
    # Renderで自動的に設定されるホスト名を追加するよ
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
    # ✨ whitenoise を'django.contrib.staticfiles'のすぐ下に追加！
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
    # ✨ whitenoise のためのミドルウェアを追加！
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
# 🚀 ここがひろとくんと一緒に改造した部分だね！
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Renderの環境変数にDATABASE_URLがあったら、それを優先して使うようにする魔法だよ！
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True # SSL接続を強制するおまじない
    )


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


# --- 静的ファイル (CSS, JavaScript, Images) ---
# 🚀 ここからが静的ファイルとメディアファイルの大事な設定！
STATIC_URL = '/static/'
# 🚀 本番環境(Render)では、静的ファイルを集める場所を指定する
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# 🚀 静的ファイルの効率的な配信と圧縮のための設定
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# --- メディアファイル (User uploads) ---
MEDIA_URL = '/media/'
# 🚀 メディアファイルの置き場所も、本番環境と開発環境で分けるのがおすすめ！
if IS_RENDER:
    # Renderのディスクは一時的なものだから、本当はS3とか別のサービスを使うのがベスト！
    # でも、まずは動かすために、一時的なフォルダを指定しておくね！
    MEDIA_ROOT = '/var/data/media' 
else:
    # 開発中は今まで通りでOK
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# --- デフォルトの主キーの型 ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- 認証関連 ---
AUTH_USER_MODEL = 'accounts.User'

# --- APIキーの設定 ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
COEFONT_API_KEY = os.getenv('COEFONT_API_KEY')
COEFONT_ID_AYA = os.getenv('COEFONT_ID_AYA')


# --- 🚀 セキュリティ設定（本番環境用） ---
if IS_RENDER:
    # CSRF対策: Renderのドメインを信頼するリストに追加
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
    if RENDER_EXTERNAL_URL:
        CSRF_TRUSTED_ORIGINS = [RENDER_EXTERNAL_URL]
    # SECURE_SSL_REDIRECT = True  # Renderがやってくれるので不要なことが多い
    # SECURE_HSTS_SECONDS = 31536000 # 365日
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True