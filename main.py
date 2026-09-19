from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from groq import Groq
import os
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file!")

app = FastAPI(title="VoltAssist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="voltassist_docs")
groq_client = Groq(api_key=GROQ_API_KEY)


class ChatMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class Question(BaseModel):
    query: str
    history: Optional[List[ChatMessage]] = []


SYSTEM_PROMPT = """You are VoltAssist, a friendly and knowledgeable AI assistant for Torrent Power, a leading Indian power utility company. You talk like a genuine, helpful human support agent — not like a search engine reading out documents.

HOW TO HANDLE DIFFERENT KINDS OF MESSAGES:

1. Greetings and small talk (e.g. "hi", "hy", "hello", "how are you", "thanks", "bye"):
   Respond warmly and naturally. If this is the first message in the conversation, briefly introduce yourself as VoltAssist and mention you can help with bills, tariffs, solar, new connections, or complaints. If the conversation has already started, just respond naturally without repeating the introduction.
   NEVER say "I don't have that information" for a greeting or casual message.

2. Real questions about Torrent Power (bills, tariff, solar, new connection, complaints, company info):
   Answer using ONLY the facts provided in the context below. Never invent specific numbers, rates, or policies not present in the context. You MAY use general, well-known knowledge of how electricity billing/utility processes normally work to add helpful explanatory framing (e.g. why slab systems exist, how billing cycles generally work) — but never state specific figures that aren't in the context.
   If the context genuinely does not cover what was asked, say so plainly, but only for real questions — never for greetings.

3. Follow-up messages (e.g. "in detail", "briefly", "what about solar"):
   Use the conversation history to understand what topic the user is continuing.

FORMATTING — CHOOSE BASED ON THE QUESTION TYPE:
- If the question asks HOW something is done, a PROCESS, STEPS, or HOW SOMETHING IS CALCULATED (e.g. "how is my bill calculated", "how do I apply", "what documents are needed", "steps to get a connection"): structure your answer as a numbered list (1. 2. 3. ...), each point on its own line, with a short explanation after each number. End with one summary sentence.
- For all other questions (what is X, tell me about X, explain X, general info): answer in flowing natural paragraphs, broken into a few short paragraphs for readability.
- NEVER use asterisks, underscores, or dash bullets. For lists, use plain numbers followed by a period only.

LENGTH — THIS IS A STRICT REQUIREMENT, NOT A SUGGESTION:
- Default (no length mentioned by the user): your answer MUST be approximately 400-550 words (around 40-50 lines). This is a firm target, not a cap. To reach it: fully explain the core answer, add every relevant related detail from the context, explain what it practically means for the customer, and add general explanatory framing where useful. Do NOT stop after a short paragraph — keep explaining and expanding until you reach this length.
- If the user asks for "short", "brief", or "quick": keep it to roughly 120-150 words (up to ~15 lines).
- If the user asks for "detail", "elaborate", or "more": expand to roughly 650-800 words (up to ~80 lines), covering everything relevant from the context and conversation so far in real depth.
- Always match the requested depth exactly — never pad a short answer, never shorten a detailed one.

CONTEXT (for real Torrent Power questions only — ignore this for greetings/small talk):
{context}
""" 


def build_retrieval_query(current_query: str, history: List[ChatMessage]) -> str:
    """Standalone, clear questions are searched using just themselves — combining
    them with unrelated previous topics dilutes the search. Only short, ambiguous
    follow-ups (like 'in detail' or 'briefly') borrow context from recent turns."""
    word_count = len(current_query.split())

    if word_count > 5:

        return current_query

    recent_user_turns = [m.content for m in history if m.role == "user"][-2:]
    return " ".join(recent_user_turns + [current_query])


@app.get("/")
def home():
    return {"message": "VoltAssist API is running", "status": "healthy"}


@app.post("/ask")
def ask(question: Question):
    if not question.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        history = question.history or []

        retrieval_query = build_retrieval_query(question.query, history)
        results = collection.query(query_texts=[retrieval_query], n_results=8)
        context = "\n".join(results["documents"][0]) if results["documents"] else ""

        messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]

        for turn in history[-8:]: 
            messages.append({"role": turn.role, "content": turn.content})

        messages.append({"role": "user", "content": question.query})

        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.4,
            max_tokens=2500
        )

        answer_text = response.choices[0].message.content
        answer_text = answer_text.replace("**", "").replace("__", "").replace("* ", "").replace("###", "").replace("##", "").replace("# ", "")
        return {"answer": answer_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")

@app.post("/ask/stream")
def ask_stream(question: Question):
    if not question.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    history = question.history or []
    retrieval_query = build_retrieval_query(question.query, history)
    results = collection.query(query_texts=[retrieval_query], n_results=8)
    context = "\n".join(results["documents"][0]) if results["documents"] else ""

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
    for turn in history[-8:]:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": question.query})

    def generate():
        stream = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.4,
            max_tokens=2500,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
             yield delta.replace("**", "").replace("__", "").replace("#", "")
    return StreamingResponse(generate(), media_type="text/plain")  