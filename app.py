"""
Fridge to Recipe - AI-Powered Recipe Suggestions
Upload a photo of your ingredients and get personalized recipe suggestions!
"""

import streamlit as st
import anthropic
import base64
import time
import requests
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


def search_unsplash_photo(query: str) -> dict:
    """Search for a food photo on Unsplash."""
    access_key = get_secret("UNSPLASH_ACCESS_KEY")
    
    if not access_key:
        return None
    
    try:
        # Add "food" to improve results
        search_query = f"{query} food dish"
        
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": search_query,
                "per_page": 1,
                "orientation": "landscape"
            },
            headers={
                "Authorization": f"Client-ID {access_key}"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                photo = data["results"][0]
                return {
                    "url": photo["urls"]["regular"],
                    "thumb": photo["urls"]["small"],
                    "author": photo["user"]["name"],
                    "author_url": photo["user"]["links"]["html"]
                }
    except Exception as e:
        pass
    
    return None


def parse_recipe_names(recipes_text: str) -> list:
    """Extract recipe names from the generated recipes text."""
    recipe_names = []
    lines = recipes_text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Look for lines that start with number and contain ** (markdown bold)
        if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            # Extract the recipe name between ** **
            if '**' in line:
                parts = line.split('**')
                if len(parts) >= 2:
                    name = parts[1].strip()
                    # Remove emoji at the start if present
                    recipe_names.append(name)
            else:
                # Fallback: just take the text after the number
                name = line[2:].strip().lstrip('.*- ')
                if name:
                    recipe_names.append(name)
    
    return recipe_names[:3]  # Max 3 recipes


# Translations
TRANSLATIONS = {
    "en": {
        "title": "🍳 Fridge to Recipe",
        "subtitle": "Snap a photo of your ingredients and discover delicious recipes!",
        "preferences": "⚙️ Dietary Preferences",
        "dietary_requirements": "Dietary Requirements",
        "preferred_cuisine": "Preferred Cuisine",
        "cuisine_any": "Any",
        "add_ingredients": "### 📸 Add Your Ingredients",
        "take_photo": "📷 Take Photo",
        "upload_image": "📁 Upload Image",
        "camera_help": "Point at your fridge or ingredients",
        "upload_help": "Choose an image",
        "your_ingredients": "Your ingredients",
        "photos_count": "📷 {count} photo(s) selected",
        "clear_photos": "🗑️ Clear All",
        "detect_ingredients": "🔍 Detect Ingredients",
        "find_recipes": "🍳 Find Recipes",
        "edit_ingredients": "✏️ Edit Ingredients",
        "edit_ingredients_help": "Remove or add ingredients before searching for recipes",
        "ingredients_detected_title": "### 🥗 Detected Ingredients",
        "validate_ingredients": "✅ Confirm & Find Recipes",
        "redetect": "🔄 Re-detect",
        "new_search": "🔄 New Search",
        "add_ingredient": "Add an ingredient...",
        "add_button": "➕ Add",
        "photo_by": "Photo by",
        "photo_on": "on Unsplash",
        "loading_photo": "Loading photo...",
        "select_recipe": "Click on a recipe to see the photo",
        "analyzing": "🔍 Analyzing your ingredients...",
        "creating_recipes": "👨‍🍳 Creating recipe suggestions...",
        "done": "✅ Done!",
        "recipes_ready": "✅ Recipes ready!",
        "detected_ingredients": "🥗 Detected Ingredients",
        "your_recipes": "### 👨‍🍳 Your Recipes",
        "save_recipes": "📥 Save Recipes",
        "history": "📜 History",
        "load_recent": "Load Recent",
        "no_history": "No history yet!",
        "configure_supabase": "Configure Supabase to save history",
        "tips": "Tips:",
        "tip_lighting": "Good lighting helps!",
        "tip_labels": "Show labels clearly",
        "tip_include": "Include all ingredients",
        "footer": "Made with ❤️ using Streamlit & Claude AI",
        "footer_tip": "Tip: Good lighting = better results!",
        "error_api_key": "⚠️ Anthropic API key not found. Please configure ANTHROPIC_API_KEY in your secrets.",
        "error_api_key_info": "Get your API key from: https://console.anthropic.com/",
        "error_busy": "The AI service is currently busy. Please try again in a few moments.",
        "error_rate_limit": "Rate limit reached. Please wait a minute before trying again.",
        "error_connection": "Could not connect to AI service. Please check your internet connection.",
        "error_tip": "💡 Tip: Wait a few seconds and try again. The AI service may be temporarily busy.",
        "dietary_options": ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Low-Carb", "Nut-Free"],
        "cuisine_options": ["Any", "Italian", "Asian", "Mexican", "Indian", "Mediterranean", "American", "French"],
        "ingredients_prompt": """Analyze this image and identify all visible food ingredients.

Return ONLY a simple list of ingredients, one per line, with a dash before each:
- ingredient 1
- ingredient 2
- ingredient 3

Be specific (e.g., "cherry tomatoes" not just "tomatoes"). Only list actual food items you can clearly see. Do not include categories or headers.""",
        "recipes_prompt": """Based on these available ingredients:

{ingredients}
{preferences}

Suggest 3 recipes that can be made primarily with these ingredients. For each recipe, provide:

1. **Recipe Name** (with emoji)
   - Difficulty: Easy/Medium/Hard
   - Time: estimated cooking time
   - Ingredients needed (mark any NOT in the list with ⚠️)
   - Brief cooking instructions (5-7 steps)
   - Pro tip for the dish

Focus on practical, delicious recipes that make good use of the available ingredients. Minimize additional ingredients needed."""
    },
    "fr": {
        "title": "🍳 Frigo en Recettes",
        "subtitle": "Prenez une photo de vos ingrédients et découvrez de délicieuses recettes !",
        "preferences": "⚙️ Préférences Alimentaires",
        "dietary_requirements": "Régimes Alimentaires",
        "preferred_cuisine": "Cuisine Préférée",
        "cuisine_any": "Toutes",
        "add_ingredients": "### 📸 Ajoutez Vos Ingrédients",
        "take_photo": "📷 Prendre Photo",
        "upload_image": "📁 Importer Image",
        "camera_help": "Visez votre frigo ou vos ingrédients",
        "upload_help": "Choisir une image",
        "your_ingredients": "Vos ingrédients",
        "photos_count": "📷 {count} photo(s) sélectionnée(s)",
        "clear_photos": "🗑️ Tout Effacer",
        "detect_ingredients": "🔍 Détecter les Ingrédients",
        "find_recipes": "🍳 Trouver des Recettes",
        "edit_ingredients": "✏️ Modifier les Ingrédients",
        "edit_ingredients_help": "Supprimez ou ajoutez des ingrédients avant de chercher des recettes",
        "ingredients_detected_title": "### 🥗 Ingrédients Détectés",
        "validate_ingredients": "✅ Confirmer & Trouver des Recettes",
        "redetect": "🔄 Re-détecter",
        "new_search": "🔄 Nouvelle Recherche",
        "add_ingredient": "Ajouter un ingrédient...",
        "add_button": "➕ Ajouter",
        "photo_by": "Photo par",
        "photo_on": "sur Unsplash",
        "loading_photo": "Chargement de la photo...",
        "select_recipe": "Cliquez sur une recette pour voir la photo",
        "analyzing": "🔍 Analyse de vos ingrédients...",
        "creating_recipes": "👨‍🍳 Création des suggestions de recettes...",
        "done": "✅ Terminé !",
        "recipes_ready": "✅ Recettes prêtes !",
        "detected_ingredients": "🥗 Ingrédients Détectés",
        "your_recipes": "### 👨‍🍳 Vos Recettes",
        "save_recipes": "📥 Sauvegarder",
        "history": "📜 Historique",
        "load_recent": "Charger",
        "no_history": "Pas encore d'historique !",
        "configure_supabase": "Configurez Supabase pour sauvegarder l'historique",
        "tips": "Conseils :",
        "tip_lighting": "Un bon éclairage aide !",
        "tip_labels": "Montrez les étiquettes",
        "tip_include": "Incluez tous les ingrédients",
        "footer": "Fait avec ❤️ avec Streamlit & Claude AI",
        "footer_tip": "Conseil : Bon éclairage = meilleurs résultats !",
        "error_api_key": "⚠️ Clé API Anthropic non trouvée. Veuillez configurer ANTHROPIC_API_KEY.",
        "error_api_key_info": "Obtenez votre clé API sur : https://console.anthropic.com/",
        "error_busy": "Le service IA est actuellement occupé. Veuillez réessayer dans quelques instants.",
        "error_rate_limit": "Limite de requêtes atteinte. Veuillez patienter une minute.",
        "error_connection": "Impossible de se connecter au service IA. Vérifiez votre connexion internet.",
        "error_tip": "💡 Conseil : Attendez quelques secondes et réessayez.",
        "dietary_options": ["Végétarien", "Végan", "Sans Gluten", "Sans Lactose", "Keto", "Low-Carb", "Sans Noix"],
        "cuisine_options": ["Toutes", "Italienne", "Asiatique", "Mexicaine", "Indienne", "Méditerranéenne", "Américaine", "Française"],
        "ingredients_prompt": """Analysez cette image et identifiez tous les ingrédients alimentaires visibles.

Retournez UNIQUEMENT une liste simple d'ingrédients, un par ligne, avec un tiret devant chaque :
- ingrédient 1
- ingrédient 2
- ingrédient 3

Soyez précis (ex: "tomates cerises" plutôt que "tomates"). Listez uniquement les aliments que vous pouvez clairement voir. N'incluez pas de catégories ou d'en-têtes.""",
        "recipes_prompt": """Basé sur ces ingrédients disponibles :

{ingredients}
{preferences}

Suggérez 3 recettes réalisables principalement avec ces ingrédients. Pour chaque recette, fournissez :

1. **Nom de la Recette** (avec emoji)
   - Difficulté : Facile/Moyen/Difficile
   - Temps : temps de préparation estimé
   - Ingrédients nécessaires (marquez ceux NON dans la liste avec ⚠️)
   - Instructions de cuisson (5-7 étapes)
   - Astuce du chef

Concentrez-vous sur des recettes pratiques et délicieuses. Minimisez les ingrédients supplémentaires nécessaires."""
    },
    "pl": {
        "title": "🍳 Z Lodówki na Talerz",
        "subtitle": "Zrób zdjęcie swoich składników i odkryj pyszne przepisy!",
        "preferences": "⚙️ Preferencje Dietetyczne",
        "dietary_requirements": "Wymagania Dietetyczne",
        "preferred_cuisine": "Preferowana Kuchnia",
        "cuisine_any": "Dowolna",
        "add_ingredients": "### 📸 Dodaj Swoje Składniki",
        "take_photo": "📷 Zrób Zdjęcie",
        "upload_image": "📁 Wgraj Obraz",
        "camera_help": "Skieruj na lodówkę lub składniki",
        "upload_help": "Wybierz obraz",
        "your_ingredients": "Twoje składniki",
        "photos_count": "📷 Wybrano {count} zdjęć",
        "clear_photos": "🗑️ Wyczyść Wszystko",
        "detect_ingredients": "🔍 Wykryj Składniki",
        "find_recipes": "🍳 Znajdź Przepisy",
        "edit_ingredients": "✏️ Edytuj Składniki",
        "edit_ingredients_help": "Usuń lub dodaj składniki przed wyszukaniem przepisów",
        "ingredients_detected_title": "### 🥗 Wykryte Składniki",
        "validate_ingredients": "✅ Potwierdź i Znajdź Przepisy",
        "redetect": "🔄 Wykryj Ponownie",
        "new_search": "🔄 Nowe Wyszukiwanie",
        "add_ingredient": "Dodaj składnik...",
        "add_button": "➕ Dodaj",
        "photo_by": "Zdjęcie:",
        "photo_on": "na Unsplash",
        "loading_photo": "Ładowanie zdjęcia...",
        "select_recipe": "Kliknij przepis, aby zobaczyć zdjęcie",
        "analyzing": "🔍 Analizowanie składników...",
        "creating_recipes": "👨‍🍳 Tworzenie propozycji przepisów...",
        "done": "✅ Gotowe!",
        "recipes_ready": "✅ Przepisy gotowe!",
        "detected_ingredients": "🥗 Wykryte Składniki",
        "your_recipes": "### 👨‍🍳 Twoje Przepisy",
        "save_recipes": "📥 Zapisz Przepisy",
        "history": "📜 Historia",
        "load_recent": "Załaduj",
        "no_history": "Brak historii!",
        "configure_supabase": "Skonfiguruj Supabase aby zapisywać historię",
        "tips": "Wskazówki:",
        "tip_lighting": "Dobre oświetlenie pomaga!",
        "tip_labels": "Pokaż etykiety wyraźnie",
        "tip_include": "Uwzględnij wszystkie składniki",
        "footer": "Stworzone z ❤️ przy użyciu Streamlit & Claude AI",
        "footer_tip": "Wskazówka: Dobre światło = lepsze wyniki!",
        "error_api_key": "⚠️ Nie znaleziono klucza API Anthropic. Skonfiguruj ANTHROPIC_API_KEY.",
        "error_api_key_info": "Uzyskaj klucz API na: https://console.anthropic.com/",
        "error_busy": "Usługa AI jest obecnie zajęta. Spróbuj ponownie za chwilę.",
        "error_rate_limit": "Osiągnięto limit zapytań. Poczekaj minutę przed ponowną próbą.",
        "error_connection": "Nie można połączyć się z usługą AI. Sprawdź połączenie internetowe.",
        "error_tip": "💡 Wskazówka: Poczekaj kilka sekund i spróbuj ponownie.",
        "dietary_options": ["Wegetariańskie", "Wegańskie", "Bezglutenowe", "Bez Laktozy", "Keto", "Low-Carb", "Bez Orzechów"],
        "cuisine_options": ["Dowolna", "Włoska", "Azjatycka", "Meksykańska", "Indyjska", "Śródziemnomorska", "Amerykańska", "Francuska"],
        "ingredients_prompt": """Przeanalizuj ten obraz i zidentyfikuj wszystkie widoczne składniki spożywcze.

Zwróć TYLKO prostą listę składników, jeden na linię, z myślnikiem przed każdym:
- składnik 1
- składnik 2
- składnik 3

Bądź konkretny (np. "pomidory koktajlowe" zamiast "pomidory"). Wymień tylko produkty spożywcze, które wyraźnie widzisz. Nie dodawaj kategorii ani nagłówków.""",
        "recipes_prompt": """Na podstawie tych dostępnych składników:

{ingredients}
{preferences}

Zaproponuj 3 przepisy, które można przygotować głównie z tych składników. Dla każdego przepisu podaj:

1. **Nazwa Przepisu** (z emoji)
   - Trudność: Łatwy/Średni/Trudny
   - Czas: szacowany czas przygotowania
   - Potrzebne składniki (oznacz te SPOZA listy symbolem ⚠️)
   - Instrukcje gotowania (5-7 kroków)
   - Wskazówka szefa kuchni

Skup się na praktycznych i pysznych przepisach. Minimalizuj dodatkowe składniki."""
    }
}


def get_text(key: str) -> str:
    """Get translated text for current language."""
    lang = st.session_state.get('language', 'en')
    return TRANSLATIONS[lang].get(key, key)

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
    
    /* Language selector flags */
    .stButton > button[kind="secondary"] {
        background: transparent;
        border: 2px solid #e0e0e0;
        font-size: 1.5rem;
        padding: 0.3rem;
        min-height: 40px;
    }
    
    .stButton > button[kind="secondary"]:hover {
        border-color: #4ECDC4;
        transform: scale(1.1);
    }
    
    /* Ingredient delete button */
    div[data-testid="column"]:first-child .stButton > button {
        background: transparent;
        border: none;
        color: #ff4444;
        font-size: 1.2rem;
        padding: 0.2rem;
        min-height: 35px;
        min-width: 35px;
    }
    
    div[data-testid="column"]:first-child .stButton > button:hover {
        background: #ffeeee;
        transform: scale(1.1);
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


def parse_ingredients_to_list(raw_text: str) -> list:
    """Parse the raw ingredients text into a clean list."""
    ingredients = []
    lines = raw_text.split('\n')
    
    # Words/phrases to skip (not actual ingredients)
    skip_phrases = [
        'none visible', 'none', 'n/a', 'aucun', 'aucune', 'pas visible', 
        'non visible', 'brak', 'nie widoczne', 'żaden', 'nothing', 
        'not visible', 'empty', 'vide', 'pusto', '(none)', '(aucun)',
        'none identified', 'aucun identifié', 'nie zidentyfikowano'
    ]
    
    for line in lines:
        line = line.strip()
        # Skip empty lines, headers, and category labels
        if not line:
            continue
        if line.upper().startswith(('INGREDIENTS', 'INGRÉDIENTS', 'SKŁADNIKI', 'CATEGORIES', 'CATÉGORIES', 'KATEGORIE')):
            continue
        if line.endswith(':') and len(line) < 50:
            continue
        
        # Remove list markers
        if line.startswith(('-', '•', '*', '–')):
            line = line[1:].strip()
        
        # Skip lines that look like category headers
        if ':' in line and len(line.split(':')[0]) < 25:
            # This might be "Proteins: chicken, beef" - extract items after colon
            after_colon = line.split(':', 1)[1].strip()
            if after_colon and after_colon.lower() not in skip_phrases:
                # Split by comma if multiple items
                items = [item.strip() for item in after_colon.split(',')]
                for item in items:
                    if item and len(item) > 1 and item.lower() not in skip_phrases:
                        ingredients.append(item)
            continue
        
        # Skip non-ingredient phrases
        if line.lower() in skip_phrases:
            continue
        
        # Add valid ingredient
        if line and len(line) > 1 and not line.startswith(('Photo', '---')):
            ingredients.append(line)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ingredients = []
    for ing in ingredients:
        ing_lower = ing.lower()
        if ing_lower not in seen and ing_lower not in skip_phrases:
            seen.add(ing_lower)
            unique_ingredients.append(ing)
    
    return unique_ingredients


def get_image_media_type(uploaded_file) -> str:
    """Get the media type of the uploaded image."""
    file_type = uploaded_file.type
    if file_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        return file_type
    return "image/jpeg"


def identify_ingredients(client, image_data: str, media_type: str, lang: str = "en") -> dict:
    """Use Claude to identify ingredients from an image with retry logic."""
    
    max_retries = 3
    retry_delay = 2  # seconds
    prompt = TRANSLATIONS[lang]["ingredients_prompt"]
    
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
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
                                "text": prompt
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


def suggest_recipes(client, ingredients: str, dietary_preferences: list = None, cuisine_preference: str = None, lang: str = "en") -> str:
    """Use Claude to suggest recipes based on identified ingredients with retry logic."""
    
    preferences_text = ""
    if dietary_preferences:
        preferences_text += f"\nDietary requirements: {', '.join(dietary_preferences)}"
    if cuisine_preference and cuisine_preference != "Any" and cuisine_preference != "Toutes" and cuisine_preference != "Dowolna":
        preferences_text += f"\nPreferred cuisine: {cuisine_preference}"
    
    max_retries = 3
    retry_delay = 2
    
    prompt_template = TRANSLATIONS[lang]["recipes_prompt"]
    prompt = prompt_template.format(ingredients=ingredients, preferences=preferences_text)
    
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
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
    # Initialize language in session state
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    
    # Language selector with flags at the top
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("🇬🇧", use_container_width=True, help="English"):
            st.session_state.language = 'en'
            st.rerun()
    with col2:
        if st.button("🇫🇷", use_container_width=True, help="Français"):
            st.session_state.language = 'fr'
            st.rerun()
    with col3:
        if st.button("🇵🇱", use_container_width=True, help="Polski"):
            st.session_state.language = 'pl'
            st.rerun()
    
    # Header
    st.markdown(f'<h1 class="main-header">{get_text("title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">{get_text("subtitle")}</p>', unsafe_allow_html=True)
    
    # Initialize clients
    anthropic_client = init_anthropic()
    supabase_client = init_supabase()
    
    # Check for API key
    if not anthropic_client:
        st.error(get_text("error_api_key"))
        st.info(get_text("error_api_key_info"))
        return
    
    # Preferences in expander (mobile-friendly)
    with st.expander(get_text("preferences"), expanded=False):
        dietary_preferences = st.multiselect(
            get_text("dietary_requirements"),
            get_text("dietary_options"),
            default=[],
            label_visibility="collapsed"
        )
        
        cuisine_preference = st.selectbox(
            get_text("preferred_cuisine"),
            get_text("cuisine_options")
        )
    
    # Image input section with tabs for camera/upload
    st.markdown(get_text("add_ingredients"))
    
    tab_camera, tab_upload = st.tabs([get_text("take_photo"), get_text("upload_image")])
    
    # Initialize images list in session state
    if 'images' not in st.session_state:
        st.session_state.images = []
    
    with tab_camera:
        camera_image = st.camera_input(
            get_text("camera_help"),
            label_visibility="collapsed",
            help=get_text("camera_help"),
            key="camera"
        )
        if camera_image:
            # Add to images list if not already there
            if camera_image not in st.session_state.images:
                st.session_state.images.append(camera_image)
    
    with tab_upload:
        uploaded_images = st.file_uploader(
            get_text("upload_help"),
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            help="JPG, PNG, WebP",
            accept_multiple_files=True
        )
        if uploaded_images:
            for img in uploaded_images:
                if img not in st.session_state.images:
                    st.session_state.images.append(img)
    
    # Display all collected images
    if st.session_state.images:
        st.markdown(f"**{get_text('photos_count').format(count=len(st.session_state.images))}**")
        
        # Show images in a grid
        cols = st.columns(min(len(st.session_state.images), 3))
        for idx, img in enumerate(st.session_state.images):
            with cols[idx % 3]:
                st.image(img, use_container_width=True)
        
        # Clear images button and detect button
        col_clear, col_detect = st.columns(2)
        with col_clear:
            if st.button(get_text("clear_photos"), use_container_width=True):
                st.session_state.images = []
                st.session_state.pop('detected_ingredients', None)
                st.session_state.pop('ingredients_list', None)
                st.session_state.pop('ingredients', None)
                st.session_state.pop('recipes', None)
                st.rerun()
        
        with col_detect:
            detect_clicked = st.button(get_text("detect_ingredients"), type="primary", use_container_width=True)
        
        # Step 1: Detect ingredients
        if detect_clicked:
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                lang = st.session_state.language
                all_ingredients = []
                total_images = len(st.session_state.images)
                
                # Analyze each image
                for idx, img in enumerate(st.session_state.images):
                    progress_text.text(f"{get_text('analyzing')} ({idx + 1}/{total_images})")
                    progress_bar.progress(int((idx + 1) / total_images * 100))
                    
                    # Encode image
                    image_data = encode_image(img)
                    media_type = get_image_media_type(img)
                    
                    # Identify ingredients
                    ingredients_result = identify_ingredients(anthropic_client, image_data, media_type, lang)
                    all_ingredients.append(ingredients_result['raw_response'])
                
                # Combine all ingredients
                combined_ingredients = "\n\n".join(all_ingredients)
                st.session_state['detected_ingredients'] = combined_ingredients
                
                progress_bar.progress(100)
                progress_text.text(get_text("done"))
                time.sleep(0.5)
                progress_bar.empty()
                progress_text.empty()
                st.rerun()
                
            except Exception as e:
                progress_bar.empty()
                progress_text.empty()
                st.error(f"⚠️ {str(e)}")
                st.info(get_text("error_tip"))
    
    # Step 2: Show editable ingredients
    if 'detected_ingredients' in st.session_state and 'recipes' not in st.session_state:
        st.divider()
        st.markdown(get_text("ingredients_detected_title"))
        st.caption(get_text("edit_ingredients_help"))
        
        # Parse ingredients into list if not already done
        if 'ingredients_list' not in st.session_state:
            st.session_state['ingredients_list'] = parse_ingredients_to_list(st.session_state['detected_ingredients'])
        
        # Display ingredients with delete buttons
        ingredients_to_remove = []
        
        for idx, ingredient in enumerate(st.session_state['ingredients_list']):
            col_del, col_ing = st.columns([1, 9])
            with col_del:
                if st.button("❌", key=f"del_{idx}", help=f"Remove {ingredient}"):
                    ingredients_to_remove.append(idx)
            with col_ing:
                st.markdown(f"<span style='font-size: 1.1rem;'>{ingredient}</span>", unsafe_allow_html=True)
        
        # Remove ingredients marked for deletion
        if ingredients_to_remove:
            st.session_state['ingredients_list'] = [
                ing for idx, ing in enumerate(st.session_state['ingredients_list']) 
                if idx not in ingredients_to_remove
            ]
            st.rerun()
        
        # Add new ingredient
        st.markdown("---")
        col_input, col_add = st.columns([4, 1])
        with col_input:
            new_ingredient = st.text_input(
                get_text("add_ingredient"),
                key="new_ingredient_input",
                label_visibility="collapsed",
                placeholder=get_text("add_ingredient")
            )
        with col_add:
            if st.button(get_text("add_button"), use_container_width=True):
                if new_ingredient and new_ingredient.strip():
                    st.session_state['ingredients_list'].append(new_ingredient.strip())
                    st.rerun()
        
        st.markdown("---")
        
        # Buttons for re-detect and confirm
        col_redetect, col_confirm = st.columns(2)
        
        with col_redetect:
            if st.button(get_text("redetect"), use_container_width=True):
                st.session_state.pop('detected_ingredients', None)
                st.session_state.pop('ingredients_list', None)
                st.rerun()
        
        with col_confirm:
            if st.button(get_text("validate_ingredients"), type="primary", use_container_width=True):
                # Convert list back to text for recipe generation
                final_ingredients = "\n".join([f"- {ing}" for ing in st.session_state['ingredients_list']])
                st.session_state['ingredients'] = final_ingredients
                
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                try:
                    progress_text.text(get_text("creating_recipes"))
                    progress_bar.progress(30)
                    
                    lang = st.session_state.language
                    recipes = suggest_recipes(
                        anthropic_client,
                        final_ingredients,
                        dietary_preferences,
                        cuisine_preference,
                        lang
                    )
                    st.session_state['recipes'] = recipes
                    
                    progress_bar.progress(90)
                    
                    # Save to Supabase if configured
                    if supabase_client:
                        save_to_supabase(
                            supabase_client,
                            final_ingredients,
                            recipes
                        )
                    
                    progress_bar.progress(100)
                    progress_text.text(get_text("done"))
                    time.sleep(0.5)
                    progress_bar.empty()
                    progress_text.empty()
                    
                    st.success(get_text("recipes_ready"))
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.empty()
                    progress_text.empty()
                    st.error(f"⚠️ {str(e)}")
                    st.info(get_text("error_tip"))
    
    # Results section
    if 'recipes' in st.session_state:
        st.divider()
        
        # Ingredients found
        if 'ingredients' in st.session_state:
            with st.expander(get_text("detected_ingredients"), expanded=False):
                st.markdown(st.session_state['ingredients'])
        
        # Recipe suggestions header
        st.markdown(get_text("your_recipes"))
        
        # Parse recipe names for selection
        recipe_names = parse_recipe_names(st.session_state['recipes'])
        
        if recipe_names:
            # Initialize selected recipe in session state
            if 'selected_recipe' not in st.session_state:
                st.session_state['selected_recipe'] = recipe_names[0]
            
            # Recipe selector buttons
            st.caption(get_text("select_recipe"))
            cols = st.columns(len(recipe_names))
            for idx, name in enumerate(recipe_names):
                with cols[idx]:
                    # Highlight selected recipe
                    button_type = "primary" if st.session_state['selected_recipe'] == name else "secondary"
                    if st.button(f"🍽️ {idx + 1}", key=f"recipe_{idx}", use_container_width=True, type=button_type):
                        st.session_state['selected_recipe'] = name
                        st.session_state.pop('current_photo', None)  # Clear cached photo
                        st.rerun()
            
            # Display photo for selected recipe
            selected = st.session_state['selected_recipe']
            
            # Load photo if not cached
            if 'current_photo' not in st.session_state or st.session_state.get('photo_recipe') != selected:
                with st.spinner(get_text("loading_photo")):
                    photo = search_unsplash_photo(selected)
                    st.session_state['current_photo'] = photo
                    st.session_state['photo_recipe'] = selected
            
            # Display photo
            photo = st.session_state.get('current_photo')
            if photo:
                st.image(photo['url'], caption=selected, use_container_width=True)
                st.caption(f"📷 {get_text('photo_by')} [{photo['author']}]({photo['author_url']}) {get_text('photo_on')}")
            
            st.markdown("---")
        
        # Full recipe details
        st.markdown(st.session_state['recipes'])
        
        # Download and New Search buttons
        col_download, col_new = st.columns(2)
        with col_download:
            st.download_button(
                label=get_text("save_recipes"),
                data=st.session_state['recipes'],
                file_name="my_recipes.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_new:
            if st.button(get_text("new_search"), use_container_width=True):
                st.session_state.images = []
                st.session_state.pop('detected_ingredients', None)
                st.session_state.pop('ingredients_list', None)
                st.session_state.pop('ingredients', None)
                st.session_state.pop('recipes', None)
                st.session_state.pop('selected_recipe', None)
                st.session_state.pop('current_photo', None)
                st.session_state.pop('photo_recipe', None)
                st.rerun()
    
    # Sidebar for history (optional)
    with st.sidebar:
        st.header(get_text("history"))
        
        if supabase_client:
            if st.button(get_text("load_recent"), use_container_width=True):
                history = load_search_history(supabase_client)
                if history:
                    for item in history[:5]:
                        with st.expander(f"🕐 {item['created_at'][:10]}"):
                            st.write(item['ingredients_detected'][:150] + "...")
                else:
                    st.info(get_text("no_history"))
        else:
            st.info(get_text("configure_supabase"))
        
        st.divider()
        st.markdown(f"""
        <div style='font-size: 0.8rem; color: #888;'>
        <strong>{get_text("tips")}</strong><br>
        • {get_text("tip_lighting")}<br>
        • {get_text("tip_labels")}<br>
        • {get_text("tip_include")}
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.divider()
    st.markdown(f"""
    <div class="footer">
        {get_text("footer")}<br>
        <small>{get_text("footer_tip")}</small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()