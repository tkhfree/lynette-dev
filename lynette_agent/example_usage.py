"""
Lynette Agent使用示例
"""

import asyncio
import time
from lynette_agent.service import CompileService, AnalyzeService, DeployService
from lynette_agent.nlp_processor import NLPProcessor


def example_nlp_processing():
    """示例：自然语言处理"""
    print("=== 自然语言处理示例 ===\n")
    
    processor = NLPProcessor()
    
    queries = [
        "编译input/Alice_main.pne文件，输出到output目录",
        "部署代码到所有节点",
        "分析input/Alice_main.pne的代码结构",
        "查询任务状态，任务ID是xxx-xxx-xxx"
    ]
    
    for query in queries:
        print(f"查询: {query}")
        result = processor.process(query)
        print(f"意图: {result['intent']}")
        print(f"参数: {result['parameters']}")
        print(f"置信度: {result['confidence']:.2f}\n")


def example_compile():
    """示例：编译PNE文件"""
    print("=== 编译示例 ===\n")
    
    service = CompileService()
    
    # 编译任务
    result = service.compile(
        mode="debug",
        input_file="input/Alice_main.pne",
        output_dir="output",
        target="v1model"
    )
    
    print(f"任务ID: {result['task_id']}")
    print(f"状态: {result['status']}")
    
    # 等待任务完成（实际应该使用异步方式）
    task_id = result['task_id']
    max_wait = 60  # 最多等待60秒
    waited = 0
    
    while waited < max_wait:
        status = service.get_task_status(task_id)
        print(f"进度: {status['progress']}%")
        
        if status['status'] == 'completed':
            print("编译完成！")
            print(f"生成的文件: {status['result']['generated_files']}")
            break
        elif status['status'] == 'failed':
            print(f"编译失败: {status['error']}")
            break
        
        time.sleep(2)
        waited += 2


def example_analyze():
    """示例：分析PNE代码"""
    print("=== 代码分析示例 ===\n")
    
    service = AnalyzeService()
    
    result = service.analyze(
        input_file="input/Alice_main.pne",
        analysis_type="all"
    )
    
    print(f"语法有效: {result['syntax_valid']}")
    print(f"服务数量: {len(result['services'])}")
    print(f"应用数量: {len(result['applications'])}")
    print(f"模块数量: {len(result['modules'])}")
    
    if result['services']:
        print("\n服务列表:")
        for svc in result['services']:
            print(f"  - {svc['name']}: {svc['applications']}")


def example_nlp_to_action():
    """示例：从自然语言到执行动作"""
    print("=== 自然语言到动作示例 ===\n")
    
    processor = NLPProcessor()
    compile_service = CompileService()
    
    # 用户输入
    user_query = "编译input/Alice_main.pne文件，使用v1model架构"
    
    # 处理自然语言
    nlp_result = processor.process(user_query)
    
    print(f"用户查询: {user_query}")
    print(f"识别意图: {nlp_result['intent']}")
    print(f"提取参数: {nlp_result['parameters']}")
    
    # 根据意图执行动作
    if nlp_result['intent'] == 'compile':
        params = nlp_result['parameters']
        # 设置默认值
        params.setdefault('output_dir', './pne_out')
        params.setdefault('target', 'v1model')
        
        result = compile_service.compile(**params)
        print(f"\n执行结果:")
        print(f"  任务ID: {result['task_id']}")
        print(f"  状态: {result['status']}")


if __name__ == "__main__":
    print("Lynette Agent 使用示例\n")
    print("=" * 50 + "\n")
    
    # 注意：以下示例需要实际的PNE文件才能运行
    # 这里仅展示如何使用API
    
    # 1. 自然语言处理示例
    example_nlp_processing()
    
    # 2. 编译示例（需要实际文件）
    # example_compile()
    
    # 3. 分析示例（需要实际文件）
    # example_analyze()
    
    # 4. 自然语言到动作示例（需要实际文件）
    # example_nlp_to_action()
    
    print("\n" + "=" * 50)
    print("示例完成！")



