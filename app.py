"""
Fridge to Recipe - AI-Powered Recipe Suggestions
Upload a photo of your ingredients and get personalized recipe suggestions!
"""

import streamlit as st
import anthropic
import openai
import base64
import time
import json
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


def get_ingredient_emoji(ingredient: str) -> str:
    """Get an emoji for an ingredient."""
    ingredient_lower = ingredient.lower()
    
    # Emoji mappings by category
    emoji_map = {
        # Proteins
        'chicken': '🍗', 'poulet': '🍗', 'kurczak': '🍗',
        'beef': '🥩', 'boeuf': '🥩', 'bœuf': '🥩', 'wołowina': '🥩',
        'pork': '🥓', 'porc': '🥓', 'wieprzowina': '🥓',
        'fish': '🐟', 'poisson': '🐟', 'ryba': '🐟',
        'salmon': '🍣', 'saumon': '🍣', 'łosoś': '🍣',
        'tuna': '🐟', 'thon': '🐟', 'tuńczyk': '🐟',
        'shrimp': '🦐', 'crevette': '🦐', 'krewetki': '🦐',
        'egg': '🥚', 'oeuf': '🥚', 'œuf': '🥚', 'jajko': '🥚', 'eggs': '🥚', 'oeufs': '🥚', 'jajka': '🥚',
        'bacon': '🥓', 'lardons': '🥓', 'boczek': '🥓',
        'ham': '🍖', 'jambon': '🍖', 'szynka': '🍖',
        'sausage': '🌭', 'saucisse': '🌭', 'kiełbasa': '🌭',
        'meat': '🍖', 'viande': '🍖', 'mięso': '🍖',
        'turkey': '🦃', 'dinde': '🦃', 'indyk': '🦃',
        'duck': '🦆', 'canard': '🦆', 'kaczka': '🦆',
        
        # Vegetables
        'tomato': '🍅', 'tomate': '🍅', 'pomidor': '🍅',
        'carrot': '🥕', 'carotte': '🥕', 'marchew': '🥕',
        'potato': '🥔', 'pomme de terre': '🥔', 'ziemniak': '🥔', 'patate': '🥔',
        'onion': '🧅', 'oignon': '🧅', 'cebula': '🧅',
        'garlic': '🧄', 'ail': '🧄', 'czosnek': '🧄',
        'pepper': '🫑', 'poivron': '🫑', 'papryka': '🫑',
        'broccoli': '🥦', 'brocoli': '🥦', 'brokuły': '🥦',
        'lettuce': '🥬', 'laitue': '🥬', 'salade': '🥬', 'sałata': '🥬',
        'spinach': '🥬', 'épinard': '🥬', 'szpinak': '🥬',
        'cucumber': '🥒', 'concombre': '🥒', 'ogórek': '🥒',
        'corn': '🌽', 'maïs': '🌽', 'kukurydza': '🌽',
        'mushroom': '🍄', 'champignon': '🍄', 'grzyb': '🍄',
        'eggplant': '🍆', 'aubergine': '🍆', 'bakłażan': '🍆',
        'zucchini': '🥒', 'courgette': '🥒', 'cukinia': '🥒',
        'pumpkin': '🎃', 'citrouille': '🎃', 'dynia': '🎃',
        'cabbage': '🥬', 'chou': '🥬', 'kapusta': '🥬',
        'celery': '🥬', 'céleri': '🥬', 'seler': '🥬',
        'asparagus': '🥦', 'asperge': '🥦', 'szparagi': '🥦',
        'peas': '🟢', 'petit pois': '🟢', 'groszek': '🟢',
        'beans': '🫘', 'haricot': '🫘', 'fasola': '🫘',
        'radish': '🔴', 'radis': '🔴', 'rzodkiewka': '🔴',
        
        # Fruits
        'apple': '🍎', 'pomme': '🍎', 'jabłko': '🍎',
        'banana': '🍌', 'banane': '🍌', 'banan': '🍌',
        'orange': '🍊', 'pomarańcza': '🍊',
        'lemon': '🍋', 'citron': '🍋', 'cytryna': '🍋',
        'lime': '🍋', 'citron vert': '🍋', 'limonka': '🍋',
        'strawberry': '🍓', 'fraise': '🍓', 'truskawka': '🍓',
        'grape': '🍇', 'raisin': '🍇', 'winogrono': '🍇',
        'watermelon': '🍉', 'pastèque': '🍉', 'arbuz': '🍉',
        'peach': '🍑', 'pêche': '🍑', 'brzoskwinia': '🍑',
        'pear': '🍐', 'poire': '🍐', 'gruszka': '🍐',
        'cherry': '🍒', 'cerise': '🍒', 'wiśnia': '🍒',
        'pineapple': '🍍', 'ananas': '🍍',
        'mango': '🥭', 'mangue': '🥭',
        'coconut': '🥥', 'noix de coco': '🥥', 'kokos': '🥥',
        'kiwi': '🥝',
        'avocado': '🥑', 'avocat': '🥑', 'awokado': '🥑',
        'melon': '🍈',
        'blueberry': '🫐', 'myrtille': '🫐', 'borówka': '🫐',
        
        # Dairy
        'milk': '🥛', 'lait': '🥛', 'mleko': '🥛',
        'cheese': '🧀', 'fromage': '🧀', 'ser': '🧀',
        'butter': '🧈', 'beurre': '🧈', 'masło': '🧈',
        'yogurt': '🥛', 'yaourt': '🥛', 'jogurt': '🥛',
        'cream': '🥛', 'crème': '🥛', 'śmietana': '🥛',
        
        # Grains & Carbs
        'bread': '🍞', 'pain': '🍞', 'chleb': '🍞',
        'rice': '🍚', 'riz': '🍚', 'ryż': '🍚',
        'pasta': '🍝', 'pâtes': '🍝', 'makaron': '🍝',
        'noodle': '🍜', 'nouille': '🍜',
        'flour': '🌾', 'farine': '🌾', 'mąka': '🌾',
        'cereal': '🥣', 'céréale': '🥣', 'płatki': '🥣',
        'oat': '🌾', 'avoine': '🌾', 'owies': '🌾',
        'croissant': '🥐',
        'bagel': '🥯',
        'pretzel': '🥨',
        'pancake': '🥞', 'crêpe': '🥞', 'naleśnik': '🥞',
        'waffle': '🧇', 'gaufre': '🧇',
        'tortilla': '🫓', 'wrap': '🫓',
        'pizza': '🍕',
        
        # Condiments & Sauces
        'salt': '🧂', 'sel': '🧂', 'sól': '🧂',
        'honey': '🍯', 'miel': '🍯', 'miód': '🍯',
        'oil': '🫒', 'huile': '🫒', 'olej': '🫒',
        'olive': '🫒',
        'vinegar': '🍶', 'vinaigre': '🍶', 'ocet': '🍶',
        'sauce': '🥫', 'sos': '🥫',
        'ketchup': '🍅',
        'mustard': '🟡', 'moutarde': '🟡', 'musztarda': '🟡',
        'mayonnaise': '🥚', 'mayo': '🥚', 'majonez': '🥚',
        'soy': '🥢', 'soja': '🥢',
        
        # Drinks
        'water': '💧', 'eau': '💧', 'woda': '💧',
        'juice': '🧃', 'jus': '🧃', 'sok': '🧃',
        'coffee': '☕', 'café': '☕', 'kawa': '☕',
        'tea': '🍵', 'thé': '🍵', 'herbata': '🍵',
        'wine': '🍷', 'vin': '🍷', 'wino': '🍷',
        'beer': '🍺', 'bière': '🍺', 'piwo': '🍺',
        
        # Nuts & Seeds
        'nut': '🥜', 'noix': '🥜', 'orzech': '🥜',
        'peanut': '🥜', 'cacahuète': '🥜', 'orzeszek': '🥜',
        'almond': '🌰', 'amande': '🌰', 'migdał': '🌰',
        'chestnut': '🌰', 'châtaigne': '🌰', 'kasztan': '🌰',
        
        # Sweets
        'chocolate': '🍫', 'chocolat': '🍫', 'czekolada': '🍫',
        'candy': '🍬', 'bonbon': '🍬', 'cukierek': '🍬',
        'cookie': '🍪', 'biscuit': '🍪', 'ciastko': '🍪',
        'cake': '🍰', 'gâteau': '🍰', 'ciasto': '🍰',
        'ice cream': '🍦', 'glace': '🍦', 'lody': '🍦',
        'sugar': '🍬', 'sucre': '🍬', 'cukier': '🍬',
        
        # Herbs & Spices
        'herb': '🌿', 'herbe': '🌿', 'zioła': '🌿',
        'basil': '🌿', 'basilic': '🌿', 'bazylia': '🌿',
        'parsley': '🌿', 'persil': '🌿', 'pietruszka': '🌿',
        'mint': '🌿', 'menthe': '🌿', 'mięta': '🌿',
        'thyme': '🌿', 'thym': '🌿', 'tymianek': '🌿',
        'rosemary': '🌿', 'romarin': '🌿', 'rozmaryn': '🌿',
        'cinnamon': '🟤', 'cannelle': '🟤', 'cynamon': '🟤',
        'ginger': '🫚', 'gingembre': '🫚', 'imbir': '🫚',
        'chili': '🌶️', 'piment': '🌶️',
        'pepper': '🌶️', 'poivre': '🌶️', 'pieprz': '🌶️',
        
        # Seafood
        'crab': '🦀', 'crabe': '🦀', 'krab': '🦀',
        'lobster': '🦞', 'homard': '🦞', 'homar': '🦞',
        'oyster': '🦪', 'huître': '🦪', 'ostryga': '🦪',
        'squid': '🦑', 'calamar': '🦑', 'kałamarnica': '🦑',
        'octopus': '🐙', 'poulpe': '🐙', 'ośmiornica': '🐙',
    }
    
    # Check for exact matches first
    for key, emoji in emoji_map.items():
        if key in ingredient_lower:
            return emoji
    
    # Default emoji for unknown ingredients
    return '🍴'




