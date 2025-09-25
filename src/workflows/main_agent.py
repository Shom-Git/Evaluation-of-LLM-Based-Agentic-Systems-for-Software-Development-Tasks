"""
Main LangGraph workflow that orchestrates the code fixing agent.
This implements a proper agentic system with multiple specialized nodes.
"""
import os
import time
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from langgraph.graph import StateGraph, START, END

class StateGraph:
    def __init__(self, schema):
        self.nodes = {}
        self.edges = {}
            
    def add_node(self, name, func):
        self.nodes[name] = func
            
    def add_edge(self, from_node, to_node):
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
            
    def add_conditional_edges(self, from_node, condition_func):
        # Store conditional edges for manual handling
        self.edges[f"{from_node}_conditional"] = condition_func
            
    def compile(self):
        return CompiledGraph(self.nodes, self.edges)
    
class CompiledGraph:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
            
    def invoke(self, initial_state):
        # Simple fallback execution without full LangGraph features
        return self._simple_execution(initial_state)
            
    def _simple_execution(self, state):
        # Execute nodes in a simple sequence for fallback
        if "analysis" in self.nodes:
            state = self.nodes["analysis"](state)
        if "strategy" in self.nodes:
            state = self.nodes["strategy"](state)
            
        strategy = state.get('current_strategy', 'rule_based')
        if strategy == 'rule_based' and "rule_generation" in self.nodes:
            state = self.nodes["rule_generation"](state)
        elif "llm_generation" in self.nodes:
            state = self.nodes["llm_generation"](state)
                
        if "test_execution" in self.nodes:
            state = self.nodes["test_execution"](state)
        if "decision" in self.nodes:
            state = self.nodes["decision"](state)
                
        return state
    
START = "START"
END = "END"

# Import all the nodes
from nodes.analysis_node import analysis_node
from nodes.strategy_node import strategy_node
from nodes.rule_based_generator import rule_based_generator_node
from nodes.llm_generator_node import llm_generator_node
from nodes.test_execution_node import test_execution_node
from nodes.decision_node import decision_node

