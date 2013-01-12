import requests
from bs4 import BeautifulSoup
import ImageEnhance
import ImageOps
import Image
from StringIO import StringIO


def brighten(image, factor):
    enh = ImageEnhance.Brightness(image)
    return enh.enhance(factor)


def contrast(image, factor):
    enh = ImageEnhance.Contrast(image)
    return enh.enhance(factor)


def clear_noise(image, max_color, min_adjacent_dots, replacement):
    pixdata = image.load()
    for y in xrange(1, image.size[1] - 1):
        for x in xrange(1, image.size[0] - 1):
            counter = 0
            if pixdata[x - 1, y - 1] < max_color:
                counter += 1
            if pixdata[x + 1, y - 1] < max_color:
                counter += 1
            if pixdata[x, y - 1] < max_color:
                counter += 1
            if pixdata[x - 1, y + 1] < max_color:
                counter += 1
            if pixdata[x + 1, y + 1] < max_color:
                counter += 1
            if pixdata[x, y + 1] < max_color:
                counter += 1
            if pixdata[x - 1, y] < max_color:
                counter += 1
            if pixdata[x + 1, y] < max_color:
                counter += 1

            if not counter > min_adjacent_dots:
                pixdata[x, y] = replacement
    return image


def preprocess_image(f):
    io = StringIO(f)
    im = Image.open(io)
    im = ImageOps.autocontrast(im)
    im = brighten(im, 2.1)
    im = ImageOps.grayscale(im)
    im = ImageOps.invert(im)
    im = im.point(lambda i: 250 if i > 1 else i)
    im = ImageOps.invert(im)
    im = clear_noise(im, 254, 1, 255)

    io = StringIO()
    im.save(io, "png")
    ret = io.getvalue()
    io.close()
    return ret


def get_delivery_status(packageNo):
    r = requests.get('http://www.ems.com.cn/mailtracking/you_jian_cha_xun.html')

    rand = requests.get('http://www.ems.com.cn/ems/rand', cookies=r.cookies,
        stream=True)

    files = {'file': ('rand.png', preprocess_image(rand.raw.read()))}

    r = requests.post('http://tesseract.ccp.li/', files=files, data={
            'options': 'nobatch digits'
        })
    code = r.text.strip()

    r = requests.post('http://www.ems.com.cn/ems/order/singleQuery_t',
        cookies=rand.cookies,
        data={
            'mailNum':  packageNo,
            'checkCode':  code
        }, headers={
            'Referer': 'http://www.ems.com.cn/mailtracking/you_jian_cha_xun.html',
        })

    soup = BeautifulSoup(r.text)
    return soup.find('table').prettify()


if __name__ == '__main__':
    import sys
    print get_delivery_status(sys.argv[1])
