# Copyright 2020 Pascal COMBES <pascom@orange.fr>
#
# This file is part of ConsoleCapture.
#
# SolarProd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SolarProd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SolarProd. If not, see <http://www.gnu.org/licenses/>

from selenium import webdriver
from selenium.common import exceptions as selenium
from PythonUtils.testdata import TestData

import os
import time
import unittest

class TestCase(type):
    __testCaseList = []

    @classmethod
    def loadTests(metacls, loader, tests, pattern):
        suite = unittest.TestSuite()
        for cls in metacls.__testCaseList:
            tests = loader.loadTestsFromTestCase(cls)
            suite.addTests(tests)
        return suite

    def __new__(metacls, *args):
        cls = super().__new__(metacls, *args)
        metacls.__testCaseList += [cls]
        return cls

def load_tests(loader, tests, pattern):
    return TestCase.loadTests(loader, tests, pattern)

class BrowserTestCase(unittest.TestCase):
    index = '''<html>
    <head>
        <meta charset='utf-8' />
        <title>Test{}</title>
    </head>
    <body>
        <p id="test">Click</p>
        {}
    </body>
</html>'''

    @classmethod
    def setUpClass(cls):
        cls.baseDir = os.path.dirname(os.path.abspath(__file__))

        profile = webdriver.FirefoxProfile()
        profile.set_preference('xpinstall.signatures.required', False)

        cls.browser = webdriver.Firefox(profile)
        print(cls.browser.install_addon(os.path.join(cls.baseDir, 'console_capture.xpi'), False))
        print(cls.browser.install_addon(os.path.join(cls.baseDir, 'dist', 'phonetic_keyboard.xpi'), False))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()

    def setUp(self):
        self.browser = self.__class__.browser
        self.browser.get(os.path.join('file://' + self.__class__.baseDir, 'test.html'))