class CodeFixingAgent:
    def __init__(self, base_dir: str = None):
        # Import config here to avoid circular imports
        from config import Config
        
        if base_dir:
            self.base_dir = Config.setup_paths(base_dir)
        else:
            self.base_dir = Config.setup_paths()
            
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph state graph for the code fixing agent."""
        
        # Create the state graph
        graph = StateGraph(dict)
        
        # Add all nodes
        graph.add_node("analysis", analysis_node)
        graph.add_node("strategy", strategy_node) 
        graph.add_node("rule_generation", rule_based_generator_node)
        graph.add_node("llm_generation", llm_generator_node)
        graph.add_node("test_execution", test_execution_node)
        graph.add_node("decision", decision_node)
        
        # Add conditional edges based on strategy
        def route_after_strategy(state: Dict) -> str:
            """Route to appropriate generator based on selected strategy."""
            strategy = state.get('current_strategy', 'rule_based')
            if strategy == 'rule_based':
                return "rule_generation"
            else:
                return "llm_generation"
        
        def route_after_decision(state: Dict) -> str:
            """Route based on decision node output."""
            if state.get('done', False):
                return END
            else:
                return "strategy"  # Try again with new strategy
        
        # Define the workflow edges
        graph.add_edge(START, "analysis")
        graph.add_edge("analysis", "strategy")
        
        # Conditional routing after strategy selection
        graph.add_conditional_edges("strategy", route_after_strategy)
        
        # Both generators go to test execution
        graph.add_edge("rule_generation", "test_execution") 
        graph.add_edge("llm_generation", "test_execution")
        
        # Test execution goes to decision
        graph.add_edge("test_execution", "decision")
        
        # Conditional routing after decision
        graph.add_conditional_edges("decision", route_after_decision)
        
        return graph.compile()
    
    def _execute_workflow_simple(self, state: Dict) -> Dict:
        """Execute workflow with proper feedback loop and multiple attempts."""
        # Import node functions
        try:
            from nodes.analysis_node import analysis_node
            from nodes.strategy_node import strategy_node  
            from nodes.rule_based_generator import rule_based_generator_node
            from nodes.llm_generator_node import llm_generator_node
            from nodes.test_execution_node import test_execution_node
        except ImportError as e:
            print(f"Import error: {e}")
            # Fallback - use the existing instances if available
            analysis_node = self._get_node_function('analysis')
            strategy_node = self._get_node_function('strategy')
            rule_based_generator_node = self._get_node_function('rule_generation')
            llm_generator_node = self._get_node_function('llm_generation')
            test_execution_node = self._get_node_function('test_execution')
        
        max_attempts = state.get('max_attempts', 3)
        print(f"🚀 Starting workflow with max {max_attempts} attempts")
        
        # Initial analysis (once)
        print("🔍 Analyzing code...")
        state = analysis_node(state)
        print(f"Analysis complete: Bug type = {state.get('code_analysis', {}).get('suspected_bug_type', 'unknown')}")
        
        attempts = []
        
        for attempt in range(max_attempts):
            print(f"\n=== 🔄 ATTEMPT {attempt + 1}/{max_attempts} ===")
            state['current_attempt'] = attempt + 1
            
            # Strategy selection with feedback from previous attempts
            print("🎯 Selecting strategy...")
            state['attempts'] = attempts  # Pass previous attempts for feedback
            state = strategy_node(state)
            strategy = state.get('current_strategy', 'rule_based')
            print(f"Strategy selected: {strategy}")
            
            # Code generation with feedback loop
            print(f"🔧 Generating code using {strategy} approach...")
            if strategy == 'rule_based':
                state = rule_based_generator_node(state)
            else:
                # LLM generator gets feedback from all previous attempts
                state = llm_generator_node(state)
            
            # Validate code generation
            candidate_code = state.get('candidate_code', '').strip()
            if not candidate_code:
                print(f"⚠️ No code generated in attempt {attempt + 1}")
                # Create failed attempt record
                attempt_record = {
                    'attempt_num': attempt + 1,
                    'candidate_code': '',
                    'test_result': {'passed': False, 'log': 'No code generated'},
                    'reasoning': 'Code generation failed',
                    'strategy_used': strategy,
                    'confidence': 0.0,
                    'success': False
                }
                attempts.append(attempt_record)
                continue
            
            print(f"✅ Code generated ({len(candidate_code)} chars)")
            print(f"Preview: {candidate_code[:100]}...")
            
            # Test execution
            print("🧪 Running tests...")
            state = test_execution_node(state)
            
            # Process test results
            test_result = state.get('test_result', {})
            success = test_result.get('passed', False)
            
            # Create attempt record with feedback
            attempt_record = {
                'attempt_num': attempt + 1,
                'candidate_code': candidate_code,
                'test_result': test_result,
                'reasoning': state.get('reasoning', '') + " " + state.get('llm_reasoning', ''),
                'strategy_used': strategy,
                'confidence': state.get('confidence_score', 0.0),
                'rule_based_fix': state.get('rule_based_fix', False),
                'success': success
            }
            attempts.append(attempt_record)
            
            if success:
                print(f"🎉 ATTEMPT {attempt + 1} SUCCEEDED!")
                state['final_status'] = 'solved'
                state['done'] = True
                state['attempts'] = attempts
                break
            else:
                error_msg = test_result.get('log', 'Unknown error')
                print(f"❌ ATTEMPT {attempt + 1} FAILED: {error_msg[:150]}...")
                
                # FEEDBACK ANALYSIS: Learn from failure
                if attempt < max_attempts - 1:  # Not the last attempt
                    print(f"🔍 Analyzing failure for next attempt...")
                    
                    # Provide feedback context for next attempt
                    failure_feedback = self._generate_failure_feedback(attempt_record, attempts)
                    state['failure_feedback'] = failure_feedback
                    state['previous_errors'] = [a['test_result'].get('log', '') for a in attempts if not a['success']]
                    
                    print(f"📝 Feedback generated: {failure_feedback[:100]}...")
                
                # Reset state for next attempt but preserve learning
                state['candidate_code'] = ''
                state['reasoning'] = ''
                state['llm_reasoning'] = ''
                state['confidence_score'] = 0.0
                state['rule_based_fix'] = False
                state['code_generated'] = False
                state['tests_executed'] = False
        
        # Final processing
        state['attempts'] = attempts
        
        if not state.get('done', False):
            state['final_status'] = 'unsolved'
            state['done'] = True
            print(f"❌ All {max_attempts} attempts failed")
        
        total_attempts = len(attempts)
        print(f"\n📊 Summary: {total_attempts} attempts made, Status: {state.get('final_status', 'unknown')}")
        
        return state
    
    def _generate_failure_feedback(self, failed_attempt: Dict, all_attempts: List[Dict]) -> str:
        """Generate feedback for the next attempt based on previous failures."""
        candidate_code = failed_attempt.get('candidate_code', '')
        test_result = failed_attempt.get('test_result', {})
        error_log = test_result.get('log', '')
        strategy_used = failed_attempt.get('strategy_used', '')
        
        feedback_parts = []
        
        # Error type analysis
        if 'SyntaxError' in error_log:
            feedback_parts.append("SYNTAX ERROR DETECTED: Check for missing colons, parentheses, or indentation issues.")
        elif 'NameError' in error_log:
            feedback_parts.append("NAME ERROR: Variable or function name not defined correctly.")
        elif 'TypeError' in error_log:
            feedback_parts.append("TYPE ERROR: Check function parameters and return types.")
        elif 'AssertionError' in error_log:
            feedback_parts.append("LOGIC ERROR: The function logic is incorrect - review the algorithm.")
        elif 'IndentationError' in error_log:
            feedback_parts.append("INDENTATION ERROR: Fix the code indentation.")
        
        # Pattern analysis from code
        if candidate_code:
            if 'for' in candidate_code and 'return' not in candidate_code:
                feedback_parts.append("MISSING RETURN: Your loop doesn't return a value.")
            if 'if' in candidate_code and ':' not in candidate_code:
                feedback_parts.append("MISSING COLON: Add colon after if statement.")
            if 'def' not in candidate_code:
                feedback_parts.append("MISSING FUNCTION: You need to define the complete function.")
        
        # Strategy-specific feedback
        if strategy_used == 'rule_based' and len(all_attempts) > 0:
            feedback_parts.append("RULE-BASED FAILED: Try more sophisticated logic or use LLM approach.")
        elif strategy_used == 'llm_guided':
            feedback_parts.append("LLM APPROACH FAILED: Review the error and try a different algorithm.")
        
        # Previous attempt patterns
        if len(all_attempts) > 1:
            prev_errors = [a['test_result'].get('log', '') for a in all_attempts if not a['success']]
            if len(set(prev_errors)) == 1:
                feedback_parts.append("REPEATED ERROR: Same error as before - try completely different approach.")
        
        return " ".join(feedback_parts) if feedback_parts else "General failure - review approach."
    
    def _get_node_function(self, node_name: str):
        """Get node function from the graph if available."""
        if hasattr(self, 'graph') and hasattr(self.graph, 'nodes'):
            return self.graph.nodes.get(node_name, lambda x: x)
        return lambda x: x  # No-op fallback
        
        # Final decision
        if not state.get('done', False):
            state['final_status'] = 'unsolved'
            state['done'] = True
            print(f"❌ All {max_attempts} attempts failed")
        
        total_attempts = len(state.get('attempts', []))
        print(f"\n📊 Summary: {total_attempts} attempts made, Status: {state.get('final_status', 'unknown')}")
            
        return state
    
    def _create_task_directory(self, task_id: str) -> str:
        """Create a unique directory for this task."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        task_dir = self.base_dir / f"{task_id}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)
        return str(task_dir)
    
    def fix_code(self, 
                 buggy_code: str, 
                 tests: str, 
                 task_id: str = "task",
                 task_prompt: str = "",
                 canonical_solution: str = None,
                 bug_type: str = "unknown",
                 max_attempts: int = 3) -> Dict[str, Any]:
        """
        Fix buggy code using the agentic workflow.
        
        Args:
            buggy_code: The buggy Python code to fix
            tests: Test cases the fixed code should pass
            task_id: Unique identifier for this task
            task_prompt: Description of what the code should do
            canonical_solution: Optional correct solution for reference
            bug_type: Type of bug if known
            max_attempts: Maximum number of fix attempts
            
        Returns:
            Dictionary containing results and execution trace
        """
        
        # Create task directory
        task_dir = self._create_task_directory(task_id)
        
        # Initialize state
        initial_state = {
            # Core task data
            'task_id': task_id,
            'buggy_code': buggy_code,
            'tests': tests,
            'task_prompt': task_prompt,
            'canonical_solution': canonical_solution,
            'bug_type': bug_type,
            
            # Execution control
            'current_attempt': 0,
            'max_attempts': max_attempts,
            'attempts': [],
            'task_dir': task_dir,
            
            # State tracking
            'analysis_complete': False,
            'strategy_selected': False,
            'code_generated': False,
            'tests_executed': False,
            'done': False,
            
            # Strategy configuration
            'strategy_sequence': ['rule_based', 'llm_guided', 'hybrid'],
            'current_strategy': 'rule_based',
            
            # Results
            'final_status': 'unsolved',
            'final_code': None,
            'confidence_score': 0.0,
            'total_time': 0.0,
            'llm_calls': 0
        }
        
        # Execute the workflow
        start_time = time.time()
        
        try:
            # Force simple execution with feedback loop (LangGraph fallback is buggy)
            final_state = self._execute_workflow_simple(initial_state)
                
            execution_time = time.time() - start_time
            final_state['total_time'] = execution_time
            
            # Save execution log
            self._save_execution_log(final_state, task_dir)
            
            return final_state
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_state = {
                **initial_state,
                'final_status': 'error',
                'error': str(e),
                'total_time': execution_time
            }
            
            self._save_execution_log(error_state, task_dir)
            raise e
    
    def _save_execution_log(self, state: Dict, task_dir: str):
        """Save detailed execution log for analysis."""
        import json
        
        log_file = Path(task_dir) / "execution_log.json"
        
        # Create a serializable version of the state
        serializable_state = {}
        for key, value in state.items():
            try:
                json.dumps(value)  # Test if serializable
                serializable_state[key] = value
            except (TypeError, ValueError):
                serializable_state[key] = str(value)
        
        with open(log_file, 'w') as f:
            json.dump(serializable_state, f, indent=2)
    
    def evaluate_on_dataset(self, dataset_path: str, output_path: str, max_problems: int = None, 
                           task_range: tuple = None, max_attempts: int = 3):
        """
        Evaluate the agent on a HumanEvalFix dataset.
        
        Args:
            dataset_path: Path to JSONL dataset file
            output_path: Path to save evaluation results
            max_problems: Maximum number of problems to evaluate (None for all)
            task_range: Tuple (start, end) for task range selection
            max_attempts: Maximum attempts per task
        """
        import json
        
        # Load dataset
        problems = []
        with open(dataset_path, 'r') as f:
            for line in f:
                if line.strip():
                    problems.append(json.loads(line))
        
        # Apply task range filter
        if task_range:
            start, end = task_range
            problems = problems[start:end+1]  # +1 to include end index
            print(f"Selected tasks {start} to {end}")
        elif max_problems:
            problems = problems[:max_problems]
        
        print(f"Evaluating on {len(problems)} problems with max {max_attempts} attempts each...")
        
        results = []
        solved_count = 0
        total_attempts = 0
        total_time = 0
        
        for i, problem in enumerate(problems):
            task_id = problem.get('task_id', f'problem_{i}')
            print(f"\nEvaluating problem {i+1}/{len(problems)}: {task_id}")
            
            try:
                result = self.fix_code(
                    buggy_code=problem['buggy_solution'],
                    tests=problem['test'],
                    task_id=task_id.replace('/', '_'),
                    task_prompt=problem.get('prompt', problem.get('docstring', '')),
                    canonical_solution=problem.get('canonical_solution'),
                    bug_type=problem.get('bug_type', 'unknown'),
                    max_attempts=max_attempts
                )
                
                if result['final_status'] == 'solved':
                    solved_count += 1
                
                attempts_made = len(result.get('attempts', []))
                total_attempts += attempts_made
                total_time += result.get('total_time', 0)
                
                # Store result summary
                result_summary = {
                    'task_id': task_id,
                    'bug_type': problem.get('bug_type'),
                    'final_status': result['final_status'],
                    'attempts': attempts_made,
                    'total_time': result.get('total_time', 0),
                    'llm_calls': result.get('llm_calls', 0),
                    'task_dir': result.get('task_dir'),
                    'first_attempt_success': attempts_made > 0 and result.get('attempts', [{}])[0].get('test_result', {}).get('passed', False)
                }
                
                results.append(result_summary)
                
                # Print progress
                pass_rate = solved_count / (i + 1)
                avg_attempts = total_attempts / (i + 1)
                print(f"Status: {result['final_status']}, Attempts: {attempts_made}")
                print(f"Pass rate so far: {pass_rate:.3f}, Avg attempts: {avg_attempts:.1f}")
                
            except Exception as e:
                print(f"Error evaluating problem {i}: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'task_id': task_id,
                    'final_status': 'error',
                    'error': str(e),
                    'attempts': 0
                })
        
        # Calculate metrics
        pass_at_1 = sum(1 for r in results if r.get('first_attempt_success', False)) / len(results) if results else 0
        pass_at_k = solved_count / len(results) if results else 0
        avg_attempts = total_attempts / len(results) if results else 0
        
        # Save results
        final_results = {
            'dataset': dataset_path,
            'task_range': f"{task_range[0]}-{task_range[1]}" if task_range else "all",
            'max_attempts': max_attempts,
            'total_problems': len(problems),
            'solved': solved_count,
            'pass_rate': pass_at_k,
            'pass_at_1': pass_at_1,
            'pass_at_k': pass_at_k,
            'avg_attempts': avg_attempts,
            'total_time': total_time,
            'results': results
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\nEvaluation complete!")
        print(f"Pass@1: {pass_at_1:.3f} ({sum(1 for r in results if r.get('first_attempt_success', False))}/{len(results)})")
        print(f"Pass@{max_attempts}: {pass_at_k:.3f} ({solved_count}/{len(results)})")
        print(f"Average attempts: {avg_attempts:.1f}")
        print(f"Total time: {total_time:.1f}s")
        print(f"Results saved to: {output_path}")
        
        return final_results

# Legacy compatibility function
def run_fix_agent_for_example(buggy_code: str, tests: str, task_id: str = "task", task_prompt: str = "") -> Dict:
    """
    Legacy compatibility function for existing CLI.
    """
    agent = CodeFixingAgent()
    result = agent.fix_code(buggy_code, tests, task_id, task_prompt)
    
    # Convert to legacy format
    legacy_result = {
        'final_status': result['final_status'],
        'task_dir': result['task_dir'],
        'history': result.get('attempts', [])
    }
    
    return legacy_result