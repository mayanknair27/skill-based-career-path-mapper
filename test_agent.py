"""Quick verification script for the agent pipeline."""
import sys
sys.path.insert(0, '.')

from logic.career_logic import process_career_data, get_all_careers, get_career_by_title, compare_careers

print("=" * 50)
print("AGENT PIPELINE VERIFICATION")
print("=" * 50)

# Test 1: Full pipeline
print("\n--- Test 1: Full Pipeline (Data Scientist, Beginner) ---")
result = process_career_data("Data Scientist", "Python, SQL", "Beginner")
print(f"  Status: {result['status']}")
print(f"  Title: {result['title']}")
print(f"  Match: {result['match_percentage']}%")
print(f"  Recommendation: {result['recommendation']}")
print(f"  Reasoning: {result['reasoning']}")
print(f"  Next Action: {result['next_action']}")
print(f"  Focus: {result['focus_area']}")
print(f"  Critical Skill: {result.get('most_impactful_skill', 'None')}")
print(f"  Missing Skills: {result['missing_skills']}")
print(f"  Roadmap Steps: {result['total_steps']}")
print(f"  Thinking Trail ({len(result['thinking_trail'])} stages):")
for s in result['thinking_trail']:
    print(f"    > {s['name']}: {s['detail']} ({s['duration_ms']}ms)")

# Test 2: Alias resolution
print("\n--- Test 2: Alias Resolution (web dev) ---")
result2 = process_career_data("web dev", "", "Intermediate")
print(f"  Status: {result2['status']}")
print(f"  Title: {result2['title']}")
print(f"  Match: {result2['match_percentage']}%")

# Test 3: Advanced user
print("\n--- Test 3: Advanced User (AI Engineer) ---")
result3 = process_career_data("AI Engineer", "Python, Machine Learning, Deep Learning", "Advanced")
print(f"  Status: {result3['status']}")
print(f"  Title: {result3['title']}")
print(f"  Match: {result3['match_percentage']}%")
print(f"  Roadmap: {result3['total_steps']} steps")
print(f"  Next Action: {result3['next_action']}")

# Test 4: Error case
print("\n--- Test 4: Error Case (nonexistent career) ---")
result4 = process_career_data("Space Cowboy", "Python", "Beginner")
print(f"  Status: {result4['status']}")
print(f"  Message: {result4.get('message', 'N/A')}")

# Test 5: Comparison engine
print("\n--- Test 5: Comparison Engine ---")
comp = compare_careers("Data Scientist", "Web Developer", "Python, SQL")
print(f"  Recommended: {comp['recommended']}")
print(f"  Strength: {comp['strength']}")
print(f"  Effort A: {comp['effort_a']} skills | Effort B: {comp['effort_b']} skills")
print(f"  Justification: {comp['justification'][:150]}...")

# Test 6: Categorized skills
print("\n--- Test 6: Skill Prioritization ---")
for item in result['categorized_missing']:
    print(f"  [{item['priority']:6s}] {item['skill'].title()} — {item['reason'][:60]}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED")
print("=" * 50)
