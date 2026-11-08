import os
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Define the Structured Output with Pydantic
class CinematicPrompt(BaseModel):
    camera_setup: str = Field(description="Specific camera lens (e.g., 50mm, 85mm), focal length, and movement (e.g., slow pan, dolly in).")
    lighting: str = Field(description="Technical lighting setup (e.g., volumetric, three-point, tungsten, soft bokeh).")
    scene_description: str = Field(description="Detailed physical description of the scene and subject.")
    veo_prompt: str = Field(description="The complete, concatenated text prompt optimized for a video generation AI like Veo 3.1.")

# Configure the page
st.set_page_config(page_title="AI Cinematic Director", page_icon="🎬", layout="centered")

# API Key Input in Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("[Get your API key from Google AI Studio](https://aistudio.google.com/app/apikey)")

st.title("🎬 AI Cinematic Director")
st.write("I will help you architect a stunning cinematic video prompt. You bring the vision, I'll handle the camera science.")

# Initialize memory
if "theme" not in st.session_state:
    st.session_state.theme = None
if "mood" not in st.session_state:
    st.session_state.mood = None
if "user_concept" not in st.session_state:
    st.session_state.user_concept = None
if "translated_prompt" not in st.session_state:
    st.session_state.translated_prompt = None
if "preview_explanation" not in st.session_state:
    st.session_state.preview_explanation = None

# The Elicitation Agent's UI
# The Elicitation Agent's UI - Now completely generalized
with st.form("elicitation_form"):
    st.subheader("Describe your vision")
    st.write("Type any concept, scene, or feeling. The more details you provide about the action, the better the camera science will be.")
    
    user_concept = st.text_area(
        "Raw Idea:", 
        placeholder="e.g., A cyberpunk street vendor cooking noodles in the neon rain, feeling isolated and gritty.",
        height=150,
        label_visibility="collapsed"
    )
    
    submitted = st.form_submit_button("Generate Director's Vision")

# The Translation Agent Logic
if submitted:
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
        st.stop()
    if not user_concept.strip():
        st.warning("Please describe a vision before submitting.")
        st.stop()
        
    st.session_state.user_concept = user_concept
    
    with st.spinner("Translation Agent is analyzing cinematography..."):
        try:
            client = genai.Client(api_key=api_key)
            
            # Updated System Prompt to handle generic inputs
            agent_prompt = f"""
            You are an expert cinematographer and AI video generation prompt engineer.
            Take the user's raw, unstructured concept and translate it into a highly technical, 
            cinematic video prompt optimized for a model like Veo 3.1.
            
            If the user's concept is vague, infer the best professional camera, lighting, 
            and motion setups to make the scene look stunning.
            
            User's Raw Concept: {st.session_state.user_concept}
            """
            
            # Call Gemini and enforce the Pydantic schema
            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=agent_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CinematicPrompt,
                    temperature=0.7,
                ),
            )
            
            # The SDK automatically parses the JSON into our Pydantic object
            st.session_state.translated_prompt = response.parsed
            
            # --- NEW: Step 3 - The Preview Agent ---
            with st.spinner("Preview Agent is visualizing the shot for the user..."):
                preview_prompt = f"""
                You are a friendly film director explaining a shot to a client.
                Take this highly technical cinematic prompt and explain what the final video 
                will actually look like on screen in one vivid, simple paragraph. 
                Do not use camera jargon. Focus on the visual emotion and what they will see.
                
                Technical Prompt: {st.session_state.translated_prompt.veo_prompt}
                """
                
                preview_response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=preview_prompt,
                )
                
                st.session_state.preview_explanation = preview_response.text
                
            st.success("Cinematography and preview generated successfully!")
            
        except Exception as e:
            st.error(f"API Error: {e}")

# Display the output if it exists in state
if st.session_state.translated_prompt and st.session_state.preview_explanation:
    st.divider()
    
    # Show the Layman's Preview First
    st.subheader("👀 What your video will look like")
    st.info(st.session_state.preview_explanation)
    
    st.divider()
    
    # Show the Technical Breakdown Second
    st.subheader("Director's Technical Breakdown")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🎥 Camera Setup**")
        st.code(st.session_state.translated_prompt.camera_setup, language="text")
    with col2:
        st.markdown("**💡 Lighting**")
        st.code(st.session_state.translated_prompt.lighting, language="text")
        
    st.markdown("**📝 Final Generative AI Video Prompt (Ready for Veo 3.1)**")
    st.code(st.session_state.translated_prompt.veo_prompt, language="text")