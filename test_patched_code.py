import json
from core.agents.critic_agent import CriticAgent

patched_code = """
import os
import mysql.connector
from mysql.connector import Error

def connect_to_database():
    required_vars = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_SSL_CA"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")
    try:
        connection = mysql.connector.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            ssl_ca=os.environ["DB_SSL_CA"],
            ssl_verify_cert=True
        )
        return connection
    except Error as e:
        raise ConnectionError(f"Database connection failed: {e}")
"""

agent = CriticAgent()
ast_report = {
    "success": True,
    "findings": [],
    "finding_count": 0,
    "code_snippet": patched_code
}
attack_report = {"success": True, "attack_paths": [], "path_count": 0}
memory_report = {"matched_patterns": []}
rag_report = {}

res = agent.review(ast_report, attack_report, memory_report, rag_report)
print(json.dumps(res, indent=2))
