from PIL import Image
import os

path = os.path.expanduser("~/Kuvat")
print("Looking in", path)

picCount = 0
removeCount = 0

for pic in os.listdir(path=path):
    print("Found", pic)
    if not pic.endswith(".png"):
        print("NON PICTURE SKIPPING")
        continue
    picCount += 1
    
    filePath = os.path.join(path, pic)
    with Image.open(fp=filePath) as img:
        doDelete = (img.width * img.height) < 100
        print(img.width, img.height, img.width * img.height, doDelete)
        if doDelete:
            removeCount += 1
            print("REMOVING FILE")
            os.remove(filePath)
        print()

print(f"Saw {picCount} pictures")
print(f"Deleted {removeCount} pictures")