def parse_recipe_names(recipes_text: str) -> list:
    """Extract recipe names from the generated recipes text."""
    recipe_names = []
    lines = recipes_text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Look for lines that start with "1.", "2.", "3." 
        if line and len(line) > 3:
            # Check if line starts with a number followed by . 
            if line[0].isdigit() and '.' in line[:3]:
                # Extract everything after "1. " or "1."
                name = line[2:].strip().lstrip('. ')
                
                # If there's markdown bold **, extract from between them
                if '**' in name:
                    parts = name.split('**')
                    if len(parts) >= 2:
                        name = parts[1].strip()
                
                # Remove leading emoji if present (emojis are > 127 in unicode)
                while name and ord(name[0]) > 127:
                    name = name[1:].strip()
                
                # Stop at line break indicators or sub-sections
                for stop_marker in [' - ', ' – ', '\n', '**']:
                    if stop_marker in name:
                        name = name.split(stop_marker)[0].strip()
                
                # Filter out non-recipe lines (instructions, etc.)
                # Recipe names are typically shorter and don't contain certain patterns
                skip_patterns = ['cook', 'boil', 'slice', 'dice', 'chop', 'mix', 'stir', 
                                'bake', 'fry', 'heat', 'add', 'pour', 'season', 'place',
                                'cuire', 'couper', 'mélanger', 'ajouter', 'verser',
                                'gotować', 'kroić', 'mieszać', 'dodać',
                                'minutes', 'mins', 'until', 'then']
                
                name_lower = name.lower()
                is_instruction = any(pattern in name_lower for pattern in skip_patterns)
                
                if name and len(name) > 2 and len(name) < 80 and not is_instruction:
                    recipe_names.append(name)
    
    return recipe_names[:3]  # Max 3 recipes


