import os
from dotenv import load_dotenv
load_dotenv()

from core.agents.critic_agent import CriticAgent
from core.agents.advanced_auto_patch_agent import AdvancedAutoPatchAgent

def main():
    print('Testing Auto Patch Agent...')
    patcher = AdvancedAutoPatchAgent()
    code = """
def login(username, password):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
"""
    res = patcher.fix_file(code)
    print("PATCH RESULT:")
    print(res)

    print('\nTesting Critic Agent...')
    critic = CriticAgent()
    rev = critic.review({'findings': [{'severity': 'CRITICAL'}]}, {}, {})
    print("CRITIC RESULT:")
    print(rev)

if __name__ == "__main__":
    main()
