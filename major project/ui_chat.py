import streamlit as st
from chatbot import HealthcareChatbot

def render_chat_interface(user_email):
    st.markdown('<div class="section-title">💬 AI Heart Health Consultant</div>', unsafe_allow_html=True)
    st.caption("A state-of-the-art NLP interface dynamically bound to your medical charts. Safe, responsive, and private.")
    
    bot = HealthcareChatbot(user_email)
    
    # Check for API Key presence
    if not bot.client:
        st.error("API Gateway offline. Ensure your OpenAI API key is properly stored in `.env`.")
        return

    # Load Memory
    chat_memory = bot.load_chat_history()
    
    # Layout Suggestions Feature
    st.markdown("### Suggested Interactions")
    cols = st.columns(3)
    if cols[0].button("What's my specific heart risk?", use_container_width=True):
        st.session_state.prompt_injection = "What is my specific heart risk and what should I do?"
    if cols[1].button("How do I fix my diet?", use_container_width=True):
        st.session_state.prompt_injection = "Based on my clinical vitals, what foods should I eat or avoid?"
    if cols[2].button("Explain Chest Pain types", use_container_width=True):
        st.session_state.prompt_injection = "Explain the types of chest pain and when I should worry?"

    st.markdown("---")

    # Render Chat Loop
    for msg in chat_memory[-10:]: # Load last 10 messages visually to prevent screen bloating
        role = msg["role"]
        with st.chat_message(role, avatar="🩺" if role == "assistant" else "👤"):
            st.write(msg["content"])
            
    # Process inputs natively
    current_prompt = st.chat_input("Message your AI Consultant...")
    
    # Handle suggested injections
    if "prompt_injection" in st.session_state and st.session_state.prompt_injection:
        current_prompt = st.session_state.prompt_injection
        st.session_state.prompt_injection = None

    if current_prompt:
        # Display instantly
        with st.chat_message("user", avatar="👤"):
            st.write(current_prompt)
            
        # Inference Generation Loop
        with st.spinner("AI evaluating clinical parameters..."):
            reply = bot.generate_response(current_prompt, chat_history_context=chat_memory)
            
        with st.chat_message("assistant", avatar="🩺"):
            st.write(reply)
            
        # UI automatically updates since it's already rendered, a rerun forces sync but native sync works fine.
        st.rerun()
