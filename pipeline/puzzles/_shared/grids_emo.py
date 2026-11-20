from PIL import Image, ImageDraw, ImageFont
EF=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109); C={}
def emo(e,size):
    k=(e,size)
    if k not in C:
        im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((80,80),e,font=EF,embedded_color=True,anchor='mm'); im=im.crop(im.getbbox())
        r=size/max(im.size); C[k]=im.resize((max(1,int(im.width*r)),max(1,int(im.height*r))),Image.LANCZOS)
    return C[k]
