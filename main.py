import os
import sys
import pyrogram
from PIL import Image
Image.MAX_IMAGE_PIXELS = 933120000

# switches
force_update_resrgan = 0 # 0 = no, 1 = yes
force_update_model = 0 # 0 = no, 1 = yes
force_re_upscale = 0 # 0 = no, 1 = yes
upscale_level = 4 # 2, 4, 8
send_to_channel = 1 # 0 = no, 1 = yes
model_name = "realesrgan-x4plus" # realesrgan-x2plus, realesrgan-x4plus, realesrgan-x8plus

# telegram bot info
api_id = 0
api_hash = ""
bot_token = ""
channel_id = ""
bot = pyrogram.Client("my_account", api_id, api_hash, bot_token=bot_token)

# variables
script_path = os.path.dirname(os.path.abspath(__file__))
workdir = os.path.join(script_path, 'workdir')
temp = ".temp" # todo: make this a variable
readydir = os.path.join(script_path, 'ready')
bin_path = os.path.join(script_path, 'bin')
bin_name = "realesrgan-ncnn-vulkan"
model_path = os.path.join(bin_path, 'models')
realesrgan_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip"
models_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth"
realesrgan_zip_name = "realesrgan-ncnn-vulkan-20220424-ubuntu.zip"

# check os. if windows, exit
if os.name == 'nt':
    print("Windows is not supported")
    sys.exit()

if not os.path.exists(workdir):
    os.makedirs(workdir)
    print("Created workdir directory")
if not os.path.exists(readydir):
    os.makedirs(readydir)
    print("Created ready directory")
if not os.path.exists(bin_path):
    os.makedirs(bin_path)
    print("Created bin directory")

# download RealESRGan with wget
def download_realesrgan():
    if os.path.exists(os.path.join(bin_path, bin_name)):
#        print('RealESRGan-ncnn-vulkan binary already downloaded')
        return
    else:
        print('RealESRGan-ncnn-vulkan binary not found. downloading...')
        os.system(f"wget {realesrgan_url} -P {bin_path} >> /dev/null 2>&1")
        print('Extracting...')
    if not os.path.exists(temp):
        os.makedirs(".temp")
    os.system(f"unzip -o {os.path.join(bin_path, realesrgan_zip_name)} -d {os.path.join(temp)} >> /dev/null 2>&1")
    os.system(f"mv {os.path.join(temp, 'realesrgan-ncnn-vulkan')} {os.path.join(bin_path, 'realesrgan-ncnn-vulkan')}")
    os.system(f"mv {os.path.join(temp, 'models')} {os.path.join(bin_path, 'models')}")
    os.system(f"rm -rf {temp}")
    os.system(f"rm -rf {os.path.join(bin_path, realesrgan_zip_name)}")
    os.system(f"chmod +x {os.path.join(bin_path, 'realesrgan-ncnn-vulkan')}")

# Download models
def download_models():
    if not os.path.exists(os.path.join(model_path)):
        print('Models directory not found. re-downloading...')
        os.system(f"rm -rf {bin_path}/*")
        download_realesrgan()
    else:
#        print('Models directory found. skipping...')
        return

# convert jpg, jpeg, webp to png
def convert2png():
    print('Converting images to png...')
    for filename in os.listdir(workdir):
        if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".webp"):
            image_path = os.path.join(workdir, filename)
            image = Image.open(image_path)
            new_filename = os.path.splitext(filename)[0] + ".png"
            new_image_path = os.path.join(workdir, new_filename)
            image.save(new_image_path, "PNG")
            os.remove(image_path)
            print(f"{filename} Converted: {new_filename}")

# check all images in workdir. if resolution is less than 1920x1080, upscale
def upscale():
    print('Upscaling images...')
    for filename in os.listdir(workdir):
        if filename.endswith(".png"):
            image_path = os.path.join(workdir, filename)
            image = Image.open(image_path)
            width, height = image.size
            if width < 920 or height < 480:
                print(f"{filename} is {width}x{height}. Upscaling...")
                os.system(f"{os.path.join(bin_path, 'realesrgan-ncnn-vulkan')} -i {image_path} -o {os.path.join(workdir, filename)} -n {os.path.join(model_name)} -s {upscale_level} >> /dev/null 2>&1")
#                os.remove(image_path)
                print(f"{filename} Upscaled")
            else:
                print(f"{filename} is {width}x{height}. Skipping...")
#                os.system(f"mv {image_path} {os.path.join(readydir, filename)}")
#                print(f"{filename} Moved")

# optimize png files with pngquant
def optimize_pngquant():
    print('Optimizing big files...')
    for filename in os.listdir(readydir):
        if filename.endswith(".png"):
            if os.path.getsize(os.path.join(readydir, filename)) < 5000000:
                continue
            else: 
                image_path = os.path.join(readydir, filename)
                old_size = os.path.getsize(image_path)
                os.system(f"pngquant --skip-if-larger --strip --force --output {image_path} {image_path}")
                print(f"{filename} Optimized: from {old_size} to {os.path.getsize(image_path)}")

# optimize png files with optipng
def optimize_optipng():
    print('Optimizing big files using Optifine Level 7...')
    for filename in os.listdir(readydir):
        if filename.endswith(".png"):
            # if file size is less than 5mb, skip
            if os.path.getsize(os.path.join(readydir, filename)) < 5000000:
                continue
            else:
                image_path = os.path.join(readydir, filename)
                old_size = os.path.getsize(image_path)
                os.system(f"optipng -o7 {image_path} >> /dev/null 2>&1")
                print(f"{filename} Optimized: from {old_size} to {os.path.getsize(image_path)}")

# downsacle big images by 25%
def downscale():
    for filename in os.listdir(workdir):
        if filename.endswith(".png"):
            if os.path.getsize(os.path.join(workdir, filename)) < 5000000:
                continue
            else:
                image_path = os.path.join(workdir, filename)
                print(f"{filename} is {os.path.getsize(image_path)} bytes. {Image.open(image_path).size}")
                image = Image.open(image_path)
                width, height = image.size
                new_width = int(width * 0.75)
                new_height = int(height * 0.75)
                image = image.resize((new_width, new_height))
                image.save(os.path.join(readydir, filename))
                moved_file = os.path.join(readydir, filename)
                print(f"{filename} Downscaled to {new_width}x{new_height}. new size: {os.path.getsize(moved_file)} ")
                os.remove(image_path)

# check telegram channel for last posted image name
def check_latest():
    print('Checking for last posted image...')

# rename files
def rename():
    
# post to channel
#def post_to_channel():
    print('Posting to channel...')

    
    

download_realesrgan()
download_models()
convert2png()
upscale()
#optimize_pngquant()
#optimize_optipng()
downscale()
#check_latest()
#post_to_channel()
