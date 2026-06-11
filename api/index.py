"""
FastAPI Server - Visconde
API para distribuição automática de alunos em salas de prova
"""

import io
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.excel_reader import ler_alunos
from app.distribuidor import distribuir
from app.excel_writer import gerar_excel
from app.upload_config import generate_session_id, is_valid_file, MAX_FILE_SIZE

app = FastAPI(
    title="Visconde API",
    version="2.4.1",
    description="API para distribuição automática de alunos em salas de prova"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions_cache: Dict[str, dict] = {}

@app.get("/api/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Visconde",
        "version": "2.4.1",
        "cache_size": len(sessions_cache)
    }

@app.get("/api/template", tags=["Templates"])
async def download_template():
    """Download do arquivo modelo de alunos"""
    try:
        template_path = Path(__file__).parent.parent / "data" / "alunos-fake.xlsx"
        
        if not template_path.exists():
            logger.error(f"Template não encontrado em {template_path}")
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        logger.info(f"Servindo template: {template_path}")
        
        return FileResponse(
            path=template_path,
            filename="modelo_salas.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer download do template: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer download: {str(e)}")

@app.post("/api/process", tags=["Processing"])
async def process_distribution(file: UploadFile = File(...)):
    """
    Processa arquivo de alunos e retorna distribuição com Excel gerado
    """
    session_id = generate_session_id()
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
        
        logger.info(f"Iniciando processamento: {file.filename}")
        
        if not is_valid_file(file.filename):
            logger.warning(f"Tipo de arquivo inválido: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ser .xlsx ou .xls"
            )
        
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo maior que {MAX_FILE_SIZE / 1024 / 1024} MB"
            )
        
        logger.info(f"Arquivo recebido: {len(contents)} bytes")
        
        temp_input = io.BytesIO(contents)
        
        try:
            logger.info(f"Lendo arquivo Excel...")
            alunos = ler_alunos(temp_input)
            logger.info(f"Leitura concluída: {len(alunos)} alunos encontrados")
        except Exception as e:
            logger.error(f"Erro ao ler arquivo Excel: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Erro ao ler arquivo Excel: {str(e)}"
            )
        
        if not alunos:
            logger.warning(f"Nenhum aluno encontrado no arquivo")
            raise HTTPException(status_code=400, detail="Nenhum aluno encontrado no arquivo")
        
        try:
            logger.info(f"Iniciando distribuição de {len(alunos)} alunos...")
            distribuicao = distribuir(alunos)
            logger.info(f"Distribuição concluída: {len(distribuicao)} salas")
        except Exception as e:
            logger.error(f"Erro ao distribuir alunos: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao distribuir alunos: {str(e)}"
            )
        
        try:
            logger.info(f"Gerando arquivo Excel...")
            template_path = Path(__file__).parent.parent / "data" / "template.xlsx"
            mapeamento_path = Path(__file__).parent.parent / "data" / "mapeamento_gabarito_identificadores.json"
            
            if not template_path.exists():
                raise FileNotFoundError(f"Template não encontrado: {template_path}")
            
            output = io.BytesIO()
            gerar_excel(
                str(template_path),
                output,
                distribuicao,
                str(mapeamento_path) if mapeamento_path.exists() else None
            )
            
            excel_bytes = output.getvalue()
            logger.info(f"Excel gerado: {len(excel_bytes)} bytes")
            
        except Exception as e:
            logger.error(f"Erro ao gerar Excel: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar Excel: {str(e)}"
            )
        
        turmas = set(a.turma for a in alunos)
        stats = {
            "total_alunos": len(alunos),
            "salas": len(distribuicao),
            "turmas": len(turmas),
            "alunos_por_sala": round(len(alunos) / len(distribuicao), 1) if distribuicao else 0
        }
        
        sessions_cache[session_id] = {
            "excel": excel_bytes,
            "stats": stats,
            "distribuicao": distribuicao,
            "filename": file.filename
        }
        
        logger.info(f"Sessão {session_id} criada com sucesso")
        
        return JSONResponse(status_code=200, content={
            "status": "success",
            "session_id": session_id,
            "stats": stats,
            "message": "Distribuição realizada com sucesso"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro interno no processamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/download/{session_id}", tags=["Download"])
async def download_result(session_id: str):
    """Download do Excel gerado para uma sessão específica"""
    try:
        if session_id not in sessions_cache:
            logger.warning(f"Sessão não encontrada: {session_id}")
            raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada")
        
        excel_bytes = sessions_cache[session_id]["excel"]
        logger.info(f"Download iniciado: {session_id}")
        
        return FileResponse(
            io.BytesIO(excel_bytes),
            filename="distribuicao_salas.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer download: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer download: {str(e)}")

@app.get("/api/stats/{session_id}", tags=["Statistics"])
async def get_stats(session_id: str):
    """Obter estatísticas de uma sessão"""
    try:
        if session_id not in sessions_cache:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return JSONResponse(status_code=200, content={
            "status": "success",
            "stats": sessions_cache[session_id]["stats"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/", tags=["Frontend"])
async def root():
    """Redireciona para o frontend"""
    try:
        frontend_path = Path(__file__).parent.parent / "BaseFrontEnd" / "index.html"
        return FileResponse(frontend_path, media_type="text/html")
    except Exception as e:
        logger.error(f"Erro ao servir frontend: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar frontend")

@app.get("/{path:path}", tags=["Frontend"])
async def serve_static(path: str):
    """Serve arquivos estáticos do frontend"""
    try:
        file_path = Path(__file__).parent.parent / "BaseFrontEnd" / path
        
        if file_path.is_file() and file_path.exists():
            return FileResponse(file_path)
        
        index_path = Path(__file__).parent.parent / "BaseFrontEnd" / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao servir arquivo estático: {e}")
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Tratador geral de exceções"""
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar o servidor"""
    logger.info("🚀 Visconde API iniciando...")
    logger.info(f"📁 Frontend: BaseFrontEnd/")
    logger.info(f"📦 Cache: Em memória")

@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar o servidor"""
    logger.info("👋 Visconde API desligando...")
    logger.info(f"📊 Sessões em cache: {len(sessions_cache)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
