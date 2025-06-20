import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, FileText, BarChart3, Image } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Plot from 'react-plotly.js';

const ChatInterface = ({ messages, onSendMessage, loading, currentDocument }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    onSendMessage(inputValue);
    setInputValue('');
  };

  const renderMessage = (message) => {
    const { type, content, chartData, sources, metadata } = message;

    return (
      <div
        key={message.id}
        className={`flex ${type === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-3xl px-4 py-2 rounded-lg ${
            type === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-800 shadow-md'
          }`}
        >
          {type === 'user' ? (
            <p>{content}</p>
          ) : (
            <div className="space-y-4">
              {/* Main Response */}
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>

              {/* Chart Display */}
              {chartData && chartData.plotly_json && (
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="text-sm font-semibold mb-2 flex items-center">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Data Visualization
                  </h4>
                  <Plot
                    data={JSON.parse(chartData.plotly_json).data}
                    layout={{
                      ...JSON.parse(chartData.plotly_json).layout,
                      autosize: true,
                      height: 400
                    }}
                    config={{ responsive: true }}
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              {/* Sources */}
              {sources && sources.length > 0 && (
                <div className="text-xs text-gray-600 border-t pt-2">
                  <span className="font-semibold">Sources: </span>
                  {sources.map((source, idx) => (
                    <span key={idx} className="inline-flex items-center mr-2">
                      {source.includes('table') ? (
                        <FileText className="w-3 h-3 mr-1" />
                      ) : source.includes('image') ? (
                        <Image className="w-3 h-3 mr-1" />
                      ) : (
                        <FileText className="w-3 h-3 mr-1" />
                      )}
                      {source}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {!currentDocument ? (
          <div className="text-center text-gray-500 mt-8">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-semibold mb-2">No Document Selected</h3>
            <p>Upload a PDF document to start asking questions</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <h3 className="text-lg font-semibold mb-4">
              Ready to analyze: {currentDocument.name}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              <div className="bg-white p-4 rounded-lg shadow-sm border">
                <h4 className="font-semibold text-gray-800 mb-2">Sample Questions:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• What are the main topics covered?</li>
                  <li>• Summarize the key findings</li>
                  <li>• Show me trends in the data</li>
                  <li>• What tables are available?</li>
                </ul>
              </div>
              <div className="bg-white p-4 rounded-lg shadow-sm border">
                <h4 className="font-semibold text-gray-800 mb-2">Capabilities:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Text analysis & Q&A</li>
                  <li>• Table data extraction</li>
                  <li>• Chart generation</li>
                  <li>• Image content analysis</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          messages.map(renderMessage)
        )}
        
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white text-gray-800 shadow-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Loader className="w-4 h-4 animate-spin" />
                <span>Analyzing document...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-white p-4">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={
              currentDocument
                ? "Ask a question about your document..."
                : "Please upload a document first..."
            }
            disabled={!currentDocument || loading}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || !currentDocument || loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;