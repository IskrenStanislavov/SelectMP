# encoding:cp1251
# Run the build process by entering 'setup.py py2exe' or
# 'python setup.py py2exe' in a console prompt.

from distutils.core import setup
import py2exe

setup(
    name = "Прехвърляне на складови данни от склада на SelectMP към Винтех Склад.",
    version = "1.0",
    #~ description = "Складовата програма на SelectMP е предоставена от Делфин 3.",
    description = "Created by Vintech Ltd; edited by Isko in dec \'14",
    # targets to build
    windows = ["SelectMP.py"],
    #~ zipfile = "m-py/libs.zip",
    )

if __name__=='__main__':
    print "run in cmd: python setup.py py2exe"