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
RESULT_DIR = os.environ.get('RESULT_DIR', '/data/results')
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
