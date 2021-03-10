import os
import shutil
from typing import Optional, List
import subprocess
import tempfile

import json

from pydantic import BaseModel

from fastapi import APIRouter, Response, File, UploadFile, Form
from fastapi import HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse


router = APIRouter()


GLRAW_DIRECTORY = os.environ.get('GLRAW_DIRECTORY', '')
RESULT_DIR = os.environ.get('RESULT_DIR', '/data/share')
WORKING_DIRECTORY = '/opt/dependencies/glraw/'


def remove_temporary_files(file_ids, file_names):
    for f, f_name in zip(file_ids, file_names):
        print("Remove", f_name, flush=True)
        try:
            os.close(f)
            os.remove(f_name)
        except:
            pass


# ROOT

@router.get("/", tags=[""])
async def get_root():
    return {}


@router.head("/", tags=[""])
async def head_root(response: Response):
    response.status_code = status.HTTP_200_OK


# CONVERSION TO RAW

@router.post('/get_raw', tags=["conversion"])
async def get_raw(background_tasks: BackgroundTasks, image_file: UploadFile = File(...)):
    basename, extension = os.path.splitext(image_file.filename)

    image_f, image_f_name = tempfile.mkstemp(suffix=extension, text=False)
    with open(script_f, 'w+b') as f:
        shutil.copyfileobj(image_file.file, f)

    glraw_binary = os.path.join(GLRAW_DIRECTORY, 'glraw-cmd')
    arguments = [ glraw_binary, "-o", RESULT_DIR, "-r", image_f_name ]

    try:
        print(' '.join(arguments), flush=True)
        p = subprocess.run(arguments, capture_output=True, check=True, cwd=WORKING_DIRECTORY)
    except:
        print(p.stdout.decode("utf-8"), flush=True)
        print(p.stderr.decode("utf-8"), flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=p.stderr.decode("utf-8"),
        )

    background_tasks.add_task(remove_temporary_files, [image_f], [image_f_name])

    return FileResponse(image_f_name, filename=image_file.filename, media_type=image_file.content_type)


# CONVERSION TO GLRAW

@router.post('/get_glraw', tags=["conversion"])
async def get_glraw(background_tasks: BackgroundTasks, image_file: UploadFile = File(...)):
    basename, extension = os.path.splitext(image_file.filename)

    image_f, image_f_name = tempfile.mkstemp(suffix=extension, text=False)
    with open(script_f, 'w+b') as f:
        shutil.copyfileobj(image_file.file, f)

    glraw_binary = os.path.join(GLRAW_DIRECTORY, 'glraw-cmd')
    arguments = [ glraw_binary, "-o", RESULT_DIR, image_f_name ]

    try:
        print(' '.join(arguments), flush=True)
        p = subprocess.run(arguments, capture_output=True, check=True, cwd=WORKING_DIRECTORY)
    except:
        print(p.stdout.decode("utf-8"), flush=True)
        print(p.stderr.decode("utf-8"), flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=p.stderr.decode("utf-8"),
        )

    background_tasks.add_task(remove_temporary_files, [image_f], [image_f_name])

    return FileResponse(image_f_name, filename=image_file.filename, media_type=image_file.content_type)
