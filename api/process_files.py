from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from services.ProcessService import ProcessService

router = APIRouter()


@router.post("/process")
async def process_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    project_id: int = Form(...),   # SERIAL integer in the `projects` table
):
    """
    Process an uploaded ARGO NetCDF file and store the parsed data in Neon DB.

    Form fields:
        file         .nc / .netcdf / .nc4 file
        user_id      Clerk user ID (TEXT, for logging / ownership validation)
        project_id   Integer PK from the `projects` table

    Returns:
        file_id, profiles_inserted, measurements_inserted
    """
    allowed_extensions = {".nc", ".netcdf", ".nc4"}
    filename = file.filename or ""
    suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Expected one of {allowed_extensions}.",
        )

    try:
        service = ProcessService()
        result = await service.process_netcdf(file, user_id=user_id, project_id=project_id)
        return {
            "status": "success",
            "filename": file.filename,
            "user_id": user_id,
            "project_id": project_id,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")