import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageCircle, ArrowLeft, Send, Bot, User, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

interface ChatMessage {
  question: string;
  answer: string;
  timestamp: Date;
}

export default function FinancialChatbot() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [hasData, setHasData] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";

  // Check if data is loaded on mount
  React.useEffect(() => {
    const checkData = async () => {
      try {
        const response = await axios.get(`${apiUrl}/api/check-data`);
        setHasData(response.data.loaded);
      } catch (error) {
        console.log("No data loaded yet");
      }
    };
    checkData();
  }, [apiUrl]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const suggestedQuestions = [
    "How much did I spend on food?",
    "What's my biggest spending category?",
    "Am I overspending?",
    "Give me tips to save money based on my data",
    "What are my top 3 expenses?",
    "How can I reduce my spending?",
    "What's my spending pattern?",
    "Should I be worried about my expenses?"
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    const userQuestion = question;
    setQuestion("");

    const tempMessage: ChatMessage = {
      question: userQuestion,
      answer: "",
      timestamp: new Date()
    };
    setChatHistory((prev) => [...prev, tempMessage]);

    try {
      console.log("💬 Asking chatbot:", userQuestion);
      
      const response = await axios.post(`${apiUrl}/ask-question`, {
        question: userQuestion,
      });

      const newAnswer = response.data.answer;
      console.log("✅ Chatbot response received");
      
      // Update hasData status if returned
      if (response.data.hasData !== undefined) {
        setHasData(response.data.hasData);
      }
      
      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          answer: newAnswer
        };
        return updated;
      });
      
    } catch (error: any) {
      console.error("❌ Chat error:", error);
      const errorMessage = error.response?.data?.error || error.message;
      
      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          answer: `⚠️ ${errorMessage}\n\nPlease try again or ask a different question.`
        };
        return updated;
      });
      
      toast.error("Failed to get response");
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (suggested: string) => {
    setQuestion(suggested);
  };

  const clearChat = () => {
    setChatHistory([]);
    toast.success("Chat cleared");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-2 sm:p-4">
      <div className="max-w-4xl mx-auto">
        <Card className="shadow-2xl border-0 min-h-[85vh] flex flex-col">
          <CardHeader className="border-b border-gray-200 bg-gradient-to-r from-blue-600 to-purple-600 rounded-t-lg p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="h-6 w-6 sm:h-7 sm:w-7 text-blue-600" />
                </div>
                <div>
                  <CardTitle className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
                    AI Chat Assistant
                    <Sparkles className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-300" />
                  </CardTitle>
                  <p className="text-blue-100 mt-1 text-xs sm:text-sm">
                    Powered by Google Gemini AI {hasData && "• 📊 Data Loaded"}
                  </p>
                </div>
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                {chatHistory.length > 0 && (
                  <Button
                    onClick={clearChat}
                    variant="outline"
                    size="sm"
                    className="bg-white/10 text-white border-white/20 hover:bg-white/20 flex-1 sm:flex-none"
                  >
                    Clear
                  </Button>
                )}
                <Button
                  onClick={() => window.location.href = "/"}
                  variant="outline"
                  size="sm"
                  className="bg-white/10 text-white border-white/20 hover:bg-white/20 flex-1 sm:flex-none"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-6" style={{ maxHeight: "calc(85vh - 200px)" }}>
            {chatHistory.length === 0 ? (
              <div className="text-center py-8 sm:py-12">
                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6">
                  <MessageCircle className="h-8 w-8 sm:h-10 sm:w-10 text-blue-600" />
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-gray-900 mb-2 sm:mb-3">
                  Start a conversation!
                </h3>
                <p className="text-sm sm:text-base text-gray-600 mb-6 sm:mb-8 px-4">
                  {hasData 
                    ? "Ask me anything about your uploaded transactions and spending patterns" 
                    : "Ask me about personal finance, or upload your CSV in the Analyzer for personalized insights"}
                </p>
                <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4 sm:p-6 max-w-2xl mx-auto">
                  <h4 className="font-semibold text-blue-900 mb-3 sm:mb-4 text-base sm:text-lg">Try asking:</h4>
                  <div className="grid grid-cols-1 gap-2 sm:gap-3">
                    {suggestedQuestions.map((q, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestedQuestion(q)}
                        className="text-left text-xs sm:text-sm text-blue-800 bg-white hover:bg-blue-100 p-2 sm:p-3 rounded-lg transition-colors border border-blue-200 hover:border-blue-400"
                      >
                        💡 {q}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <>
                {chatHistory.map((chat, index) => (
                  <div key={index} className="space-y-4">
                    <div className="flex justify-end">
                      <div className="flex items-start gap-3 max-w-[80%]">
                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl rounded-tr-sm px-5 py-3 shadow-md">
                          <p className="text-sm leading-relaxed">{chat.question}</p>
                          <p className="text-xs text-blue-100 mt-2">
                            {chat.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                          <User className="h-4 w-4 text-white" />
                        </div>
                      </div>
                    </div>

                    {chat.answer ? (
                      <div className="flex justify-start">
                        <div className="flex items-start gap-3 max-w-[80%]">
                          <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                            <Bot className="h-4 w-4 text-white" />
                          </div>
                          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-5 py-3 shadow-md">
                            <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                              {chat.answer}
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="flex justify-start">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                            <Bot className="h-4 w-4 text-white" />
                          </div>
                          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-5 py-3 shadow-md">
                            <div className="flex items-center gap-2">
                              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                              <p className="text-sm text-gray-600">Thinking...</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </CardContent>

          <div className="border-t border-gray-200 p-3 sm:p-4 bg-white rounded-b-lg">
            <form onSubmit={handleSubmit} className="flex gap-2 sm:gap-3">
              <Input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask me about budgeting, saving, or financial tips..."
                className="flex-1 text-sm sm:text-base py-4 sm:py-6 px-3 sm:px-4 rounded-xl border-2 border-gray-200 focus:border-blue-500"
                disabled={loading}
              />
              <Button
                type="submit"
                disabled={loading || !question.trim()}
                className="px-4 sm:px-6 py-4 sm:py-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl flex-shrink-0"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                ) : (
                  <Send className="h-4 w-4 sm:h-5 sm:w-5" />
                )}
              </Button>
            </form>
            <p className="text-xs text-gray-500 mt-2 text-center px-2">
              {hasData 
                ? "💡 AI is analyzing your transaction data for personalized advice" 
                : "💡 Upload your CSV in the Analyzer for personalized insights based on your data"}
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
