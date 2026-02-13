"""
Fridge to Recipe - AI-Powered Recipe Suggestions
Upload a photo of your ingredients and get personalized recipe suggestions!
"""

import streamlit as st
import anthropic
import base64
from datetime import datetime
from supabase import create_client, Client
import os
from streamlit_camera_input_live import camera_input


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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .ingredient-tag {
        display: inline-block;
        background-color: #4ECDC4;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .recipe-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
    }
    .stButton > button {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
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
    """Use Claude to identify ingredients from an image."""
    
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


def suggest_recipes(client, ingredients: str, dietary_preferences: list = None, cuisine_preference: str = None) -> str:
    """Use Claude to suggest recipes based on identified ingredients."""
    
    preferences_text = ""
    if dietary_preferences:
        preferences_text += f"\nDietary requirements: {', '.join(dietary_preferences)}"
    if cuisine_preference and cuisine_preference != "Any":
        preferences_text += f"\nPreferred cuisine: {cuisine_preference}"
    
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
    st.markdown("<p style='text-align: center; color: #666;'>Upload a photo of your ingredients and discover delicious recipes!</p>", unsafe_allow_html=True)
    
    # Initialize clients
    anthropic_client = init_anthropic()
    supabase_client = init_supabase()
    
    # Check for API key
    if not anthropic_client:
        st.error("⚠️ Anthropic API key not found. Please set ANTHROPIC_API_KEY in your .env file.")
        st.info("Get your API key from: https://console.anthropic.com/")
        return
    
    # Sidebar for preferences
    with st.sidebar:
        st.header("⚙️ Preferences")
        
        dietary_preferences = st.multiselect(
            "Dietary Requirements",
            ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Low-Carb", "Nut-Free"],
            default=[]
        )
        
        cuisine_preference = st.selectbox(
            "Preferred Cuisine",
            ["Any", "Italian", "Asian", "Mexican", "Indian", "Mediterranean", "American", "French"]
        )
        
        st.divider()
        
        # History section (if Supabase is configured)
        if supabase_client:
            st.header("📜 Recent Searches")
            if st.button("Load History"):
                history = load_search_history(supabase_client)
                if history:
                    for item in history[:5]:
                        with st.expander(f"🕐 {item['created_at'][:10]}"):
                            st.write("**Ingredients:**")
                            st.write(item['ingredients_detected'][:200] + "...")
                else:
                    st.info("No search history yet!")
        else:
            st.info("💡 Configure Supabase to save your search history!")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📸 Upload or Take a Photo")
        
        uploaded_file = st.file_uploader(
            "Upload a photo of your fridge, pantry, or ingredients",
            type=["jpg", "jpeg", "png", "webp"],
            help="Supported formats: JPG, PNG, WebP"
        )
        
        st.markdown("<div style='text-align:center;'>or</div>", unsafe_allow_html=True)
        
        camera_image = camera_input("Take a picture with your camera")
        
        image_source = uploaded_file or camera_image
        
        if image_source:
            st.image(image_source, caption="Your ingredients", use_container_width=True)
            # Process button
            if st.button("🔍 Identify Ingredients & Get Recipes", type="primary", use_container_width=True):
                with st.spinner("🔍 Analyzing your ingredients..."):
                    image_data = encode_image(image_source)
                    media_type = get_image_media_type(image_source)
                    ingredients_result = identify_ingredients(anthropic_client, image_data, media_type)
                    st.session_state['ingredients'] = ingredients_result['raw_response']
                with st.spinner("👨‍🍳 Generating recipe suggestions..."):
                    recipes = suggest_recipes(
                        anthropic_client,
                        st.session_state['ingredients'],
                        dietary_preferences,
                        cuisine_preference
                    )
                    st.session_state['recipes'] = recipes
                if supabase_client:
                    save_to_supabase(
                        supabase_client,
                        st.session_state['ingredients'],
                        st.session_state['recipes']
                    )
                st.success("✅ Analysis complete!")
    
    with col2:
        st.header("🥗 Detected Ingredients")
        
        if 'ingredients' in st.session_state:
            st.markdown(st.session_state['ingredients'])
        else:
            st.info("Upload an image and click 'Identify Ingredients' to see results here.")
    
    # Recipe suggestions section
    st.divider()
    st.header("👨‍🍳 Recipe Suggestions")
    
    if 'recipes' in st.session_state:
        st.markdown(st.session_state['recipes'])
        
        # Download button for recipes
        st.download_button(
            label="📥 Download Recipes",
            data=st.session_state['recipes'],
            file_name="my_recipes.txt",
            mime="text/plain"
        )
    else:
        st.info("Your personalized recipe suggestions will appear here after analysis.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 1rem;'>
        <p>Made with ❤️ using Streamlit, Claude AI, and Supabase</p>
        <p style='font-size: 0.8rem;'>Tip: For best results, ensure good lighting and clearly visible ingredients!</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
