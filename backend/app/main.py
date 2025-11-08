"""FastAPI app entrypoint for TeamSero backend (AI interviewer).

This file wires routes together. Run via: uvicorn backend.app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .routes import candidates, interviews, jobs


def create_app() -> FastAPI:
    app = FastAPI(title="TeamSero AI Interviewer")
    # mount a static directory for serving generated audio/video assets in dev
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")
    app.include_router(candidates.router)
    app.include_router(interviews.router)
    app.include_router(jobs.router)

    @app.get("/health")
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