class BaseTest(BrowserTestCase):
    @TestData({
        "English (upper)": {'lang': "en", 'letters': {l : l for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}},
        "English (lower)": {'lang': "en", 'letters': {l : l for l in "abcdefghijklmnopqrstuvwxyz"}},
        "French  (upper)": {'lang': "fr", 'letters': {l : l for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZÀÂÄÉÈÊËÎÏÔÖÛÜ"}},
        "French  (lower)": {'lang': "fr", 'letters': {l : l for l in "abcdefghijklmnopqrstuvwxyzàâäéèêëîïôöûü"}},
        "German  (upper)": {'lang': "de", 'letters': {l : l for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"}},
        "German  (lower)": {'lang': "de", 'letters': {l : l for l in "abcdefghijklmnopqrstuvwxyzäöüß"}},
        "Russian (upper)": {'lang': "ru", 'letters': {ll : cl for ll, cl in zip("ABCDEFGIJKLMNOPRTUVXZÈ", "АБСДЕФГИЖКЛМНОПРТУВХЗЭ")}},
        "Russian (lower)": {'lang': "ru", 'letters': {ll : cl for ll, cl in zip("abcdefgijklmnoprtuvxzè", "абсдефгижклмнопртувхзэ")}},
    })
    def testSingleLetters(self, lang, letters):
        textElement = self.getTextElement(lang)

        for k, v in letters.items():
            for i in range(1, 5):
                textElement.send_keys(k)
                self.assertEqual(textElement.get_property('value'), v * i)
            textElement.clear()
            self.assertEqual(textElement.get_property('value'), '')

    @TestData({
        "Russian (upper)": {'lang': "ru", 'letters': {
            "YA": "Я", "Ya": "Я", "YI": "Й", "Yi": "Й", "YO": "Ё", "Yo": "Ё", "YU": "Ю", "Yu": "Ю", "YY": "Ы", "Yy": "Ы",   # Soft vovels
            "TS": "Ц", "Ts": "Ц", "SH": "Ш", "Sh": "Ш", "CH": "Ч", "Ch": "Ч",                                               # Compound letters
            "SHСH": "Щ", "SHСh": "Щ", "SHсH": "Щ", "SHсh": "Щ", "ShСH": "Щ", "ShСh": "Щ", "ShсH": "Щ", "Shсh": "Щ",         # Shcha
            "QD": "Ъ", "Qd": "Ъ", "QS": "Ь", "Qs": "Ь",                                                                     # Signs
        }},
        "Russian (lower)": {'lang': "ru", 'letters': {
            "ya": "я", "yA": "я", "yi": "й", "yI": "й", "yo": "ё", "yO": "ё", "yu": "ю", "yU": "ю", "yy": "ы", "yY": "ы",   # Soft vovels
            "ts": "ц", "tS": "ц", "sh": "ш", "sH": "ш", "ch": "ч", "cH": "ч",                                               # Compound letters
            "shсh": "щ", "shсH": "щ", "shСh": "щ", "shСH": "щ", "sHсh": "щ", "sHсH": "щ", "sHСh": "щ", "sHСH": "щ",         # shcha
            "qd": "ъ", "qD": "ъ", "qs" : "ь", "qS" : "ь",                                                                   # Signs
        }},
    })
    def testComposedLetters(self, lang, letters):
        textElement = self.getTextElement(lang)

        for k, v in letters.items():
            for i in range(1, 5):
                textElement.send_keys(k)
                self.assertEqual(textElement.get_property('value'), v * i)
            textElement.clear()
            self.assertEqual(textElement.get_property('value'), '')

    @TestData({
        "English (upper)": {
            'lang': "en",
            'inputData': "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z",
            'outputData': "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        },
        "English (upper)": {
            'lang': "en",
            'inputData': "a b c d e f g h i j k l m n o p q r s t u v w x y z",
            'outputData': "abcdefghijklmnopqrstuvwxyz"
        },
        "French (upper)":  {
            'lang': "fr",
            'inputData': "A À Â Ä B C D E É È Ê Ë F G H I Î Ï J K L M N O Ô Ö P Q R S T U Û Ü V W X Y Z",
            'outputData': "AÀÂÄBCDEÉÈÊËFGHIÎÏJKLMNOÔÖPQRSTUÛÜVWXYZ"
        },
        "French (lower)":  {
            'lang': "fr",
            'inputData': "a à â ä b c d e é è ê ë f g h i î ï j k l m n o ô ö p q r s t u û ü v w x y z",
            'outputData': "aàâäbcdeéèêëfghiîïjklmnoôöpqrstuûüvwxyz"
        },
        "German (upper)":  {
            'lang': "de",
            'inputData': "A Ä B C D E F G H I J K L M N O Ö P Q R S T U Ü V W X Y Z",
            'outputData': "AÄBCDEFGHIJKLMNOÖPQRSTUÜVWXYZ"
        },
        "German (lower)":  {
            'lang': "de",
            'inputData': "a ä b c d e f g h i j k l m n o ö p q r s t u ü v w x y z ß",
            'outputData': "aäbcdefghijklmnoöpqrstuüvwxyzß"
        },
        "Russian (upper)": {
            'lang': "ru",
            'inputData': "A B V G D E YO J Z I YI K L M N O P R C T U F X CH SH SHCH TS QD YY QS È YU YA",
            'outputData': "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЧШЩЦЪЫЬЭЮЯ"
        },
        "Russian (lower)": {
            'lang': "ru",
            'inputData': "a b v g d e yo j z i yi k l m n o p r c t u f x ch sh shch ts qd yy qs è yu ya",
            'outputData': "абвгдеёжзийклмнопрстуфхчшщцъыьэюя"
        },
    })
    def testAlphabet(self, lang, inputData, outputData):
        textElement = self.getTextElement(lang)
        l = 0
        for keys in inputData.split(' '):
            textElement.send_keys(keys)
            l = l + 1
            self.assertEqual(textElement.get_property('value'), outputData[0:l])

        textElement.clear()
        self.assertEqual(textElement.get_property('value'), '')

class TextAreaTest(BaseTest, metaclass=TestCase):
    def getTextElement(self, lang):
        return self.browser.find_element_by_css_selector(f'textarea[lang="{lang}"]')

class TextInputTest(BaseTest, metaclass=TestCase):
    def getTextElement(self, lang):
        return self.browser.find_element_by_css_selector(f'input[type="text"][lang="{lang}"]')
