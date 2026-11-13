"""Composição da aplicação. Rotas e regras ficam nos controllers."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from .database import initialize_database
from .core.config import FRONTEND_URL, CORS_ORIGINS, ENVIRONMENT
from .core.security import SECRET
from .controllers import auth, catalog, tickets, orders, dashboard, operations, insights, admin

@asynccontextmanager
async def lifespan(app):
    if len(SECRET) < 32:
        raise RuntimeError('Configure JWT_SECRET com pelo menos 32 caracteres no .env')
    if ENVIRONMENT != "production":
        initialize_database()
    yield

app = FastAPI(title='IndusTrack', version='1.0.2', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=['*'], allow_headers=['*'],
)

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(status_code=409, content={'detail': 'Registro duplicado ou referência inválida.'})

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
