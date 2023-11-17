import time
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

root_path = Path(__file__).parent / "files"
root_path.mkdir(parents=True, exist_ok=True)

jobs = {}


@app.get("/")
async def root():
    return {"health": "ok"}


# ========== File Management  ==========

@app.get("/files/")
async def get_files():
    return {"files": [str(f.name) for f in root_path.iterdir()]}


@app.post("/files/")
async def post_file(file: UploadFile = File(...)):
    # save file
    contents = await file.read()
    (root_path / file.filename).write_bytes(contents)

    return {"filename": file.filename}


@app.get("/files/{filename}")
async def get_file(filename: str):
    filepath = root_path / filename
    return FileResponse(filepath)


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    filepath = root_path / filename
    filepath.unlink()
    return {"filename": filename}


# ========== Jobs Management ==========

@app.get("/jobs/")
async def get_jobs():
    return {
        "running_jobs": {k: v for k, v in jobs.items() if v["status"] == "running"},
        "finished_jobs": {k: v for k, v in jobs.items() if v["status"] == "done"}
    }


@app.post("/jobs/")
async def post_job(filename: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(ffmpeg_job, filename)
    jobs[filename] = {"status": "running", "progress": 0, "src": filename}
    return {"filename": filename}


@app.get("/jobs/{filename}")
async def get_job(filename: str):
    if filename not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[filename]


@app.delete("/jobs/{filename}")
async def delete_job(filename: str):
    if filename not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    remove_job(filename)
    return {"filename": filename}


def update_progress(filename: str, progress: int):
    jobs[filename]["progress"] = progress


def update_status(filename: str, status: str):
    jobs[filename]["status"] = status


def remove_job(filename: str):
    del jobs[filename]


# ========== Jobs ==========

def ffmpeg_job(filename: str):
    print(f"Starting job for {filename}")

    for i in range(10):
        update_progress(filename, i * 10)
        time.sleep(1)

    update_status(filename, "done")

    print(f"Job for {filename} done")
