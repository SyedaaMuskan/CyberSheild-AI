from core.agents.orchestrator import SecurityOrchestrator
orchestrator = SecurityOrchestrator()
res = orchestrator.analyze("query = 'SELECT * FROM users WHERE username = ' + user_input")
print('RAG:', res.get('rag_report'))
print('MEM:', res.get('memory_report'))
