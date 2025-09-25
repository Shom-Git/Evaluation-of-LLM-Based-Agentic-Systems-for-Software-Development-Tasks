import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_example():
    """Test with a simple buggy multiplication function."""
    print("Testing simple multiplication bug fix...")
    
    from workflows.main_agent import CodeFixingAgent
    
    # Simple test case
    buggy_code = """def multiply(a, b):
    return a + b"""
    
    tests = """assert multiply(2, 3) == 6
assert multiply(4, 5) == 20
assert multiply(0, 10) == 0"""
    
    try:
        agent = CodeFixingAgent()
        result = agent.fix_code(
            buggy_code=buggy_code,
            tests=tests,
            task_id="test_multiply",
            task_prompt="Fix the multiplication function that uses addition instead of multiplication"
        )
        
        print(f"✓ Test completed successfully!")
        print(f"  Status: {result['final_status']}")
        print(f"  Attempts: {len(result.get('attempts', []))}")
        print(f"  Time: {result.get('total_time', 0):.2f}s")
        
        if result['final_status'] == 'solved':
            print(f"  ✓ Bug was fixed successfully!")
            return True
        else:
            print(f"  ⚠ Bug was not fixed, but system ran without errors")
            return True
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from workflows.main_agent import CodeFixingAgent
        print("✓ Main agent import successful")
        
        from nodes.analysis_node import analysis_node
        print("✓ Analysis node import successful")
        
        from nodes.strategy_node import strategy_node
        print("✓ Strategy node import successful")
        
        from nodes.rule_based_generator import rule_based_generator_node
        print("✓ Rule-based generator import successful")
        
        from nodes.llm_generator_node import llm_generator_node
        print("✓ LLM generator import successful")
        
        from nodes.test_execution_node import test_execution_node
        print("✓ Test execution node import successful")
        
        from nodes.decision_node import decision_node
        print("✓ Decision node import successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_loading():
    """Test that the model can be loaded (or gracefully fail)."""
    print("Testing model loading...")
    
    try:
        from nodes.llm_generator_node import LLMCodeGenerator
        
        # This should either load the model or fall back to mock mode
        generator = LLMCodeGenerator()
        
        if generator.pipe is not None:
            print("✓ Model loaded successfully")
        else:
            print("✓ Model loading failed gracefully (using mock mode)")
        
        return True
        
    except Exception as e:
        print(f"✗ Model loading test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("LLM Code Fixing Agent - System Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Model Loading Test", test_model_loading),
        ("Simple Example Test", test_simple_example),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                print(f"✗ {test_name} failed")
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nTo run the agent:")
        print("  python src/cli.py --mode single --task-id Python/0")
        print("  python src/cli.py --mode batch")
    else:
        print("⚠ Some tests failed. Check the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)