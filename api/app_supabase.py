from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from supabase import create_client, Client
import google.generativeai as genai
from datetime import datetime
import json

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
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.replace('Bearer ', '')
    try:
        user = supabase.auth.get_user(token)
        return user.user.id if user and user.user else None
    except:
        return None

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from Python Flask server! 🐍'})

@app.route('/api/analyze-transactions', methods=['POST'])
def analyze_transactions():
    try:
        # Get user ID from auth token
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'error': 'Unauthorized. Please login.'}), 401
        
        if 'csvFile' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['csvFile']
        df = pd.read_csv(file)
        
        # Normalize column names
        df.columns = df.columns.str.strip()
        
        # Handle different CSV formats
        if 'Description' in df.columns:
            desc_col = 'Description'
        elif 'description' in df.columns:
            desc_col = 'description'
        else:
            return jsonify({'error': 'CSV must have a Description column'}), 400
        
        if 'Amount' in df.columns:
            amt_col = 'Amount'
        elif 'amount' in df.columns:
            amt_col = 'amount'
        else:
            return jsonify({'error': 'CSV must have an Amount column'}), 400
        
        date_col = 'Date' if 'Date' in df.columns else ('date' if 'date' in df.columns else None)
        
        df['description'] = df[desc_col]
        df['amount'] = pd.to_numeric(df[amt_col], errors='coerce').abs()
        df['date'] = df[date_col] if date_col else datetime.now().strftime('%Y-%m-%d')
        df['drcr'] = df['DR/CR'] if 'DR/CR' in df.columns else 'DR'
        df = df.dropna(subset=['amount'])
        
        # Categorize transactions
        df['category'] = df['description'].apply(categorize_transaction_fallback)
        
        # Delete existing transactions for this user (optional - or keep history)
        # supabase.table('transactions').delete().eq('user_id', user_id).execute()
        
        # Insert transactions into Supabase
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
        
        # Batch insert (Supabase supports up to 1000 rows at once)
        if transactions_to_insert:
            supabase.table('transactions').insert(transactions_to_insert).execute()
        
        # Calculate analytics
        income_df = df[df['drcr'] == 'CR']
        expense_df = df[df['drcr'] == 'DR']
        
        total_inflow = income_df['amount'].sum()
        total_outflow = expense_df['amount'].sum()
        
        category_totals = df[df['category'] != 'Income'].groupby('category')['amount'].sum()
        
        response_data = {
            'categorized': df[['description', 'category', 'amount', 'date']].to_dict('records'),
            'analytics': {
                'totalInflow': float(total_inflow),
                'totalOutflow': float(total_outflow),
                'score': 75,
                'aiTip': 'Track your expenses regularly and look for areas to reduce spending.'
            },
            'message': f'Successfully uploaded {len(df)} transactions for user {user_id}'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    try:
        # Get user ID from auth token
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'error': 'Unauthorized. Please login.'}), 401
        
        data = request.get_json()
        user_question = data.get('question')
        
        if not user_question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Fetch user's transactions from Supabase
        response = supabase.table('transactions').select('*').eq('user_id', user_id).execute()
        
        has_data = len(response.data) > 0
        
        if has_data:
            df = pd.DataFrame(response.data)
            
            income_df = df[df['category'] == 'Income']
            expense_df = df[df['category'] != 'Income']
            
            total_income = income_df['amount'].sum()
            total_expenses = expense_df['amount'].sum()
            
            expense_breakdown = expense_df.groupby('category')['amount'].sum().to_dict()
            
            breakdown_text = "\n".join([
                f"- {cat}: ₹{amt:.2f}" for cat, amt in expense_breakdown.items()
            ])
            
            prompt = f"""You are a helpful financial advisor for SnapSpend. The user has uploaded their transaction data. Here's their financial summary:

📊 Financial Overview:
- Total Income: ₹{total_income:.2f}
- Total Expenses: ₹{total_expenses:.2f}
- Net Savings: ₹{(total_income - total_expenses):.2f}

💰 Spending by Category:
{breakdown_text}

User Question: "{user_question}"

Provide a helpful, personalized answer based on their actual transaction data. Keep it conversational and actionable (2-4 sentences)."""
        else:
            prompt = f"""You are a helpful financial advisor for SnapSpend. Provide general financial advice.

User Question: "{user_question}"

Provide helpful financial advice (2-4 sentences)."""
        
        if model is None:
            answer = "I'm currently unable to process your question. Please check if the AI service is properly configured."
        else:
            response = model.generate_content(prompt)
            answer = response.text.strip()
        
        return jsonify({
            'answer': answer,
            'hasData': has_data
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to answer question', 'details': str(e)}), 500

@app.route('/api/check-data', methods=['GET'])
def check_data():
    try:
        # Get user ID from auth token
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'loaded': False, 'count': 0, 'message': 'Not logged in'})
        
        # Fetch user's transactions from Supabase
        response = supabase.table('transactions').select('category').eq('user_id', user_id).execute()
        
        if not response.data:
            return jsonify({'loaded': False, 'count': 0})
        
        df = pd.DataFrame(response.data)
        categories = df['category'].unique().tolist()
        
        return jsonify({
            'loaded': True,
            'count': len(response.data),
            'categories': categories
        })
        
    except Exception as e:
        return jsonify({'loaded': False, 'count': 0, 'error': str(e)})

@app.route('/api/recent-transactions', methods=['GET'])
def get_recent_transactions():
    try:
        # Get user ID from auth token
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'transactions': [], 'message': 'Not logged in'})
        
        # Fetch recent transactions from Supabase
        response = supabase.table('transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('date', desc=True)\
            .limit(10)\
            .execute()
        
        return jsonify({
            'transactions': response.data,
            'count': len(response.data)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transactions', 'details': str(e)}), 500

@app.route('/api/category-totals', methods=['GET'])
def get_category_totals():
    try:
        # Get user ID from auth token
        auth_header = request.headers.get('Authorization')
        user_id = get_user_from_token(auth_header)
        
        if not user_id:
            return jsonify({'categories': [], 'message': 'Not logged in'})
        
        # Fetch user's transactions from Supabase
        response = supabase.table('transactions').select('*').eq('user_id', user_id).execute()
        
        if not response.data:
            return jsonify({'categories': [], 'totalExpenses': 0})
        
        df = pd.DataFrame(response.data)
        expense_df = df[df['category'] != 'Income']
        
        category_totals = expense_df.groupby('category')['amount'].sum()
        total_expenses = category_totals.sum()
        
        categories = []
        colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6']
        
        for i, (category, total) in enumerate(category_totals.items()):
            percentage = (total / total_expenses * 100) if total_expenses > 0 else 0
            categories.append({
                'category': category,
                'total': float(total),
                'percentage': round(percentage, 1),
                'color': colors[i % len(colors)]
            })
        
        categories.sort(key=lambda x: x['total'], reverse=True)
        
        return jsonify({
            'categories': categories,
            'totalExpenses': float(total_expenses)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch category totals', 'details': str(e)}), 500

# Vercel serverless handler
def handler(request):
    with app.request_context(request.environ):
        return app.full_dispatch_request()
