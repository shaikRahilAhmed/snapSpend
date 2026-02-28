
import React, { useState, useRef } from "react";
import { Line, Bar, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Title,
} from "chart.js";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, MessageCircle, TrendingUp, TrendingDown, DollarSign, Target } from "lucide-react";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Title
);

interface Transaction {
  description: string;
  category: string;
  amount: number;
  date: string;
}

interface AnalyticsData {
  totalInflow: number;
  totalOutflow: number;
  oneTimeExpenses: Transaction[];
  billCalendar: { description: string; date: string }[];
  reduceAdvice: string[];
  halfMonthComparison: { firstHalf: number; secondHalf: number };
  top3Spends: number[];
  score: number;
  simulatedSavedAmount: string;
  aiTip: string;
}

interface ApiResponse {
  categorized: Transaction[];
  analytics: AnalyticsData;
}

export default function TransactionAnalyzer() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    console.log("📁 File selected:", file.name);
    setLoading(true);
    const formData = new FormData();
    formData.append("csvFile", file);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";
      console.log("🌐 Uploading to:", `${apiUrl}/analyze-transactions`);
      
      const response = await fetch(`${apiUrl}/analyze-transactions`, {
        method: "POST",
        body: formData,
      });
      
      console.log("📡 Response status:", response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
        console.error("❌ Upload failed:", errorData);
        throw new Error(errorData.error || errorData.details || 'Upload failed');
      }
      
      const result = await response.json();
      console.log("✅ Upload successful, transactions:", result.categorized?.length);
      
      if (result.warning) {
        console.warn("⚠️", result.warning);
        alert(`⚠️ ${result.warning}\n\nYour transactions have been categorized using basic rules. The app will still work normally!`);
      }
      
      setData(result);
    } catch (error: any) {
      console.error('❌ Upload error:', error);
      alert(`Upload failed: ${error.message}\n\nPlease check:\n1. Backend is running on port 5000\n2. CSV file format is correct\n3. Browser console for details`);
    } finally {
      setLoading(false);
    }
  };

  const getDayWiseExpenditureData = () => {
    if (!data) return { labels: [], datasets: [] };
    
    const dayMap: { [key: number]: number } = {};
    data.categorized.forEach((transaction) => {
      if (transaction.category !== "Income") {
        const day = parseInt(transaction.date.split("-")[2], 10);
        if (!dayMap[day]) dayMap[day] = 0;
        dayMap[day] += transaction.amount;
      }
    });

    const days = Array.from({ length: 31 }, (_, i) => i + 1);
    const expenditures = days.map((day) => dayMap[day] || 0);

    return {
      labels: days,
      datasets: [
        {
          label: "Daily Expenditure (₹)",
          data: expenditures,
          fill: false,
          borderColor: "#3b82f6",
          backgroundColor: "#3b82f6",
          pointRadius: 4,
          tension: 0.2,
        },
      ],
    };
  };

  const getCategorySpendingData = () => {
    if (!data) return { labels: [], datasets: [] };
    
    const categoryTotals: { [key: string]: number } = {};
    data.categorized.forEach((transaction) => {
      if (!categoryTotals[transaction.category]) {
        categoryTotals[transaction.category] = 0;
      }
      categoryTotals[transaction.category] += transaction.amount;
    });

    const categories = Object.keys(categoryTotals);
    const amounts = categories.map((category) => categoryTotals[category]);
    const colors = [
      "#ef4444", "#f97316", "#eab308", "#22c55e", 
      "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899"
    ];

    return {
      labels: categories,
      datasets: [
        {
          label: "Amount Spent (₹)",
          data: amounts,
          backgroundColor: colors.slice(0, categories.length),
          borderWidth: 2,
          borderColor: "#ffffff",
        },
      ],
    };
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-2 sm:p-4">
      <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8">
        {/* Header */}
        <div className="text-center space-y-3 sm:space-y-4 px-2">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
            Transaction Analyzer
          </h1>
          <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your CSV file to get AI-powered insights into your spending patterns and financial habits
          </p>
        </div>

        {/* Upload Section */}
        <Card className="shadow-xl border-0">
          <CardContent className="p-4 sm:p-8">
            <div className="flex flex-col gap-3 sm:gap-4">
              <input
                type="file"
                accept=".csv"
                ref={fileInput}
                className="hidden"
                onChange={handleFileUpload}
              />
              <Button
                onClick={() => fileInput.current?.click()}
                disabled={loading}
                size="lg"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 sm:px-8 py-4 sm:py-6 w-full sm:w-auto text-sm sm:text-base"
              >
                <Upload className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                {loading ? "Analyzing..." : "Upload CSV File"}
              </Button>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Button
                  onClick={() => window.location.href = "/chatbot"}
                  variant="outline"
                  size="lg"
                  className="px-6 sm:px-8 py-4 sm:py-6 w-full sm:w-auto text-sm sm:text-base"
                >
                  <MessageCircle className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                  AI Chat
                </Button>
                <Button
                  onClick={() => window.location.href = "/nudge"}
                  size="lg"
                  className="bg-purple-600 hover:bg-purple-700 text-white px-6 sm:px-8 py-4 sm:py-6 w-full sm:w-auto text-sm sm:text-base"
                >
                  <Target className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                  Budget Nudge Dashboard
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {data && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              <Card className="shadow-lg border-0">
                <CardHeader className="pb-2 sm:pb-3">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600 flex items-center">
                    <TrendingUp className="mr-2 h-3 w-3 sm:h-4 sm:w-4 text-green-600" />
                    Total Income
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl sm:text-3xl font-bold text-green-600">
                    {formatCurrency(data.analytics.totalInflow)}
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-lg border-0">
                <CardHeader className="pb-2 sm:pb-3">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600 flex items-center">
                    <TrendingDown className="mr-2 h-3 w-3 sm:h-4 sm:w-4 text-red-600" />
                    Total Expenses
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl sm:text-3xl font-bold text-red-600">
                    {formatCurrency(data.analytics.totalOutflow)}
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-lg border-0">
                <CardHeader className="pb-2 sm:pb-3">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600 flex items-center">
                    <DollarSign className="mr-2 h-3 w-3 sm:h-4 sm:w-4 text-blue-600" />
                    First Half Spending
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-xl sm:text-2xl font-bold text-gray-900">
                    {formatCurrency(data.analytics.halfMonthComparison.firstHalf)}
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-lg border-0">
                <CardHeader className="pb-2 sm:pb-3">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600 flex items-center">
                    <Target className="mr-2 h-3 w-3 sm:h-4 sm:w-4 text-purple-600" />
                    Financial Score
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl sm:text-3xl font-bold text-purple-600">
                    {data.analytics.score}/100
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* AI Insights */}
            <Card className="shadow-xl border-0 bg-gradient-to-r from-blue-50 to-indigo-50">
              <CardHeader>
                <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                  <MessageCircle className="mr-2 h-5 w-5 text-blue-600" />
                  AI Financial Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <h4 className="font-semibold text-gray-900 mb-2">Smart Recommendation</h4>
                  <p className="text-gray-700 italic leading-relaxed">{data.analytics.aiTip}</p>
                </div>
                
                {data.analytics.reduceAdvice.length > 0 && (
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <h4 className="font-semibold text-gray-900 mb-3">Money Saving Opportunities</h4>
                    <ul className="space-y-2">
                      {data.analytics.reduceAdvice.map((advice, index) => (
                        <li key={index} className="flex items-start">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <span className="text-gray-700">{advice}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Daily Spending Trend */}
              <Card className="shadow-xl border-0">
                <CardHeader>
                  <CardTitle className="text-xl font-bold text-gray-900">Daily Spending Trend</CardTitle>
                  <CardDescription>Track your daily expenditure throughout the month</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <Line
                      data={getDayWiseExpenditureData()}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false },
                          tooltip: {
                            callbacks: {
                              label: (context) => `₹${context.parsed.y.toLocaleString()}`
                            }
                          }
                        },
                        scales: {
                          x: { 
                            title: { display: true, text: "Day of Month", font: { weight: 'bold' } },
                            grid: { display: false }
                          },
                          y: { 
                            title: { display: true, text: "Amount (₹)", font: { weight: 'bold' } },
                            ticks: {
                              callback: (value) => `₹${Number(value).toLocaleString()}`
                            }
                          },
                        },
                      }}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Category Breakdown */}
              <Card className="shadow-xl border-0">
                <CardHeader>
                  <CardTitle className="text-xl font-bold text-gray-900">Spending by Category</CardTitle>
                  <CardDescription>See where your money goes across different categories</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <Bar
                      data={getCategorySpendingData()}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false },
                          tooltip: {
                            callbacks: {
                              label: (context) => `₹${context.parsed.y.toLocaleString()}`
                            }
                          }
                        },
                        scales: {
                          x: { 
                            title: { display: true, text: "Category", font: { weight: 'bold' } },
                            grid: { display: false }
                          },
                          y: { 
                            title: { display: true, text: "Amount (₹)", font: { weight: 'bold' } },
                            ticks: {
                              callback: (value) => `₹${Number(value).toLocaleString()}`
                            }
                          },
                        },
                      }}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Category Distribution Pie Chart */}
            <Card className="shadow-xl border-0">
              <CardHeader>
                <CardTitle className="text-xl font-bold text-gray-900 text-center">
                  Category Distribution Overview
                </CardTitle>
                <CardDescription className="text-center">
                  Visual breakdown of your spending across all categories
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-w-lg mx-auto h-96">
                  <Pie
                    data={getCategorySpendingData()}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { 
                          position: "bottom",
                          labels: { padding: 20, usePointStyle: true }
                        },
                        tooltip: {
                          callbacks: {
                            label: (context) => {
                              const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                              const percentage = ((context.parsed * 100) / total).toFixed(1);
                              return `${context.label}: ₹${context.parsed.toLocaleString()} (${percentage}%)`;
                            }
                          }
                        }
                      },
                    }}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Transaction History */}
            <Card className="shadow-xl border-0">
              <CardHeader>
                <CardTitle className="text-xl font-bold text-gray-900">Transaction History</CardTitle>
                <CardDescription>All your categorized transactions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Description
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data.categorized.map((transaction, index) => (
                        <tr key={index} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 text-sm text-gray-900">
                            {transaction.description}
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {transaction.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-gray-900">
                            {formatCurrency(transaction.amount)}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {transaction.date}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
