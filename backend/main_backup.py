
from pathlib import Path
from datetime import datetime, timezone

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="SkyRisk Auditor API",
    description="Academic flight-risk decision-support prototype",
    version="0.2.0",
)

# Load the trained model once when the API starts
MODEL_DIR = Path(__file__).parent / "model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()


class NotamRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


@app.get("/")
def home():
    return {
        "project": "SkyRisk Auditor",
        "status": "running",
        "message": "NOTAM classification model connected."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "notam_model_loaded": True,
        "number_of_categories": model.config.num_labels
    }


@app.post("/api/notam/prepare")
def prepare_notam(request: NotamRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="NOTAM text cannot be empty."
        )

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = torch.softmax(outputs.logits, dim=-1)[0]

    predicted_id = int(torch.argmax(probabilities).item())
    category = model.config.id2label[predicted_id]
    confidence = float(probabilities[predicted_id].item())

    return {
        "status": "success",
        "text": text,
        "predicted_category": category,
        "confidence": round(confidence, 4),
        "confidence_percent": round(confidence * 100, 2),
        "model": "Fine-tuned DistilBERT",
        "classification_note": (
            "Model confidence is not a measure of aviation safety "
            "or NOTAM operational validity."
        )
    }
