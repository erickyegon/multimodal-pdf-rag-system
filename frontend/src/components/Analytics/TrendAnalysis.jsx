import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const TrendAnalysis = ({ data }) => {
  if (!data || !data.analysis) return null;

  const extractTrendInfo = (analysis) => {
    // Simple trend extraction - in production, you'd use more sophisticated parsing
    const trends = [];
    const sentences = analysis.split('. ');
    
    sentences.forEach((sentence, index) => {
      if (sentence.toLowerCase().includes('increase') || sentence.toLowerCase().includes('growth')) {
        trends.push({
          id: index,
          direction: 'up',
          text: sentence.trim(),
          confidence: 0.8
        });
      } else if (sentence.toLowerCase().includes('decrease') || sentence.toLowerCase().includes('decline')) {
        trends.push({
          id: index,
          direction: 'down',
          text: sentence.trim(),
          confidence: 0.8
        });
      } else if (sentence.toLowerCase().includes('stable') || sentence.toLowerCase().includes('consistent')) {
        trends.push({
          id: index,
          direction: 'stable',
          text: sentence.trim(),
          confidence: 0.7
        });
      }
    });

    return trends.slice(0, 5); // Return top 5 trends
  };

  const trends = extractTrendInfo(data.analysis);

  const getTrendIcon = (direction) => {
    switch (direction) {
      case 'up': return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'down': return <TrendingDown className="w-5 h-5 text-red-500" />;
      default: return <Minus className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTrendColor = (direction) => {
    switch (direction) {
      case 'up': return 'border-l-green-500 bg-green-50';
      case 'down': return 'border-l-red-500 bg-red-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
        Trend Analysis
      </h3>

      {trends.length > 0 ? (
        <div className="space-y-3">
          {trends.map((trend) => (
            <div
              key={trend.id}
              className={`p-3 border-l-4 rounded-r-lg ${getTrendColor(trend.direction)}`}
            >
              <div className="flex items-start space-x-3">
                {getTrendIcon(trend.direction)}
                <div className="flex-1">
                  <p className="text-sm text-gray-800">{trend.text}</p>
                  <div className="mt-1 flex items-center">
                    <span className="text-xs text-gray-500">
                      Confidence: {Math.round(trend.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg border">
          <div className="text-center py-8">
            <p className="text-gray-600 mb-4">{data.analysis}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrendAnalysis;
