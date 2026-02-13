# 🍳 Fridge to Recipe

An AI-powered application that identifies ingredients from photos and suggests personalized recipes. Built with Streamlit, Claude AI, and Supabase.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- 📸 **Image Upload**: Upload photos of your fridge, pantry, or ingredients
- 🔍 **AI Ingredient Detection**: Uses Claude's vision capabilities to identify ingredients
- 👨‍🍳 **Smart Recipe Suggestions**: Get 3 personalized recipes based on what you have
- ⚙️ **Dietary Preferences**: Filter by vegetarian, vegan, gluten-free, keto, etc.
- 🌍 **Cuisine Selection**: Choose your preferred cuisine style
- 📜 **Search History**: Save and view your past searches (with Supabase)
- 📥 **Export Recipes**: Download your recipes as text files

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd fridge-to-recipe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

Required:
- `ANTHROPIC_API_KEY`: Get from [Anthropic Console](https://console.anthropic.com/)

Optional (for history feature):
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key

### 3. Setup Supabase (Optional)

If you want to enable search history:

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to SQL Editor in your Supabase dashboard
3. Copy and run the contents of `supabase_schema.sql`
4. Get your API credentials from Settings → API

### 4. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Usage

1. **Upload an Image**: Click the upload area and select a photo of your ingredients
2. **Set Preferences**: Use the sidebar to select dietary requirements and cuisine preferences
3. **Analyze**: Click "Identify Ingredients & Get Recipes"
4. **Explore Recipes**: View the suggested recipes and cooking instructions
5. **Save**: Download your favorite recipes or view search history

## Project Structure

```
fridge-to-recipe/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your environment variables (git-ignored)
├── supabase_schema.sql   # Database schema for Supabase
└── README.md             # This file
```

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) - Fast Python web apps
- **AI/Vision**: [Claude API](https://anthropic.com/) - Advanced vision and language AI
- **Database**: [Supabase](https://supabase.com/) - Open source Firebase alternative
- **Language**: Python 3.9+

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key for Claude |
| `SUPABASE_URL` | No | Supabase project URL |
| `SUPABASE_KEY` | No | Supabase anonymous key |

## Tips for Best Results

1. **Good Lighting**: Ensure your ingredients are well-lit
2. **Clear View**: Arrange items so they're clearly visible
3. **Multiple Angles**: For full fridges, consider multiple photos
4. **Labels Visible**: Turn products so labels are readable when possible

## Customization Ideas

- Add user authentication with Supabase Auth
- Implement recipe rating and favorites
- Add nutritional information
- Create shopping lists for missing ingredients
- Add meal planning features
- Integrate with grocery delivery APIs

## Troubleshooting

**"Anthropic API key not found"**
- Ensure `.env` file exists with valid `ANTHROPIC_API_KEY`
- Restart the Streamlit server after adding the key

**"Failed to save to database"**
- Check Supabase credentials in `.env`
- Ensure the database schema has been applied
- Check Supabase dashboard for any errors

**Image not processing**
- Ensure image is JPG, PNG, or WebP format
- Check file size (keep under 20MB)
- Try a clearer, well-lit photo

## License

MIT License - feel free to use and modify for your own projects!

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
