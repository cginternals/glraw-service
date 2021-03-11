import os
import shutil
from typing import Optional, List
import subprocess
import tempfile
from enum import Enum

import json

from pydantic import BaseModel

from fastapi import APIRouter, Response, File, UploadFile, Form, Depends
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


class OpenGL_Format(str, Enum):
    GL_RED = 'GL_RED'
    GL_GREEN = 'GL_GREEN'
    GL_BLUE = 'GL_BLUE'
    GL_RG = 'GL_RG'
    GL_RGB = 'GL_RGB'
    GL_BGR = 'GL_BGR'
    GL_RGBA = 'GL_RGBA'
    GL_BGRA = 'GL_BGRA'


class OpenGL_Type(str, Enum):
    GL_UNSIGNED_BYTE = 'GL_UNSIGNED_BYTE'
    GL_BYTE = 'GL_BYTE'
    GL_UNSIGNED_SHORT = 'GL_UNSIGNED_SHORT'
    GL_SHORT = 'GL_SHORT'
    GL_UNSIGNED_INT = 'GL_UNSIGNED_INT'
    GL_INT = 'GL_INT'
    GL_FLOAT = 'GL_FLOAT'


class OpenGL_Compressed_Format(str, Enum):
    GL_COMPRESSED_RED_RGTC1 = 'GL_COMPRESSED_RED_RGTC1'
    GL_COMPRESSED_SIGNED_RED_RGTC1 = 'GL_COMPRESSED_SIGNED_RED_RGTC1'
    GL_COMPRESSED_RG_RGTC2 = 'GL_COMPRESSED_RG_RGTC2'
    GL_COMPRESSED_SIGNED_RG_RGTC2 = 'GL_COMPRESSED_SIGNED_RG_RGTC2'
    GL_COMPRESSED_RGBA_BPTC_UNORM = 'GL_COMPRESSED_RGBA_BPTC_UNORM'
    GL_COMPRESSED_RGB_BPTC_SIGNED_FLOAT = 'GL_COMPRESSED_RGB_BPTC_SIGNED_FLOAT'
    GL_COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT = 'GL_COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT'
    GL_COMPRESSED_RGB_S3TC_DXT1_EXT = 'GL_COMPRESSED_RGB_S3TC_DXT1_EXT'
    GL_COMPRESSED_RGBA_S3TC_DXT1_EXT = 'GL_COMPRESSED_RGBA_S3TC_DXT1_EXT'
    GL_COMPRESSED_RGBA_S3TC_DXT3_EXT = 'GL_COMPRESSED_RGBA_S3TC_DXT3_EXT'
    GL_COMPRESSED_RGBA_S3TC_DXT5_EXT = 'GL_COMPRESSED_RGBA_S3TC_DXT5_EXT'


class Transform_Mode(str, Enum):
    nearest = 'nearest'
    linear = 'linear'


class Aspect_Ratio_Mode(str, Enum):
    IgnoreAspectRatio = 'IgnoreAspectRatio'
    KeepAspectRatio = 'KeepAspectRatio'
    KeepAspectRatioByExpanding = 'KeepAspectRatioByExpanding'


class ConversionParameters(BaseModel):
    no_suffixes: Optional[bool] = False
    format: Optional[OpenGL_Format] = OpenGL_Format.GL_RGBA
    type: Optional[OpenGL_Type] = OpenGL_Type.GL_UNSIGNED_BYTE
    compressed_format: Optional[OpenGL_Compressed_Format] = ''
    mirror_vertical: Optional[bool] = False
    mirror_horizontal: Optional[bool] = False
    scale: Optional[float] = 1.0
    width_scale: Optional[float] = 1.0
    height_scale: Optional[float] = 1.0
    width: Optional[int] = 1.0
    height: Optional[int] = 1.0
    aspect_ratio_mode: Optional[Aspect_Ratio_Mode] = Aspect_Ratio_Mode.IgnoreAspectRatio
    transform_mode: Optional[Transform_Mode] = Transform_Mode.nearest


def configure_call(input_filename: str, raw: bool, parameters: ConversionParameters):
    glraw_binary = os.path.join(GLRAW_DIRECTORY, 'glraw-cmd')
    arguments = [ glraw_binary, "-o", RESULT_DIR ]

    if raw:
        arguments.extend([ "-r" ])
    if parameters.no_suffixes:
        arguments.extend([ '--no-suffixes', parameters.no_suffixes ])
    if parameters.format:
        arguments.extend([ '--format', parameters.format.value ])
    if parameters.type:
        arguments.extend([ '--type', parameters.type.value ])
    if parameters.compressed_format:
        arguments.extend([ '--compressed-format', parameters.compressed_format.value ])
    if parameters.mirror_vertical:
        arguments.extend([ '--mirror-vertical', parameters.mirror_vertical ])
    if parameters.mirror_horizontal:
        arguments.extend([ '--mirror-horizontal', parameters.mirror_horizontal ])
    if parameters.scale and parameters.scale != 1.0:
        arguments.extend([ '--scale', parameters.scale ])
    if parameters.width_scale and parameters.width_scale != 1.0:
        arguments.extend([ '--width-scale', parameters.width_scale ])
    if parameters.height_scale and parameters.height_scale != 1.0:
        arguments.extend([ '--height-scale', parameters.height_scale ])
    if parameters.width:
        arguments.extend([ '--width', parameters.width ])
    if parameters.height:
        arguments.extend([ '--height', parameters.height ])
    if parameters.aspect_ratio_mode:
        arguments.extend([ '--aspect-ratio-mode', parameters.aspect_ratio_mode.value ])
    if parameters.transform_mode:
        arguments.extend([ '--transform-mode', parameters.transform_mode.value ])

    arguments.extend([ input_filename ])

    return arguments


# ROOT

@router.get("/", tags=[""])
async def get_root():
    return {}


@router.head("/", tags=[""])
async def head_root(response: Response):
    response.status_code = status.HTTP_200_OK


# CONVERSION TO RAW

@router.post('/get_raw', tags=["conversion"])
async def get_raw(background_tasks: BackgroundTasks, parameters: ConversionParameters = Depends(ConversionParameters), image_file: UploadFile = File(...)):
    basename, extension = os.path.splitext(image_file.filename)

    image_f, image_f_name = tempfile.mkstemp(suffix=extension, text=False)
    with open(image_f, 'w+b') as f:
        shutil.copyfileobj(image_file.file, f)

    arguments = configure_call(image_f_name, True, parameters)

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
async def get_glraw(background_tasks: BackgroundTasks, parameters: ConversionParameters = Depends(ConversionParameters), image_file: UploadFile = File(...)):
    basename, extension = os.path.splitext(image_file.filename)

    image_f, image_f_name = tempfile.mkstemp(suffix=extension, text=False)
    with open(image_f, 'w+b') as f:
        shutil.copyfileobj(image_file.file, f)

    arguments = configure_call(image_f_name, True, parameters)

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
