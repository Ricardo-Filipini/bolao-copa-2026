from fastapi import FastAPI

app = FastAPI(
    title="Bolão Copa 2026",
    description="API do Bolão da Copa do Mundo 2026 - Confraria do Café",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint para validação do serviço."""
    return {"status": "ok"}
