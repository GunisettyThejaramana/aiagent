from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import Base, engine
from app.routes import router
from app.indexing.document_index import DocumentIndex


# ----------------------------------------------------
# Create Database Tables
# ----------------------------------------------------
Base.metadata.create_all(bind=engine)


# ----------------------------------------------------
# Build Local Document Index
# ----------------------------------------------------
document_index = DocumentIndex()

try:
    documents = document_index.build()
    print("=" * 60)
    print("Enterprise AI Assistant")
    print("Local Document Index Ready")
    print(f"Indexed Documents : {len(documents)}")
    print("=" * 60)

except Exception as e:
    print("=" * 60)
    print("Document Index Error")
    print(str(e))
    print("=" * 60)


# ----------------------------------------------------
# FastAPI App
# ----------------------------------------------------
app = FastAPI(
    title="Enterprise AI Assistant",
    version="1.0.0"
)


# ----------------------------------------------------
# Static Files
# ----------------------------------------------------
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# ----------------------------------------------------
# Templates
# ----------------------------------------------------
templates = Jinja2Templates(
    directory="templates"
)


# ----------------------------------------------------
# Home Page
# ----------------------------------------------------
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


# ----------------------------------------------------
# API Routes
# ----------------------------------------------------
app.include_router(router)