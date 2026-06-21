import re
from core.tools.ast_analyzer import analyze_python_ast

code = """
def connect_to_database():
    db_host = "production.db.azure.com"
    db_user = "admin"
    db_pass = "SuperSecretPassword123!"
    
    connection = db.connect(host=db_host, user=db_user, password=db_pass)
    return connection
"""

res = analyze_python_ast(code)
print(res)
