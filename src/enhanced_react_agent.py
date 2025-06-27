"""
Enhanced ReAct Agent with Memory
增强版ReAct Agent，支持记忆功能，所有请求都通过ReAct循环处理
"""
import re
import json
import pickle
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from colorama import init, Fore, Style

from src.deepseek_client import DeepSeekClient
from .tools import ToolRegistry, create_core_tool_registry

# 初始化colorama
init(autoreset=True)

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, memory_file: str = "agent_memory.pkl"):
        self.memory_file = memory_file
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_summaries: List[Dict[str, Any]] = []
        self.load_memory()
    
    def load_memory(self):
        """加载记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'rb') as f:
                    memory_data = pickle.load(f)
                    self.conversation_history = memory_data.get('conversation_history', [])
                    self.session_summaries = memory_data.get('session_summaries', [])
            except Exception as e:
                print(f"加载记忆失败: {e}")
    
    def save_memory(self):
        """保存记忆"""
        try:
            memory_data = {
                'conversation_history': self.conversation_history,
                'session_summaries': self.session_summaries
            }
            with open(self.memory_file, 'wb') as f:
                pickle.dump(memory_data, f)
        except Exception as e:
            print(f"保存记忆失败: {e}")
    
    def add_session(self, problem: str, solution: str, conversation: List[Dict[str, str]]):
        """添加会话记录"""
        session = {
            'timestamp': datetime.now().isoformat(),
            'problem': problem,
            'solution': solution,
            'conversation_length': len(conversation)
        }
        self.session_summaries.append(session)
        
        # 保存完整对话历史（限制数量以避免内存过大）
        if len(self.conversation_history) > 50:  # 保留最近50次对话
            self.conversation_history = self.conversation_history[-50:]
        
        self.conversation_history.extend(conversation)
        self.save_memory()
    
    def get_relevant_context(self, current_problem: str, max_context: int = 3) -> str:
        """获取相关的历史上下文"""
        if not self.session_summaries:
            return ""
        
        # 简单的关键词匹配来找相关历史
        relevant_sessions = []
        problem_keywords = set(current_problem.lower().split())
        
        for session in self.session_summaries[-10:]:  # 检查最近10次会话
            session_keywords = set(session['problem'].lower().split())
            # 计算关键词重叠度
            overlap = len(problem_keywords & session_keywords)
            if overlap > 0:
                relevant_sessions.append((session, overlap))
        
        # 按相关性排序
        relevant_sessions.sort(key=lambda x: x[1], reverse=True)
        
        if not relevant_sessions:
            return ""
        
        context_parts = []
        for session, _ in relevant_sessions[:max_context]:
            context_parts.append(f"历史问题: {session['problem']}")
            context_parts.append(f"解决方案: {session['solution']}")
            context_parts.append(f"时间: {session['timestamp'][:19].replace('T', ' ')}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def get_memory_summary(self) -> str:
        """获取记忆摘要"""
        if not self.session_summaries:
            return "暂无历史记录"
        
        total_sessions = len(self.session_summaries)
        recent_sessions = self.session_summaries[-5:]
        
        summary = f"总共处理了 {total_sessions} 个问题\n\n最近的问题:\n"
        for i, session in enumerate(recent_sessions, 1):
            summary += f"{i}. {session['problem'][:50]}{'...' if len(session['problem']) > 50 else ''}\n"
            summary += f"   时间: {session['timestamp'][:19].replace('T', ' ')}\n"
        
        return summary

class EnhancedReActAgent:
    """增强版ReAct Agent - 支持记忆功能，所有请求都通过ReAct循环处理"""
    
    def __init__(
        self,
        deepseek_client: DeepSeekClient,
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: int = 10,
        verbose: bool = True,
        enable_memory: bool = True,
        memory_file: str = "agent_memory.pkl"
    ):
        self.client = deepseek_client
        # 使用create_core_tool_registry确保所有工具都被正确加载
        self.tool_registry = tool_registry or create_core_tool_registry(deepseek_client)
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.enable_memory = enable_memory
        
        # 初始化记忆管理器
        self.memory_manager = MemoryManager(memory_file) if enable_memory else None
        
        # 持久化对话历史（跨会话）
        self.persistent_conversation: List[Dict[str, str]] = []
        
        # 当前会话的对话历史
        self.conversation_history: List[Dict[str, str]] = []
        
        # 当前问题
        self.current_problem: str = ""
        
        # ReAct 系统提示词
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tool_registry.list_tools()
        ])
        
        base_prompt = f"""你是一个ReAct (Reasoning and Acting) 智能代理。你需要通过交替进行推理(Thought)和行动(Action)来解决问题。

