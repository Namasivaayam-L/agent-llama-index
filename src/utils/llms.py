import os
from dotenv import load_dotenv
load_dotenv(os.path.join('./config/','.env'))

from llama_index.llms.groq import Groq
from llama_index.llms.azure_openai import AzureOpenAI

api_key = "<api-key>"
azure_endpoint = "https://<your-resource-name>.openai.azure.com/"
api_version = "2023-07-01-preview"

llm = AzureOpenAI(
    model="gpt-4o-mini",
    deployment_name="gpt-4o-mini",
    azure_endpoint="https://rishu-m5xq6fjk-eastus2.openai.azure.com/",
    api_key="59bDP9skAdEAkK6mxHESimmW75H2aKrjRr5YEUdBmGPedEyQJhRlJQQJ99BAACHYHv6XJ3w3AAAAACOGLvm7",
    api_version="2024-05-01-preview",
)



models = {
    # "gemini-1.5-flash-001":Gemini(os.getenv('GOOGLE_API_KEY'), model='models/gemini-1.5-flash-001'),
    # "gemini-1.5-flash-002":Gemini(os.getenv('GOOGLE_API_KEY'), model='models/gemini-1.5-flash-002'),
    "gpt-4o-mini": llm,
    "llama-3.3-70b-versatile":Groq('llama-3.3-70b-versatile'),
    "llama-3.1-8b-instant":Groq('llama-3.1-8b-instant'),
    "llama-3.3-70b-specdec":Groq('llama-3.3-70b-specdec'),
    "mixtral-8x7b-32768":Groq('mixtral-8x7b-32768'),
    # "BAAI/bge-small-en-v1.5":HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5"),
}