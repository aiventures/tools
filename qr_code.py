""" Creating a QR Code  
    https://stackoverflow.com/questions/43295189/extending-a-image-and-adding-text-on-the-extended-area-using-python-pil
    https://pypi.org/project/qrcode/
"""

import os
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import qrcode
from util import const_local as C

f_qr=os.path.join(C.P_DESKTOP,"qr.png")
f_out = os.path.join(C.P_DESKTOP,"qr_with_text.png")
# create an qr code
s_qr="this is a test sdjkgsd jghsdkjhgskjd gskdjhgksdjhgskgjh kshgksdjhgksdghj "
# image 474
qr = qrcode.QRCode(version=15, box_size=6, border=1)
qr.add_data(s_qr)
img = qr.make_image(fill_color="black", back_color="white")
img.save(f_qr)

# create the image
img_size=800
font_size=15
background = Image.new('RGBA', (img_size, img_size), (255,255,255,255))
draw = ImageDraw.Draw(background)

# add text
font = ImageFont.load_default(font_size)
# font = ImageFont.truetype('arial.ttf',40)
font = ImageFont.truetype('cour.ttf',40)
draw.text(xy=(140,90), text="Top text\nnew line", fill=(0,0,0),font=font,stroke_width=1)
draw.text(xy=(140,660), text="Bottom text\nnew line", fill=(0,0,0),font=font,stroke_width=1)

# add qr code 
qr_img = Image.open(f_qr)
background.paste(qr_img, (140,180))
background.save(f_out)
# draw.text((5,5), "Top text", (0,0,0))
# draw.text((5,210),"Bottom", (0,0,0),font)

