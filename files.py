#!/usr/bin/env python3

'''
Files class containing easy-to-use implementations of common methods from Dropbox's Python SDK
'''

import dropbox
from datetime import datetime
import time
import os

class Files:

  def __init__(
    self, 
    apikey: str):

    self.key = apikey
    self.dbx = dropbox.Dropbox(apikey)

  def getDropboxFileInstance(self):
    return dropbox.files.FileMetadata

  def getDropboxFolderInstance(self):
    return dropbox.files.FolderMetadata

  def getDropboxDeletedInstance(self):
    return dropbox.files.DeletedMetadata

  '''
  read file from directory in Dropbox

  pass dst as kwarg if specific destination
  else saves to current directory with given name
  '''
  def readFromDir(
    self,
    src: str,
    return_content=False,
    **kwargs):

    try:
      md, res = self.dbx.files_download(src)

      if return_content:
        return res.content

      with open((kwargs["dst"] if "dst" in kwargs else src.split("/")[-1]), "wb") as file:
        file.write(res.content)

      return res
    except dropbox.exceptions.ApiError as error_message:
      return error_message.error

  '''
  write file to directory in Dropbox
  '''
  def writeToDir(
    self,
    fname: str,
    dst: str,
    overwrite=True):

    try:
      with open(fname, "rb") as f:
        file = f.read()
    except FileNotFoundError as error_message:
      return error_message

    # time at which file was modified locally
    mtime = os.path.getmtime(fname)

    mode = (
      dropbox.files.WriteMode.overwrite
      if overwrite
      else dropbox.files.WriteMode.add)

    try:
      return self.dbx.files_upload(
                    file, f"{dst}", mode,
                    client_modified=datetime(*time.gmtime(mtime)[:6]),
                    mute=True)
    except dropbox.exceptions.ApiError as error_message:
      return error_message.error

  '''
  remove file from directory in Dropbox
  '''
  def removeFromDir(
    self,
    src: str):

    try:
      return self.dbx.files_delete_v2(src)
    except dropbox.exceptions.ApiError as error_message:
      return error_message.error

  '''
  get contents of directory in Dropbox
  '''
  def getContentsOfDir(
    self,
    src: str):
    
    try:
      return self.dbx.files_list_folder(src)
    except dropbox.exceptions.ApiError as error_message:
      return error_message.error

  '''
  get contents of directory as list
  quite slow for level > 1

  level - depth of directory
  return_name_only - True for name, False for entire dir location
  '''
  def getContentsOfDirAsList(
    self,
    src: str,
    level: int = 1,
    return_name_only: bool = True,
    **kwargs):

    try:
      curr_level = (1 if "curr_level" not in kwargs else kwargs["curr_level"])
      main = ([] if "main" not in kwargs else kwargs["main"])

      res = self.dbx.files_list_folder(src)

      for entry in res.entries:
        if isinstance(entry, dropbox.files.FolderMetadata) and curr_level < level:
          main += self.getContentsOfDirAsDict(entry.path_display, level=level, return_name_only=return_name_only, main=main, curr_level=curr_level+1)
        elif not isinstance(entry, dropbox.files.DeletedMetadata):
          main += [(entry.name if return_name_only else entry.path_display)]

      return main

    except dropbox.exceptions.ApiError as error_message:
      return error_message.error

  '''
  get contents of directory in organized format

  pass return_as as tree or all
  '''
  def getContentsOfDirAsDict(
    self,
    src: str,
    return_as="tree",
    **kwargs):

    try:
      res = self.dbx.files_list_folder(src)

      if return_as == "tree":
        tree = {"_files_": []}

        for entry in res.entries:
          if isinstance(entry, dropbox.files.FolderMetadata):
            tree[entry.path_display.split("/")[-1]] = self.getContentsOfDirAsDict(entry.path_display, return_as="tree")
          elif isinstance(entry, dropbox.files.FileMetadata):
            tree["_files_"] += [entry.name]

        return tree
      else:
        root = (True if "main" not in kwargs else False)
        main = ({} if "main" not in kwargs else kwargs["main"])
        files = []

        for entry in res.entries:
          if isinstance(entry, dropbox.files.FolderMetadata):
            main[entry.path_display] = self.getContentsOfDirAsDict(entry.path_display, return_as="all", main=main)
          elif isinstance(entry, dropbox.files.FileMetadata):
            files += [entry.name]

        main[src] = files
        return (main if root == True else files)

    except dropbox.exceptions.ApiError as error_message:
      return error_message.error