import os
from dotenv import load_dotenv
load_dotenv()
from core.agents.memory_agent import MemoryAgent
from core.agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent

print("Testing MemoryAgent init...")
mem = MemoryAgent()
print("MemoryAgent initialized.", mem.container)

print("Testing KnowledgeRetrievalAgent init...")
rag = KnowledgeRetrievalAgent()
print("KnowledgeRetrievalAgent initialized.", rag.client)

print("Testing Memory search...")
try:
    res = mem.search("code", {"findings": [{"category": "SQL Injection", "issue": "SQLi"}]})
    print("Memory search result:", res)
except Exception as e:
    print("Memory Error:", e)

print("Testing RAG retrieve...")
try:
    res = rag.retrieve({"attack_paths": [{"attack_type": "SQL Injection"}]})
    print("RAG retrieve result:", res)
except Exception as e:
    print("RAG Error:", e)

print("Done")