def get_recipe_emojis(recipe_name: str) -> str:
    """Get 2-4 emojis for a recipe based on ingredients and cooking style."""
    recipe_lower = recipe_name.lower()
    emojis = []
    
    # Main protein/ingredient
    if any(word in recipe_lower for word in ['chicken', 'poulet', 'kurczak']):
        emojis.append('🍗')
    if any(word in recipe_lower for word in ['beef', 'boeuf', 'bœuf', 'steak', 'wołowina']):
        emojis.append('🥩')
    if any(word in recipe_lower for word in ['pork', 'porc', 'wieprzowina']):
        emojis.append('🥓')
    if any(word in recipe_lower for word in ['fish', 'poisson', 'ryba', 'salmon', 'saumon', 'łosoś']):
        emojis.append('🐟')
    if any(word in recipe_lower for word in ['shrimp', 'crevette', 'krewetk', 'seafood']):
        emojis.append('🦐')
    if any(word in recipe_lower for word in ['egg', 'oeuf', 'œuf', 'jajko', 'omelette', 'omlet']):
        emojis.append('🍳')
    
    # Dish type
    if any(word in recipe_lower for word in ['salad', 'salade', 'sałatka']):
        emojis.append('🥗')
    if any(word in recipe_lower for word in ['soup', 'soupe', 'zupa']):
        emojis.append('🍲')
    if any(word in recipe_lower for word in ['pasta', 'spaghetti', 'pâtes', 'makaron', 'noodle', 'primavera']):
        emojis.append('🍝')
    if any(word in recipe_lower for word in ['pizza']):
        emojis.append('🍕')
    if any(word in recipe_lower for word in ['burger', 'hamburger']):
        emojis.append('🍔')
    if any(word in recipe_lower for word in ['sandwich', 'panini']):
        emojis.append('🥪')
    if any(word in recipe_lower for word in ['taco', 'burrito', 'mexican', 'mexicain']):
        emojis.append('🌮')
    if any(word in recipe_lower for word in ['curry']):
        emojis.append('🍛')
    if any(word in recipe_lower for word in ['rice', 'riz', 'ryż', 'risotto']):
        emojis.append('🍚')
    if any(word in recipe_lower for word in ['stir fry', 'wok', 'sauté', 'asian', 'asiatique']):
        emojis.append('🥘')
    
    # Vegetables
    if any(word in recipe_lower for word in ['vegetable', 'légume', 'warzywo', 'veggie', 'primavera']):
        emojis.append('🥬')
    if any(word in recipe_lower for word in ['tomato', 'tomate', 'pomidor']):
        emojis.append('🍅')
    if any(word in recipe_lower for word in ['pepper', 'poivron', 'papryka']):
        emojis.append('🫑')
    if any(word in recipe_lower for word in ['mushroom', 'champignon', 'grzyb']):
        emojis.append('🍄')
    if any(word in recipe_lower for word in ['carrot', 'carotte', 'marchew']):
        emojis.append('🥕')
    
    # Flavor profiles
    if any(word in recipe_lower for word in ['lemon', 'citron', 'cytryn']):
        emojis.append('🍋')
    if any(word in recipe_lower for word in ['garlic', 'ail', 'czosnek']):
        emojis.append('🧄')
    if any(word in recipe_lower for word in ['cheese', 'fromage', 'ser', 'parmesan']):
        emojis.append('🧀')
    if any(word in recipe_lower for word in ['spicy', 'épicé', 'pikantny', 'chili']):
        emojis.append('🌶️')
    if any(word in recipe_lower for word in ['herb', 'herbe', 'zioł']):
        emojis.append('🌿')
    
    # Cooking style
    if any(word in recipe_lower for word in ['grill', 'bbq', 'barbecue']):
        emojis.append('🔥')
    if any(word in recipe_lower for word in ['roast', 'rôti', 'pieczony', 'baked']):
        emojis.append('🍖')
    if any(word in recipe_lower for word in ['fried', 'frit', 'smażony', 'crispy']):
        emojis.append('✨')
    
    # Desserts
    if any(word in recipe_lower for word in ['cake', 'gâteau', 'ciasto', 'dessert']):
        emojis.append('🍰')
    if any(word in recipe_lower for word in ['chocolate', 'chocolat', 'czekolada']):
        emojis.append('🍫')
    if any(word in recipe_lower for word in ['fruit', 'smoothie']):
        emojis.append('🍓')
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emojis = []
    for e in emojis:
        if e not in seen:
            seen.add(e)
            unique_emojis.append(e)
    
    # Return 2-4 emojis, or default if none found
    if len(unique_emojis) == 0:
        return '🍽️🍴'
    elif len(unique_emojis) == 1:
        return unique_emojis[0] + '🍽️'
    else:
        return ''.join(unique_emojis[:4])


