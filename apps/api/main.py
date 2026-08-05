"""FastAPI application with health endpoint."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Experience Learning Layer", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "database": "connected"}


def cli() -> None:
    """CLI entry point."""
    import uvicorn

    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    cli()
