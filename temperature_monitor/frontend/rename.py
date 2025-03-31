import os


for file in os.listdir('.'):
    os.rename(file, file.split('_')[-1])
