from collections import defaultdict


conversation_memory = defaultdict(list)


def add_message(user_id: str, role: str, content: str):
    """
    Add a user or assistant message to conversation memory.
    """

    conversation_memory[user_id].append({
        "role": role,
        "content": content
    })


def get_memory(user_id: str):
    """
    Get conversation history for a user.
    """

    return conversation_memory.get(user_id, [])


def clear_memory(user_id: str):
    """
    Clear conversation history for a user.
    """

    if user_id in conversation_memory:
        del conversation_memory[user_id]


def get_last_question(user_id: str):
    """
    Get the last user question.
    """

    history = conversation_memory.get(user_id, [])

    for item in reversed(history):
        if item["role"] == "user":
            return item["content"]

    return None