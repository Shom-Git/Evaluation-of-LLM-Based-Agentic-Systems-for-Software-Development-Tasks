import re
import ast
from typing import Dict, List, Tuple, Optional
from core.state import AgentState, CodeAnalysis, BugType

class CodeAnalyzer:
    def __init__(self):
        self.bug_patterns = {
            BugType.OPERATOR_MISUSE: [
                (r'def\s+\w*mul\w*.*?return.*?\+', "Multiplication function using addition"),
                (r'def\s+\w*add\w*.*?return.*?-', "Addition function using subtraction"),
                (r'def\s+\w*sub\w*.*?return.*?\+', "Subtraction function using addition"),
                (r'def\s+\w*div\w*.*?return.*?\*', "Division function using multiplication"),
                (r'if\s+.*?==\s+.*?:\s*return\s+True.*?return\s+False', "Logical comparison reversal"),
            ],
            BugType.MISSING_LOGIC: [
                (r'def\s+.*?:\s*pass', "Function with only pass statement"),
                (r'for\s+.*?:\s*$', "Empty for loop"),
                (r'if\s+.*?:\s*$', "Empty if statement"),
                (r'def\s+(?!.*return).*?:', "Function missing return statement"),
            ],
            BugType.VARIABLE_MISUSE: [
                (r'(\w+)\s*=.*?\1\s*[+\-*/]\s*\w+', "Variable used before definition"),
                (r'return\s+\w+\s*/\s*\w+', "Division by variable instead of length"),
                (r'sum\s*\(\s*(\w+)\s*\)\s*/\s*\1', "Dividing by list instead of length"),
            ],
            BugType.VALUE_MISUSE: [
                (r'prod_value\s*=\s*0', "Product initialized to 0 instead of 1"),
                (r'=\s*1\.0\s*\+', "Adding 1.0 to decimal part"),
                (r'<\s*0.*?return\s+True', "Wrong comparison for below zero"),
            ],
            BugType.EXCESS_LOGIC: [
                (r'return\s+.*?\+\s*1\.0', "Adding unnecessary 1.0"),
                (r'\w+\s*\+\s*\w+\s*\+\s*\w+', "Excessive operations"),
            ]
        }
    
    def analyze_code_structure(self, code: str) -> Dict:
        """Analyze the basic structure of the code."""
        try:
            tree = ast.parse(code)
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'returns': len([n for n in ast.walk(node) if isinstance(n, ast.Return)]),
                        'complexity': self._calculate_complexity(node)
                    }
                    functions.append(func_info)
            
            return {
                'functions': functions,
                'total_lines': len(code.split('\n')),
                'has_syntax_error': False
            }
        except SyntaxError as e:
            return {
                'functions': [],
                'total_lines': len(code.split('\n')),
                'has_syntax_error': True,
                'syntax_error': str(e)
            }
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def detect_bug_patterns(self, code: str) -> Tuple[BugType, List[str], float]:
        """Detect specific bug patterns in the code."""
        detected_patterns = []
        confidence_scores = []
        suspected_type = BugType.UNKNOWN
        
        for bug_type, patterns in self.bug_patterns.items():
            for pattern, description in patterns:
                if re.search(pattern, code, re.MULTILINE | re.DOTALL):
                    detected_patterns.append(description)
                    confidence_scores.append(0.8)  # High confidence for pattern matches
                    suspected_type = bug_type
        
        # Additional heuristic analysis
        if 'mul' in code and '+' in code and suspected_type == BugType.UNKNOWN:
            detected_patterns.append("Possible operator misuse in multiplication")
            confidence_scores.append(0.6)
            suspected_type = BugType.OPERATOR_MISUSE
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        return suspected_type, detected_patterns, avg_confidence
    
    def analyze_test_requirements(self, tests: str) -> List[str]:
        """Extract requirements from test cases."""
        requirements = []
        
        # Extract assert statements
        assert_patterns = re.findall(r'assert\s+(.+)', tests)
        for pattern in assert_patterns:
            requirements.append(f"Must satisfy: {pattern}")
        
        # Extract expected behaviors from docstring examples
        docstring_examples = re.findall(r'>>>\s*(.+?)\n\s*(.+)', tests)
        for call, expected in docstring_examples:
            requirements.append(f"Example: {call} should return {expected}")
        
        return requirements

def analysis_node(state: Dict) -> Dict:
    """
    Comprehensive code analysis node that identifies bugs and requirements.
    """
    analyzer = CodeAnalyzer()
    
    # Extract basic information
    buggy_code = state.get('buggy_code', '')
    tests = state.get('tests', '')
    task_prompt = state.get('task_prompt', '')
    
    # Perform structural analysis
    structure = analyzer.analyze_code_structure(buggy_code)
    
    # Detect bug patterns
    suspected_type, patterns, confidence = analyzer.detect_bug_patterns(buggy_code)
    
    # Analyze test requirements
    test_requirements = analyzer.analyze_test_requirements(tests)
    
    # Extract function information
    func_info = structure['functions'][0] if structure['functions'] else {
        'name': 'unknown', 'args': [], 'returns': 0, 'complexity': 1
    }
    
    # Create analysis object
    code_analysis = {
        'function_name': func_info['name'],
        'parameters': func_info['args'],
        'return_type': None,
        'suspected_bug_type': suspected_type.value,
        'complexity_score': func_info['complexity'],
        'patterns_detected': patterns,
        'confidence': confidence
    }
    
    # Update state
    updated_state = {
        **state,
        'code_analysis': code_analysis,
        'test_requirements': test_requirements,
        'error_patterns': patterns,
        'analysis_complete': True
    }
    
    return updated_state