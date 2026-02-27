from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import google.generativeai as genai
from datetime import datetime
import json
import random

app = Flask(__name__)
CORS(app)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Try to initialize model with fallback options
try:
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    print("[OK] Using Gemini 2.5 Flash")
except Exception as e:
    try:
        model = genai.GenerativeModel('models/gemini-flash-latest')
        print("[OK] Using Gemini Flash Latest")
    except Exception as e2:
        try:
            model = genai.GenerativeModel('models/gemini-pro-latest')
            print("[OK] Using Gemini Pro Latest")
        except Exception as e3:
            model = None
            print(f"[WARNING] Could not initialize Gemini model: {e3}")

# Global storage for transactions (in-memory)
stored_transactions_df = None

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
    """Rule-based categorization fallback"""
    desc_lower = str(description).lower()
    
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in desc_lower for keyword in keywords):
            return category
    
    return 'Shopping'

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from Python Flask server! 🐍'})

@app.route('/api/analyze-transactions', methods=['POST'])
def analyze_transactions():
    global stored_transactions_df
    
    try:
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
        df['date'] = df[date_col] if date_col else 'Unknown'
        df['drcr'] = df['DR/CR'] if 'DR/CR' in df.columns else 'DR'
        df = df.dropna(subset=['amount'])
        
        # Use fallback categorization for serverless
        df['category'] = df['description'].apply(categorize_transaction_fallback)
        
        stored_transactions_df = df.copy()
        
        # Analytics
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
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    global stored_transactions_df
    
    try:
        data = request.get_json()
        user_question = data.get('question')
        
        if not user_question:
            return jsonify({'error': 'Question is required'}), 400
        
        has_data = stored_transactions_df is not None and len(stored_transactions_df) > 0
        
        if has_data:
            income_df = stored_transactions_df[stored_transactions_df['category'] == 'Income']
            expense_df = stored_transactions_df[stored_transactions_df['category'] != 'Income']
            
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
    global stored_transactions_df
    if stored_transactions_df is None:
        return jsonify({'loaded': False, 'count': 0})
    return jsonify({
        'loaded': True,
        'count': len(stored_transactions_df),
        'categories': stored_transactions_df['category'].unique().tolist()
    })

# Vercel serverless handler
def handler(request):
    with app.request_context(request.environ):
        return app.full_dispatch_request()
