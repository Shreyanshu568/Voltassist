# VoltAssist — AI-Powered Customer Support Chatbot

VoltAssist is an AI chatbot that answers customer queries about electricity bills, 
tariffs, solar connections, and service processes using Retrieval-Augmented Generation 
(RAG). It was built as an independent case study using a real Indian power utility 
company's publicly available information, to demonstrate an end-to-end GenAI application.

> **Disclaimer:** This is an independent, unofficial project built for educational and 
> portfolio purposes using publicly available information. It is not affiliated with, 
> endorsed by, or officially connected to any power utility company.

## Features
- Retrieval-Augmented Generation (RAG) pipeline using ChromaDB vector search and Groq's LLM API
- Real-time streaming responses (word-by-word, ChatGPT-style)
- Multi-turn conversation memory with sliding-window context for natural follow-ups
- Dynamic response formatting — flowing paragraphs vs. numbered steps based on question type
- Configurable response length (brief / default / detailed) via prompt engineering
- Fully responsive UI — split desktop layout, mobile-first chat experience
- Dark/light theme toggle with persistence

## Tech Stack
**Backend:** Python, FastAPI, ChromaDB, Groq API  
**Frontend:** HTML, CSS, JavaScript  
**Concepts:** RAG, Vector Embeddings, Prompt Engineering, REST APIs, Streaming Responses

## Project Structure
voltassist/
├── data/ # Knowledge base (Q&A text files)
├── frontend/ # UI (HTML, CSS, JS)
├── ingest.py # Loads data into ChromaDB
├── main.py # FastAPI backend + RAG logic
└── requirements.txt

## Author
Built by Shreyanshu Mishra as a personal project to explore GenAI and RAG systems.
