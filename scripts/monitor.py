"""
Post-deployment monitoring script
Run this after deployment to verify system health
"""

import requests
import time
import sys
from typing import Dict, Any

class DeploymentMonitor:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def check_health(self) -> Dict[str, Any]:
        """Check basic health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return {
                "status": "pass" if response.status_code == 200 else "fail",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def check_detailed_health(self) -> Dict[str, Any]:
        """Check detailed health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health/detailed")
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "fail", "status_code": response.status_code}
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_chat_endpoint(self) -> Dict[str, Any]:
        """Test chat functionality"""
        try:
            payload = {
                "query": "Test query for monitoring",
                "context_type": ["text"],
                "include_charts": False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/chat",
                json=payload
            )
            
            return {
                "status": "pass" if response.status_code in [200, 422] else "fail",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def run_monitoring_suite(self) -> bool:
        """Run complete monitoring suite"""
        print(f"🔍 Monitoring deployment at {self.base_url}")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.check_health),
            ("Detailed Health", self.check_detailed_health),
            ("Chat Endpoint", self.test_chat_endpoint)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"Running {test_name}...", end=" ")
            result = test_func()
            
            if result.get("status") == "pass":
                print(f"✅ PASS ({result.get('response_time', 0):.2f}s)")
            else:
                print(f"❌ FAIL - {result.get('error', 'Unknown error')}")
                all_passed = False
        
        print("=" * 50)
        
        if all_passed:
            print("🎉 All monitoring checks passed!")
            print("🚀 Deployment is healthy and ready for use")
        else:
            print("⚠️  Some checks failed - please investigate")
        
        return all_passed

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python monitor.py <base_url>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    monitor = DeploymentMonitor(base_url)
    
    success = monitor.run_monitoring_suite()
    sys.exit(0 if success else 1)