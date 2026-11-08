import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from fpdf import FPDF

# --- 1. Define the Structured Outputs with Pydantic ---
class CinematicPrompt(BaseModel):
    camera_setup: str = Field(description="Specific camera lens (e.g., 50mm, 85mm), focal length, and movement.")
    lighting: str = Field(description="Technical lighting setup (e.g., volumetric, three-point, tungsten, soft bokeh).")
    scene_description: str = Field(description="Detailed physical description of the scene and subject.")
    veo_prompt: str = Field(description="The complete, concatenated text prompt optimized for a video generation AI like Veo 3.1.")

class CanvaAIPrompts(BaseModel):
    magic_design_prompt: str = Field(description="A prompt for Canva Magic Design to generate a layout. (e.g., 'A cinematic YouTube thumbnail for a cyberpunk noodle stand, bold neon text, dark background')")
    magic_media_prompt: str = Field(description="A prompt for Canva Magic Media (Text-to-Image) to generate a static background asset. Focus heavily on art style, lighting, and colors.")

# --- 2. Helper Function: PDF Generator ---
def create_pdf(preview_text, camera, lighting, veo_prompt, audio_prompt, canva_design, canva_media):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "AI Cinematic Director - Production Breakdown", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "Visual Preview:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, preview_text)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "Camera Setup:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, camera)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "Lighting:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, lighting)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "Final Veo 3.1 Video Prompt:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, veo_prompt)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "Audio & Music Prompt (Suno/MusicFX):", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, audio_prompt)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "Canva Magic Design Prompt:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, canva_design)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "Canva Magic Media Prompt:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, canva_media)
    
    return pdf.output()

# --- 3. App Configuration & Memory Init ---
st.set_page_config(page_title="AI Cinematic Director", page_icon="🎬", layout="wide")

if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemini-3.5-flash-lite"
if "user_concept" not in st.session_state:
    st.session_state.user_concept = None
if "translated_prompt" not in st.session_state:
    st.session_state.translated_prompt = None
if "preview_explanation" not in st.session_state:
    st.session_state.preview_explanation = None
if "audio_prompt" not in st.session_state:
    st.session_state.audio_prompt = None
if "canva_prompts" not in st.session_state:
    st.session_state.canva_prompts = None

# --- 4. The Robust Sidebar Gatekeeper (Provider & Model Selection) ---
with st.sidebar:
    st.header("⚙️ System Config")
    
    provider = st.selectbox(
        "Select AI Provider", 
        ["Gemini", "ChatGPT", "Claude"]
    )
    
    if provider != "Gemini":
        st.info(f"{provider} integration is coming soon! Please select Gemini to continue.")
        st.session_state.api_key_valid = False
    else:
        selected_model = st.selectbox(
            "Select Model", 
            ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"]
        )
        
        api_input = st.text_input(
            "Gemini API Key", 
            type="password", 
            placeholder="Paste your API key here...",
            value=st.session_state.api_key
        )
        
        if api_input.strip():
            st.session_state.api_key = api_input.strip()
            st.session_state.api_key_valid = True
            st.session_state.selected_model = selected_model
            st.success("✅ API Key provided")
        else:
            st.session_state.api_key_valid = False
            st.info("Awaiting API Key...")
            st.markdown("[Get a free Google API key here](https://aistudio.google.com/app/apikey)")
            
    st.divider()
    
    if st.button("🔄 Reset Workflow", use_container_width=True):
        st.session_state.user_concept = None
        st.session_state.translated_prompt = None
        st.session_state.preview_explanation = None
        st.session_state.audio_prompt = None
        st.session_state.canva_prompts = None
        st.rerun()

# --- 5. Lock the App ---
st.title("🎬 AI Cinematic Director")
if not st.session_state.api_key_valid:
    st.warning("👈 Please select a provider and authenticate in the sidebar to access the Director.")
    st.stop()

# --- 6. The Elicitation Agent UI ---
with st.form("elicitation_form"):
    st.subheader("Describe your vision")
    st.write("Type any concept, scene, or feeling. The more details you provide, the better the camera science will be.")
    
    user_concept = st.text_area(
        "Raw Idea:", 
        placeholder="e.g., A cyberpunk street vendor cooking noodles in the neon rain, feeling isolated and gritty...",
        height=100,
        label_visibility="collapsed"
    )
    
    submitted = st.form_submit_button("Generate Full Production Suite")

