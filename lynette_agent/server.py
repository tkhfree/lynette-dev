"""
Lynette Agent API服务器
基于FastAPI实现
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os

from lynette_agent.service import CompileService, AnalyzeService, DeployService
from lynette_agent.nlp_processor import NLPProcessor

app = FastAPI(title="Lynette Agent API", version="0.1.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
compile_service = CompileService()
analyze_service = AnalyzeService()
deploy_service = DeployService()
nlp_processor = NLPProcessor()

# API Key验证（简化版，实际应该使用更安全的认证方式）
API_KEY = os.getenv("LYNETTE_API_KEY", "default_api_key")

def verify_api_key(authorization: str = Header(None)):
    """验证API Key"""
    if authorization is None:
        raise HTTPException(status_code=401, detail="缺少Authorization头")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization格式错误")
    
    api_key = authorization.replace("Bearer ", "")
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key无效")
    
    return api_key


# 请求模型
class CompileRequest(BaseModel):
    mode: str
    input_file: Optional[str] = None
    config_file: Optional[str] = None
    output_dir: str = "./pne_out"
    target: str = "v1model"
    options: Optional[Dict] = {}


class DeployRequest(BaseModel):
    task_id: Optional[str] = None
    output_dir: Optional[str] = None
    deploy_type: str
    nodes: Optional[List[str]] = None
    options: Optional[Dict] = {}


class AnalyzeRequest(BaseModel):
    input_file: str
    analysis_type: str = "all"


class NLPExecuteRequest(BaseModel):
    query: str
    context: Optional[Dict] = {}


class NLPChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[List[Dict]] = []


# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Lynette Agent API",
        "version": "0.1.0",
        "status": "running"
    }


@app.post("/api/v1/compile")
async def compile_pne(request: CompileRequest, 
                     api_key: str = Depends(verify_api_key)):
    """编译PNE文件"""
    try:
        result = compile_service.compile(
            mode=request.mode,
            input_file=request.input_file,
            config_file=request.config_file,
            output_dir=request.output_dir,
            target=request.target,
            p4_only=request.options.get("p4_only", False),
            check=request.options.get("check", False)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/compile/{task_id}/status")
async def get_compile_status(task_id: str,
                            api_key: str = Depends(verify_api_key)):
    """查询编译任务状态"""
    try:
        status = compile_service.get_task_status(task_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/deploy")
async def deploy_p4(request: DeployRequest,
                   api_key: str = Depends(verify_api_key)):
    """部署P4代码"""
    try:
        if request.task_id:
            # 从编译任务获取输出目录
            compile_status = compile_service.get_task_status(request.task_id)
            if compile_status["status"] != "completed":
                raise HTTPException(
                    status_code=400,
                    detail="编译任务尚未完成"
                )
            output_dir = compile_status["result"]["output_dir"]
        elif request.output_dir:
            output_dir = request.output_dir
        else:
            raise HTTPException(
                status_code=400,
                detail="需要提供task_id或output_dir"
            )
        
        result = deploy_service.deploy(
            output_dir=output_dir,
            deploy_type=request.deploy_type,
            nodes=request.nodes,
            port=request.options.get("port", 13345)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze")
async def analyze_pne(request: AnalyzeRequest,
                     api_key: str = Depends(verify_api_key)):
    """分析PNE代码"""
    try:
        result = analyze_service.analyze(
            input_file=request.input_file,
            analysis_type=request.analysis_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/nlp/execute")
async def nlp_execute(request: NLPExecuteRequest,
                     api_key: str = Depends(verify_api_key)):
    """自然语言执行接口"""
    try:
        # 处理自然语言查询
        nlp_result = nlp_processor.process(request.query)
        
        # 根据意图执行相应操作
        intent = nlp_result["intent"]
        params = nlp_result["parameters"]
        
        if intent == "compile":
            result = compile_service.compile(**params)
            return {
                "intent": intent,
                "parameters": params,
                "task_id": result["task_id"],
                "status": result["status"],
                "message": f"已理解您的请求，正在编译PNE文件..."
            }
        elif intent == "deploy":
            result = deploy_service.deploy(**params)
            return {
                "intent": intent,
                "parameters": params,
                "task_id": result["task_id"],
                "status": result["status"],
                "message": f"已理解您的请求，正在部署..."
            }
        elif intent == "analyze":
            result = analyze_service.analyze(**params)
            return {
                "intent": intent,
                "parameters": params,
                "result": result,
                "message": "分析完成"
            }
        elif intent == "check_status":
            if "task_id" not in params:
                raise HTTPException(
                    status_code=400,
                    detail="未找到任务ID"
                )
            status = compile_service.get_task_status(params["task_id"])
            return {
                "intent": intent,
                "parameters": params,
                "status": status,
                "message": "查询完成"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"无法识别的意图: {intent}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/nlp/chat")
async def nlp_chat(request: NLPChatRequest,
                  api_key: str = Depends(verify_api_key)):
    """对话式交互接口"""
    try:
        # 处理自然语言查询
        nlp_result = nlp_processor.process(request.message)
        
        intent = nlp_result["intent"]
        params = nlp_result["parameters"]
        
        # 生成响应消息
        if intent == "compile":
            result = compile_service.compile(**params)
            response = f"好的，我将为您编译PNE文件。编译任务ID: {result['task_id']}"
            if "input_file" in params:
                response += f"，文件: {params['input_file']}"
        elif intent == "deploy":
            result = deploy_service.deploy(**params)
            response = f"好的，我将为您部署P4代码。部署任务ID: {result['task_id']}"
        elif intent == "analyze":
            result = analyze_service.analyze(**params)
            response = f"分析完成。发现 {len(result.get('services', []))} 个服务，{len(result.get('applications', []))} 个应用"
        else:
            response = "抱歉，我无法理解您的请求。请尝试使用以下命令：编译、部署、分析等。"
        
        return {
            "response": response,
            "intent": intent,
            "parameters": params,
            "session_id": request.session_id or "default"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



