# Based on https://github.com/RameshAditya/asciify
# and https://stackoverflow.com/a/22336005/124019 (for masking)
# Edited for: 
#  - custom width
#  - transparency 

from PIL import Image, ImageOps, ImageDraw

# trailing space is because transparency comes out as pure black
ASCII_CHARS = ['.',',',':',';','+','*','?','%','S','#','@', ' ']
ASCII_CHARS = ASCII_CHARS[::-1]

WIDTH = 32

def resize(image, new_width=WIDTH):
    (old_width, old_height) = image.size
    aspect_ratio = float(old_height)/(float(old_width) *2)
    new_height = int(aspect_ratio * new_width)
    new_dim = (new_width, new_height)
    new_image = image.resize(new_dim)
    return new_image


def grayscalify(image):
    return image.convert('L')

def modify(image):
    initial_pixels = list(image.getdata())
    buckets = 255 // len(ASCII_CHARS) + 1
    new_pixels = [ASCII_CHARS[pixel_value//buckets] for pixel_value in initial_pixels]
    return ''.join(new_pixels)

def mask(image):
    bigsize = (image.size[0] * 3, image.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(image.size, Image.ANTIALIAS)
    image.putalpha(mask)
    return image


def do(image, new_width):
    image = mask(image)
    image = resize(image, new_width)
    image = grayscalify(image)

    pixels = modify(image)
    len_pixels = len(pixels)

    # Construct the image from the character list
    new_image = [pixels[index:index+new_width] for index in range(0, len_pixels, new_width)]

    return '\n'.join(new_image)

def asciify_runner(path, width):
    image = None
    try:
        image = Image.open(path)
    except Exception:
        print("Unable to find image in",path)
        #print(e)
        return
    image = do(image, width)
    return image

if __name__ == '__main__':
    import sys
    import urllib.request
    if sys.argv[1].startswith('http://') or sys.argv[1].startswith('https://'):
        urllib.request.urlretrieve(sys.argv[1], "asciify.jpg")
        path = "asciify.jpg"
    else:
        path = sys.argv[1]

    if len(sys.argv) == 3:
        width = int(sys.argv[2])
    else:
        width = WIDTH
    image = asciify_runner(path, width)
    print(image)
