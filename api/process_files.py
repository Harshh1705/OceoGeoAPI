from fastapi import APIRouter, HTTPException, UploadFile, File
from services.ProcessService import ProcessService

router = APIRouter()


@router.post("/process")
async def process_file(file: UploadFile = File(...)):
    """
    Endpoint to process uploaded files using ProcessService.
    
    Args:
        file: The file to be processed
        
    Returns:
        Processing result from ProcessService
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        process_service = ProcessService(file)
        result = process_service.process_files(file)
        
        return {
            "status": "success",
            "filename": file.filename,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}"
        )
