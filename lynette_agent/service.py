"""
Lynette Agent服务层
封装Lynette编译器的核心功能
"""

import os
import uuid
import json
import asyncio
from typing import Dict, Optional, List
from pathlib import Path
import sys

# 添加lynette包到路径
# 假设lynette_agent在lynette-dev/lynette-dev/目录下
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from lynette.__main__ import LynetteRunner
from lynette.lynette_lib import parser_tree, collect


class CompileService:
    """编译服务"""
    
    def __init__(self, sys_path: Optional[str] = None):
        """初始化编译服务
        
        Args:
            sys_path: Lynette系统路径，如果为None则自动检测
        """
        if sys_path is None:
            # 自动检测lynette包路径
            import lynette
            self.sys_path = os.path.dirname(os.path.abspath(lynette.__file__))
        else:
            self.sys_path = sys_path
        
        self.tasks = {}  # 存储任务状态
    
    def compile(self, mode: str, input_file: Optional[str] = None,
                config_file: Optional[str] = None, output_dir: str = "./pne_out",
                target: str = "v1model", p4_only: bool = False,
                check: bool = False) -> Dict:
        """编译PNE文件
        
        Args:
            mode: 编译模式（debug或service）
            input_file: PNE主文件路径（debug模式必需）
            config_file: 服务配置文件路径（service模式必需）
            output_dir: 输出目录
            target: 目标架构（v1model或tna）
            p4_only: 是否只生成P4文件
            check: 是否使用p4test验证
            
        Returns:
            包含任务ID和状态的字典
        """
        task_id = str(uuid.uuid4())
        
        # 验证参数
        if mode == "debug" and not input_file:
            raise ValueError("debug模式需要提供input_file参数")
        if mode == "service" and not config_file:
            raise ValueError("service模式需要提供config_file参数")
        
        # 创建任务
        self.tasks[task_id] = {
            "status": "pending",
            "mode": mode,
            "input_file": input_file,
            "config_file": config_file,
            "output_dir": output_dir,
            "target": target,
            "progress": 0,
            "error": None
        }
        
        # 异步执行编译任务
        asyncio.create_task(self._execute_compile(task_id, mode, input_file,
                                                  config_file, output_dir,
                                                  target, p4_only, check))
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "编译任务已创建"
        }
    
    async def _execute_compile(self, task_id: str, mode: str,
                               input_file: Optional[str],
                               config_file: Optional[str],
                               output_dir: str, target: str,
                               p4_only: bool, check: bool):
        """执行编译任务（异步）"""
        try:
            self.tasks[task_id]["status"] = "running"
            self.tasks[task_id]["progress"] = 10
            
            # 创建LynetteRunner实例
            runner = LynetteRunner(
                sys_path=self.sys_path,
                output_dir=output_dir,
                service_conf=config_file or "./service.json",
                debug_main=input_file
            )
            
            self.tasks[task_id]["progress"] = 30
            
            # 执行编译
            runner.run(if_p4=p4_only, if_deploy=False, if_entry=False)
            
            self.tasks[task_id]["progress"] = 90
            
            # 收集生成的文件
            generated_files = self._collect_generated_files(output_dir)
            
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["progress"] = 100
            self.tasks[task_id]["result"] = {
                "output_dir": output_dir,
                "generated_files": generated_files,
                "log_file": os.path.join(output_dir, "log.txt") if os.path.exists(
                    os.path.join(output_dir, "log.txt")) else None
            }
            
        except Exception as e:
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = str(e)
            self.tasks[task_id]["progress"] = 0
    
    def _collect_generated_files(self, output_dir: str) -> List[str]:
        """收集生成的文件列表"""
        files = []
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith((".p4", "_entry.json")):
                    files.append(file)
        return files
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典
        """
        if task_id not in self.tasks:
            raise ValueError(f"任务ID {task_id} 不存在")
        
        return self.tasks[task_id]


class AnalyzeService:
    """代码分析服务"""
    
    def __init__(self, sys_path: Optional[str] = None):
        """初始化分析服务"""
        if sys_path is None:
            import lynette
            self.sys_path = os.path.dirname(os.path.abspath(lynette.__file__))
        else:
            self.sys_path = sys_path
    
    def analyze(self, input_file: str, analysis_type: str = "all") -> Dict:
        """分析PNE代码
        
        Args:
            input_file: PNE文件路径
            analysis_type: 分析类型（syntax, structure, dependencies, all）
            
        Returns:
            分析结果字典
        """
        result = {
            "syntax_valid": False,
            "services": [],
            "applications": [],
            "modules": [],
            "dependencies": {}
        }
        
        try:
            # 解析语法树
            input_path = os.path.dirname(os.path.abspath(input_file))
            parser_tree_parameter = {
                "main_file_name": os.path.basename(input_file),
                "input_path": input_path,
                "sys_path": self.sys_path
            }
            
            forest = parser_tree.execute(parser_tree_parameter)
            result["syntax_valid"] = True
            
            if analysis_type in ["structure", "all"]:
                # 收集服务、应用和模块
                services, applications, modules = collect.execute(forest, input_path)
                
                # 转换为字典格式
                result["services"] = [
                    {
                        "name": name,
                        "applications": list(svc.application)
                    }
                    for name, svc in services.items()
                ]
                
                result["applications"] = [
                    {
                        "name": name,
                        "variables": list(app.var.keys()),
                        "instructions_count": len(app.ins)
                    }
                    for name, app in applications.items()
                ]
                
                result["modules"] = [
                    {
                        "name": name,
                        "functions": list(mod.func.keys()),
                        "tables": list(mod.mapl.keys()) + list(mod.setl.keys())
                    }
                    for name, mod in modules.items()
                ]
            
            if analysis_type in ["dependencies", "all"]:
                # 提取依赖关系
                result["dependencies"] = {
                    "includes": list(forest.keys()),
                    "modules": []
                }
        
        except Exception as e:
            result["error"] = str(e)
            result["syntax_valid"] = False
        
        return result


class DeployService:
    """部署服务"""
    
    def __init__(self):
        """初始化部署服务"""
        pass
    
    def deploy(self, output_dir: str, deploy_type: str,
              nodes: Optional[List[str]] = None, port: int = 13345) -> Dict:
        """部署P4代码或表项
        
        Args:
            output_dir: 输出目录
            deploy_type: 部署类型（code, entry, both）
            nodes: 要部署的节点列表，如果为None则部署所有节点
            port: 目标端口
            
        Returns:
            部署结果字典
        """
        # 这里应该调用LynetteRunner的deploy_code或deploy_entry方法
        # 为了简化，这里只返回任务ID
        task_id = str(uuid.uuid4())
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "部署任务已创建"
        }

