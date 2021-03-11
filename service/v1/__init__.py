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
            if f:
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
    with open(image_f, 'w+b') as f:
        shutil.copyfileobj(image_file.file, f)

    glraw_binary = os.path.join(GLRAW_DIRECTORY, 'glraw-cmd')
    arguments = [ glraw_binary, "-o", RESULT_DIR, "-r", image_f_name ]

    result_file = ''

    try:
        print(' '.join(arguments), flush=True)
        p = subprocess.run(arguments, capture_output=True, check=True, cwd=WORKING_DIRECTORY)

        list_of_strings = [x.decode('utf-8').rstrip('\n') for x in iter(p.stderr.splitlines())]

        created_files = [ l[0:-len(" created.")] for l in list_of_strings if l.endswith(" created.") ]
        
        if len(created_files) != 1:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.stderr.decode("utf-8"),
            )
        
        result_file = os.path.join(RESULT_DIR, created_files[0])
        result_basename, result_extension = created_files[0].split(".", 1)
    except subprocess.CalledProcessError as e:
        print(e.stdout.decode("utf-8"), flush=True)
        print(e.stderr.decode("utf-8"), flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.stderr.decode("utf-8"),
        )

    background_tasks.add_task(remove_temporary_files, [image_f, None], [image_f_name, result_file])

    return FileResponse(result_file, filename=basename+"."+result_extension, media_type='application/octet-stream')


# CONVERSION TO GLRAW

@router.post('/get_glraw', tags=["conversion"])
async def get_glraw(background_tasks: BackgroundTasks, image_file: UploadFile = File(...)):
    basename, extension = os.path.splitext(image_file.filename)

    image_f, image_f_name = tempfile.mkstemp(suffix=extension, text=False)
    with open(image_f, 'w+b') as f:
        shutil.copyfileobj(image_file.file, f)

    glraw_binary = os.path.join(GLRAW_DIRECTORY, 'glraw-cmd')
    arguments = [ glraw_binary, "-o", RESULT_DIR, image_f_name ]

    result_file = ''

    try:
        print(' '.join(arguments), flush=True)
        p = subprocess.run(arguments, capture_output=True, check=True, cwd=WORKING_DIRECTORY)

        list_of_strings = [x.decode('utf-8').rstrip('\n') for x in iter(p.stderr.splitlines())]

        created_files = [ l[0:-len(" created.")] for l in list_of_strings if l.endswith(" created.") ]
        
        if len(created_files) != 1:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.stderr.decode("utf-8"),
            )
        
        result_file = os.path.join(RESULT_DIR, created_files[0])
        result_basename, result_extension = created_files[0].split(".", 1)
    except subprocess.CalledProcessError as e:
        print(e.stdout.decode("utf-8"), flush=True)
        print(e.stderr.decode("utf-8"), flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.stderr.decode("utf-8"),
        )

    background_tasks.add_task(remove_temporary_files, [image_f, None], [image_f_name, result_file])

    return FileResponse(result_file, filename=basename+"."+result_extension, media_type='application/octet-stream')
