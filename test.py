from fastapi.routing import APIRoute
from app.main import app

print("=" * 80)
print("Registered API Routes")
print("=" * 80)

for route in app.routes:
    if isinstance(route, APIRoute):
        methods = ", ".join(sorted(route.methods))
        print(f"{methods:20} {route.path}")

print("=" * 80)