def format_recipe_for_display(recipe: dict, index: int, lang: str) -> str:
    """Format a single recipe for markdown display."""
    labels = {
        "en": {"difficulty": "Difficulty", "time": "Time", "ingredients": "Ingredients", 
               "missing": "Missing", "instructions": "Instructions", "tip": "Pro tip"},
        "fr": {"difficulty": "Difficulté", "time": "Temps", "ingredients": "Ingrédients",
               "missing": "Manquants", "instructions": "Instructions", "tip": "Astuce"},
        "pl": {"difficulty": "Trudność", "time": "Czas", "ingredients": "Składniki",
               "missing": "Brakujące", "instructions": "Instrukcje", "tip": "Wskazówka"}
    }
    l = labels.get(lang, labels["en"])
    
    emojis = get_recipe_emojis(recipe.get("name", ""))
    
    md = f"### {index}. {emojis} {recipe.get('name', 'Recipe')}\n\n"
    md += f"**{l['difficulty']}:** {recipe.get('difficulty', 'N/A')} | "
    md += f"**{l['time']}:** {recipe.get('time', 'N/A')}\n\n"
    
    # Ingredients
    md += f"**{l['ingredients']}:**\n"
    for ing in recipe.get("ingredients", []):
        md += f"- {get_ingredient_emoji(ing)} {ing}\n"
    
    # Missing ingredients
    missing = recipe.get("missing_ingredients", [])
    if missing:
        md += f"\n**⚠️ {l['missing']}:**\n"
        for ing in missing:
            md += f"- {get_ingredient_emoji(ing)} {ing}\n"
    
    # Instructions
    md += f"\n**{l['instructions']}:**\n"
    for i, step in enumerate(recipe.get("instructions", []), 1):
        md += f"{i}. {step}\n"
    
    # Tip
    tip = recipe.get("tip", "")
    if tip:
        md += f"\n💡 **{l['tip']}:** {tip}\n"
    
    return md



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
        "select_model": "🤖 AI Model",
        "model_claude": "Claude (Anthropic)",
        "model_gpt4": "GPT-4o (OpenAI)",
        "model_gpt4_mini": "GPT-4o-mini (OpenAI)",
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
        "error_api_key": "⚠️ No AI API key found. Please configure ANTHROPIC_API_KEY or OPENAI_API_KEY in your secrets.",
        "error_api_key_info": "Get API keys from: https://console.anthropic.com/ or https://platform.openai.com/",
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
        "select_model": "🤖 Modèle IA",
        "model_claude": "Claude (Anthropic)",
        "model_gpt4": "GPT-4o (OpenAI)",
        "model_gpt4_mini": "GPT-4o-mini (OpenAI)",
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
        "error_api_key": "⚠️ Aucune clé API IA trouvée. Configurez ANTHROPIC_API_KEY ou OPENAI_API_KEY.",
        "error_api_key_info": "Obtenez vos clés API sur : console.anthropic.com ou platform.openai.com",
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
        "select_model": "🤖 Model AI",
        "model_claude": "Claude (Anthropic)",
        "model_gpt4": "GPT-4o (OpenAI)",
        "model_gpt4_mini": "GPT-4o-mini (OpenAI)",
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
        "error_api_key": "⚠️ Nie znaleziono klucza API. Skonfiguruj ANTHROPIC_API_KEY lub OPENAI_API_KEY.",
        "error_api_key_info": "Uzyskaj klucze API na: console.anthropic.com lub platform.openai.com",
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


