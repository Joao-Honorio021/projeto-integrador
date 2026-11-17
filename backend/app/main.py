"""Composição da aplicação. Rotas e regras ficam nos controllers."""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError as DatabaseTimeoutError
from .database import initialize_database, engine
from .core.config import CORS_ORIGINS, ENVIRONMENT
from .core.security import SECRET
from .controllers import auth, catalog, tickets, orders, dashboard, operations, insights, admin

class ApiPrefixMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] == "http" and (path == "/api" or path.startswith("/api/")):
            raw_path = scope.get("raw_path", b"")
            scope = {
                **scope,
                "path": path[4:] or "/",
                "raw_path": raw_path[4:] if raw_path.startswith(b"/api") else raw_path,
            }
        await self.app(scope, receive, send)

@asynccontextmanager
async def lifespan(app):
    if len(SECRET) < 32:
        raise RuntimeError('Configure JWT_SECRET com pelo menos 32 caracteres no .env')
    if ENVIRONMENT in ('development', 'test') and engine.dialect.name == 'sqlite':
        initialize_database()
    try:
        yield
    finally:
        engine.dispose()

app = FastAPI(
    title='IndusTrack',
    version='1.0.2',
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=['*'], allow_headers=['*'],
)
app.add_middleware(ApiPrefixMiddleware)

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(status_code=409, content={'detail': 'Registro duplicado ou referência inválida.'})

@app.exception_handler(OperationalError)
@app.exception_handler(DatabaseTimeoutError)
async def database_unavailable(request, exc):
    # Não registrar SQL, parâmetros, URL de conexão ou a mensagem bruta do driver.
    logging.getLogger(__name__).error('Banco indisponível: %s %s (%s)', request.method, request.url.path, type(exc).__name__)
    return JSONResponse(status_code=503, content={'detail': 'Banco de dados indisponível. Tente novamente em instantes.'})

for controller in (auth, catalog, tickets, orders, dashboard, operations, insights, admin):
    app.include_router(controller.router)

@app.get('/health')
def health():
    from sqlalchemy import text
    from .database import engine
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return {'status': 'ok', 'version': '1.0.2'}
    except Exception:
        return JSONResponse(status_code=503, content={'status': 'unavailable'})
