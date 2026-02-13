"""
Fridge to Recipe - AI-Powered Recipe Suggestions
Upload a photo of your ingredients and get personalized recipe suggestions!
"""

import streamlit as st
import anthropic
import base64
import time
from datetime import datetime
from supabase import create_client, Client
import os


def get_secret(key: str, default=None):
    """Get secret from Streamlit secrets (cloud) or environment variables (local)."""
    # First try Streamlit secrets (for Streamlit Cloud)
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        pass
    
    # Fall back to environment variables (for local development)
    return os.getenv(key, default)

# Page configuration
st.set_page_config(
    page_title="Fridge to Recipe",
    page_icon="🍳",
    layout="centered",  # Better for mobile
    initial_sidebar_state="collapsed"  # Collapsed by default on mobile
)

# Mobile-friendly CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main-header {
        font-size: clamp(1.8rem, 5vw, 3rem);
        font-weight: bold;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.5rem 0;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: clamp(0.9rem, 2.5vw, 1.1rem);
        padding: 0 1rem;
        margin-bottom: 1rem;
    }
    
    /* Better button styling for touch */
    .stButton > button {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-weight: bold;
        font-size: 1rem;
        min-height: 50px;  /* Easier to tap on mobile */
        width: 100%;
        touch-action: manipulation;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(78, 205, 196, 0.4);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
    }
    
    /* Image/camera input improvements */
    [data-testid="stFileUploader"], 
    [data-testid="stCameraInput"] {
        border: 2px dashed #4ECDC4;
        border-radius: 15px;
        padding: 1rem;
    }
    
    /* Improve readability on small screens */
    .stMarkdown {
        font-size: clamp(0.9rem, 2.5vw, 1rem);
    }
    
    /* Better spacing for mobile */
    .block-container {
        padding: 1rem 1rem 3rem 1rem;
        max-width: 100%;
    }
    
    @media (min-width: 768px) {
        .block-container {
            padding: 2rem 3rem 3rem 3rem;
            max-width: 900px;
        }
    }
    
    /* Expander improvements */
    .streamlit-expanderHeader {
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        min-height: 50px;
    }
    
    /* Success/info messages */
    .stSuccess, .stInfo {
        border-radius: 10px;
    }
    
    /* Hide hamburger menu on mobile for cleaner look */
    #MainMenu {visibility: hidden;}
    
    /* Footer styling */
    .footer {
        text-align: center;
        color: #888;
        padding: 1rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Supabase client
@st.cache_resource
def init_supabase() -> Client:
    """Initialize Supabase client with credentials from secrets."""
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    
    if not url or not key:
        return None
    
    return create_client(url, key)


# Initialize Anthropic client
@st.cache_resource
def init_anthropic():
    """Initialize Anthropic client."""
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def encode_image(uploaded_file) -> str:
    """Encode uploaded image to base64."""
    return base64.standard_b64encode(uploaded_file.getvalue()).decode("utf-8")


def get_image_media_type(uploaded_file) -> str:
    """Get the media type of the uploaded image."""
    file_type = uploaded_file.type
    if file_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        return file_type
    return "image/jpeg"


def identify_ingredients(client, image_data: str, media_type: str) -> dict:
    """Use Claude to identify ingredients from an image with retry logic."""
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": """Analyze this image and identify all visible food ingredients. 
                        
Return your response in this exact format:
INGREDIENTS:
- ingredient 1
- ingredient 2
- ingredient 3
(etc.)

CATEGORIES:
- Proteins: list any proteins
- Vegetables: list any vegetables
- Fruits: list any fruits
- Dairy: list any dairy products
- Grains/Carbs: list any grains or carbs
- Condiments/Sauces: list any condiments or sauces
- Other: list anything else

Be specific about what you see. If you can identify specific varieties (e.g., cherry tomatoes vs regular tomatoes), please do so."""
                            }
                        ],
                    }
                ],
            )
            return {"raw_response": message.content[0].text}
        
        except anthropic.APIStatusError as e:
            # Handle overloaded (529) and rate limit (429) errors
            if e.status_code in [529, 503]:  # Overloaded or service unavailable
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("The AI service is currently busy. Please try again in a few moments.")
            elif e.status_code == 429:  # Rate limit
                raise Exception("Rate limit reached. Please wait a minute before trying again.")
            else:
                raise Exception(f"API error ({e.status_code}): {str(e)}")
        except anthropic.APIConnectionError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception("Could not connect to AI service. Please check your internet connection.")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")


def suggest_recipes(client, ingredients: str, dietary_preferences: list = None, cuisine_preference: str = None) -> str:
    """Use Claude to suggest recipes based on identified ingredients with retry logic."""
    
    preferences_text = ""
    if dietary_preferences:
        preferences_text += f"\nDietary requirements: {', '.join(dietary_preferences)}"
    if cuisine_preference and cuisine_preference != "Any":
        preferences_text += f"\nPreferred cuisine: {cuisine_preference}"
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Based on these available ingredients:

{ingredients}
{preferences_text}

Suggest 3 recipes that can be made primarily with these ingredients. For each recipe, provide:

1. **Recipe Name** (with emoji)
   - Difficulty: Easy/Medium/Hard
   - Time: estimated cooking time
   - Ingredients needed (mark any NOT in the list with ⚠️)
   - Brief cooking instructions (5-7 steps)
   - Pro tip for the dish

Focus on practical, delicious recipes that make good use of the available ingredients. Minimize additional ingredients needed."""
                    }
                ],
            )
            return message.content[0].text
        
        except anthropic.APIStatusError as e:
            if e.status_code in [529, 503]:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("The AI service is currently busy. Please try again in a few moments.")
            elif e.status_code == 429:
                raise Exception("Rate limit reached. Please wait a minute before trying again.")
            else:
                raise Exception(f"API error ({e.status_code}): {str(e)}")
        except anthropic.APIConnectionError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception("Could not connect to AI service. Please check your internet connection.")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")