def init_openai():
    """Initialize OpenAI client."""
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        return None
    return openai.OpenAI(api_key=api_key)


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


def identify_ingredients_claude(client, image_data: str, media_type: str, lang: str = "en") -> dict:
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


def identify_ingredients_openai(client, image_data: str, media_type: str, model: str, lang: str = "en") -> dict:
    """Use OpenAI to identify ingredients from an image with retry logic."""
    
    max_retries = 3
    retry_delay = 2
    prompt = TRANSLATIONS[lang]["ingredients_prompt"]
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            return {"raw_response": response.choices[0].message.content}
        
        except openai.RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception("Rate limit reached. Please wait a minute before trying again.")
        except openai.APIConnectionError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception("Could not connect to AI service. Please check your internet connection.")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")


def get_recipe_prompt(ingredients: str, preferences_text: str, lang: str) -> str:
    """Generate the recipe suggestion prompt."""
    lang_instructions = {
        "en": "Respond in English.",
        "fr": "Réponds en français.",
        "pl": "Odpowiedz po polsku."
    }
    
    return f"""Based on these available ingredients:

{ingredients}
{preferences_text}

Suggest 3 recipes that can be made primarily with these ingredients.

{lang_instructions.get(lang, lang_instructions["en"])}

IMPORTANT: Return your response as a valid JSON object with this exact structure:
{{
    "recipes": [
        {{
            "name": "Recipe Name Here",
            "difficulty": "Easy/Medium/Hard",
            "time": "30 minutes",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "missing_ingredients": ["ingredient that is NOT in the available list"],
            "instructions": ["Step 1 description", "Step 2 description", "Step 3 description"],
            "tip": "Pro tip for this dish"
        }}
    ]
}}

Make sure to:
- Include exactly 3 recipes
- List 5-7 instruction steps per recipe
- Mark any ingredients NOT in the available list in "missing_ingredients"
- Keep recipe names short and descriptive (max 6 words)
- Return ONLY the JSON, no other text before or after"""


