from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from core.orchestrator import SecurityOrchestrator
import os

app = FastAPI(title="CyberShield AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = SecurityOrchestrator()

class AnalyzeRequest(BaseModel):
    code: str

@app.get("/")
def read_root():
    return {"status": "success", "message": "🛡️ CyberShield AI Backend is Online and Ready!"}


@app.post("/api/analyze")
def analyze_code(req: AnalyzeRequest):
    result = orchestrator.analyze(req.code)
    # The pdf_report path might not be servable directly unless we set up StaticFiles, 
    # but we will just pass the path for now or return it as part of the JSON payload.
    return result

@app.get("/api/download/pdf")
def download_pdf():
    pdf_path = "security_report.pdf"
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename="CyberShield AI_Security_Report.pdf")
    return HTTPException(status_code=404, detail="PDF report not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
