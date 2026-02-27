from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
import json
import random

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Try to initialize model with fallback options
try:
    # Use the latest available models
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
    
    return 'Shopping'  # Default category

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from Python Flask server! 🐍'})

@app.route('/api/debug-data', methods=['GET'])
def debug_data():
    """Debug endpoint to check data status"""
    global stored_transactions_df
    return jsonify({
        'is_none': stored_transactions_df is None,
        'count': len(stored_transactions_df) if stored_transactions_df is not None else 0,
        'columns': stored_transactions_df.columns.tolist() if stored_transactions_df is not None else [],
        'has_category': 'category' in stored_transactions_df.columns if stored_transactions_df is not None else False
    })

@app.route('/api/check-data', methods=['GET'])
def check_data():
    """Check if transaction data is loaded"""
    global stored_transactions_df
    if stored_transactions_df is None:
        return jsonify({
            'loaded': False,
            'message': 'No data loaded. Please upload CSV first.',
            'count': 0
        })
    return jsonify({
        'loaded': True,
        'message': 'Data is loaded!',
        'count': len(stored_transactions_df),
        'categories': stored_transactions_df['category'].unique().tolist() if 'category' in stored_transactions_df.columns else []
    })

@app.route('/analyze-transactions', methods=['POST'])
def analyze_transactions():
    global stored_transactions_df
    
    try:
        print("[FILE] File upload received")
        
        if 'csvFile' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['csvFile']
        
        # Read CSV using pandas
        df = pd.read_csv(file)
        print(f"[OK] Loaded {len(df)} rows from CSV")
        
        # Normalize column names
        df.columns = df.columns.str.strip()
        
        # Handle different CSV formats
        if 'Description' in df.columns:
            desc_col = 'Description'
        elif 'description' in df.columns:
            desc_col = 'description'
        elif 'Transaction Description' in df.columns:
            desc_col = 'Transaction Description'
        else:
            return jsonify({'error': 'CSV must have a Description column'}), 400
        
        if 'Amount' in df.columns:
            amt_col = 'Amount'
        elif 'amount' in df.columns:
            amt_col = 'amount'
        elif 'Transaction Amount' in df.columns:
            amt_col = 'Transaction Amount'
        else:
            return jsonify({'error': 'CSV must have an Amount column'}), 400
        
        if 'Date' in df.columns:
            date_col = 'Date'
        elif 'date' in df.columns:
            date_col = 'date'
        elif 'Transaction Date' in df.columns:
            date_col = 'Transaction Date'
        else:
            date_col = None
        
        # Extract and clean data
        df['description'] = df[desc_col]
        df['amount'] = pd.to_numeric(df[amt_col], errors='coerce').abs()
        df['date'] = df[date_col] if date_col else 'Unknown'
        df['drcr'] = df['DR/CR'] if 'DR/CR' in df.columns else 'DR'
        
        # Remove NaN amounts
        df = df.dropna(subset=['amount'])
        
        print(f"[DATA] Processing {len(df)} valid transactions")
        
        # Try AI categorization first
        using_fallback = False
        try:
            if model is None:
                raise ValueError("Gemini model not initialized")
                
            print("[AI] Attempting AI categorization with Gemini...")
            
            # Prepare prompt for Gemini
            transactions_text = "\n".join([
                f"{i+1}. {row['description']} | Amount: ₹{row['amount']} | Date: {row['date']}"
                for i, row in df.head(50).iterrows()  # Limit to 50 for API
            ])
            
            prompt = f"""Categorize these transactions into: Food, Travel, Shopping, Bills, Health, Groceries, Income.
Return ONLY a JSON array with this exact format:
[{{"description": "...", "category": "...", "amount": ..., "date": "..."}}]

Transactions:
{transactions_text}"""
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                categorized_list = json.loads(json_text)
                
                # Create category mapping
                category_map = {item['description']: item['category'] for item in categorized_list}
                df['category'] = df['description'].map(category_map).fillna('Shopping')
                
                print("[OK] AI categorization successful")
            else:
                raise ValueError("Invalid JSON response from AI")
                
        except Exception as e:
            print(f"[WARN] AI categorization failed: {str(e)}")
            print("[INFO] Using rule-based fallback categorization")
            using_fallback = True
            df['category'] = df['description'].apply(categorize_transaction_fallback)
        
        # Store for chatbot use - MUST declare global first!
        global stored_transactions_df
        stored_transactions_df = df.copy()
        print(f"[OK] Stored {len(stored_transactions_df)} transactions for chatbot")
        
        # === ANALYTICS USING PANDAS ===
        
        # Income vs Expenses
        income_df = df[df['drcr'] == 'CR']
        expense_df = df[df['drcr'] == 'DR']
        
        total_inflow = income_df['amount'].sum()
        total_outflow = expense_df['amount'].sum()
        
        # One-time expenses (unique merchants)
        merchant_counts = df['description'].value_counts()
        one_time_merchants = merchant_counts[merchant_counts == 1].index
        one_time_expenses = df[
            (df['description'].isin(one_time_merchants)) & 
            (df['drcr'] == 'DR')
        ][['description', 'amount', 'date']].to_dict('records')
        
        # Bill calendar
        bill_keywords = ['electricity', 'mobile', 'netflix', 'bill', 'subscription']
        bill_df = df[df['description'].str.lower().str.contains('|'.join(bill_keywords), na=False)]
        bill_calendar = bill_df[['description', 'date']].to_dict('records')
        
        # Category-wise spending
        category_totals = df[df['category'] != 'Income'].groupby('category')['amount'].sum()
        
        # Reduction advice
        reduce_advice = [
            f"Try reducing {cat} spend of ₹{amt:.0f} to ₹{amt*0.7:.0f}."
            for cat, amt in category_totals.items() if amt > 1000
        ]
        
        # Half-month comparison - Extract day from date
        first_half = 0
        second_half = 0
        try:
            df['day'] = pd.to_datetime(df['date'], errors='coerce').dt.day
            # Recalculate expense_df after adding day column
            expense_df_with_day = df[df['drcr'] == 'DR'].copy()
            first_half = expense_df_with_day[expense_df_with_day['day'] <= 15]['amount'].sum()
            second_half = expense_df_with_day[expense_df_with_day['day'] > 15]['amount'].sum()
        except Exception as e:
            print(f"[WARN] Date parsing warning: {e}")
            # Use default values if date parsing fails
            first_half = total_outflow / 2
            second_half = total_outflow / 2
        
        # Top 3 spends
        try:
            top_3_spends = expense_df.nlargest(3, 'amount')['amount'].tolist()
            if len(top_3_spends) == 0:
                top_3_spends = [0, 0, 0]
        except Exception as e:
            print(f"[WARN] Top spends calculation warning: {e}")
            top_3_spends = [0, 0, 0]
        
        # Financial health score
        score = 100
        if total_outflow > total_inflow:
            score -= 20
        if len(reduce_advice) >= 3:
            score -= 10
        if first_half > second_half * 1.5:
            score -= 15
        
        # Simulated savings
        saved_total = sum(top_3_spends)
        simulated_amount = saved_total * 1.07  # 7% interest
        
        # AI tip generation
        ai_tip = "Track your expenses regularly and look for areas to reduce spending."
        if not using_fallback and model is not None:
            try:
                tip_prompt = f"""Based on this financial data:
- Total Income: ₹{total_inflow:.2f}
- Total Expenses: ₹{total_outflow:.2f}
- Top spending categories: {', '.join(category_totals.nlargest(3).index.tolist())}

Give ONE short, actionable financial tip (max 2 sentences). Be friendly and helpful."""
                
                tip_response = model.generate_content(tip_prompt)
                ai_tip = tip_response.text.strip()
            except Exception as e:
                print(f"[WARN] AI tip generation failed: {e}")
                pass
        
        # Prepare response
        categorized_transactions = df[['description', 'category', 'amount', 'date']].to_dict('records')
        
        print(f"[OK] Analysis complete - {len(categorized_transactions)} transactions")
        
        response_data = {
            'categorized': categorized_transactions,
            'analytics': {
                'totalInflow': float(total_inflow),
                'totalOutflow': float(total_outflow),
                'oneTimeExpenses': one_time_expenses[:10],  # Limit to 10
                'billCalendar': bill_calendar,
                'reduceAdvice': reduce_advice,
                'halfMonthComparison': {
                    'firstHalf': float(first_half),
                    'secondHalf': float(second_half)
                },
                'top3Spends': [float(x) for x in top_3_spends],
                'score': int(score),
                'simulatedSavedAmount': f"{simulated_amount:.2f}",
                'aiTip': ai_tip
            },
            'warning': 'AI categorization unavailable. Using rule-based categorization.' if using_fallback else None
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/ask-question', methods=['POST'])
def ask_question():
    global stored_transactions_df
    
    try:
        print("[CHAT] AI Chat question received")
        
        data = request.get_json()
        user_question = data.get('question')
        
        if not user_question:
            return jsonify({'error': 'Question is required'}), 400
        
        print(f"[AI] Processing question: {user_question[:50]}...")
        
        # Check if we have transaction data
        has_data = stored_transactions_df is not None and len(stored_transactions_df) > 0
        
        if has_data:
            print(f"[DATA] Using transaction data with {len(stored_transactions_df)} transactions")
            
            # Build financial summary using pandas
            income_df = stored_transactions_df[stored_transactions_df['category'] == 'Income']
            expense_df = stored_transactions_df[stored_transactions_df['category'] != 'Income']
            
            total_income = income_df['amount'].sum()
            total_expenses = expense_df['amount'].sum()
            
            # Category breakdown
            expense_breakdown = expense_df.groupby('category')['amount'].sum().to_dict()
            
            breakdown_text = "\n".join([
                f"- {cat}: ₹{amt:.2f}" for cat, amt in expense_breakdown.items()
            ])
            
            # Get top transactions
            top_expenses = expense_df.nlargest(5, 'amount')[['description', 'amount', 'category']].to_dict('records')
            top_expenses_text = "\n".join([
                f"- {exp['description']}: ₹{exp['amount']:.2f} ({exp['category']})" 
                for exp in top_expenses
            ])
            
            # Create context-aware prompt with user's data
            prompt = f"""You are a helpful financial advisor for SnapSpend. The user has uploaded their transaction data. Here's their financial summary:

📊 Financial Overview:
- Total Income: ₹{total_income:.2f}
- Total Expenses: ₹{total_expenses:.2f}
- Net Savings: ₹{(total_income - total_expenses):.2f}

💰 Spending by Category:
{breakdown_text}

🔝 Top 5 Expenses:
{top_expenses_text}

User Question: "{user_question}"

Provide a helpful, personalized answer based on their actual transaction data. Be specific and reference their spending patterns when relevant. Keep it conversational and actionable (2-4 sentences). Use plain text, no bold or formatting."""
        else:
            print("[INFO] No transaction data available, providing general advice")
            # General financial advice prompt
            prompt = f"""You are a helpful financial advisor for SnapSpend, a personal finance management app. The user hasn't uploaded their transaction data yet, so provide general financial advice.

User Question: "{user_question}"

Provide helpful financial advice or information. Keep your response concise and practical (2-4 sentences). Focus on actionable financial advice. Use plain text, no bold or formatting."""
        
        if model is None:
            answer = "I'm currently unable to process your question. The AI service is not configured. However, I can see you have data uploaded. Please check the Transaction Analyzer for detailed insights."
            print("[WARN] Gemini model not initialized")
        else:
            try:
                response = model.generate_content(prompt)
                answer = response.text.strip()
            except Exception as ai_error:
                print(f"[ERROR] Gemini API error: {str(ai_error)}")
                # Fallback response
                if has_data:
                    answer = f"Based on your data: You have ₹{total_income:.2f} income and ₹{total_expenses:.2f} expenses. Your top spending category is {list(expense_breakdown.keys())[0] if expense_breakdown else 'unknown'}. Consider reviewing your spending in the Transaction Analyzer for detailed insights."
                else:
                    answer = "I'm having trouble connecting to the AI service. Please try uploading your CSV in the Transaction Analyzer first, or try again later."
        
        print("[OK] AI response generated")
        return jsonify({
            'answer': answer,
            'hasData': has_data
        })
        
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to answer question', 'details': str(e)}), 500

@app.route('/generate-nudges', methods=['POST'])
def generate_nudges():
    """Generate humorous nudges based on budget limits"""
    try:
        data = request.get_json()
        budgets = data.get('budgets', [])
        
        nudges = []
        
        humorous_messages = {
            'high': [
                "🚨 BREAKING: Your {category} budget just called 911!",
                "[WARN] Plot twist: Your wallet is filing for bankruptcy because of {category}!",
                "🎭 {category} spending at {percentage}%! Even your bank account is shocked!",
                "🔥 Your {category} expenses are on fire! And not in a good way!",
                "💸 Houston, we have a problem! {category} budget is in the danger zone!",
                "🆘 Your {category} spending needs an intervention. Like, right now!"
            ],
            'medium': [
                "[DATA] {category} at {percentage}%. Time to pump the brakes a little!",
                "💡 Fun fact: You're {percentage}% through your {category} budget!",
                "⚡ {category} spending is heating up. Cool it down a bit?",
                "🎯 {category} budget halfway gone. Let's be strategic here!",
                "⏰ Tick tock! {category} budget is running out faster than expected!"
            ],
            'low': [
                "🎉 {category} budget looking good! You're a financial ninja!",
                "⭐ Crushing it! Only {percentage}% of {category} budget used!",
                "🏆 {category} spending is under control. You're a legend!",
                "💪 {category} game strong! Keep up the excellent work!",
                "✨ {category} spending? More like {category} SAVING! Nice job!"
            ]
        }
        
        for budget in budgets:
            percentage = (budget['spent'] / budget['limit']) * 100
            
            if percentage >= 90:
                message_type = 'high'
            elif percentage >= 50:
                message_type = 'medium'
            else:
                message_type = 'low'
            
            message_template = random.choice(humorous_messages[message_type])
            message = message_template.replace('{category}', budget['category']).replace('{percentage}', str(int(percentage)))
            
            nudges.append({
                'category': budget['category'],
                'message': message,
                'type': 'danger' if percentage >= 90 else 'warning' if percentage >= 75 else 'success',
                'percentage': int(percentage),
                'remaining': budget['limit'] - budget['spent']
            })
        
        return jsonify({'nudges': nudges})
        
    except Exception as e:
        print(f"[ERROR] Error generating nudges: {str(e)}")
        return jsonify({'error': 'Failed to generate nudges'}), 500

@app.route('/predict-overspending', methods=['POST'])
def predict_overspending():
    """Predict future overspending using pandas analysis"""
    global stored_transactions_df
    
    try:
        if stored_transactions_df is None or len(stored_transactions_df) == 0:
            return jsonify({'error': 'No transactions available. Upload CSV first.'}), 400
        
        # Get current date info
        df = stored_transactions_df.copy()
        df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
        df['day'] = df['date_parsed'].dt.day
        
        # Calculate current day and days in month
        valid_days = df['day'].dropna()
        if len(valid_days) == 0:
            return jsonify({'error': 'No valid dates found'}), 400
        
        current_day = int(valid_days.max())
        days_in_month = 30  # Assume 30 days
        
        # Calculate spending velocity
        expense_df = df[df['category'] != 'Income']
        total_spent = expense_df['amount'].sum()
        
        daily_average = total_spent / current_day if current_day > 0 else 0
        projected_monthly_spend = daily_average * days_in_month
        
        # Category-wise predictions
        category_predictions = []
        for category in expense_df['category'].unique():
            cat_df = expense_df[expense_df['category'] == category]
            cat_spent = cat_df['amount'].sum()
            cat_daily_avg = cat_spent / current_day if current_day > 0 else 0
            cat_projected = cat_daily_avg * days_in_month
            
            category_predictions.append({
                'category': category,
                'currentSpent': float(cat_spent),
                'projectedSpend': int(cat_projected),
                'dailyAverage': int(cat_daily_avg)
            })
        
        # Generate warnings
        warnings = []
        if projected_monthly_spend > total_spent * 1.5:
            overspend_pct = int(((projected_monthly_spend / total_spent) - 1) * 100)
            warnings.append({
                'type': 'danger',
                'message': f"[WARN] At your current pace, you'll spend ₹{int(projected_monthly_spend)} this month! That's {overspend_pct}% more than expected!"
            })
        
        # Check category-wise overspending
        for pred in category_predictions:
            if pred['projectedSpend'] > pred['currentSpent'] * 2:
                warnings.append({
                    'type': 'warning',
                    'message': f"[DATA] {pred['category']} spending is accelerating! Projected: ₹{pred['projectedSpend']}"
                })
        
        return jsonify({
            'currentDay': current_day,
            'daysInMonth': days_in_month,
            'totalSpent': int(total_spent),
            'dailyAverage': int(daily_average),
            'projectedMonthlySpend': int(projected_monthly_spend),
            'predictions': category_predictions,
            'warnings': warnings
        })
        
    except Exception as e:
        print(f"[ERROR] Error predicting overspending: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to predict overspending', 'details': str(e)}), 500

@app.route('/suggest-alternatives', methods=['POST'])
def suggest_alternatives():
    """Suggest smart spending alternatives"""
    global stored_transactions_df
    
    try:
        if stored_transactions_df is None or len(stored_transactions_df) == 0:
            return jsonify({'error': 'No transactions available. Upload CSV first.'}), 400
        
        # Analyze spending patterns
        df = stored_transactions_df.copy()
        expense_df = df[df['category'] != 'Income']
        
        # Count food delivery orders
        food_delivery_count = len(expense_df[
            expense_df['description'].str.lower().str.contains('swiggy|zomato', na=False)
        ])
        
        # Count coffee purchases
        coffee_count = len(expense_df[
            expense_df['description'].str.lower().str.contains('starbucks|cafe|coffee', na=False)
        ])
        
        # Count cab rides
        cab_count = len(expense_df[
            expense_df['description'].str.lower().str.contains('uber|ola|taxi', na=False)
        ])
        
        alternatives = [
            {
                'category': 'Food',
                'current': 'Food Delivery (Swiggy/Zomato)',
                'currentCost': 800,
                'alternative': 'Cook at Home',
                'alternativeCost': 200,
                'savings': 600,
                'monthlySavings': 18000,
                'icon': '🍳',
                'tip': f"You ordered food delivery {food_delivery_count} times! Meal prep on Sundays to save time and money!"
            },
            {
                'category': 'Travel',
                'current': 'Uber/Ola',
                'currentCost': 250,
                'alternative': 'Metro/Bus',
                'alternativeCost': 40,
                'savings': 210,
                'monthlySavings': 6300,
                'icon': '🚇',
                'tip': f"You took {cab_count} cab rides! Public transport is faster during rush hour!"
            },
            {
                'category': 'Food',
                'current': 'Daily Starbucks Coffee',
                'currentCost': 300,
                'alternative': 'Home Coffee',
                'alternativeCost': 30,
                'savings': 270,
                'monthlySavings': 8100,
                'icon': '☕',
                'tip': f"You bought coffee {coffee_count} times! Invest in a good coffee maker - pays for itself in 2 weeks!"
            },
            {
                'category': 'Shopping',
                'current': 'Impulse Online Shopping',
                'currentCost': 2000,
                'alternative': 'Wait 24 Hours Rule',
                'alternativeCost': 500,
                'savings': 1500,
                'monthlySavings': 1500,
                'icon': '🛍️',
                'tip': 'Add to cart, wait 24 hours. Still want it? Then buy!'
            },
            {
                'category': 'Bills',
                'current': 'Multiple Streaming Services',
                'currentCost': 1500,
                'alternative': 'Share Family Plans',
                'alternativeCost': 500,
                'savings': 1000,
                'monthlySavings': 1000,
                'icon': '📺',
                'tip': 'Split Netflix, Prime, Hotstar with friends!'
            }
        ]
        
        total_monthly_savings = sum(alt['monthlySavings'] for alt in alternatives)
        yearly_projection = total_monthly_savings * 12
        
        return jsonify({
            'alternatives': alternatives,
            'totalMonthlySavings': total_monthly_savings,
            'yearlyProjection': yearly_projection,
            'message': f"💰 You could save ₹{total_monthly_savings:,}/month (₹{yearly_projection:,}/year) with these smart choices!"
        })
        
    except Exception as e:
        print(f"[ERROR] Error suggesting alternatives: {str(e)}")
        return jsonify({'error': 'Failed to suggest alternatives'}), 500

@app.route('/check-achievements', methods=['GET'])
def check_achievements():
    """Check gamification achievements"""
    global stored_transactions_df
    
    try:
        if stored_transactions_df is None or len(stored_transactions_df) == 0:
            return jsonify({'error': 'No transactions available. Upload CSV first.'}), 400
        
        df = stored_transactions_df.copy()
        expense_df = df[df['category'] != 'Income']
        
        # Calculate metrics
        food_delivery_count = len(expense_df[
            expense_df['description'].str.lower().str.contains('swiggy|zomato', na=False)
        ])
        
        total_expenses = expense_df['amount'].sum()
        total_income = df[df['category'] == 'Income']['amount'].sum()
        savings = total_income - total_expenses
        
        achievements = [
            {
                'id': 'budget_saver',
                'title': 'Budget Saver',
                'description': 'Stay under budget for 7 consecutive days',
                'icon': '🏆',
                'unlocked': savings > 5000,
                'progress': min(100, int((savings / 5000) * 100)),
                'reward': 'Financial Ninja Badge'
            },
            {
                'id': 'no_delivery',
                'title': 'No-Delivery Streak',
                'description': '7 days without food delivery orders',
                'icon': '🔥',
                'unlocked': food_delivery_count == 0,
                'progress': max(0, 100 - (food_delivery_count * 14)),
                'reward': 'Home Chef Badge'
            },
            {
                'id': 'savings_champion',
                'title': 'Savings Champion',
                'description': 'Save ₹5,000 in a single month',
                'icon': '💎',
                'unlocked': savings >= 5000,
                'progress': min(100, int((savings / 5000) * 100)),
                'reward': 'Money Master Badge'
            },
            {
                'id': 'financial_levelup',
                'title': 'Financial Level Up',
                'description': 'Improve financial score by 20 points',
                'icon': '⭐',
                'unlocked': True,
                'progress': 100,
                'reward': 'Score Booster Badge'
            },
            {
                'id': 'smart_spender',
                'title': 'Smart Spender',
                'description': 'Use 3 cost-saving alternatives in a week',
                'icon': '🧠',
                'unlocked': False,
                'progress': 33,
                'reward': 'Wise Wallet Badge'
            }
        ]
        
        unlocked_count = sum(1 for a in achievements if a['unlocked'])
        total_points = unlocked_count * 100
        
        return jsonify({
            'achievements': achievements,
            'unlockedCount': unlocked_count,
            'totalAchievements': len(achievements),
            'totalPoints': total_points,
            'level': (total_points // 200) + 1,
            'nextLevelPoints': (((total_points // 200) + 1) * 200) - total_points
        })
        
    except Exception as e:
        print(f"[ERROR] Error checking achievements: {str(e)}")
        return jsonify({'error': 'Failed to check achievements'}), 500

@app.route('/api/recent-transactions', methods=['GET'])
def get_recent_transactions():
    """Get recent transactions for dashboard"""
    global stored_transactions_df
    
    try:
        if stored_transactions_df is None or len(stored_transactions_df) == 0:
            return jsonify({
                'transactions': [],
                'message': 'No data available. Upload CSV first.'
            })
        
        # Get recent transactions (last 10)
        df = stored_transactions_df.copy()
        df = df[df['category'] != 'Income']  # Exclude income
        
        # Sort by date if possible
        try:
            df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.sort_values('date_parsed', ascending=False).head(10)
        except:
            df = df.head(10)
        
        transactions = []
        for idx, row in df.iterrows():
            transactions.append({
                'id': f"tx_{idx}",
                'date': str(row['date']),
                'description': row['description'],
                'amount': float(row['amount']),
                'category': row['category']
            })
        
        print(f"[OK] Returning {len(transactions)} recent transactions")
        return jsonify({
            'transactions': transactions,
            'count': len(transactions)
        })
        
    except Exception as e:
        print(f"[ERROR] Error fetching recent transactions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch transactions', 'details': str(e)}), 500

@app.route('/api/category-totals', methods=['GET'])
def get_category_totals():
    """Get category-wise spending totals"""
    global stored_transactions_df
    
    try:
        if stored_transactions_df is None or len(stored_transactions_df) == 0:
            return jsonify({
                'categories': [],
                'message': 'No data available. Upload CSV first.'
            })
        
        df = stored_transactions_df.copy()
        expense_df = df[df['category'] != 'Income']
        
        # Calculate category totals
        category_totals = expense_df.groupby('category')['amount'].sum()
        total_expenses = category_totals.sum()
        
        categories = []
        colors = ['#64748b', '#475569', '#334155', '#1e293b', '#0f172a', '#94a3b8', '#cbd5e1']
        
        for i, (category, total) in enumerate(category_totals.items()):
            percentage = (total / total_expenses * 100) if total_expenses > 0 else 0
            categories.append({
                'category': category,
                'total': float(total),
                'percentage': round(percentage, 1),
                'color': colors[i % len(colors)]
            })
        
        # Sort by total descending
        categories.sort(key=lambda x: x['total'], reverse=True)
        
        print(f"[OK] Returning {len(categories)} category totals")
        return jsonify({
            'categories': categories,
            'totalExpenses': float(total_expenses)
        })
        
    except Exception as e:
        print(f"[ERROR] Error fetching category totals: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch category totals', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n[START] Python Flask server starting on port {port}")
    print(f"[API] API endpoints:")
    print(f"   - GET  http://localhost:{port}/api/hello")
    print(f"   - POST http://localhost:{port}/analyze-transactions")
    print(f"   - POST http://localhost:{port}/ask-question")
    print(f"   - POST http://localhost:{port}/generate-nudges")
    print(f"   - POST http://localhost:{port}/predict-overspending")
    print(f"   - POST http://localhost:{port}/suggest-alternatives")
    print(f"   - GET  http://localhost:{port}/check-achievements")
    print(f"   - GET  http://localhost:{port}/api/recent-transactions")
    print(f"   - GET  http://localhost:{port}/api/category-totals")
    print(f"\n[OK] CORS enabled for all origins")
    print(f"[KEY] Gemini API Key: {'✓ Configured' if os.getenv('GEMINI_API_KEY') else '✗ Missing'}\n")
    
    app.run(debug=True, host='0.0.0.0', port=port)

