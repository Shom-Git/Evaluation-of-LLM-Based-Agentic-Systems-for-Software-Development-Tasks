from typing import Dict, List
from core.state import FixStrategy, BugType

class StrategySelector:
    def __init__(self):
        # Define strategy effectiveness for different bug types
        self.strategy_effectiveness = {
            BugType.OPERATOR_MISUSE: {
                FixStrategy.RULE_BASED: 0.9,
                FixStrategy.LLM_GUIDED: 0.7,
                FixStrategy.HYBRID: 0.95
            },
            BugType.MISSING_LOGIC: {
                FixStrategy.RULE_BASED: 0.3,
                FixStrategy.LLM_GUIDED: 0.8,
                FixStrategy.HYBRID: 0.85
            },
            BugType.VARIABLE_MISUSE: {
                FixStrategy.RULE_BASED: 0.4,
                FixStrategy.LLM_GUIDED: 0.9,
                FixStrategy.HYBRID: 0.9
            },
            BugType.VALUE_MISUSE: {
                FixStrategy.RULE_BASED: 0.8,
                FixStrategy.LLM_GUIDED: 0.7,
                FixStrategy.HYBRID: 0.9
            },
            BugType.EXCESS_LOGIC: {
                FixStrategy.RULE_BASED: 0.6,
                FixStrategy.LLM_GUIDED: 0.8,
                FixStrategy.HYBRID: 0.85
            },
            BugType.UNKNOWN: {
                FixStrategy.RULE_BASED: 0.2,
                FixStrategy.LLM_GUIDED: 0.7,
                FixStrategy.HYBRID: 0.6
            }
        }
    
    def select_strategy(self, 
                       suspected_bug_type: BugType, 
                       confidence: float,
                       previous_attempts: List[Dict],
                       complexity_score: int) -> FixStrategy:
        """Select the best strategy based on analysis and history."""
        
        # If we have high confidence and it's a simple bug, try rule-based first
        if confidence > 0.8 and suspected_bug_type in [BugType.OPERATOR_MISUSE, BugType.VALUE_MISUSE]:
            if not any(attempt.get('strategy_used') == FixStrategy.RULE_BASED.value 
                      for attempt in previous_attempts):
                return FixStrategy.RULE_BASED
        
        # If rule-based failed or confidence is medium, try LLM
        if confidence > 0.5:
            if not any(attempt.get('strategy_used') == FixStrategy.LLM_GUIDED.value 
                      for attempt in previous_attempts):
                return FixStrategy.LLM_GUIDED
        
        # For complex cases or when other strategies failed, use hybrid
        return FixStrategy.HYBRID
    
    def adapt_strategy_sequence(self, 
                               current_attempt: int,
                               previous_results: List[Dict]) -> List[FixStrategy]:
        """Adapt strategy sequence based on previous results."""
        
        if current_attempt == 0:
            return [FixStrategy.RULE_BASED, FixStrategy.LLM_GUIDED, FixStrategy.HYBRID]
        
        # If rule-based worked well, prioritize it
        rule_based_success = any(
            attempt.get('strategy_used') == FixStrategy.RULE_BASED.value and 
            attempt.get('test_result', {}).get('passed', False)
            for attempt in previous_results
        )
        
        if rule_based_success:
            return [FixStrategy.RULE_BASED, FixStrategy.HYBRID]
        
        # If LLM showed promise, focus on LLM strategies
        llm_partial_success = any(
            attempt.get('strategy_used') == FixStrategy.LLM_GUIDED.value and
            len(attempt.get('test_result', {}).get('errors', [])) < 3
            for attempt in previous_results
        )
        
        if llm_partial_success:
            return [FixStrategy.LLM_GUIDED, FixStrategy.HYBRID]
        
        return [FixStrategy.HYBRID]

def strategy_node(state: Dict) -> Dict:
    """
    Strategy selection node that chooses the best fix approach.
    """
    selector = StrategySelector()
    
    # Extract analysis results
    code_analysis = state.get('code_analysis', {})
    suspected_type_str = code_analysis.get('suspected_bug_type', 'unknown')
    suspected_type = BugType(suspected_type_str) if suspected_type_str != 'unknown' else BugType.UNKNOWN
    confidence = code_analysis.get('confidence', 0.0)
    complexity = code_analysis.get('complexity_score', 1)
    
    # Get attempt history
    attempts = state.get('attempts', [])
    current_attempt = state.get('current_attempt', 0)
    
    # Select strategy
    selected_strategy = selector.select_strategy(
        suspected_type, confidence, attempts, complexity
    )
    
    # Adapt strategy sequence for future attempts
    strategy_sequence = selector.adapt_strategy_sequence(current_attempt, attempts)
    
    # Update state
    updated_state = {
        **state,
        'current_strategy': selected_strategy.value,
        'strategy_sequence': [s.value for s in strategy_sequence],
        'strategy_selected': True
    }
    
    return updated_state