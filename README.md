# 🤖 Evaluation of LLM-Based Agentic Systems for Software Development Tasks

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GPU Required](https://img.shields.io/badge/GPU-Required-red.svg)](https://pytorch.org/get-started/locally/)

A sophisticated AI agent system that automatically fixes buggy Python code using advanced LangGraph workflows, rule-based heuristics, and LLM-guided code generation with comprehensive feedback loops.

## 🎯 **Project Overview**

### **Problem Statement**
Software debugging is one of the most time-consuming and challenging tasks in development. Traditional automated debugging tools often fail to understand context, lack reasoning capabilities, and cannot learn from previous attempts. This project addresses these limitations by creating an intelligent agentic system that combines multiple approaches to fix buggy Python code.

### **Solution Architecture**
We designed a multi-layered agentic system that:
- **Analyzes** code structure and identifies bug patterns using AST parsing
- **Strategizes** the optimal approach (rule-based, LLM-guided, or hybrid)  
- **Generates** corrected code using specialized algorithms
- **Tests** the solutions in sandboxed environments
- **Learns** from failures through comprehensive feedback loops
- **Iterates** up to N attempts with progressive learning

### **Key Innovation: Feedback-Driven Learning**
Unlike traditional systems that make isolated attempts, our agent implements a sophisticated feedback mechanism:
- Each failed attempt generates detailed error analysis
- Subsequent attempts receive context from all previous failures
- The system adapts its strategy based on error patterns
- LLM prompts are enhanced with failure-specific guidance

## 🏗️ **System Architecture**

### **Core Components**

#### **🔍 Analysis Node**
- **AST-based code parsing** for structural analysis
- **Bug pattern detection** (syntax errors, logic errors, missing implementations)
- **Complexity scoring** and confidence assessment
- **Test requirement extraction** from assertion statements

#### **🎯 Strategy Node**
- **Multi-strategy selection**: rule-based → LLM-guided → hybrid progression
- **Context-aware strategy switching** based on previous failures
- **Confidence-based strategy weighting**

#### **🛠️ Code Generation Nodes**
- **Rule-Based Generator**: Deterministic fixes for common patterns
- **LLM Generator**: StarCoder2-3B with advanced prompting and feedback integration
- **Hybrid Approach**: Combines rule-based fixes with LLM refinement

#### **🧪 Test Execution Node**
- **Sandboxed execution** environment for safety
- **Comprehensive error categorization** (syntax, runtime, logic errors)
- **Detailed logging** with execution traces and suggestions

#### **🔄 Feedback System**
- **Error pattern analysis** from failed attempts
- **Progressive prompt enhancement** for LLM calls
- **Strategy adaptation** based on failure history
- **Learning accumulation** across attempts

## 🚀 **Getting Started**

### **Prerequisites**

#### **Hardware Requirements**
- **GPU**: NVIDIA GPU with 8GB+ VRAM (recommended)
- **RAM**: 16GB+ system memory
- **Storage**: 10GB+ free space for models and experiments

#### **Software Requirements**
- **Python**: 3.8 or higher
- **CUDA**: Compatible version for PyTorch
- **Git**: For cloning the repository

### **Installation**

1. **Clone the Repository**
```bash
git clone https://github.com/Shom-Git/Evaluation-of-LLM-Based-Agentic-Systems-for-Software-Development-Tasks.git
cd Evaluation-of-LLM-Based-Agentic-Systems-for-Software-Development-Tasks
```

2. **Create Virtual Environment**
```bash
# Using conda (recommended)
conda create -n agent-env python=3.10
conda activate agent-env

# Or using venv
python -m venv agent-env
# Windows:
agent-env\Scripts\activate
# Linux/Mac:
source agent-env/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **GPU Setup** *(Manual Configuration Required)*
```bash
# Install PyTorch with CUDA support (adjust for your CUDA version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU availability
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
```

5. **Download Dataset**
```bash
cd data
python get_data.py  # Downloads HumanEvalFix dataset
```

### **Environment Setup (Optional)**

You can use the provided `environment.yml` file for quick setup with conda:
```bash
conda env create -f environment.yml
conda activate agent-env
```

> **Note:** The actual environment and dependencies may need adjustment depending on your GPU model, CUDA version, and system configuration. Some packages (especially for PyTorch and transformers) are highly dependent on your hardware and drivers. Always verify GPU compatibility and adjust the environment as needed for your machine.

### **Manual Setup Requirements**

⚠️ **Important**: The following require manual configuration:

1. **CUDA Installation**: Install appropriate CUDA toolkit for your GPU
2. **GPU Memory**: Ensure 8GB+ VRAM for StarCoder2-3B model
3. **Model Download**: First run will download ~6GB StarCoder2-3B model
4. **Experiments Directory**: System creates `./experiments/` for results storage

## 🎮 **Usage Guide**

### **Command Line Interface**

The system provides a comprehensive CLI with multiple operation modes:

#### **Single Task Mode**
Fix a specific task from the dataset:
```bash
# Basic single task execution
python src/cli.py --mode single --task-id Python/0 --max-attempts 3

# With custom configuration
python src/cli.py --mode single --task-id Python/5 --max-attempts 5 --experiments-dir ./my_experiments
```

#### **Batch Evaluation Mode**
Evaluate on multiple tasks with comprehensive metrics:

**Option 1: Command Line Arguments**
```bash
# Evaluate specific task range
python src/cli.py --mode batch --task-range 0-30 --max-attempts 3

# Evaluate first N tasks
python src/cli.py --mode batch --max-tasks 20 --max-attempts 3

# Full dataset evaluation
python src/cli.py --mode batch --max-attempts 3
```

**Option 2: Interactive Mode**
```bash
python src/cli.py --mode batch
# Then choose:
# 1. Specify task range (e.g., 0-30)
# 2. Specify max tasks
# 3. Full dataset
```

### **Example Output**

#### **Single Task Execution**
```
🚀 Starting workflow with max 3 attempts
🔍 Analyzing code...
Analysis complete: Bug type = missing_logic

=== 🔄 ATTEMPT 1/3 ===
🎯 Selecting strategy...
Strategy selected: rule_based
🔧 Generating code using rule_based approach...
✅ Code generated (156 chars)
🧪 Running tests...
❌ ATTEMPT 1 FAILED: AssertionError: expected True, got False
🔍 Analyzing failure for next attempt...
📝 Feedback generated: LOGIC ERROR: Algorithm is wrong - review logic

=== 🔄 ATTEMPT 2/3 ===
🎯 Selecting strategy...
Strategy selected: llm_guided
🔧 Generating code using llm_guided approach...
✅ Code generated (198 chars)
🧪 Running tests...
🎉 ATTEMPT 2 SUCCEEDED!

📊 Summary: 2 attempts made, Status: solved
Final status: solved
Total attempts: 2
Total time: 89.45s
LLM calls: 1
```

#### **Batch Evaluation Results**
```
Evaluating on 21 problems with max 3 attempts each...

Evaluating problem 1/21: Python/40
Status: solved, Attempts: 2
Pass rate so far: 1.000, Avg attempts: 2.0

Evaluating problem 2/21: Python/41
Status: solved, Attempts: 1
Pass rate so far: 1.000, Avg attempts: 1.5

...

Evaluation complete!
Pass@1: 0.476 (10/21)    # First attempt success rate
Pass@3: 0.524 (11/21)    # Success within 3 attempts  
Average attempts: 1.8     # Mean attempts needed
Total time: 1250.5s       # Total execution time
Results saved to: experiments/results.json
```

## 📊 **Performance & Results**

### **Achieved Performance**
During extensive evaluation on the HumanEvalFix dataset:

- **Pass@1 = 48.4%** on tasks 40-60 (21 tasks achieved ones)
- **Pass@3 = 52.4%** with feedback learning
- **Average attempts**: 1.8 per task
- **Strategy effectiveness**: Hybrid > LLM-guided > Rule-based

### **Performance Characteristics**
- **Execution Time**: 60-120 seconds per task (GPU-dependent)
- **Memory Usage**: ~8GB GPU VRAM, ~4GB System RAM
- **Success Patterns**: Logic errors > Syntax errors > Complex algorithmic bugs

### **Development Challenges**
⏱️ **Time Investment Note**: A significant portion of the development time (approximately 60-70%) was spent on system verification and waiting for long evaluation runs to complete. The iterative nature of testing improvements on the full dataset required patience and careful experiment design.

## 🔧 **System Features**

### **Advanced Capabilities**
- ✅ **Multi-Strategy Approach**: Rule-based, LLM-guided, and hybrid generation
- ✅ **Feedback Learning**: Each attempt learns from previous failures
- ✅ **Sandboxed Execution**: Safe code execution with timeout protection
- ✅ **Comprehensive Logging**: Detailed execution traces and error analysis
- ✅ **GPU Optimization**: 8-bit quantization for efficient model usage
- ✅ **Flexible CLI**: Interactive and command-line batch processing
- ✅ **Progress Tracking**: Real-time metrics and success rate monitoring

### **System Verification**
```bash
# Quick system test
python test_fixes.py

# Verify specific components
python -c "from src.workflows.main_agent import CodeFixingAgent; print('✅ System ready!')"
```

### Common Issues

1. **GPU Memory Issues**:
```python
# In src/config.py
USE_8BIT = True  # Enable 8-bit quantization
# Or force CPU mode:
DEVICE = "cpu"
```

2. **Import Errors**:
## 📁 **Project Structure**

```
Evaluation-of-LLM-Based-Agentic-Systems-for-Software-Development-Tasks/
├── README.md                      #  This documentation
├── environment.yml               #  Python which I had
├── test_fixes.py                  #  System verification script
├── data/
│   ├── get_data.py               #  Dataset download utility
│   └── humanevalpack_python.jsonl #  HumanEvalFix dataset
└── src/
    ├── cli.py                    #  Main command-line interface
    ├── config.py                 #  System configuration
    ├── core/
    │   └── state.py             #  State management classes
    ├── workflows/
    │   └── main_agent.py        #  Main orchestration workflow
    └── nodes/
        ├── analysis_node.py      #  Code analysis with AST parsing
        ├── strategy_node.py      #  Strategy selection logic
        ├── rule_based_generator.py #  Deterministic bug fixes
        ├── llm_generator_node.py #  LLM-guided code generation
        ├── test_execution_node.py #  Sandboxed test execution
        ├── sandbox_runner.py     #  Safe execution environment
        └── utils.py             #  Utility functions
```


## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 📞 **Support**

If you encounter issues or have questions:

1. **Run** `python test_fixes.py` for system verification
2. **Create** a GitHub issue with detailed information
3. **Include** system specs, error logs, and reproduction steps

---


## Advanced Usage

### Custom Bug Detection
Add new patterns in `src/nodes/analysis_node.py`:
```python
self.bug_patterns = {
    BugType.YOUR_TYPE: [
        (r'your_regex_pattern', "Description"),
    ]
}
```

### Custom Fix Rules
Add rules in `src/nodes/rule_based_generator.py`:
```python
self.fix_rules = {
    BugType.YOUR_TYPE: [
        {
            'pattern': r'buggy_pattern',
            'replacement': r'fixed_pattern',
            'description': 'What this fixes'
        }
    ]
}
```

## Evaluation Metrics

The system implements proper HumanEvalFix evaluation:
- **Pass@k**: Standard metric from the paper
- **Bug type analysis**: Performance breakdown by bug category
- **Strategy effectiveness**: Which approaches work best
- **Time and resource usage**: Efficiency metrics

## Differences from Original Implementation

### Improvements
1. **Proper Agentic Architecture**: Specialized nodes vs monolithic LLM node
2. **Multi-Strategy Approach**: Rule-based, LLM-guided, and hybrid strategies
3. **Better Error Analysis**: Detailed categorization and feedback
4. **Iterative Learning**: Each attempt builds on previous ones
5. **Fallback Support**: Works without LangGraph dependencies
6. **Comprehensive Logging**: Full execution traces for analysis

### Architecture Changes
- Split single ReAct loop into specialized nodes
- Added strategy selection and routing
- Enhanced state management
- Better separation of concerns
- Improved error handling and recovery

## Citation

If you use this system, please cite the relevant papers:
- HumanEvalFix: https://arxiv.org/pdf/2210.03629
- HumanEvalPack: https://arxiv.org/pdf/2308.07124
