import { useState, useCallback, useRef } from 'react';
import { toast } from 'react-toastify';
import { v4 as uuidv4 } from 'uuid';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const abortControllerRef = useRef(null);

  const sendMessage = useCallback(async (query, options = {}) => {
    if (!query.trim()) return;

    const userMessage = {
      id: uuidv4(),
      type: 'user',
      content: query,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setStreamingMessage('');

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/chat/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          context_type: options.contentTypes || ['text', 'table', 'image'],
          include_charts: options.includeCharts !== false
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      const assistantMessage = {
        id: uuidv4(),
        type: 'assistant',
        content: result.response,
        chartData: result.chart_data,
        sources: result.sources,
        metadata: result.metadata,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      if (error.name === 'AbortError') {
        toast.info('Request cancelled');
        return;
      }

      console.error('Chat error:', error);
      toast.error('Failed to get response. Please try again.');

      const errorMessage = {
        id: uuidv4(),
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  const sendStreamingMessage = useCallback(async (query, options = {}) => {
    if (!query.trim()) return;

    const userMessage = {
      id: uuidv4(),
      type: 'user',
      content: query,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setStreamingMessage('');

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          context_type: options.contentTypes || ['text', 'table', 'image'],
          include_charts: options.includeCharts !== false
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedResponse = '';
      let chartData = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'text') {
                accumulatedResponse += data.content;
                setStreamingMessage(accumulatedResponse);
              } else if (data.type === 'chart') {
                chartData = data.content;
              }
            } catch (e) {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }

      const assistantMessage = {
        id: uuidv4(),
        type: 'assistant',
        content: accumulatedResponse,
        chartData: chartData,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStreamingMessage('');

    } catch (error) {
      console.error('Streaming error:', error);
      toast.error('Failed to get response. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setStreamingMessage('');
  }, []);

  const deleteMessage = useCallback((messageId) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  }, []);

  const regenerateResponse = useCallback(async (messageId) => {
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex === -1) return;

    // Find the user message that preceded this assistant message
    const userMessage = messages[messageIndex - 1];
    if (!userMessage || userMessage.type !== 'user') return;

    // Remove the assistant message and regenerate
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
    await sendMessage(userMessage.content);
  }, [messages, sendMessage]);

  return {
    messages,
    loading,
    streamingMessage,
    sendMessage,
    sendStreamingMessage,
    cancelRequest,
    clearChat,
    deleteMessage,
    regenerateResponse
  };
};