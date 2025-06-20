import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  X, 
  Home, 
  Upload, 
  BarChart3, 
  FileText, 
  Trash2,
  Plus
} from 'lucide-react';

const Sidebar = ({ 
  isOpen, 
  onClose, 
  documents, 
  currentDocument, 
  onDocumentSelect, 
  onDocumentDelete 
}) => {
  const location = useLocation();

  const navigation = [
    { name: 'Chat', href: '/', icon: Home },
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  const isActive = (href) => {
    return location.pathname === href;
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 lg:hidden">
            <h2 className="text-lg font-semibold text-gray-900">Menu</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Navigation
              </h3>
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => onClose()}
                    className={`
                      flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                      ${isActive(item.href)
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                );
              })}
            </div>

            {/* Documents Section */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Documents
                </h3>
                <Link
                  to="/upload"
                  className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                >
                  <Plus className="w-4 h-4" />
                </Link>
              </div>
              
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {documents && documents.length > 0 ? (
                  documents.map((doc) => (
                    <div
                      key={doc.id}
                      className={`
                        flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors
                        ${currentDocument?.id === doc.id
                          ? 'bg-blue-50 border border-blue-200'
                          : 'hover:bg-gray-50'
                        }
                      `}
                      onClick={() => onDocumentSelect(doc)}
                    >
                      <div className="flex items-center flex-1 min-w-0">
                        <FileText className="w-4 h-4 text-gray-400 mr-2 flex-shrink-0" />
                        <span className="text-sm text-gray-700 truncate">
                          {doc.name}
                        </span>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDocumentDelete(doc.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4">
                    <FileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No documents uploaded</p>
                    <Link
                      to="/upload"
                      className="text-xs text-blue-600 hover:text-blue-700 mt-1 inline-block"
                    >
                      Upload your first document
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </nav>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
