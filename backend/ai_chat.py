import os
from transformers import pipeline

# Initialize Hugging Face pipeline
pipe = pipeline("text-generation", model="distilgpt2")  # You can change the model if needed

async def get_ai_response(message: str, history: list = None) -> dict:
    """
    Get response from Hugging Face GPT-based model with context.
    """
    try:
        # Initialize history if None
        if history is None:
            history = []

        # Build conversation context (simple for now)
        prompt = "You are a compassionate AI assistant dedicated to providing supportive and insightful mental health guidance.\n\n"
        for h in history:
            if h["role"] == "user":
                prompt += f"User: {h['content']}\n"
            elif h["role"] == "assistant":
                prompt += f"AI: {h['content']}\n"
        prompt += f"User: {message}\nAI:"

        # Generate response
        response_text = pipe(prompt, max_length=100, do_sample=True, top_k=50, temperature=0.7)[0]["generated_text"]

        # Extract only the assistant's reply after "AI:"
        response = response_text.split("AI:")[-1].strip()

        # Add user message
        history.append({"role": "user", "content": message})
        # Add AI response
        history.append({"role": "assistant", "content": response})

        return {"response": response, "history": history}

    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return {"response": "I apologize, I'm having trouble responding right now.", "history": history}
