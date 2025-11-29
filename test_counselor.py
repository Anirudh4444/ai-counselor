from google import genai
import os

# Import the counselor function
import sys
sys.path.insert(0, '/Users/anirudhkumar/.gemini/antigravity/scratch')
from gemini_demo import get_counselor_response

print("="*70)
print("AI Counselor Testing - Sample Scenarios")
print("="*70)

# Test scenarios
test_scenarios = [
    "I've been feeling really anxious lately and can't sleep well",
    "I feel like nobody understands what I'm going through",
    "I'm having trouble getting out of bed in the morning"
]

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\n{'='*70}")
    print(f"Test Scenario {i}")
    print(f"{'='*70}")
    print(f"\nUser: {scenario}\n")
    print("Counselor Response:")
    print("-" * 70)
    
    response = get_counselor_response(scenario)
    print(response)
    print()
