import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

// Mock data for testing
const mockDocuments = [
  {
    id: 'test-1',
    filename: 'Kenya-Demographic-and-Health-Survey-2022.pdf',
    uploadDate: '2025-06-20T12:11:05.446110',
    size: 9732220,
    pageCount: 700,
    textChunks: 2645,
    tablesFound: 170,
    imagesFound: 45,
    status: 'completed'
  }
];

const mockMessages = [
  {
    id: 1,
    type: 'user',
    content: 'What is this document about?',
    timestamp: new Date()
  },
  {
    id: 2,
    type: 'assistant',
    content: 'This is the Kenya Demographic and Health Survey 2022 Main Report Volume 1. It contains comprehensive data on demographic trends, health indicators, and socioeconomic factors in Kenya.',
    timestamp: new Date()
  }
];

function TestApp() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentDocument, setCurrentDocument] = useState(mockDocuments[0]);
  const [messages, setMessages] = useState(mockMessages);
  const [newMessage, setNewMessage] = useState('');

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: newMessage,
        timestamp: new Date()
      };
      setMessages([...messages, userMessage]);
      setNewMessage('');
      
      // Simulate AI response
      setTimeout(() => {
        const aiResponse = {
          id: Date.now() + 1,
          type: 'assistant',
          content: 'This is a demo response. The system is working correctly!',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
      }, 1000);
    }
  };

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        {/* Sidebar */}
        <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
          <div className="flex items-center justify-between h-16 px-4 border-b">
            <h1 className="text-xl font-bold text-gray-800">PDF RAG System</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          
          <nav className="mt-4">
            <Link to="/" className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100">
              💬 Chat
            </Link>
            <Link to="/upload" className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100">
              📤 Upload
            </Link>
            <Link to="/analytics" className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100">
              📊 Analytics
            </Link>
          </nav>
          
          <div className="mt-8 px-4">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Documents</h3>
            <div className="mt-2">
              {mockDocuments.map(doc => (
                <div
                  key={doc.id}
                  className={`p-3 rounded-lg cursor-pointer ${currentDocument?.id === doc.id ? 'bg-blue-100 border-blue-300' : 'bg-gray-50 hover:bg-gray-100'}`}
                  onClick={() => setCurrentDocument(doc)}
                >
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {doc.filename}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {(doc.size / 1024 / 1024).toFixed(1)} MB • {doc.pageCount} pages
                  </div>
                  <div className="text-xs text-green-600 mt-1">
                    ✅ {doc.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="bg-white shadow-sm border-b">
            <div className="flex items-center justify-between h-16 px-4">
              <div className="flex items-center">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600"
                >
                  ☰
                </button>
                <h2 className="ml-4 text-lg font-semibold text-gray-800">
                  {currentDocument ? currentDocument.filename : 'Multimodal PDF RAG System'}
                </h2>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500">Demo Mode</span>
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
              </div>
            </div>
          </header>
          
          {/* Main Content Area */}
          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route
                path="/"
                element={
                  <div className="flex h-full">
                    {/* Chat Interface */}
                    <div className="flex-1 flex flex-col">
                      {/* Messages */}
                      <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {messages.map(message => (
                          <div
                            key={message.id}
                            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                          >
                            <div
                              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                                message.type === 'user'
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-white text-gray-800 shadow'
                              }`}
                            >
                              <p className="text-sm">{message.content}</p>
                              <p className="text-xs mt-1 opacity-70">
                                {message.timestamp.toLocaleTimeString()}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      {/* Message Input */}
                      <div className="border-t bg-white p-4">
                        <div className="flex space-x-2">
                          <input
                            type="text"
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                            placeholder="Ask a question about your document..."
                            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <button
                            onClick={handleSendMessage}
                            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            Send
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    {/* Document Info Panel */}
                    {currentDocument && (
                      <div className="w-1/3 border-l bg-white p-4">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Document Info</h3>
                        <div className="space-y-3">
                          <div>
                            <span className="text-sm font-medium text-gray-500">Filename:</span>
                            <p className="text-sm text-gray-900">{currentDocument.filename}</p>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-gray-500">Size:</span>
                            <p className="text-sm text-gray-900">{(currentDocument.size / 1024 / 1024).toFixed(1)} MB</p>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-gray-500">Pages:</span>
                            <p className="text-sm text-gray-900">{currentDocument.pageCount}</p>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-gray-500">Text Chunks:</span>
                            <p className="text-sm text-gray-900">{currentDocument.textChunks}</p>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-gray-500">Tables Found:</span>
                            <p className="text-sm text-gray-900">{currentDocument.tablesFound}</p>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-gray-500">Images Found:</span>
                            <p className="text-sm text-gray-900">{currentDocument.imagesFound}</p>
                          </div>
                          <div>
                            <span className="text-sm font-medium text-gray-500">Status:</span>
                            <p className="text-sm text-green-600">✅ {currentDocument.status}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                }
              />
              <Route
                path="/upload"
                element={
                  <div className="p-8">
                    <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload Documents</h2>
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                        <div className="text-4xl text-gray-400 mb-4">📄</div>
                        <p className="text-lg text-gray-600 mb-2">Drag and drop your PDF files here</p>
                        <p className="text-sm text-gray-500 mb-4">or click to browse</p>
                        <button className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600">
                          Choose Files
                        </button>
                      </div>
                    </div>
                  </div>
                }
              />
              <Route
                path="/analytics"
                element={
                  <div className="p-8">
                    <h2 className="text-2xl font-bold text-gray-800 mb-6">Analytics Dashboard</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                      <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-2xl font-bold text-blue-600">1</div>
                        <div className="text-sm text-gray-500">Documents</div>
                      </div>
                      <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-2xl font-bold text-green-600">2,645</div>
                        <div className="text-sm text-gray-500">Text Chunks</div>
                      </div>
                      <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-2xl font-bold text-purple-600">170</div>
                        <div className="text-sm text-gray-500">Tables</div>
                      </div>
                      <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-2xl font-bold text-orange-600">45</div>
                        <div className="text-sm text-gray-500">Images</div>
                      </div>
                    </div>
                  </div>
                }
              />
            </Routes>
          </main>
        </div>
        
        {/* Toast Notifications */}
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

export default TestApp;
