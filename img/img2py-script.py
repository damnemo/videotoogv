#!/usr/bin/python
#
#	mettere lo script nella cartella e
#	lanciarlo da riga di comando dal giusto
#	indirizzo
#
import os, sys

def locate_wxpath():
    for path in sys.path:
        if path.find("wx")!=-1:
            path = os.path.join(path, "wx", "tools", "img2py.py")
            if os.path.lexists(path):
                return path
    raise Exception("cannot locate wx path make sure wxPython is installed")

def strip_extension(filename):
    return os.path.splitext(filename)[0]

def main():
    try:
        wxpath = locate_wxpath()
    except Exception, err:
        print err
        return

    dirpath = os.getcwd()
    file_list = os.listdir(dirpath)
    startloop = True
    for file in file_list:
        file_base, file_ext  = os.path.splitext(file)
        args = ""
        if file_ext.lower() in [".jpg", ".png", ".gif", ".bmp", ".ico"]:
            if file_ext.lower() == ".ico":
                args = args + " -i"

            if startloop:
                # create new my_images.py
                args = args + " -n "
                startloop = False
            else:
                # append to my_images.py
                args = args + " -a -n "
            
            img2py_command = 'python %s %s %s "%s" "%s"' % (
                wxpath,
                args,
                file_base,
                os.path.join(dirpath, file),
                os.path.join(dirpath, "images.py")
            )
            print os.popen(img2py_command).read()

if __name__ == '__main__':
    main()
