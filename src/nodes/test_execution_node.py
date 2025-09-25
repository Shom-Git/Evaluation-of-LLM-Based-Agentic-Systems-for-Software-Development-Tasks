import subprocess
import os
import time
import ast
import traceback
from typing import Dict, List, Tuple
from pathlib import Path

class TestExecutor:
    def __init__(self):
        self.timeout = 10  # seconds
    
    def create_test_file(self, code: str, tests: str, output_dir: str, attempt: int) -> str:
        """Create a test file with the candidate code and tests."""
        os.makedirs(output_dir, exist_ok=True)
        test_file = os.path.join(output_dir, f"candidate_{attempt}.py")
        
        # Combine code and tests
        full_content = f"{code}\n\n{tests}"
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        return test_file
    
    def execute_tests(self, test_file: str) -> Tuple[bool, str, float, List[str]]:
        """Execute the test file and return results."""
        start_time = time.time()
        
        try:
            # First, check for syntax errors
            with open(test_file, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            try:
                ast.parse(code_content)
            except SyntaxError as e:
                execution_time = time.time() - start_time
                return False, f"SyntaxError: {str(e)}", execution_time, ["syntax_error"]
            
            # Execute the file
            result = subprocess.run(
                ["python", test_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                cwd=os.path.dirname(test_file)
            )
            
            execution_time = time.time() - start_time
            
            # Analyze the output
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            combined_output = (stdout + "\n" + stderr).strip()
            
            # Determine if tests passed
            passed = result.returncode == 0 and not stderr
            
            # Extract error types
            error_types = self._analyze_errors(combined_output)
            
            return passed, combined_output, execution_time, error_types
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, f"Execution timed out after {self.timeout} seconds", execution_time, ["timeout"]
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Execution error: {str(e)}", execution_time, ["execution_error"]
    
    def _analyze_errors(self, output: str) -> List[str]:
        """Analyze error output to categorize error types."""
        error_types = []
        output_lower = output.lower()
        
        if "syntaxerror" in output_lower:
            error_types.append("syntax_error")
        if "nameerror" in output_lower:
            error_types.append("name_error")
        if "typeerror" in output_lower:
            error_types.append("type_error")
        if "assertionerror" in output_lower:
            error_types.append("assertion_error")
        if "indentationerror" in output_lower:
            error_types.append("indentation_error")
        if "valueerror" in output_lower:
            error_types.append("value_error")
        if "zerodivisionerror" in output_lower:
            error_types.append("zero_division_error")
        if "indexerror" in output_lower:
            error_types.append("index_error")
        if "keyerror" in output_lower:
            error_types.append("key_error")
        if "attributeerror" in output_lower:
            error_types.append("attribute_error")
        
        # If no specific errors found but execution failed
        if not error_types and output.strip():
            error_types.append("unknown_error")
        
        return error_types
    
    def analyze_test_results(self, passed: bool, output: str, error_types: List[str]) -> Dict:
        """Provide detailed analysis of test results."""
        analysis = {
            "passed": passed,
            "error_types": error_types,
            "suggestions": []
        }
        
        if not passed:
            # Provide specific suggestions based on error types
            if "syntax_error" in error_types:
                analysis["suggestions"].append("Check syntax: missing colons, parentheses, or indentation")
            if "assertion_error" in error_types:
                analysis["suggestions"].append("Logic error: function output doesn't match expected results")
            if "name_error" in error_types:
                analysis["suggestions"].append("Variable or function name not defined")
            if "type_error" in error_types:
                analysis["suggestions"].append("Type mismatch: check data types and operations")
            if "indentation_error" in error_types:
                analysis["suggestions"].append("Fix indentation: use consistent spaces or tabs")
            
            # Parse specific assertion failures
            if "assert" in output:
                analysis["suggestions"].append("Check function logic against failing assertions")
        
        return analysis

def test_execution_node(state: Dict) -> Dict:
    """
    Test execution node that runs candidate code and provides detailed feedback.
    """
    # Get required information
    candidate_code = state.get('candidate_code', '')
    tests = state.get('tests', '')
    task_dir = state.get('task_dir', '/tmp')
    current_attempt = state.get('current_attempt', 0)
    
    # Skip if no code generated
    if not candidate_code:
        return {
            **state,
            'test_result': {
                'passed': False,
                'log': 'No candidate code generated',
                'execution_time': 0.0,
                'errors': ['no_code'],
                'candidate_file': ''
            },
            'tests_executed': True
        }
    
    executor = TestExecutor()
    
    # Create and execute test file
    test_file = executor.create_test_file(candidate_code, tests, task_dir, current_attempt)
    passed, output, exec_time, error_types = executor.execute_tests(test_file)
    
    # Analyze results
    analysis = executor.analyze_test_results(passed, output, error_types)
    
    # Create test result
    test_result = {
        'passed': passed,
        'log': output,
        'execution_time': exec_time,
        'errors': error_types,
        'candidate_file': test_file,
        'suggestions': analysis.get('suggestions', [])
    }
    
    # Update state
    updated_state = {
        **state,
        'test_result': test_result,
        'tests_executed': True
    }
    
    return updated_state