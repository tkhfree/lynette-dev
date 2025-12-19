"""
自然语言处理模块
将用户自然语言输入转换为结构化请求
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class Intent(Enum):
    """用户意图类型"""
    COMPILE = "compile"
    DEPLOY = "deploy"
    ANALYZE = "analyze"
    VALIDATE = "validate"
    CHECK_STATUS = "check_status"
    UNKNOWN = "unknown"


class NLPProcessor:
    """自然语言处理器"""
    
    # 意图识别关键词
    INTENT_PATTERNS = {
        Intent.COMPILE: [
            r"编译", r"生成", r"转换", r"compile", r"generate", r"convert",
            r"把.*编译成", r"将.*转换为", r"把.*转成"
        ],
        Intent.DEPLOY: [
            r"部署", r"发送", r"上传", r"deploy", r"send", r"upload",
            r"部署到", r"发送到", r"上传到"
        ],
        Intent.ANALYZE: [
            r"分析", r"检查", r"查看", r"analyze", r"check", r"view",
            r"分析代码", r"检查语法", r"查看结构"
        ],
        Intent.VALIDATE: [
            r"验证", r"校验", r"validate", r"verify"
        ],
        Intent.CHECK_STATUS: [
            r"状态", r"进度", r"结果", r"status", r"progress", r"result",
            r"查询.*状态", r"查看.*进度"
        ]
    }
    
    # 参数提取模式
    PARAMETER_PATTERNS = {
        "file_path": [
            r"([\w/\\\-]+\.pne)",
            r"文件[：:]\s*([\w/\\\-]+\.pne)",
            r"([\w/\\\-]+_main\.pne)"
        ],
        "config_file": [
            r"配置[文件]?[：:]\s*([\w/\\\-]+\.json)",
            r"service\.json",
            r"([\w/\\\-]+service\.json)"
        ],
        "output_dir": [
            r"(?:输出到|输出目录|output)[：:]\s*([\w/\\\-]+)",
            r"输出[：:]\s*([\w/\\\-]+)"
        ],
        "target": [
            r"(?:目标|架构|target)[：:]\s*(v1model|tna)",
            r"(v1model|tna)"
        ],
        "node": [
            r"(?:节点|node)[：:]\s*(\w+)",
            r"节点[：:]\s*(\w+)"
        ],
        "deploy_type": [
            r"(?:部署|发送)(?:代码|表项|entry|code)?",
            r"(code|entry|both)"
        ],
        "task_id": [
            r"任务[ID]?[：:]\s*([\w\-]+)",
            r"task[：:]\s*([\w\-]+)"
        ]
    }
    
    def __init__(self):
        """初始化NLP处理器"""
        # 编译意图的正则表达式
        self.intent_regex = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self.intent_regex[intent] = [re.compile(p, re.IGNORECASE) for p in patterns]
        
        # 参数提取的正则表达式
        self.param_regex = {}
        for param_name, patterns in self.PARAMETER_PATTERNS.items():
            self.param_regex[param_name] = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def classify_intent(self, query: str) -> Intent:
        """分类用户意图
        
        Args:
            query: 用户查询文本
            
        Returns:
            识别出的意图类型
        """
        query_lower = query.lower()
        
        # 按优先级检查各个意图
        for intent in [Intent.CHECK_STATUS, Intent.VALIDATE, Intent.ANALYZE, 
                       Intent.DEPLOY, Intent.COMPILE]:
            for pattern in self.intent_regex[intent]:
                if pattern.search(query):
                    return intent
        
        return Intent.UNKNOWN
    
    def extract_parameters(self, query: str, intent: Intent) -> Dict:
        """从查询中提取参数
        
        Args:
            query: 用户查询文本
            intent: 识别出的意图
            
        Returns:
            提取的参数字典
        """
        parameters = {}
        
        if intent == Intent.COMPILE:
            # 提取文件路径
            file_path = self._extract_first_match("file_path", query)
            if file_path:
                parameters["input_file"] = file_path
            
            # 提取配置文件
            config_file = self._extract_first_match("config_file", query)
            if config_file:
                parameters["config_file"] = config_file
            
            # 提取输出目录
            output_dir = self._extract_first_match("output_dir", query)
            if output_dir:
                parameters["output_dir"] = output_dir
            
            # 提取目标架构
            target = self._extract_first_match("target", query)
            if target:
                parameters["target"] = target
            
            # 判断模式
            if "service" in query.lower() or "config" in query.lower():
                parameters["mode"] = "service"
            elif file_path:
                parameters["mode"] = "debug"
        
        elif intent == Intent.DEPLOY:
            # 提取输出目录
            output_dir = self._extract_first_match("output_dir", query)
            if output_dir:
                parameters["output_dir"] = output_dir
            
            # 提取部署类型
            deploy_type = self._extract_first_match("deploy_type", query)
            if deploy_type:
                parameters["deploy_type"] = deploy_type
            else:
                # 默认部署代码
                parameters["deploy_type"] = "code"
            
            # 提取节点列表
            nodes = self._extract_all_matches("node", query)
            if nodes:
                parameters["nodes"] = nodes
        
        elif intent == Intent.ANALYZE:
            # 提取文件路径
            file_path = self._extract_first_match("file_path", query)
            if file_path:
                parameters["input_file"] = file_path
            
            # 判断分析类型
            if "语法" in query or "syntax" in query.lower():
                parameters["analysis_type"] = "syntax"
            elif "依赖" in query or "dependencies" in query.lower():
                parameters["analysis_type"] = "dependencies"
            elif "结构" in query or "structure" in query.lower():
                parameters["analysis_type"] = "structure"
            else:
                parameters["analysis_type"] = "all"
        
        elif intent == Intent.CHECK_STATUS:
            # 提取任务ID
            task_id = self._extract_first_match("task_id", query)
            if task_id:
                parameters["task_id"] = task_id
        
        elif intent == Intent.VALIDATE:
            # 提取P4文件路径
            p4_file = re.search(r"([\w/\\\-]+\.p4)", query)
            if p4_file:
                parameters["p4_file"] = p4_file.group(1)
            
            # 提取目标架构
            target = self._extract_first_match("target", query)
            if target:
                parameters["target"] = target
        
        return parameters
    
    def _extract_first_match(self, param_name: str, text: str) -> Optional[str]:
        """提取第一个匹配的参数值
        
        Args:
            param_name: 参数名称
            text: 要搜索的文本
            
        Returns:
            匹配的值，如果没有匹配则返回None
        """
        if param_name not in self.param_regex:
            return None
        
        for pattern in self.param_regex[param_name]:
            match = pattern.search(text)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        
        return None
    
    def _extract_all_matches(self, param_name: str, text: str) -> List[str]:
        """提取所有匹配的参数值
        
        Args:
            param_name: 参数名称
            text: 要搜索的文本
            
        Returns:
            匹配的值列表
        """
        if param_name not in self.param_regex:
            return []
        
        matches = []
        for pattern in self.param_regex[param_name]:
            for match in pattern.finditer(text):
                value = match.group(1) if match.groups() else match.group(0)
                if value not in matches:
                    matches.append(value)
        
        return matches
    
    def process(self, query: str) -> Dict:
        """处理自然语言查询
        
        Args:
            query: 用户查询文本
            
        Returns:
            包含意图和参数的字典
        """
        intent = self.classify_intent(query)
        parameters = self.extract_parameters(query, intent)
        
        return {
            "intent": intent.value,
            "parameters": parameters,
            "confidence": self._calculate_confidence(query, intent, parameters)
        }
    
    def _calculate_confidence(self, query: str, intent: Intent, 
                              parameters: Dict) -> float:
        """计算识别置信度
        
        Args:
            query: 原始查询
            intent: 识别出的意图
            parameters: 提取的参数
            
        Returns:
            置信度分数（0-1）
        """
        if intent == Intent.UNKNOWN:
            return 0.0
        
        # 基础置信度
        confidence = 0.5
        
        # 如果提取到了关键参数，提高置信度
        if intent == Intent.COMPILE:
            if "input_file" in parameters or "config_file" in parameters:
                confidence += 0.3
        elif intent == Intent.DEPLOY:
            if "output_dir" in parameters:
                confidence += 0.3
        elif intent == Intent.ANALYZE:
            if "input_file" in parameters:
                confidence += 0.3
        elif intent == Intent.CHECK_STATUS:
            if "task_id" in parameters:
                confidence += 0.3
        
        # 如果查询中包含明确的动作词，提高置信度
        action_words = ["编译", "部署", "分析", "验证", "检查"]
        if any(word in query for word in action_words):
            confidence += 0.2
        
        return min(confidence, 1.0)