⚠️ **重要：你必须优先使用工具来解决问题，而不是直接给出答案！**

可用工具:
{tools_description}

🎯 **系统三大核心功能智能判断指南:**

**功能1: 📤 文件上传智能分类处理**
- 🔍 **判断条件**: 用户上传了文件
- 🛠️ **使用工具**: `template_classifier`
- ✅ **处理逻辑**: 
  - 自动判断文档类型：模板文档 vs 资料文档
  - 模板文档 → 保存到模板库(templates_storage)，保留原始文件名 → **任务完成，停止处理**
  - 资料文档 → 自动调用RAG工具进行embedding处理
- 🔍 **关键词**: 上传、文档分类、文件处理、新文档
- 📄 **特征**: 用户刚上传的文档，需要智能分类处理
- ⚠️ **重要**: 对于纯粹的模板文档上传，template_classifier成功保存后即可给出Final Answer，无需继续处理

**功能2: 📄 长文档生成需求判断**
- 🔍 **判断条件**: 用户需求是生成长篇文档（多章节、连续文本、超过500字）
- 🛠️ **使用工具**: `advanced_long_document_generator`
- ✅ **处理逻辑**: 
  - 直接调用高级长文档生成工具
  - AI驱动的创作指令分析 → 智能大纲生成 → 逐章节内容生成 → 专业DOCX输出
- 🔍 **关键词**: 方案、报告、计划、规程、制度、分析、研究、技术文档、项目文档
- 📄 **特征**: 
  - 技术方案、施工方案、设计方案
  - 技术报告、可行性报告、评估报告
  - 项目计划、实施计划、工作计划
  - 操作规程、管理制度、技术规范

**功能3: 📋 模板文档生成需求判断**
- 🔍 **判断条件**: 用户需求是生成基于模板的文档（表格格式、需要填写的模板）
- 🛠️ **使用工具**: `professional_document_tool`
- ✅ **处理逻辑**: 
  - 从templates_storage文件夹中找到用户描述的模板文件
  - 结合用户提供的关键词去RAG检索相关资料
  - 将检索到的资料智能插入到模板的对应位置
- 🔍 **关键词**: 模板、记录、表格、申请、审批、检查、验收、登记、填写、复核
- 📄 **特征**: 
  - 各种记录表：复核记录、检查记录、验收记录、巡检记录
  - 申请表单：施工申请、变更申请、材料申请
  - 审批表格：审批单、签证单、工程联系单
  - 检测表格：试验记录、测量记录、质检记录
- 📋 **调用示例**: 参数格式为 file_path="templates_storage/现场复核记录.doc", user_request="为一号楼项目生成复核记录表"
- ⚠️ **注意**: 如果模板文件不存在，可以降级使用advanced_long_document_generator生成类似文档

**如果是其他需求（如简单问答、文档搜索等）**:
- 🛠️ **使用工具**: `rag_tool`
- ✅ **处理逻辑**: 进行向量搜索和内容检索

你必须严格按照以下格式进行推理和行动:

Thought: [你的推理过程，分析当前情况和下一步需要做什么，首先判断属于哪个核心功能]
Action: [工具名称]
Action Input: [工具的输入参数，如果是单个参数直接写，多个参数用JSON格式]
Observation: [工具执行结果，这部分由系统自动填充]

然后继续:
Thought: [基于观察结果的进一步推理]
Action: [下一个行动]
...

当你有了最终答案时，使用:
Thought: [最终推理]
Final Answer: [你的最终答案]

⚠️ **特别注意任务完成信号**:
- 当工具返回包含 "success": true, "status": "completed" 的结果时，这表示任务已经完全完成
- 此时应该立即停止ReAct循环，给出Final Answer，不要继续尝试其他操作
- 成功的文档生成会包含 docx_url 或 output_path，这就是最终结果
- **对于模板文档上传**: 当template_classifier成功保存模板文档后（返回"已保存到模板库"信息），任务即完成，应立即给出Final Answer，不要继续处理