def parse_recipe_response(response_text: str) -> dict:
    """Parse the JSON response from the AI model."""
    # Clean up response if needed (remove markdown code blocks if present)
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"raw_text": response_text, "parse_error": str(e)}


def suggest_recipes_claude(client, ingredients: str, dietary_preferences: list = None, cuisine_preference: str = None, lang: str = "en") -> dict:
    """Use Claude to suggest recipes based on identified ingredients."""
    
    preferences_text = ""
    if dietary_preferences:
        preferences_text += f"\nDietary requirements: {', '.join(dietary_preferences)}"
    if cuisine_preference and cuisine_preference != "Any" and cuisine_preference != "Toutes" and cuisine_preference != "Dowolna":
        preferences_text += f"\nPreferred cuisine: {cuisine_preference}"
    
    max_retries = 3
    retry_delay = 2
    prompt = get_recipe_prompt(ingredients, preferences_text, lang)

    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            return parse_recipe_response(message.content[0].text)
        
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
            if "JSON" in str(e) or "json" in str(e):
                raise Exception(f"Failed to parse recipe data: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")


def suggest_recipes_openai(client, model: str, ingredients: str, dietary_preferences: list = None, cuisine_preference: str = None, lang: str = "en") -> dict:
    """Use OpenAI to suggest recipes based on identified ingredients."""
    
    preferences_text = ""
    if dietary_preferences:
        preferences_text += f"\nDietary requirements: {', '.join(dietary_preferences)}"
    if cuisine_preference and cuisine_preference != "Any" and cuisine_preference != "Toutes" and cuisine_preference != "Dowolna":
        preferences_text += f"\nPreferred cuisine: {cuisine_preference}"
    
    max_retries = 3
    retry_delay = 2
    prompt = get_recipe_prompt(ingredients, preferences_text, lang)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            return parse_recipe_response(response.choices[0].message.content)
        
        except openai.RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception("Rate limit reached. Please wait a minute before trying again.")
        except openai.APIConnectionError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception("Could not connect to AI service. Please check your internet connection.")
        except Exception as e:
            if "JSON" in str(e) or "json" in str(e):
                raise Exception(f"Failed to parse recipe data: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")


