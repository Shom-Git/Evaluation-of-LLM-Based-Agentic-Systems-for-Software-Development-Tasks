from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum

class FixStrategy(Enum):
    RULE_BASED = "rule_based"
    LLM_GUIDED = "llm_guided" 
    HYBRID = "hybrid"

class BugType(Enum):
    OPERATOR_MISUSE = "operator_misuse"
    MISSING_LOGIC = "missing_logic"
    VARIABLE_MISUSE = "variable_misuse"
    VALUE_MISUSE = "value_misuse"
    EXCESS_LOGIC = "excess_logic"
    UNKNOWN = "unknown"

@dataclass
class TestResult:
    passed: bool
    log: str
    execution_time: float
    candidate_file: str
    errors: List[str] = field(default_factory=list)
    
@dataclass 
class Attempt:
    attempt_num: int
    candidate_code: str
    test_result: TestResult
    reasoning: str
    strategy_used: FixStrategy
    confidence: float
    rule_based_fix: bool = False

@dataclass
class CodeAnalysis:
    function_name: str
    parameters: List[str]
    return_type: Optional[str]
    suspected_bug_type: BugType
    complexity_score: int
    patterns_detected: List[str]
    confidence: float

@dataclass
class AgentState:
    # Core task data
    task_id: str
    buggy_code: str
    tests: str
    task_prompt: str
    canonical_solution: Optional[str] = None
    bug_type: str = "unknown"
    
    # Analysis state
    code_analysis: Optional[CodeAnalysis] = None
    test_requirements: List[str] = field(default_factory=list)
    error_patterns: List[str] = field(default_factory=list)
    
    # Execution state
    current_attempt: int = 0
    max_attempts: int = 3
    attempts: List[Attempt] = field(default_factory=list)
    
    # Strategy state
    current_strategy: FixStrategy = FixStrategy.RULE_BASED
    strategy_sequence: List[FixStrategy] = field(default_factory=lambda: [
        FixStrategy.RULE_BASED, 
        FixStrategy.LLM_GUIDED, 
        FixStrategy.HYBRID
    ])
    
    # Output state
    task_dir: str = ""
    final_status: Literal["solved", "unsolved", "error"] = "unsolved"
    final_code: Optional[str] = None
    confidence_score: float = 0.0
    
    # Node completion tracking
    analysis_complete: bool = False
    strategy_selected: bool = False
    code_generated: bool = False
    tests_executed: bool = False
    
    # Metadata
    total_time: float = 0.0
    llm_calls: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LangGraph compatibility."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, (Enum, FixStrategy, BugType)):
                result[key] = value.value
            elif hasattr(value, '__dict__'):  # dataclass instances
                result[key] = value.__dict__ if value else None
            elif isinstance(value, list) and value and hasattr(value[0], '__dict__'):
                result[key] = [item.__dict__ for item in value]
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create from dictionary for LangGraph compatibility."""
        # This would need proper deserialization logic
        # For now, create a new instance with basic fields
        return cls(
            task_id=data.get('task_id', ''),
            buggy_code=data.get('buggy_code', ''),
            tests=data.get('tests', ''),
            task_prompt=data.get('task_prompt', ''),
            task_dir=data.get('task_dir', '')
        )