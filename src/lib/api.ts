import { supabase } from "@/integrations/supabase/client";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Get auth headers with Supabase token
 */
async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  
  if (!session?.access_token) {
    throw new Error("Not authenticated. Please login.");
  }
  
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json'
  };
}

/**
 * Upload CSV file and analyze transactions
 */
export async function analyzeTransactions(file: File) {
  const { data: { session } } = await supabase.auth.getSession();
  
  if (!session?.access_token) {
    throw new Error("Not authenticated. Please login.");
  }
  
  const formData = new FormData();
  formData.append("csvFile", file);
  
  const response = await fetch(`${API_URL}/api/analyze-transactions`, {
    method: "POST",
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    },
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errorData.error || errorData.details || 'Upload failed');
  }
  
  return await response.json();
}

/**
 * Ask AI chatbot a question
 */
export async function askQuestion(question: string) {
  const headers = await getAuthHeaders();
  
  const response = await axios.post(
    `${API_URL}/api/ask-question`,
    { question },
    { headers }
  );
  
  return response.data;
}

/**
 * Check if user has uploaded data
 */
export async function checkData() {
  const headers = await getAuthHeaders();
  
  const response = await axios.get(
    `${API_URL}/api/check-data`,
    { headers }
  );
  
  return response.data;
}

/**
 * Get recent transactions
 */
export async function getRecentTransactions() {
  const headers = await getAuthHeaders();
  
  const response = await axios.get(
    `${API_URL}/api/recent-transactions`,
    { headers }
  );
  
  return response.data;
}

/**
 * Get category totals
 */
export async function getCategoryTotals() {
  const headers = await getAuthHeaders();
  
  const response = await axios.get(
    `${API_URL}/api/category-totals`,
    { headers }
  );
  
  return response.data;
}
