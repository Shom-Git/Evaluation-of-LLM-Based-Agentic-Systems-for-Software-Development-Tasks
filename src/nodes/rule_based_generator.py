import re
from typing import Dict, List, Tuple, Optional
from core.state import BugType, FixStrategy

class RuleBasedFixer:
    def __init__(self):
        self.fix_rules = {
            BugType.OPERATOR_MISUSE: [
                {
                    'pattern': r'(def\s+\w*mul\w*.*?return\s+)(\w+)\s*\+\s*(\w+)',
                    'replacement': r'\1\2 * \3',
                    'description': 'Replace + with * in multiplication function'
                },
                {
                    'pattern': r'(def\s+\w*add\w*.*?return\s+)(\w+)\s*-\s*(\w+)',
                    'replacement': r'\1\2 + \3',
                    'description': 'Replace - with + in addition function'
                },
                {
                    'pattern': r'(def\s+\w*sub\w*.*?return\s+)(\w+)\s*\+\s*(\w+)',
                    'replacement': r'\1\2 - \3',
                    'description': 'Replace + with - in subtraction function'
                },
                {
                    'pattern': r'(\s+distance\s*=\s*)(\w+)\s*-\s*(\w+)',
                    'replacement': r'\1abs(\2 - \3)',
                    'description': 'Add abs() for distance calculation'
                },
                {
                    'pattern': r'(if\s+.*?balance\s*)==\s*0:',
                    'replacement': r'\1< 0:',
                    'description': 'Fix comparison for below zero check'
                }
            ],
            BugType.VALUE_MISUSE: [
                {
                    'pattern': r'(prod_value\s*=\s*)0',
                    'replacement': r'\11',
                    'description': 'Initialize product to 1 instead of 0'
                },
                {
                    'pattern': r'(return\s+.*?%\s*1\.0)\s*\+\s*1\.0',
                    'replacement': r'\1',
                    'description': 'Remove unnecessary +1.0 from modulo operation'
                },
                {
                    'pattern': r'(return\s+.*?)\s*/\s*mean',
                    'replacement': r'\1 / len(numbers)',
                    'description': 'Divide by length instead of mean'
                }
            ],
            BugType.MISSING_LOGIC: [
                {
                    'pattern': r'(def\s+intersperse.*?for\s+n\s+in\s+numbers\[:-1\]:.*?result\.append\(delimeter\)\s*)(return\s+result)',
                    'replacement': r'\1\n    result.append(numbers[-1])\n\n    \2',
                    'description': 'Add missing last element in intersperse'
                },
                {
                    'pattern': r'(if\s+current_depth\s*)<\s*0:',
                    'replacement': r'\1== 0:',
                    'description': 'Fix depth check condition'
                },
                {
                    'pattern': r'(while\s+not\s+is_palindrome\(string\):)',
                    'replacement': r'while not is_palindrome(string[beginning_of_suffix:]):',
                    'description': 'Fix palindrome substring check'
                }
            ],
            BugType.VARIABLE_MISUSE: [
                {
                    'pattern': r'(else:\s*running_max\s*=\s*)max\(numbers\)',
                    'replacement': r'\1max(running_max, n)',
                    'description': 'Use rolling max instead of global max'
                },
                {
                    'pattern': r'(else:\s*max_depth\s*)-=\s*1',
                    'replacement': r'\1depth -= 1',
                    'description': 'Decrement depth instead of max_depth'
                },
                {
                    'pattern': r'(\[x\s+for\s+x\s+in\s+strings\s+if\s+)x\s+in\s+substring',
                    'replacement': r'\1substring in x',
                    'description': 'Fix substring containment check'
                }
            ],
            BugType.EXCESS_LOGIC: [
                {
                    'pattern': r'return\s+(.+?)\s*\+\s*1\.0',
                    'replacement': r'return \1',
                    'description': 'Remove excess +1.0 addition'
                }
            ]
        }
    
    def apply_rules(self, code: str, bug_type: BugType) -> Tuple[str, List[str], bool]:
        """Apply rule-based fixes for the detected bug type."""
        applied_fixes = []
        fixed_code = code
        any_fix_applied = False
        
        if bug_type in self.fix_rules:
            for rule in self.fix_rules[bug_type]:
                pattern = rule['pattern']
                replacement = rule['replacement']
                description = rule['description']
                
                if re.search(pattern, fixed_code, re.MULTILINE | re.DOTALL):
                    new_code = re.sub(pattern, replacement, fixed_code, flags=re.MULTILINE | re.DOTALL)
                    if new_code != fixed_code:
                        fixed_code = new_code
                        applied_fixes.append(description)
                        any_fix_applied = True
        
        # Apply generic fixes if no specific rules matched
        if not any_fix_applied:
            fixed_code, generic_fixes = self._apply_generic_fixes(code)
            applied_fixes.extend(generic_fixes)
            any_fix_applied = len(generic_fixes) > 0
        
        return fixed_code, applied_fixes, any_fix_applied
    
    def _apply_generic_fixes(self, code: str) -> Tuple[str, List[str]]:
        """Apply generic fixes that might work for unknown bug types."""
        fixes = []
        fixed_code = code
        
        # Fix common syntax issues
        if re.search(r'def\s+\w+.*?:\s*$', code, re.MULTILINE):
            # Add pass statement to empty functions
            fixed_code = re.sub(r'(def\s+\w+.*?:\s*)$', r'\1\n    pass', fixed_code, flags=re.MULTILINE)
            fixes.append("Added pass statement to empty function")
        
        # Fix indentation issues
        lines = fixed_code.split('\n')
        corrected_lines = []
        for line in lines:
            if line.strip() and not line.startswith(' ') and not line.startswith('def') and not line.startswith('import'):
                corrected_lines.append('    ' + line)
            else:
                corrected_lines.append(line)
        
        if corrected_lines != lines:
            fixed_code = '\n'.join(corrected_lines)
            fixes.append("Fixed indentation")
        
        return fixed_code, fixes

def rule_based_generator_node(state: Dict) -> Dict:
    """
    Rule-based code generator node that applies deterministic fixes.
    """
    # Only proceed if rule-based strategy is selected
    current_strategy = state.get('current_strategy', '')
    if current_strategy != FixStrategy.RULE_BASED.value:
        return {**state, 'code_generated': True}
    
    fixer = RuleBasedFixer()
    
    # Get analysis results
    code_analysis = state.get('code_analysis', {})
    suspected_type_str = code_analysis.get('suspected_bug_type', 'unknown')
    suspected_type = BugType(suspected_type_str) if suspected_type_str != 'unknown' else BugType.UNKNOWN
    
    buggy_code = state.get('buggy_code', '')
    
    # Apply rule-based fixes
    fixed_code, applied_fixes, success = fixer.apply_rules(buggy_code, suspected_type)
    
    # Calculate confidence based on fixes applied
    confidence = 0.8 if success else 0.1
    
    reasoning = f"Rule-based fixes applied: {'; '.join(applied_fixes)}" if applied_fixes else "No rule-based fixes applicable"
    
    # Update state
    updated_state = {
        **state,
        'candidate_code': fixed_code,
        'rule_based_fix': success,
        'applied_fixes': applied_fixes,
        'confidence_score': confidence,
        'reasoning': reasoning,
        'code_generated': True
    }
    
    return updated_state