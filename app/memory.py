from collections import defaultdict


conversation_memory = defaultdict(list)

MAX_MEMORY_MESSAGES = 10


def add_message(user_id: str, role: str, content: str):
    """
    Add a user/assistant message to conversation memory.
    Keeps only the most recent messages.
    """

    conversation_memory[user_id].append({
        "role": role,
        "content": str(content)
    })

    if len(conversation_memory[user_id]) > MAX_MEMORY_MESSAGES:
        conversation_memory[user_id] = conversation_memory[user_id][-MAX_MEMORY_MESSAGES:]


def get_memory(user_id: str):
    """
    Get recent conversation history.
    """

    return conversation_memory.get(user_id, [])


def clear_memory(user_id: str):
    """
    Clear conversation memory for a user.
    """

    conversation_memory.pop(user_id, None)


def get_last_question(user_id: str):
    """
    Get the last user question.
    """

    history = conversation_memory.get(user_id, [])

    for item in reversed(history):
        if item.get("role") == "user":
            return item.get("content")

    return None