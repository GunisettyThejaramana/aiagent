"""Fast local Ollama AI helpers."""
from __future__ import annotations
import json, re
from datetime import date, datetime
from decimal import Decimal
from typing import Any
import pandas as pd
from app.ollama_client import ollama_client


def _normalize_fast_text(text: str) -> str:
    text = str(text or "").lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text)


def get_fast_response(question: str, language: str = "en-US") -> str | None:
    q = _normalize_fast_text(question)
    lang = str(language or "en-US").lower()
    hi, ta = lang.startswith("hi") or lang == "hindi", lang.startswith("ta") or lang == "tamil"
    if q in {"hello", "hi", "hey", "hello there", "hi there", "hey there", "good morning", "good afternoon", "good evening", "good night"}:
        if hi: return "नमस्ते! मैं आपकी मदद के लिए तैयार हूँ।"
        if ta: return "வணக்கம்! நான் உங்களுக்கு உதவ தயாராக இருக்கிறேன்."
        return "Hello! How can I help you?"
    if q in {"thanks", "thank you", "thanks a lot", "thank you so much", "thanks so much"}:
        if hi: return "कोई बात नहीं! मैं मदद करने के लिए यहाँ हूँ।"
        if ta: return "பரவாயில்லை! உதவுவதில் மகிழ்ச்சி."
        return "You're welcome! I'm happy to help."
    if q in {"bye", "goodbye", "see you", "see you later"}:
        if hi: return "अलविदा! आपका दिन शुभ हो।"
        if ta: return "விடைபெறுகிறேன்! உங்கள் நாள் இனிதாக அமையட்டும்."
        return "Goodbye! Have a great day."
    if q in {"how are you", "how are you doing", "how r you"}:
        if hi: return "मैं अच्छा हूँ और आपकी मदद के लिए तैयार हूँ।"
        if ta: return "நான் நன்றாக இருக்கிறேன். உங்களுக்கு உதவ தயாராக இருக்கிறேன்."
        return "I'm doing well and ready to help!"
    return None


def safe_value(value: Any):
    if isinstance(value, Decimal): return float(value)
    if isinstance(value, (date, datetime)): return value.isoformat()
    try: json.dumps(value); return value
    except Exception: return str(value)


def _history_messages(history):
    out=[]
    for item in (history or [])[-2:]:
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and item.get("content"):
            content=str(item["content"])
            if len(content)>700: content=content[:700]
            out.append({"role":item["role"],"content":content})
    return out


def ask_general_ai(question: str, history: list | None = None, language: str = "en-US") -> str:
    fast=get_fast_response(question, language)
    if fast is not None: return fast
    messages=[{"role":"system","content":"You are a fast enterprise AI assistant running locally with Ollama. Answer the user's question directly and accurately. Be concise by default. Do not invent company-specific facts. Match the user's language when possible."}]
    messages.extend(_history_messages(history))
    messages.append({"role":"user","content":str(question)[:4000]})
    try:
        return ollama_client.chat(messages, temperature=0.3, num_predict=160, think=False)
    except Exception as exc:
        print("Ollama general AI error:", exc)
        return "I'm unable to reach the local AI model right now. Please make sure Ollama is running."


def ask_database_ai(question: str, records: list[dict], sql: str | None = None, language: str = "en-US", history: list | None = None) -> str:
    if not records: return "I couldn't find any matching records for your question."
    return "\n".join(f"{re.sub(r'_+', ' ', str(k)).capitalize()}: {safe_value(v)}" for r in records[:20] for k,v in r.items())


def ask_document_ai(question: str, context: str, language: str = "en-US", history: list | None = None) -> str:
    if not context: return "I couldn't find relevant information in the available documents."
    context=str(context)[:10000]
    prompt=f"QUESTION:\n{question}\n\nDOCUMENT EVIDENCE:\n{context}\n\nAnswer only from the evidence. Be direct. If the answer is not present, say so. Do not invent facts."
    try:
        return ollama_client.generate("You answer questions using supplied document evidence only. Be concise and accurate.", prompt, temperature=0.1, num_predict=180, think=False)
    except Exception as exc:
        print("Ollama document answer error:", exc)
        return "I found relevant document information, but the local AI model could not generate the final answer."


def ask_combined_ai(question: str, database_records: list[dict], document_context: str, sql: str | None = None, language: str = "en-US", history: list | None = None) -> str:
    db=json.dumps(database_records[:30], ensure_ascii=False, default=str)
    docs=str(document_context or "")[:10000]
    prompt=f"QUESTION:\n{question}\n\nDATABASE RESULTS:\n{db}\n\nDOCUMENT EVIDENCE:\n{docs}\n\nAnswer using only these sources. Give the direct answer first. Do not invent or change numbers."
    try:
        return ollama_client.generate("You combine database results and document evidence. Be concise and use only supplied evidence.", prompt, temperature=0.1, num_predict=192, think=False)
    except Exception as exc:
        print("Ollama combined answer error:", exc)
        if database_records: return ask_database_ai(question, database_records, sql, language)
        return "I found source information, but the local AI model could not generate the combined answer."


def ask_llm(question: str, dataframe: pd.DataFrame, language: str = "en-US"):
    if dataframe is None or dataframe.empty: return "No matching information was found."
    if "Document Content" in dataframe.columns:
        return ask_document_ai(question, "\n\n".join(dataframe["Document Content"].astype(str).head(10).tolist()), language)
    records=[{str(k):safe_value(v) for k,v in row.to_dict().items()} for _,row in dataframe.head(100).iterrows()]
    return ask_database_ai(question, records, language=language)
