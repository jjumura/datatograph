from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import uuid
from typing import Dict, Optional
from app.utils.simple_animation import create_simple_animation, create_progress_animation

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/test")
async def test_animation():
    """
    테스트용 간단한 애니메이션 생성하는 엔드포인트
    기존 코드에 영향 없음
    """
    try:
        Path("temp_charts").mkdir(exist_ok=True)  # 디렉토리 확인
        animation_path = create_simple_animation(None, f"test_anim_{uuid.uuid4().hex[:6]}.gif")
        return FileResponse(
            path=animation_path,
            media_type="image/gif",
            filename=Path(animation_path).name
        )
    except Exception as e:
        logger.error(f"애니메이션 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"애니메이션 생성에 실패했습니다: {str(e)}")

@router.post("/progress")
async def visualize_progress(progress_data: Optional[Dict[str, float]] = Body(None)):
    """
    현재 작업 진행 상황을 시각화하여 애니메이션으로 반환하는 엔드포인트
    
    Args:
        progress_data: {'단계명': 진행률(0-100)} 형태의 딕셔너리. 
                      None인 경우 샘플 데이터가 사용됨
    
    Returns:
        애니메이션 GIF 파일
    """
    try:
        Path("temp_charts").mkdir(exist_ok=True)  # 디렉토리 확인
        animation_path = create_progress_animation(progress_data)
        
        logger.info(f"생성된 진행 상황 애니메이션: {animation_path}")
        
        return FileResponse(
            path=animation_path,
            media_type="image/gif",
            filename=Path(animation_path).name
        )
    except Exception as e:
        logger.error(f"진행 상황 애니메이션 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"진행 상황 애니메이션 생성에 실패했습니다: {str(e)}")
