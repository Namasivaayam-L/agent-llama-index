import os
from dotenv import load_dotenv
load_dotenv(os.path.join('./config/','.env'))

# from llama_index.llms.gemini import Gemini
from llama_index.llms.groq import Groq


models = {
    # "gemini-1.5-flash-001":Gemini(os.getenv('GOOGLE_API_KEY'), model='models/gemini-1.5-flash-001'),
    # "gemini-1.5-flash-002":Gemini(os.getenv('GOOGLE_API_KEY'), model='models/gemini-1.5-flash-002'),
    "llama-3.3-70b-versatile":Groq('llama-3.3-70b-versatile'),
    "llama-3.1-8b-instant":Groq('llama-3.1-8b-instant'),
    "llama-3.3-70b-specdec":Groq('llama-3.3-70b-specdec'),
    "mixtral-8x7b-32768":Groq('mixtral-8x7b-32768'),
    # "BAAI/bge-small-en-v1.5":HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5"),
}