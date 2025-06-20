import React from 'react';
import { Menu, FileText, Search, Bell, User, LogOut } from 'lucide-react';

const Header = ({ onSidebarToggle, currentDocument, onClearChat }) => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onSidebarToggle}
            className="p-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-6 h-6 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">PDF RAG System</h1>
            </div>
            
            {currentDocument && (
              <>
                <span className="text-gray-400">|</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Current:</span>
                  <span className="text-sm font-medium text-gray-900 max-w-xs truncate">
                    {currentDocument.name}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="hidden md:flex items-center space-x-4 flex-1 max-w-md mx-8">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents or ask a question..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-3">
          {currentDocument && (
            <button
              onClick={onClearChat}
              className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Clear Chat
            </button>
          )}
          
          <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <Bell className="w-5 h-5" />
          </button>
          
          <div className="flex items-center space-x-2 pl-3 border-l border-gray-200">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-blue-600" />
            </div>
            <div className="hidden md:block">
              <p className="text-sm font-medium text-gray-900">User</p>
              <p className="text-xs text-gray-500">Free Plan</p>
            </div>
            <button className="p-1 text-gray-400 hover:text-gray-600">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
