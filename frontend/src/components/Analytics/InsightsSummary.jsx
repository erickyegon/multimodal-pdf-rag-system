import React from 'react';
import { Lightbulb, CheckCircle, AlertCircle, Info } from 'lucide-react';

const InsightsSummary = ({ insights, analysis }) => {
  const processInsights = (insights, analysis) => {
    let processedInsights = [];

    // If insights array exists, use it
    if (insights && Array.isArray(insights)) {
      processedInsights = insights.map((insight, index) => ({
        id: index,
        text: insight,
        type: 'insight',
        priority: 'medium'
      }));
    }

    // If no insights but analysis exists, extract key points
    if (processedInsights.length === 0 && analysis) {
      const sentences = analysis.split('. ').filter(s => s.length > 20);
      processedInsights = sentences.slice(0, 5).map((sentence, index) => ({
        id: index,
        text: sentence.trim() + (sentence.endsWith('.') ? '' : '.'),
        type: 'finding',
        priority: index < 2 ? 'high' : 'medium'
      }));
    }

    return processedInsights;
  };

  const insightsList = processInsights(insights, analysis);

  const getInsightIcon = (type, priority) => {
    if (priority === 'high') {
      return <AlertCircle className="w-5 h-5 text-orange-500" />;
    } else if (type === 'insight') {
      return <Lightbulb className="w-5 h-5 text-yellow-500" />;
    } else {
      return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getInsightStyle = (priority) => {
    switch (priority) {
      case 'high':
        return 'border-l-orange-500 bg-orange-50';
      case 'medium':
        return 'border-l-blue-500 bg-blue-50';
      default:
        return 'border-l-gray-500 bg-gray-50';
    }
  };

  if (insightsList.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Lightbulb className="w-5 h-5 mr-2 text-blue-600" />
          Key Insights
        </h3>
        <div className="text-center py-8">
          <Lightbulb className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-600">No insights available</p>
          <p className="text-sm text-gray-500 mt-1">
            Run an analysis to generate insights
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg border">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <Lightbulb className="w-5 h-5 mr-2 text-blue-600" />
        Key Insights
      </h3>

      <div className="space-y-3">
        {insightsList.map((insight) => (
          <div
            key={insight.id}
            className={`p-3 border-l-4 rounded-r-lg ${getInsightStyle(insight.priority)}`}
          >
            <div className="flex items-start space-x-3">
              {getInsightIcon(insight.type, insight.priority)}
              <div className="flex-1">
                <p className="text-sm text-gray-800">{insight.text}</p>
                <div className="mt-1 flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    insight.priority === 'high' 
                      ? 'bg-orange-100 text-orange-700' 
                      : 'bg-blue-100 text-blue-700'
                  }`}>
                    {insight.priority === 'high' ? 'High Priority' : 'Key Finding'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-600">
          💡 <strong>Tip:</strong> These insights are automatically extracted from your document analysis. 
          Ask more specific questions to get deeper insights.
        </p>
      </div>
    </div>
  );
};

export default InsightsSummary;