# --- 7. The Core Agents Pipeline ---
if submitted:
    if not user_concept.strip():
        st.warning("Please describe a vision before submitting.")
        st.stop()
        
    st.session_state.user_concept = user_concept
    
    with st.spinner(f"Multi-Agent Squad is designing your production using {st.session_state.selected_model}..."):
        try:
            client = genai.Client(api_key=st.session_state.api_key)
            MODEL = st.session_state.selected_model
            
            # Agent 1: Translation Agent (Visuals)
            agent_prompt = f"""
            You are an expert cinematographer and AI video generation prompt engineer.
            Translate the user's raw, unstructured concept into a highly technical, 
            cinematic video prompt optimized for a model like Veo 3.1.
            User's Raw Concept: {st.session_state.user_concept}
            """
            response = client.models.generate_content(
                model=MODEL,
                contents=agent_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CinematicPrompt,
                    temperature=0.7,
                ),
            )
            st.session_state.translated_prompt = response.parsed
            
            # Agent 2: Preview Agent (Layman Summary)
            preview_prompt = f"""
            You are a friendly film director explaining a shot to a client.
            Take this highly technical cinematic prompt and explain what the final video 
            will actually look like on screen in one vivid, simple paragraph. 
            Do not use camera jargon. Focus on the visual emotion.
            Technical Prompt: {st.session_state.translated_prompt.veo_prompt}
            """
            preview_response = client.models.generate_content(
                model=MODEL,
                contents=preview_prompt,
            )
            st.session_state.preview_explanation = preview_response.text
            
            # Agent 3: Audio Director (Music/Foley)
            audio_agent_prompt = f"""
            You are an expert film composer and sound designer.
            Read this visual scene description, then write a highly specific music generation 
            prompt for an AI tool like Suno or MusicFX. 
            Include the musical genre, specific instruments, tempo, mood, and any atmospheric Foley/sound effects.
            Visual Scene: {st.session_state.translated_prompt.veo_prompt}
            User's Core Emotion: {st.session_state.user_concept}
            """
            audio_response = client.models.generate_content(
                model=MODEL,
                contents=audio_agent_prompt,
            )
            st.session_state.audio_prompt = audio_response.text
            
            # Agent 4: Canva AI Prompt Agent (Post-Production)
            canva_agent_prompt = f"""
            You are an expert graphic designer using Canva's generative AI tools.
            Based on the user's concept and visual scene, write two highly optimized text prompts.
            1. 'magic_design_prompt': For generating a full template layout (poster/thumbnail). Mention the layout intent, text style, and vibe.
            2. 'magic_media_prompt': For generating a high-quality static image asset. Focus strictly on visual aesthetics, art style, and lighting.
            User's Concept: {st.session_state.user_concept}
            Visual Scene: {st.session_state.translated_prompt.veo_prompt}
            """
            canva_response = client.models.generate_content(
                model=MODEL,
                contents=canva_agent_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CanvaAIPrompts,
                    temperature=0.7,
                ),
            )
            st.session_state.canva_prompts = canva_response.parsed
            
        except Exception as e:
            st.error(f"API Error: {e}")

# --- 8. Display & Download Results ---
if st.session_state.translated_prompt:
    st.divider()
    
    st.subheader("👀 Visual Preview")
    st.info(st.session_state.preview_explanation)
    
    st.divider()
    
    st.subheader("🎥 1. Video Generation (Veo 3.1 / Sora)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Camera Setup**")
        st.code(st.session_state.translated_prompt.camera_setup, language="text")
    with col2:
        st.markdown("**Lighting**")
        st.code(st.session_state.translated_prompt.lighting, language="text")
        
    st.markdown("**Final Video Prompt**")
    st.code(st.session_state.translated_prompt.veo_prompt, language="text")
    
    st.divider()
    
    st.subheader("🎵 2. Audio Generation (Suno / MusicFX)")
    st.code(st.session_state.audio_prompt, language="text")
    
    st.divider()
    
    st.subheader("🎨 3. Canva Post-Production (Magic Studio)")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**🪄 Magic Design Prompt**")
        st.code(st.session_state.canva_prompts.magic_design_prompt, language="text")
    with col4:
        st.markdown("**🖼️ Magic Media Prompt**")
        st.code(st.session_state.canva_prompts.magic_media_prompt, language="text")
    
    st.divider()
    
    pdf_bytes = create_pdf(
        st.session_state.preview_explanation,
        st.session_state.translated_prompt.camera_setup,
        st.session_state.translated_prompt.lighting,
        st.session_state.translated_prompt.veo_prompt,
        st.session_state.audio_prompt,
        st.session_state.canva_prompts.magic_design_prompt,
        st.session_state.canva_prompts.magic_media_prompt
    )
    
    st.download_button(
        label="📥 Download Full Production Breakdown (PDF)",
        data=pdf_bytes,
        file_name="ai_production_breakdown.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )