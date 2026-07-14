"""
Evaluation harness for multi-agent system
"""
import json
import time
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from agents.orchestration import get_orchestrator


class Evaluator:
    """Evaluation harness for the multi-agent system"""
    
    def __init__(self, test_cases_path: str = "test_cases.json"):
        self.test_cases_path = Path(__file__).parent / test_cases_path
        self.orchestrator = get_orchestrator(use_langgraph=False)
        self.results = []
    
    def load_test_cases(self) -> List[Dict]:
        """Load test cases from JSON"""
        with open(self.test_cases_path, 'r') as f:
            data = json.load(f)
        return data.get('test_cases', [])
    
    def evaluate_test_case(self, test_case: Dict) -> Dict:
        """Evaluate a single test case"""
        test_id = test_case['id']
        test_name = test_case['name']
        input_data = test_case['input']
        expected = test_case.get('expected_output', {})
        
        print(f"\n{'='*60}")
        print(f"Running: {test_name} ({test_id})")
        print(f"{'='*60}")
        
        # Record start time
        start_time = time.time()
        tool_calls = 0
        
        # Run test
        try:
            if input_data['type'] == 'arxiv_id':
                result = self.orchestrator.process(
                    input_data['value'],
                    input_type='arxiv_id'
                )
                tool_calls = self._count_tool_calls(result)
            elif input_data['type'] == 'search':
                # Handle search separately
                from agents.tools import arxiv_api
                search_results = arxiv_api.search_papers(
                    input_data['query'],
                    input_data.get('max_results', 5)
                )
                result = {
                    'success': len(search_results) > 0,
                    'search_results': search_results
                }
                tool_calls = 1
            else:
                result = {'success': False, 'error': f"Unknown input type: {input_data['type']}"}
            
            latency = time.time() - start_time
            
            # Evaluate against expected output
            evaluation = self._evaluate_result(result, expected, test_case)
            
            test_result = {
                'test_id': test_id,
                'test_name': test_name,
                'success': evaluation['passed'],
                'latency': latency,
                'tool_calls': tool_calls,
                'evaluation': evaluation,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            latency = time.time() - start_time
            test_result = {
                'test_id': test_id,
                'test_name': test_name,
                'success': False,
                'latency': latency,
                'tool_calls': tool_calls,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        return test_result
    
    def _count_tool_calls(self, result: Dict) -> int:
        """Count number of tool calls made"""
        count = 0
        if result.get('reader', {}).get('status') == 'success':
            count += 1  # Reader used tools
        if result.get('reviewer', {}).get('status') == 'success':
            count += 1  # Reviewer used tools
        if result.get('critic', {}).get('status') == 'success':
            count += 1  # Critic used tools
        return count
    
    def _evaluate_result(self, result: Dict, expected: Dict, test_case: Dict) -> Dict:
        """Evaluate result against expected output"""
        evaluation = {
            'passed': True,
            'checks': {},
            'constraint_violations': []
        }
        
        # Check each expected condition
        if 'has_summary' in expected:
            has_summary = bool(result.get('summary') or result.get('reviewer', {}).get('summary'))
            evaluation['checks']['has_summary'] = has_summary
            if expected['has_summary'] and not has_summary:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append("Missing summary")
        
        if 'has_review' in expected:
            has_review = bool(result.get('review') or result.get('reviewer', {}).get('review'))
            evaluation['checks']['has_review'] = has_review
            if expected['has_review'] and not has_review:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append("Missing review")
        
        if 'has_validation' in expected:
            has_validation = bool(result.get('validation') or result.get('critic', {}).get('validation'))
            evaluation['checks']['has_validation'] = has_validation
            if expected['has_validation'] and not has_validation:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append("Missing validation")
        
        if 'min_summary_length' in expected:
            summary = result.get('summary', '') or result.get('reviewer', {}).get('summary', '')
            length_ok = len(summary) >= expected['min_summary_length']
            evaluation['checks']['min_summary_length'] = length_ok
            if not length_ok:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append(f"Summary too short: {len(summary)} < {expected['min_summary_length']}")
        
        if 'handles_error' in expected:
            handles_error = not result.get('success', True) or len(result.get('errors', [])) > 0
            evaluation['checks']['handles_error'] = handles_error
            if expected['handles_error'] and not handles_error:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append("Should have handled error but didn't")
        
        if 'validation_passed' in expected:
            validation = result.get('validation') or result.get('critic', {}).get('validation', {})
            validation_ok = validation.get('is_complete', False) if isinstance(validation, dict) else False
            evaluation['checks']['validation_passed'] = validation_ok
            if expected['validation_passed'] and not validation_ok:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append("Validation did not pass")
        
        if 'all_agents_ran' in expected:
            reader_ok = result.get('reader', {}).get('status') == 'success'
            reviewer_ok = result.get('reviewer', {}).get('status') == 'success'
            critic_ok = result.get('critic', {}).get('status') == 'success'
            all_ran = reader_ok and reviewer_ok and critic_ok
            evaluation['checks']['all_agents_ran'] = all_ran
            if expected['all_agents_ran'] and not all_ran:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append("Not all agents ran successfully")
        
        if 'has_structured_info' in expected:
            structured_info = result.get('reader', {}).get('structured_info', {})
            has_info = bool(structured_info and isinstance(structured_info, dict))
            evaluation['checks']['has_structured_info'] = has_info
            if expected['has_structured_info'] and not has_info:
                evaluation['passed'] = False
                evaluation['constraint_violations'].append("Missing structured information")
        
        return evaluation
    
    def run_all_tests(self) -> Dict:
        """Run all test cases"""
        test_cases = self.load_test_cases()
        
        print(f"\n{'='*60}")
        print(f"Running {len(test_cases)} test cases")
        print(f"{'='*60}")
        
        for test_case in test_cases:
            result = self.evaluate_test_case(test_case)
            self.results.append(result)
            
            # Print result
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            print(f"{status} - {result['test_name']} ({result['latency']:.2f}s)")
            if not result['success']:
                if 'error' in result:
                    print(f"  Error: {result['error']}")
                if 'evaluation' in result:
                    violations = result['evaluation'].get('constraint_violations', [])
                    for violation in violations:
                        print(f"  Violation: {violation}")
        
        # Compute metrics
        metrics = self.compute_metrics()
        
        return {
            'results': self.results,
            'metrics': metrics
        }
    
    def compute_metrics(self) -> Dict:
        """Compute evaluation metrics"""
        if not self.results:
            return {}
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        total_constraint_violations = sum(
            len(r.get('evaluation', {}).get('constraint_violations', []))
            for r in self.results
        )
        
        avg_latency = sum(r['latency'] for r in self.results) / total_tests if total_tests > 0 else 0
        total_tool_calls = sum(r.get('tool_calls', 0) for r in self.results)
        avg_tool_calls = total_tool_calls / total_tests if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate,
            'total_constraint_violations': total_constraint_violations,
            'avg_latency_seconds': avg_latency,
            'total_tool_calls': total_tool_calls,
            'avg_tool_calls_per_test': avg_tool_calls
        }
    
    def save_results(self, output_path: str = "eval_results.json"):
        """Save evaluation results"""
        output_path = Path(__file__).parent / output_path
        with open(output_path, 'w') as f:
            json.dump({
                'results': self.results,
                'metrics': self.compute_metrics()
            }, f, indent=2)
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    evaluator = Evaluator()
    results = evaluator.run_all_tests()
    
    # Print summary
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    metrics = results['metrics']
    print(f"Total Tests: {metrics['total_tests']}")
    print(f"Passed: {metrics['passed_tests']}")
    print(f"Failed: {metrics['failed_tests']}")
    print(f"Success Rate: {metrics['success_rate']*100:.1f}%")
    print(f"Avg Latency: {metrics['avg_latency_seconds']:.2f}s")
    print(f"Total Constraint Violations: {metrics['total_constraint_violations']}")
    print(f"Avg Tool Calls per Test: {metrics['avg_tool_calls_per_test']:.1f}")
    
    # Save results
    evaluator.save_results()

