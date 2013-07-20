# -*- coding: utf-8 -*-


def activate(mail, link):
    return """Merhaba {0},

Bil553.com sitesindeki kayıt işlemlerini tamamlamak için, aşağıdaki linki kullanmalısınız.

{1}""".format(mail, link)


def unlock(mail, link):
    return """Merhaba {0},

Bil553.com sitesi sahipleri olarak ülke değistirdiğinizi saptadık.
Bu nedenle hesabınızı pasif hale geçirdik.
Tekrar aktif hale getirmek için bu linke tıklayın.

{1}""".format(mail, link)


def reset(mail, link):
    return """Merhaba {0},

Bil553.com sitesindeki şifre sıfırlama işlemlerini tamamlamak için, aşağıdaki linki kullanmalısınız.

{1}""".format(mail, link)


def change(mail, ip):
    return """Merhaba {0},

Bil553.com sitesindeki şifre değiştirme işlemi {1} nolu ipden gerçekleşmiştir.
Eğer bu işlemi siz yapmadıysanız bizim ile irtibata geçiniz.
""".format(mail, ip)
