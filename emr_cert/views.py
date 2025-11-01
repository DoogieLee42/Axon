from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse


def _resolve_frontend_index() -> Path | None:
    """
    Return the path to the built React index.html if it exists.
    """
    dist_root = getattr(settings, "FRONTEND_DIST", None)
    if not dist_root:
        return None
    index_path = Path(dist_root) / "index.html"
    if index_path.exists():
        return index_path
    return None


def frontend_app(_request):
    """
    Serve the compiled React SPA entrypoint. When the frontend build has not
    been generated yet guide the developer instead of failing silently.
    """
    index_file = _resolve_frontend_index()
    if not index_file:
        return HttpResponse(
            "React build not found. Run 'npm run build' inside the frontend/ directory.",
            status=503,
        )
    return FileResponse(open(index_file, "rb"), content_type="text/html")