def save_to_supabase(supabase: Client, ingredients: str, recipes: str):
    """Save the search to Supabase for history."""
    try:
        data = {
            "ingredients_detected": ingredients,
            "recipes_suggested": recipes,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("recipe_searches").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save to database: {e}")
        return False


def load_search_history(supabase: Client, limit: int = 10):
    """Load recent search history from Supabase."""
    try:
        response = supabase.table("recipe_searches")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Failed to load history: {e}")
        return []


def main():
    # Header
    st.markdown('<h1 class="main-header">🍳 Fridge to Recipe</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Snap a photo of your ingredients and discover delicious recipes!</p>', unsafe_allow_html=True)
    
    # Initialize clients
    anthropic_client = init_anthropic()
    supabase_client = init_supabase()
    
    # Check for API key
    if not anthropic_client:
        st.error("⚠️ Anthropic API key not found. Please configure ANTHROPIC_API_KEY in your secrets.")
        st.info("Get your API key from: https://console.anthropic.com/")
        return
    
    # Preferences in expander (mobile-friendly)
    with st.expander("⚙️ Dietary Preferences", expanded=False):
        dietary_preferences = st.multiselect(
            "Dietary Requirements",
            ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Low-Carb", "Nut-Free"],
            default=[],
            label_visibility="collapsed"
        )
        
        cuisine_preference = st.selectbox(
            "Preferred Cuisine",
            ["Any", "Italian", "Asian", "Mexican", "Indian", "Mediterranean", "American", "French"]
        )
    
    # Image input section with tabs for camera/upload
    st.markdown("### 📸 Add Your Ingredients")
    
    tab_camera, tab_upload = st.tabs(["📷 Take Photo", "📁 Upload Image"])
    
    image_source = None
    
    with tab_camera:
        camera_image = st.camera_input(
            "Point at your fridge or ingredients",
            label_visibility="collapsed",
            help="Tap to take a photo"
        )
        if camera_image:
            image_source = camera_image
    
    with tab_upload:
        uploaded_image = st.file_uploader(
            "Choose an image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            help="Supported formats: JPG, PNG, WebP"
        )
        if uploaded_image:
            image_source = uploaded_image
    
    # Process image if available
    if image_source:
        # Show preview
        st.image(image_source, caption="Your ingredients", use_container_width=True)
        
        # Analyze button
        if st.button("🔍 Find Recipes", type="primary", use_container_width=True):
            
            # Progress indicator
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                progress_text.text("🔍 Analyzing your ingredients...")
                progress_bar.progress(25)
                
                # Encode image
                image_data = encode_image(image_source)
                media_type = get_image_media_type(image_source)
                
                # Identify ingredients
                ingredients_result = identify_ingredients(anthropic_client, image_data, media_type)
                st.session_state['ingredients'] = ingredients_result['raw_response']
                
                progress_text.text("👨‍🍳 Creating recipe suggestions...")
                progress_bar.progress(60)
                
                # Get recipe suggestions
                recipes = suggest_recipes(
                    anthropic_client,
                    st.session_state['ingredients'],
                    dietary_preferences,
                    cuisine_preference
                )
                st.session_state['recipes'] = recipes
                
                progress_bar.progress(90)
                
                # Save to Supabase if configured
                if supabase_client:
                    save_to_supabase(
                        supabase_client,
                        st.session_state['ingredients'],
                        st.session_state['recipes']
                    )
                
                progress_bar.progress(100)
                progress_text.text("✅ Done!")
                
                # Clear progress after a moment
                time.sleep(0.5)
                progress_bar.empty()
                progress_text.empty()
                
                st.success("✅ Recipes ready!")
                
            except Exception as e:
                progress_bar.empty()
                progress_text.empty()
                st.error(f"⚠️ {str(e)}")
                st.info("💡 Tip: Wait a few seconds and try again. The AI service may be temporarily busy.")
    
    # Results section
    if 'ingredients' in st.session_state or 'recipes' in st.session_state:
        st.divider()
        
        # Ingredients found
        if 'ingredients' in st.session_state:
            with st.expander("🥗 Detected Ingredients", expanded=False):
                st.markdown(st.session_state['ingredients'])
        
        # Recipe suggestions
        if 'recipes' in st.session_state:
            st.markdown("### 👨‍🍳 Your Recipes")
            st.markdown(st.session_state['recipes'])
            
            # Download button
            st.download_button(
                label="📥 Save Recipes",
                data=st.session_state['recipes'],
                file_name="my_recipes.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Sidebar for history (optional)
    with st.sidebar:
        st.header("📜 History")
        
        if supabase_client:
            if st.button("Load Recent", use_container_width=True):
                history = load_search_history(supabase_client)
                if history:
                    for item in history[:5]:
                        with st.expander(f"🕐 {item['created_at'][:10]}"):
                            st.write(item['ingredients_detected'][:150] + "...")
                else:
                    st.info("No history yet!")
        else:
            st.info("Configure Supabase to save history")
        
        st.divider()
        st.markdown("""
        <div style='font-size: 0.8rem; color: #888;'>
        <strong>Tips:</strong><br>
        • Good lighting helps!<br>
        • Show labels clearly<br>
        • Include all ingredients
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.divider()
    st.markdown("""
    <div class="footer">
        Made with ❤️ using Streamlit & Claude AI<br>
        <small>Tip: Good lighting = better results!</small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()