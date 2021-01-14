#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pathlib
import shutil
from uuid import uuid4

from PIL import Image
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

# Server constants
SERVER_HOST = 'http://127.0.0.1:8000'
FILE_FILTER = ['.jpeg', '.jpg', '.png', '.gif']
ORIGINAL_FOLDER = 'uploads/original/'
COMPRESS_FOLDER = 'uploads/compress/'

# Init FastAPI
app = FastAPI()


@app.post('/image')
async def post_image(image: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    # early return if file type is not valid
    if pathlib.Path(image.filename).suffix.lower() not in FILE_FILTER:
        return {'error': f'use {format(",".join(FILE_FILTER))} formats only'}

    # create folder if not exists
    if not os.path.exists(ORIGINAL_FOLDER):
        os.makedirs(ORIGINAL_FOLDER)

    # target folder + generated file name + file extensions
    target_file = f'{ORIGINAL_FOLDER}{uuid4()}{pathlib.Path(image.filename).suffix}'

    # copy file to local disk
    save_me(image, target_file)

    # send compression task to background
    background_tasks.add_task(compress_me, target_file)

    return {'url': f'{SERVER_HOST}/image/{pathlib.Path(target_file).stem}{pathlib.Path(target_file).suffix}'}


@app.get('/image/{image_name}')
async def get_image(image_name: str):
    # check if file exists before response
    if not os.path.exists(f'{ORIGINAL_FOLDER}{image_name}'):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(f'{ORIGINAL_FOLDER}{image_name}')


def save_me(image: UploadFile, target_path: str):
    #  open file for write
    with open(target_path, 'wb') as buffer:
        shutil.copyfileobj(image.file, buffer)


def compress_me(file: str):
    # create folder if not exists
    if not os.path.exists(COMPRESS_FOLDER):
        os.makedirs(COMPRESS_FOLDER)

    # compress images
    picture = Image.open(file)
    picture.save(f'{COMPRESS_FOLDER}{pathlib.Path(file).stem}{pathlib.Path(file).suffix}', optimize=True, quality=10)