🚨 **关键规则:**
1. **禁止直接回答** - 对于任何可以用工具解决的问题，都必须先调用相应工具
2. **工具优先** - 分析问题时首先考虑使用哪个工具，而不是自己编造答案
3. **识别任务完成** - 当工具返回"success": true, "status": "completed"时，立即停止并给出Final Answer
4. **三功能判断流程** - 这是最重要的！按以下顺序判断：
   
   **第一步：需求类型判断**
   - 📤 **文件上传** → `template_classifier` (智能分类处理)
   - 📄 **长文档生成** → `advanced_long_document_generator` (专业长文档生成)
   - 📋 **模板文档生成** → `professional_document_tool` (模板+RAG填充)
   - 📚 **其他检索需求** → `rag_tool` (向量搜索)
   
   **第二步：关键词识别**
   - 上传关键词：上传、文档分类、文件处理、新文档
   - 长文档关键词：方案、报告、计划、规程、制度、分析、研究、技术文档
   - 模板关键词：模板、记录、表格、申请、审批、检查、验收、登记、填写
   - 检索关键词：搜索、查找、检索、分析、提取
   
   **第三步：处理逻辑确认**
   - 上传处理：智能分类 → 模板保存 或 RAG处理
   - 长文档生成：创作指令分析 → 大纲生成 → 章节生成 → DOCX输出
   - 模板文档生成：找到模板文件 → RAG检索资料 → 智能填充插入
   - 检索处理：向量搜索 → 内容提取 → 结果返回

4. Action必须是可用工具列表中的工具名称
5. Action Input必须符合工具的要求
6. 每次行动后等待Observation结果
7. 基于Observation继续推理和行动，直到找到最终答案
8. 最多进行{self.max_iterations}轮推理和行动

