from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import Base, engine
from app.routes import router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Enterprise AI Assistant",
    version="1.0.0"
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "title": "Enterprise AI Assistant"
        }
    )


app.include_router(router)