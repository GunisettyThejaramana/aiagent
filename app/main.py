from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import Base, engine
from app.routes import router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise AI Assistant",
    version="1.0.0"
)

# Static Files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Home Page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Enterprise AI Assistant"
        }
    )

# API Routes
app.include_router(router)