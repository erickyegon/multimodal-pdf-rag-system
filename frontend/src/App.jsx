import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

// Components
import {
  Header,
  Sidebar,
  ChatInterface,
  UploadPage,
  AnalyticsPage,
  DocumentViewer
} from './components';

// Hooks
import { useChat, useDocument } from './hooks';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentDocument, setCurrentDocument] = useState(null);
  
  const {
    messages,
    loading,
    sendMessage,
    clearChat
  } = useChat();
  
  const {
    documents,
    uploadDocument,
    deleteDocument,
    getDocuments
  } = useDocument();

  useEffect(() => {
    // Load documents on app start
    getDocuments();
  }, []);

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          documents={documents}
          currentDocument={currentDocument}
          onDocumentSelect={setCurrentDocument}
          onDocumentDelete={deleteDocument}
        />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
            currentDocument={currentDocument}
            onClearChat={clearChat}
          />
          
          {/* Main Content Area */}
          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route
                path="/"
                element={
                  <div className="flex h-full">
                    <div className="flex-1">
                      <ChatInterface
                        messages={messages}
                        onSendMessage={sendMessage}
                        loading={loading}
                        currentDocument={currentDocument}
                      />
                    </div>
                    {currentDocument && (
                      <div className="w-1/3 border-l">
                        <DocumentViewer document={currentDocument} />
                      </div>
                    )}
                  </div>
                }
              />
              <Route
                path="/upload"
                element={
                  <UploadPage
                    onUpload={uploadDocument}
                    documents={documents}
                  />
                }
              />
              <Route
                path="/analytics"
                element={
                  <AnalyticsPage
                    currentDocument={currentDocument}
                  />
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

export default App;