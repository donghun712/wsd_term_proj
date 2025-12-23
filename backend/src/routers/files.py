import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

# 라우터 설정
router = APIRouter(prefix="/files", tags=["Files (Upload)"])

# 이미지가 저장될 서버 내부 폴더 경로
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    """
    [추가 엔드포인트] 파일 업로드
    - 파일을 받아 서버의 'uploads' 폴더에 저장합니다.
    - 저장된 파일에 접근할 수 있는 URL을 반환합니다.
    """
    try:
        # 1. 파일명 중복 방지를 위해 UUID 사용
        file_extension = file.filename.split(".")[-1]
        new_filename = f"{uuid.uuid4()}.{file_extension}"
        file_location = f"{UPLOAD_DIR}/{new_filename}"
        
        # 2. 파일 저장 (WB: Write Binary)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. 결과 반환
        return {
            "original_name": file.filename,
            "saved_name": new_filename,
            "url": f"/api/v1/files/{new_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@router.get("/{filename}")
async def get_file(filename: str):
    """
    [추가 엔드포인트] 이미지 조회 (서빙)
    - 업로드된 파일을 브라우저에서 볼 수 있게 해줍니다.
    """
    file_path = f"{UPLOAD_DIR}/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)