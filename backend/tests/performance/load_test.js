import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests should be below 2s
    http_req_failed: ['rate<0.1'],     // Error rate should be below 10%
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function() {
  // Test health check
  let healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });

  // Test chat endpoint (mock request)
  let chatPayload = JSON.stringify({
    query: 'What are the main topics in this document?',
    context_type: ['text'],
    include_charts: false
  });

  let chatResponse = http.post(`${BASE_URL}/api/v1/chat/chat`, chatPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(chatResponse, {
    'chat request status is 200 or 422': (r) => [200, 422].includes(r.status),
    'chat response time < 5000ms': (r) => r.timings.duration < 5000,
  });

  sleep(1);
}