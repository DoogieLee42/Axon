from pathlib import Path

BASE_DIR=Path(__file__).resolve().parent.parent
DB_ROOT=BASE_DIR/'db'
FRONTEND_DIR=BASE_DIR/'frontend'
FRONTEND_DIST=FRONTEND_DIR/'dist'

SECRET_KEY='dev'
DEBUG=True
ALLOWED_HOSTS=['*']
INSTALLED_APPS=[
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'db.patients','db.medical_records','db.master_files',
    'emr_etl.masterdata','emr_etl.samio',
    'simple_history','auditlog','import_export'
]
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware','simple_history.middleware.HistoryRequestMiddleware']
ROOT_URLCONF='emr_cert.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='emr_cert.wsgi.application'
DATABASES={
    'default':{'ENGINE':'django.db.backends.sqlite3','NAME':DB_ROOT/'clinical.sqlite3'},
    'master_files':{'ENGINE':'django.db.backends.sqlite3','NAME':DB_ROOT/'master_files.sqlite3'}
}
DATABASE_ROUTERS=[
    'db.routers.ClinicalDBRouter',
    'db.routers.MasterFileDBRouter'
]
LANGUAGE_CODE='ko-kr'
TIME_ZONE='Asia/Seoul'
USE_I18N=True
USE_TZ=True
STATIC_URL='static/'
STATIC_ROOT=BASE_DIR/'staticfiles'
STATICFILES_DIRS=[]

frontend_assets=FRONTEND_DIST/'assets'
if frontend_assets.exists():
    STATICFILES_DIRS.append(frontend_assets)

CSRF_TRUSTED_ORIGINS=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