def save_to_supabase(supabase: Client, ingredients: str, recipes_data):
    """Save the search to Supabase for history."""

    try:
        # Handle both structured and raw data
        if isinstance(recipes_data, dict) and "recipes" in recipes_data:
            # Extract recipe names for easy display in history
            recipe_names = [r.get("name", "Unknown") for r in recipes_data.get("recipes", [])]
            recipes_json = json.dumps(recipes_data, ensure_ascii=False)
            recipes_text = ", ".join(recipe_names)
        elif isinstance(recipes_data, dict) and "raw_text" in recipes_data:
            recipes_json = json.dumps(recipes_data, ensure_ascii=False)
            recipes_text = recipes_data.get("raw_text", "")[:500]
        else:
            recipes_json = None
            recipes_text = str(recipes_data)
        
        data = {
            "ingredients_detected": ingredients,
            "recipes_suggested": recipes_text,
            "recipes_json": recipes_json,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("recipe_searches").insert(data).execute()
        return True
    except Exception as e:
        # If recipes_json column doesn't exist, try without it
        try:
            data = {
                "ingredients_detected": ingredients,
                "recipes_suggested": recipes_text if 'recipes_text' in dir() else str(recipes_data),
                "created_at": datetime.now().isoformat()
            }
            supabase.table("recipe_searches").insert(data).execute()
            return True
        except Exception as e2:
            st.error(f"Failed to save to database: {e2}")
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
    openai_client = init_openai()
    supabase_client = init_supabase()
    
    # Check for at least one API key
    if not anthropic_client and not openai_client:
        st.error(get_text("error_api_key"))
        st.info(get_text("error_api_key_info"))
        return
    
    # Build available models list
    available_models = []
    if anthropic_client:
        available_models.append(("claude", get_text("model_claude")))
    if openai_client:
        available_models.append(("gpt-4o", get_text("model_gpt4")))
        available_models.append(("gpt-4o-mini", get_text("model_gpt4_mini")))
    
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
    
    # Set default model if only one available
    if 'selected_model' not in st.session_state:
        st.session_state['selected_model'] = available_models[0][0] if available_models else "claude"
    
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
                selected_model = st.session_state.get('selected_model', 'claude')
                all_ingredients = []
                total_images = len(st.session_state.images)
                
                # Analyze each image
                for idx, img in enumerate(st.session_state.images):
                    progress_text.text(f"{get_text('analyzing')} ({idx + 1}/{total_images})")
                    progress_bar.progress(int((idx + 1) / total_images * 100))
                    
                    # Encode image
                    image_data = encode_image(img)
                    media_type = get_image_media_type(img)
                    
                    # Identify ingredients using selected model
                    if selected_model == "claude":
                        ingredients_result = identify_ingredients_claude(anthropic_client, image_data, media_type, lang)
                    else:
                        ingredients_result = identify_ingredients_openai(openai_client, image_data, media_type, selected_model, lang)
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
        
        # Display ingredients with delete buttons in 2 columns
        ingredients_to_remove = []
        ingredients = st.session_state['ingredients_list']
        
        # Create 2 columns
        col_left, col_right = st.columns(2)
        
        for idx, ingredient in enumerate(ingredients):
            # Alternate between left and right columns
            with col_left if idx % 2 == 0 else col_right:
                col_del, col_ing = st.columns([1, 5])
                with col_del:
                    if st.button("❌", key=f"del_{idx}", help=f"Remove {ingredient}"):
                        ingredients_to_remove.append(idx)
                with col_ing:
                    emoji = get_ingredient_emoji(ingredient)
                    st.markdown(f"<span style='font-size: 1.2rem;'>{emoji}</span> <span style='font-size: 0.95rem;'>{ingredient}</span>", unsafe_allow_html=True)
        
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
                    selected_model = st.session_state.get('selected_model', 'claude')
                    
                    # Generate recipes using selected model
                    if selected_model == "claude":
                        recipes = suggest_recipes_claude(
                            anthropic_client,
                            final_ingredients,
                            dietary_preferences,
                            cuisine_preference,
                            lang
                        )
                    else:
                        recipes = suggest_recipes_openai(
                            openai_client,
                            selected_model,
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
                # Show ingredients with emojis in 2 columns
                if 'ingredients_list' in st.session_state:
                    ingredients = st.session_state['ingredients_list']
                    col_left, col_right = st.columns(2)
                    for idx, ing in enumerate(ingredients):
                        with col_left if idx % 2 == 0 else col_right:
                            emoji = get_ingredient_emoji(ing)
                            st.markdown(f"{emoji} {ing}")
                else:
                    st.markdown(st.session_state['ingredients'])
        
        # Recipe suggestions header
        st.markdown(get_text("your_recipes"))
        
        recipes_data = st.session_state['recipes']
        lang = st.session_state.language
        
        # Check if we have structured data or raw text
        if isinstance(recipes_data, dict) and "recipes" in recipes_data:
            # Structured JSON data
            recipe_list = recipes_data["recipes"]
            
            # Initialize selected recipe index
            if 'selected_recipe_idx' not in st.session_state:
                st.session_state['selected_recipe_idx'] = 0
            
            # Display recipe cards with emojis and names (as clickable tabs)
            if recipe_list:
                cols = st.columns(len(recipe_list))
                for idx, recipe in enumerate(recipe_list):
                    with cols[idx]:
                        name = recipe.get("name", f"Recipe {idx + 1}")
                        emojis = get_recipe_emojis(name)
                        is_selected = (idx == st.session_state['selected_recipe_idx'])
                        
                        # Card as clickable button
                        if st.button(
                            f"{emojis}",
                            key=f"recipe_card_{idx}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            st.session_state['selected_recipe_idx'] = idx
                            st.rerun()
                        
                        # Recipe name below button
                        text_style = "font-weight: 700;" if is_selected else "font-weight: 500;"
                        st.markdown(f"<p style='text-align: center; font-size: 0.85rem; {text_style} margin-top: -10px;'>{name}</p>", unsafe_allow_html=True)
                
                # Custom CSS for recipe cards
                st.markdown("""
                <style>
                    /* Recipe card buttons */
                    [data-testid="stHorizontalBlock"] [data-testid="stButton"] button {
                        min-height: 100px !important;
                        font-size: 2.5rem !important;
                        border-radius: 15px !important;
                        background: linear-gradient(135deg, #667eea22, #764ba222) !important;
                        border: 3px solid transparent !important;
                        transition: all 0.2s ease !important;
                    }
                    [data-testid="stHorizontalBlock"] [data-testid="stButton"] button:hover {
                        background: linear-gradient(135deg, #667eea33, #764ba233) !important;
                        transform: translateY(-2px);
                    }
                    [data-testid="stHorizontalBlock"] [data-testid="stButton"] button[kind="primary"] {
                        background: linear-gradient(135deg, #667eea44, #764ba244) !important;
                        border: 3px solid #667eea !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Show only selected recipe details
                st.markdown("---")
                selected_idx = st.session_state['selected_recipe_idx']
                if selected_idx < len(recipe_list):
                    selected_recipe = recipe_list[selected_idx]
                    st.markdown(format_recipe_for_display(selected_recipe, selected_idx + 1, lang))
                
                # Prepare download content (all recipes)
                download_content = "\n\n".join([format_recipe_for_display(r, i, lang) for i, r in enumerate(recipe_list, 1)])
        
        elif isinstance(recipes_data, dict) and "raw_text" in recipes_data:
            # Fallback: raw text (JSON parsing failed)
            st.warning("⚠️ Recipe formatting limited")
            st.markdown(recipes_data["raw_text"])
            download_content = recipes_data["raw_text"]
        
        else:
            # Legacy: plain text
            st.markdown(recipes_data)
            download_content = recipes_data
        
        # Download and New Search buttons
        col_download, col_new = st.columns(2)
        with col_download:
            st.download_button(
                label=get_text("save_recipes"),
                data=download_content,
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
                st.session_state.pop('selected_recipe_idx', None)
                st.rerun()
    
    # Sidebar for model selection and history
    with st.sidebar:
        # Model selector
        if len(available_models) > 1:
            st.header(get_text("select_model"))
            model_options = [m[1] for m in available_models]
            model_keys = [m[0] for m in available_models]
            selected_model_label = st.selectbox(
                get_text("select_model"),
                model_options,
                index=0,
                label_visibility="collapsed"
            )
            selected_model = model_keys[model_options.index(selected_model_label)]
            st.session_state['selected_model'] = selected_model
            st.divider()
        
        # History section
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