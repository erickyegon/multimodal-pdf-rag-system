import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Simple components that work immediately
const Sidebar = () => {
  const location = useLocation();
  
  return (
    <div className="w-64 bg-white shadow-lg">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold text-gray-800">PDF RAG System</h1>
      </div>
      <nav className="p-4">
        <div className="space-y-2">
          <Link
            to="/"
            className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              location.pathname === '/' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            💬 Chat
          </Link>
          <Link
            to="/upload"
            className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              location.pathname === '/upload' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            📤 Upload
          </Link>
          <Link
            to="/analytics"
            className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              location.pathname === '/analytics' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            📊 Analytics
          </Link>
        </div>
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Documents</h3>
          <div className="text-center py-4">
            <div className="text-gray-300 mb-2">📄</div>
            <p className="text-sm text-gray-500">No documents uploaded</p>
            <Link to="/upload" className="text-xs text-blue-600 hover:text-blue-700 mt-1 inline-block">
              Upload your first document
            </Link>
          </div>
        </div>
      </nav>
    </div>
  );
};

const ChatPage = () => (
  <div className="flex-1 flex flex-col">
    <header className="bg-white shadow-sm border-b px-6 py-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">Chat Interface</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-green-600">Connected</span>
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
        </div>
      </div>
    </header>
    <main className="flex-1 flex flex-col p-6">
      <div className="flex-1 bg-white rounded-lg shadow-sm border p-6">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🤖</div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Welcome to PDF RAG System</h3>
          <p className="text-gray-600 mb-6">Upload a PDF document to start asking questions about its content.</p>
          <Link to="/upload" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors inline-block">
            Upload Your First Document
          </Link>
        </div>
      </div>
      <div className="mt-4 bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center space-x-4">
          <input 
            type="text" 
            placeholder="Ask a question about your documents..." 
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled
          />
          <button className="bg-gray-400 text-white px-6 py-2 rounded-lg cursor-not-allowed" disabled>
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">Upload a document first to enable chat functionality</p>
      </div>
    </main>
  </div>
);

const UploadPage = () => (
  <div className="flex-1 p-6">
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload Documents</h2>
      <div className="bg-white rounded-lg shadow-sm border-2 border-dashed border-gray-300 p-12 text-center">
        <div className="text-6xl mb-4">📄</div>
        <h3 className="text-xl font-semibold text-gray-800 mb-2">Drag and drop your PDF files here</h3>
        <p className="text-gray-600 mb-6">Or click to browse and select files</p>
        <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
          Choose Files
        </button>
        <p className="text-sm text-gray-500 mt-4">Supported formats: PDF (max 50MB)</p>
      </div>
    </div>
  </div>
);

const AnalyticsPage = () => (
  <div className="flex-1 p-6">
    <div className="max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Analytics Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Total Documents</h3>
          <p className="text-3xl font-bold text-blue-600">0</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Total Queries</h3>
          <p className="text-3xl font-bold text-green-600">0</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Avg Response Time</h3>
          <p className="text-3xl font-bold text-purple-600">0ms</p>
        </div>
      </div>
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Upload documents to see analytics</h3>
        <p className="text-gray-600">Charts and detailed analytics will appear here once you upload and process documents.</p>
      </div>
    </div>
  </div>
);

function SimpleApp() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Routes>
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </div>
    </Router>
  );
}

export default SimpleApp;
