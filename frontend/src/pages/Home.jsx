import React from 'react';
import { FileText, Upload, BarChart3, Zap, Shield, Cpu } from 'lucide-react';

const Home = () => {
  const features = [
    {
      icon: FileText,
      title: 'Multimodal Analysis',
      description: 'Extract and analyze text, tables, and images from your PDFs with advanced AI.'
    },
    {
      icon: BarChart3,
      title: 'Smart Visualizations',
      description: 'Automatically generate charts and graphs from your document data.'
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Get instant answers to complex questions about your documents.'
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Your documents are processed securely with enterprise-grade encryption.'
    },
    {
      icon: Cpu,
      title: 'AI-Powered',
      description: 'Advanced language models ensure accurate, hallucination-free responses.'
    },
    {
      icon: Upload,
      title: 'Easy Upload',
      description: 'Support for large PDFs up to 100MB with thousands of pages.'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Analyze PDFs with
            <span className="text-blue-600"> AI Intelligence</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Upload your PDF documents and ask questions to get instant, accurate answers. 
            Extract insights, generate charts, and analyze complex data with multimodal AI.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/upload"
              className="bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Upload Your First PDF
            </a>
            <button className="border border-blue-600 text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-50 transition-colors">
              View Demo
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Stats Section */}
        <div className="mt-20 bg-white rounded-xl shadow-lg p-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">99.9%</div>
              <div className="text-gray-600">Accuracy Rate</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">5000+</div>
              <div className="text-gray-600">Pages Supported</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">< 2s</div>
              <div className="text-gray-600">Response Time</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">100MB</div>
              <div className="text-gray-600">Max File Size</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;