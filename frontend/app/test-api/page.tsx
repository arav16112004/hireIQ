"use client";

import { useState } from 'react';
import apiClient from '@/lib/api';

export default function TestAPIPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testHealth = async () => {
    setLoading(true);
    try {
      const res = await apiClient.health();
      setResult({ success: true, data: res.data });
    } catch (error: any) {
      setResult({ success: false, error: error.message, details: error.response?.data });
    } finally {
      setLoading(false);
    }
  };

  const testRegister = async () => {
    setLoading(true);
    try {
      const res = await apiClient.auth.register({
        email: 'test@example.com',
        password: 'testpass123',
        name: 'Test User',
        role: 'candidate'
      });
      setResult({ success: true, data: res.data });
    } catch (error: any) {
      setResult({ 
        success: false, 
        error: error.message, 
        details: error.response?.data,
        status: error.response?.status 
      });
    } finally {
      setLoading(false);
    }
  };

  const testLogin = async () => {
    setLoading(true);
    try {
      const res = await apiClient.auth.login('test@example.com', 'testpass123');
      setResult({ success: true, data: res.data });
    } catch (error: any) {
      setResult({ 
        success: false, 
        error: error.message, 
        details: error.response?.data,
        status: error.response?.status 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">API Test Page</h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Test Endpoints</h2>
          
          <div className="space-y-4">
            <button
              onClick={testHealth}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Test Health
            </button>

            <button
              onClick={testRegister}
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 ml-2"
            >
              Test Register
            </button>

            <button
              onClick={testLogin}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 ml-2"
            >
              Test Login
            </button>
          </div>
        </div>

        {result && (
          <div className={`rounded-lg shadow p-6 ${result.success ? 'bg-green-50' : 'bg-red-50'}`}>
            <h3 className="font-semibold mb-2">
              {result.success ? '✅ Success' : '❌ Error'}
            </h3>
            <pre className="bg-gray-900 text-green-400 p-4 rounded overflow-auto text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