开始解决问题吧！"""
        
        return base_prompt
    
    def _parse_response(self, response: str) -> Tuple[str, Optional[str], Optional[str]]:
        """解析LLM响应，提取推理、行动和输入"""
        # 查找Thought
        thought_match = re.search(r'Thought:\s*(.*?)(?=\n(?:Action|Final Answer):|$)', response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""
        
        # 查找Final Answer
        final_answer_match = re.search(r'Final Answer:\s*(.*)', response, re.DOTALL)
        if final_answer_match:
            final_answer = final_answer_match.group(1).strip()
            return thought, None, final_answer
        
        # 查找Action和Action Input
        action_match = re.search(r'Action:\s*(.*?)(?=\n|$)', response)
        action = action_match.group(1).strip() if action_match else None
        
        action_input_match = re.search(r'Action Input:\s*(.*?)(?=\n(?:Thought|Action|Final Answer):|$)', response, re.DOTALL)
        action_input = action_input_match.group(1).strip() if action_input_match else ""
        
        return thought, action, action_input
    
    def _execute_action(self, action: str, action_input: str) -> str:
        """执行工具行动"""
        try:
            tool = self.tool_registry.get_tool(action)
            if not tool:
                return f"错误：工具 '{action}' 不存在。可用工具: {', '.join([t['name'] for t in self.tool_registry.list_tools()])}"
            
            # 尝试解析JSON格式的输入
            try:
                if action_input.startswith('{') and action_input.endswith('}'):
                    params = json.loads(action_input)
                    return tool.execute(**params)
                else:
                    # 对于长文档生成工具，如果输入是简单字符串，将其作为request参数
                    if action == "long_document_generator":
                        return tool.execute(action="generate", request=action_input)
                    else:
                        # 其他工具尝试作为单个参数传递
                        return tool.execute(action_input)
            except json.JSONDecodeError:
                # JSON解析失败，根据工具类型处理
                if action == "long_document_generator":
                    return tool.execute(action="generate", request=action_input)
                else:
                    return tool.execute(action_input)
        
        except Exception as e:
            return f"执行工具 '{action}' 时发生错误: {str(e)}"
    
    def _print_step(self, step_type: str, content: str, color: str = Fore.WHITE):
        """打印步骤信息"""
        if self.verbose:
            print(f"{color}{step_type}: {content}")
    
    def solve(self, problem: str, use_enhanced_framework: bool = False) -> str:
        """
        解决问题的主要方法
        
        Args:
            problem: 用户问题
            use_enhanced_framework: 是否使用增强版三步骤框架（已弃用，统一使用ReAct循环）
        
        Returns:
            解决方案和结果
        """
        self.current_problem = problem
        self.conversation_history.append({"role": "user", "content": problem})
        
        # 统一使用ReAct循环处理所有请求
        # Agent会通过Thought → Action的方式自己决定调用哪个工具
        return self._react_loop(problem)
    
    def _react_loop(self, problem: str) -> str:
        """ReAct循环逻辑 - 处理所有类型的请求"""
        if self.verbose:
            print(f"{Fore.CYAN}{'='*50}")
            print(f"{Fore.CYAN}ReAct Agent 开始解决问题")
            print(f"{Fore.CYAN}问题: {problem}")
            print(f"{Fore.CYAN}{'='*50}")
        
        # 构建对话历史
        conversation = []
        conversation.append({"role": "system", "content": self.system_prompt})
        
        # 添加历史上下文（如果启用记忆）
        if self.memory_manager:
            context = self.memory_manager.get_relevant_context(problem)
            if context:
                conversation.append({"role": "system", "content": f"相关历史经验:\n{context}"})
                if self.verbose:
                    print(f"{Fore.YELLOW}📚 找到相关历史经验")
        
        conversation.append({"role": "user", "content": f"问题: {problem}"})
        
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n{Fore.YELLOW}--- 第 {iteration + 1} 轮 ---")
            
            # 获取LLM响应
            response, usage_info = self.client.chat_completion(conversation)
            conversation.append({"role": "assistant", "content": response})
            
            # 解析响应
            thought, action, action_input_or_final = self._parse_response(response)
            
            # 打印推理过程
            if thought:
                self._print_step("Thought", thought, Fore.BLUE)
            
            # 检查是否是最终答案
            if action is None and action_input_or_final:
                self._print_step("Final Answer", action_input_or_final, Fore.GREEN)
                
                # 保存到记忆
                if self.memory_manager:
                    self.memory_manager.add_session(problem, action_input_or_final, conversation)
                    if self.verbose:
                        print(f"{Fore.YELLOW}💾 已保存到记忆")
                
                return action_input_or_final
            
            # 执行行动
            if action:
                self._print_step("Action", action, Fore.MAGENTA)
                if action_input_or_final:
                    self._print_step("Action Input", action_input_or_final, Fore.MAGENTA)
                
                # 执行工具
                observation = self._execute_action(action, action_input_or_final or "")
                self._print_step("Observation", observation, Fore.CYAN)
                
                # 将观察结果添加到对话
                conversation.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                # 如果没有明确的action，可能是格式错误
                error_msg = "响应格式不正确，请按照 Thought -> Action -> Action Input 的格式"
                self._print_step("Error", error_msg, Fore.RED)
                conversation.append({"role": "user", "content": f"Error: {error_msg}"})
        
        # 达到最大迭代次数
        final_msg = f"达到最大迭代次数 ({self.max_iterations})，未能找到最终答案。"
        if self.verbose:
            print(f"{Fore.RED}{final_msg}")
        
        # 即使未完成也保存到记忆
        if self.memory_manager:
            self.memory_manager.add_session(problem, final_msg, conversation)
        
        return final_msg
    
    def interactive_mode(self):
        """增强的交互模式，支持记忆"""
        print(f"{Fore.GREEN}欢迎使用增强版 ReAct Agent 交互模式！")
        print(f"{Fore.YELLOW}可用工具: {', '.join([tool['name'] for tool in self.tool_registry.list_tools()])}")
        
        if self.memory_manager:
            print(f"{Fore.YELLOW}记忆功能: 已启用")
            print(f"{Fore.YELLOW}特殊命令: 输入 'memory' 查看历史记录")
        
        print(f"{Fore.YELLOW}输入 'quit' 或 'exit' 退出\n")
        
        while True:
            try:
                problem = input(f"{Fore.WHITE}请输入问题: ").strip()
                if problem.lower() in ['quit', 'exit', '退出']:
                    print(f"{Fore.GREEN}再见！")
                    break
                
                if problem.lower() == 'memory' and self.memory_manager:
                    print(f"\n{Fore.CYAN}📚 记忆摘要:")
                    print(self.memory_manager.get_memory_summary())
                    print()
                    continue
                
                if problem:
                    answer = self.solve(problem)
                    print(f"\n{Fore.GREEN}{'='*50}")
                    print(f"{Fore.GREEN}最终答案: {answer}")
                    print(f"{Fore.GREEN}{'='*50}\n")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}程序被中断")
                break
            except Exception as e:
                print(f"{Fore.RED}发生错误: {str(e)}")
    
    def clear_memory(self):
        """清除记忆"""
        if self.memory_manager:
            self.memory_manager.conversation_history.clear()
            self.memory_manager.session_summaries.clear()
            self.memory_manager.save_memory()
            print("记忆已清除") 