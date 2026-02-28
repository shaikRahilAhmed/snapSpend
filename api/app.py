from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from supabase import create_client, Client
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure Supabase
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

try:
    model = genai.GenerativeModel('models/gemini-2.5-flash')
except:
    try:
        model = genai.GenerativeModel('models/gemini-flash-latest')
    except:
        model = None

# Category keywords for fallback
CATEGORY_RULES = {
    'Income': ['salary', 'income', 'credit', 'reimbursement', 'payment from'],
    'Food': ['food', 'restaurant', 'swiggy', 'zomato', 'cafe', 'starbucks', 'dominos', 'pizza'],
    'Travel': ['uber', 'ola', 'taxi', 'flight', 'train', 'bus', 'irctc', 'indigo', 'metro'],
    'Shopping': ['amazon', 'flipkart', 'myntra', 'shopping', 'mall', 'store'],
    'Bills': ['electricity', 'mobile', 'bill', 'netflix', 'hotstar', 'subscription', 'airtel', 'jio'],
    'Health': ['hospital', 'doctor', 'medicine', 'pharmacy', 'pharmeasy', 'health', 'clinic'],
    'Groceries': ['grocery', 'dmart', 'bigbasket', 'supermarket', 'vegetables', 'fruits']
}

def categorize_transaction_fallback(description):
    desc_lower = str(description).lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in desc_lower for keyword in keywords):
            return category
    return 'Shopping'

def get_user_from_token(auth_header):
    """Extract user from Authorization header"""
    # TEMPORARY: For testing without auth, return a dummy user ID
    # TODO: Enable auth in production
    return "test-user-123"
    
    # Uncomment below for production with auth:
    # if not auth_header or not auth_header.startswith('Bearer '):
    #     return None
    # token = auth_header.replace('Bearer ', '')
    # try:
    #     user = supabase.auth.get_user(token)
    #     return user.user.id if user and user.user else None
    # except:
    #     return None

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from Python Flask server! 🐍'})

@app.route('/api/analyze-transactions', methods=['POST'])
def analyze_transactions():
    try:
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'error': 'Unauthorized. Please login.'}), 401
        
        if 'csvFile' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['csvFile']
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        
        desc_col = 'Description' if 'Description' in df.columns else 'description'
        amt_col = 'Amount' if 'Amount' in df.columns else 'amount'
        date_col = 'Date' if 'Date' in df.columns else 'date'
        
        df['description'] = df[desc_col]
        df['amount'] = pd.to_numeric(df[amt_col], errors='coerce').abs()
        df['date'] = df[date_col] if date_col in df.columns else datetime.now().strftime('%Y-%m-%d')
        df['drcr'] = df['DR/CR'] if 'DR/CR' in df.columns else 'DR'
        df = df.dropna(subset=['amount'])
        df['category'] = df['description'].apply(categorize_transaction_fallback)
        
        transactions_to_insert = []
        for _, row in df.iterrows():
            transactions_to_insert.append({
                'user_id': user_id,
                'date': str(row['date']),
                'description': row['description'],
                'amount': float(row['amount']),
                'category': row['category'],
                'transaction_type': row['drcr'],
                'categorization_method': 'rule_based'
            })
        
        if transactions_to_insert:
            supabase.table('transactions').insert(transactions_to_insert).execute()
        
        income_df = df[df['drcr'] == 'CR']
        expense_df = df[df['drcr'] == 'DR']
        
        response_data = {
            'categorized': df[['description', 'category', 'amount', 'date']].to_dict('records'),
            'analytics': {
                'totalInflow': float(income_df['amount'].sum()),
                'totalOutflow': float(expense_df['amount'].sum()),
                'score': 75,
                'aiTip': 'Track your expenses regularly.'
            }
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    try:
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        user_question = data.get('question')
        
        response = supabase.table('transactions').select('*').eq('user_id', user_id).execute()
        has_data = len(response.data) > 0
        
        if has_data and model:
            df = pd.DataFrame(response.data)
            prompt = f"Financial advisor question: {user_question}. Answer in 2-3 sentences."
            answer = model.generate_content(prompt).text.strip()
        else:
            answer = "Please upload your CSV first for personalized advice."
        
        return jsonify({'answer': answer, 'hasData': has_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-data', methods=['GET'])
def check_data():
    try:
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'loaded': False, 'count': 0})
        
        response = supabase.table('transactions').select('category').eq('user_id', user_id).execute()
        
        return jsonify({
            'loaded': len(response.data) > 0,
            'count': len(response.data)
        })
    except:
        return jsonify({'loaded': False, 'count': 0})

# Export for Vercel
handler = app
