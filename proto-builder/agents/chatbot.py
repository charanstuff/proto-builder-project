# import autogen
# from config.settings import config

# chatbot = autogen.AssistantAgent(
#     "Chatbot",
#     llm_config={
#         "api_key": config.OPENAI_API_KEY,
#         "model": config.OPENAI_MODEL
#         },
#     system_message="""You are a friendly and inquisitive Chatbot Agent responsible for understanding the user’s software idea. Your job is to interact with the user and gather all essential details about their idea.

# Instructions:
# - Ask clarifying questions to uncover the user’s vision, requirements, and any constraints.
# - Provide context and examples when asking questions (e.g., "What problem does your idea solve?" or "Can you describe the core features?").
# - Use delimiters or headers to clearly separate different sections if needed.
# - After gathering input, summarize the key points and ask the user to confirm or clarify further.

# Example Output:
# "I understand you’re exploring a new idea for an app. Could you please explain what main problem this app addresses? For example, is it intended to streamline a process, solve a specific user pain point, or something else? Also, can you list the core features you envision? If you have any sketches or examples, feel free to share!" """
# )
import autogen
from config.settings import config
import openai

# Determine if the model supports system messages.
supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

llm_config = {
    "api_key": config.OPENAI_API_KEY,
    "model": config.OPENAI_MODEL
}

# Use your elaborate system prompt if supported.
if supports_system_message:
    llm_config["system_message"] = """You are a friendly and inquisitive Chatbot Agent responsible for understanding the user’s software idea. Your job is to interact with the user and gather all essential details about their idea.

Instructions:
- Ask clarifying questions to uncover the user’s vision, requirements, and any constraints.
- Provide context and examples when asking questions (e.g., "What problem does your idea solve?" or "Can you describe the core features?").
- Use delimiters or headers to clearly separate different sections if needed.
- After gathering input, summarize the key points and ask the user to confirm or clarify further.

Example Output:
"I understand you’re exploring a new idea for an app. Could you please explain what main problem this app addresses? For example, is it intended to streamline a process, solve a specific user pain point, or something else? Also, can you list the core features you envision? If you have any sketches or examples, feel free to share!" """

chatbot = autogen.AssistantAgent("Chatbot", llm_config=llm_config)

if not supports_system_message:
    # Clear internal system message
    chatbot._oai_system_message = ""
    # Patch generate_reply to call OpenAI’s API directly.
    def patched_generate_reply(messages, sender=None):
        response = openai.ChatCompletion.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            api_key=config.OPENAI_API_KEY
        )
        return {"content": response.choices[0].message["content"]}
    chatbot.generate_reply = patched_generate_reply

def generate_chatbot_response(user_input):
    """Generates a chatbot response. For models without system support, instructions are embedded in the prompt."""
    if not supports_system_message:
        instructions = (
            "You are a friendly and inquisitive Chatbot Agent responsible for understanding the user’s software idea. "
            "Your job is to interact with the user and gather all essential details about their idea. "
            "Ask clarifying questions, provide context, and summarize key points.\n"
        )
        full_prompt = f"{instructions}\nUser's input: {user_input}"
    else:
        full_prompt = user_input

    response = chatbot.generate_reply(messages=[{"role": "user", "content": full_prompt}])
    return response["content"]
