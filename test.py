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
from ConsoleCapture import captureConsole

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
        captureConsole(cls.browser, os.path.join(cls.baseDir, 'console_capture.xpi'))
        print(cls.browser.install_addon(os.path.join(cls.baseDir, 'dist', 'keyboard_compositor.xpi'), False))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()

    def setUp(self):
        self.browser = self.__class__.browser
        self.browser.get(os.path.join('file://' + self.__class__.baseDir, 'test.html'))

class BaseTest(BrowserTestCase):
    def assertKeyEvent(self, keyEvent, eventType, key, **kwArgs):
        self.assertEqual(keyEvent['type'], eventType)
        self.assertEqual(keyEvent['key'], key)
        self.assertEqual(keyEvent['altKey'], kwArgs['altKey'] if 'altKey' in kwArgs else False)
        self.assertEqual(keyEvent['ctrlKey'], kwArgs['ctrlKey'] if 'ctrlKey' in kwArgs else False)
        self.assertEqual(keyEvent['metaKey'], kwArgs['metaKey'] if 'metaKey' in kwArgs else False)
        self.assertEqual(keyEvent['shiftKey'], kwArgs['shiftKey'] if 'shiftKey' in kwArgs else False)
        for k, v in kwArgs:
            self.assertEqual(keyEvent[k], v)

    @TestData(
        [{'lang': "en", 'keys': l, 'letter': l} for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] +
        [{'lang': "en", 'keys': l, 'letter': l} for l in "abcdefghijklmnopqrstuvwxyz"] +
        [{'lang': "fr", 'keys': l, 'letter': l} for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZÀÂÄÉÈÊËÎÏÔÖÛÜ"] +
        [{'lang': "fr", 'keys': l, 'letter': l} for l in "abcdefghijklmnopqrstuvwxyzàâäéèêëîïôöûü"] +
        [{'lang': "de", 'keys': l, 'letter': l} for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"] +
        [{'lang': "de", 'keys': l, 'letter': l} for l in "abcdefghijklmnopqrstuvwxyzäöüß"] +
        [{'lang': "ru", 'keys': k, 'letter': l} for k, l in zip("ABCDEFGIJKLMNOPRTUVXZÈ", "АБСДЕФГИЖКЛМНОПРТУВХЗЭ")] +
        [{'lang': "ru", 'keys': k, 'letter': l} for k, l in zip("abcdefgijklmnoprtuvxzè", "абсдефгижклмнопртувхзэ")],
    afterEach=lambda self: self.clearTextElements())
    def testSingleKey(self, lang, keys, letter):
        self.browser.clearConsoleCapture()
        textElement = self.getTextElement(lang)

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(textElement.get_property('value'), letter * i)

        capture = self.browser.getConsoleCapture()
        numEvents = 3 if (keys == letter) else 8
        self.assertEqual(len(capture), 4*numEvents)
        for i in range(0, 4):
            self.assertEqual(capture[i*numEvents]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents]['arguments'][1], 'keydown', keys)
            self.assertEqual(capture[i*numEvents + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 1]['arguments'][1], 'keypress', keys)
            self.assertEqual(capture[i*numEvents + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 2]['arguments'][1], 'keyup', keys)
            if (keys != letter):
                self.assertEqual(capture[i*numEvents + 3]['arguments'][0], f'KeyDown[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 3]['arguments'][1], 'keydown', 'Backspace')
                self.assertEqual(capture[i*numEvents + 4]['arguments'][0], f'KeyUp[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 4]['arguments'][1], 'keyup', 'Backspace')
                self.assertEqual(capture[i*numEvents + 5]['arguments'][0], f'KeyDown[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 5]['arguments'][1], 'keydown', letter)
                self.assertEqual(capture[i*numEvents + 6]['arguments'][0], f'KeyPress[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 6]['arguments'][1], 'keypress', letter)
                self.assertEqual(capture[i*numEvents + 7]['arguments'][0], f'KeyUp[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 7]['arguments'][1], 'keyup', letter)

    @TestData([
        {'lang': "ru", 'keys': k, 'letter': l} for k, l in dict({
            "YA": "Я", "Ya": "Я", "YI": "Й", "Yi": "Й", "YO": "Ё", "Yo": "Ё", "YU": "Ю", "Yu": "Ю", "YY": "Ы", "Yy": "Ы",   # Soft vovels
            "SH": "Ш", "Sh": "Ш",                                                                                           # Compound letters
            "QD": "Ъ", "Qd": "Ъ", "QS": "Ь", "Qs": "Ь",                                                                     # Signs
        }).items()] + [
        {'lang': "ru", 'keys': k, 'letter': l} for k, l in dict({
            "ya": "я", "yA": "я", "yi": "й", "yI": "й", "yo": "ё", "yO": "ё", "yu": "ю", "yU": "ю", "yy": "ы", "yY": "ы",   # Soft vovels
            "sh": "ш", "sH": "ш",                                                                                           # Compound letters
            "qd": "ъ", "qD": "ъ", "qs" : "ь", "qS" : "ь",                                                                   # Signs
        }).items()],
    afterEach=lambda self: self.clearTextElements())
    def testPrefixComposition(self, lang, keys, letter):
        self.browser.clearConsoleCapture()
        textElement = self.getTextElement(lang)

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(textElement.get_property('value'), letter * i)

        capture = self.browser.getConsoleCapture()
        numEvents = 5 * len(keys) + 3
        self.assertEqual(len(capture), 4*numEvents)
        for i in range(0, 4):
            for j in range(0, len(keys)):
                self.assertEqual(capture[i*numEvents + 3*j]['arguments'][0], f'KeyDown[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 3*j]['arguments'][1], 'keydown', keys[j])
                self.assertEqual(capture[i*numEvents + 3*j + 1]['arguments'][0], f'KeyPress[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 3*j + 1]['arguments'][1], 'keypress', keys[j])
                self.assertEqual(capture[i*numEvents + 3*j + 2]['arguments'][0], f'KeyUp[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 3*j + 2]['arguments'][1], 'keyup', keys[j])
            for j in range(0, len(keys)):
                self.assertEqual(capture[i*numEvents + 3*len(keys) + 2*j]['arguments'][0], f'KeyDown[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 3*len(keys) + 2*j]['arguments'][1], 'keydown', 'Backspace')
                self.assertEqual(capture[i*numEvents + 3*len(keys) + 2*j + 1]['arguments'][0], f'KeyUp[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 3*len(keys) + 2*j + 1]['arguments'][1], 'keyup', 'Backspace')

                self.assertEqual(capture[i*numEvents + 5*len(keys)]['arguments'][0], f'KeyDown[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 5*len(keys)]['arguments'][1], 'keydown', letter)
                self.assertEqual(capture[i*numEvents + 5*len(keys) + 1]['arguments'][0], f'KeyPress[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 5*len(keys) + 1]['arguments'][1], 'keypress', letter)
                self.assertEqual(capture[i*numEvents + 5*len(keys) + 2]['arguments'][0], f'KeyUp[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 5*len(keys) + 2]['arguments'][1], 'keyup', letter)

    @TestData(
        [{'lang': "ru", 'keys': k, 'letter': l} for k, l in dict({"TS": "Ц", "Ts": "Ц", "CH": "Ч", "Ch": "Ч"}).items()] +
        [{'lang': "ru", 'keys': k, 'letter': l} for k, l in dict({"ts": "ц", "tS": "ц", "ch": "ч", "cH": "ч"}).items()],
    afterEach=lambda self: self.clearTextElements())
    def testSuffixComposition(self, lang, keys, letter):
        self.browser.clearConsoleCapture()
        textElement = self.getTextElement(lang)

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(textElement.get_property('value'), letter * i)

        capture = self.browser.getConsoleCapture()
        numEvents = 11 + 2 * len(keys) + 3
        self.assertEqual(len(capture), 4*numEvents)
        for i in range(0, 4):
            self.assertEqual(capture[i*numEvents]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents]['arguments'][1], 'keydown', keys[0])
            self.assertEqual(capture[i*numEvents + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 1]['arguments'][1], 'keypress', keys[0])
            self.assertEqual(capture[i*numEvents + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 2]['arguments'][1], 'keyup', keys[0])
            # Key is corrected (5 events):
            self.assertEqual(capture[i*numEvents + 8]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 8]['arguments'][1], 'keydown', keys[1])
            self.assertEqual(capture[i*numEvents + 8 + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 8 + 1]['arguments'][1], 'keypress', keys[1])
            self.assertEqual(capture[i*numEvents + 8 + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 8 + 2]['arguments'][1], 'keyup', keys[1])
            for j in range(0, len(keys)):
                self.assertEqual(capture[i*numEvents + 11 + 2*j]['arguments'][0], f'KeyDown[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 11 + 2*j]['arguments'][1], 'keydown', 'Backspace')
                self.assertEqual(capture[i*numEvents + 11 + 2*j + 1]['arguments'][0], f'KeyUp[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 11 + 2*j + 1]['arguments'][1], 'keyup', 'Backspace')
            self.assertEqual(capture[i*numEvents + 11 + 2*len(keys)]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 11 + 2*len(keys)]['arguments'][1], 'keydown', letter)
            self.assertEqual(capture[i*numEvents + 11 + 2*len(keys) + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 11 + 2*len(keys) + 1]['arguments'][1], 'keypress', letter)
            self.assertEqual(capture[i*numEvents + 11 + 2*len(keys) + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 11 + 2*len(keys) + 2]['arguments'][1], 'keyup', letter)

    @TestData([
        {'lang': "ru", 'keys': k, 'letter': l} for k, l in dict({
            "SHCH": "Щ", "SHCh": "Щ", "SHcH": "Щ", "SHch": "Щ", "ShCH": "Щ", "ShCh": "Щ", "ShcH": "Щ", "Shch": "Щ"
        }).items()] + [
        {'lang': "ru", 'keys': k, 'letter': l} for k, l in dict({
            "shch": "щ", "shcH": "щ", "shCh": "щ", "shCH": "щ", "sHch": "щ", "sHcH": "щ", "sHCh": "щ", "sHCH": "щ",         # shcha
        }).items()], afterEach=lambda self: self.clearTextElements())
    def testShchaComposition(self, lang, keys, letter):
        self.browser.clearConsoleCapture()
        textElement = self.getTextElement(lang)

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(textElement.get_property('value'), letter * i)

        capture = self.browser.getConsoleCapture()
        numEvents = 33
        self.assertEqual(len(capture), 4*numEvents)
        for i in range(0, 4):
            self.assertEqual(capture[i*numEvents]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents]['arguments'][1], 'keydown', keys[0])
            self.assertEqual(capture[i*numEvents + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 1]['arguments'][1], 'keypress', keys[0])
            self.assertEqual(capture[i*numEvents + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 2]['arguments'][1], 'keyup', keys[0])
            self.assertEqual(capture[i*numEvents + 3]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 3]['arguments'][1], 'keydown', keys[1])
            self.assertEqual(capture[i*numEvents + 3 + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 3 + 1]['arguments'][1], 'keypress', keys[1])
            self.assertEqual(capture[i*numEvents + 3 + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 3 + 2]['arguments'][1], 'keyup', keys[1])
            # Keys are corrected (7 events):
            self.assertEqual(capture[i*numEvents + 13]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 13]['arguments'][1], 'keydown', keys[2])
            self.assertEqual(capture[i*numEvents + 13 + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 13 + 1]['arguments'][1], 'keypress', keys[2])
            self.assertEqual(capture[i*numEvents + 13 + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 13 + 2]['arguments'][1], 'keyup', keys[2])
            # Key is corrected (5 events):
            self.assertEqual(capture[i*numEvents + 21]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 21]['arguments'][1], 'keydown', keys[3])
            self.assertEqual(capture[i*numEvents + 21 + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 21 + 1]['arguments'][1], 'keypress', keys[3])
            self.assertEqual(capture[i*numEvents + 21 + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 21 + 2]['arguments'][1], 'keyup', keys[3])
            for j in range(0, 3):
                self.assertEqual(capture[i*numEvents + 24 + 2*j]['arguments'][0], f'KeyDown[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 24 + 2*j]['arguments'][1], 'keydown', 'Backspace')
                self.assertEqual(capture[i*numEvents + 24 + 2*j + 1]['arguments'][0], f'KeyUp[{lang}]')
                self.assertKeyEvent(capture[i*numEvents + 24 + 2*j + 1]['arguments'][1], 'keyup', 'Backspace')
            self.assertEqual(capture[i*numEvents + 30]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 30]['arguments'][1], 'keydown', letter)
            self.assertEqual(capture[i*numEvents + 30 + 1]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 30 + 1]['arguments'][1], 'keypress', letter)
            self.assertEqual(capture[i*numEvents + 30 + 2]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[i*numEvents + 30 + 2]['arguments'][1], 'keyup', letter)

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
    }, afterEach=lambda self: self.clearTextElements())
    def testAlphabet(self, lang, inputData, outputData):
        self.browser.clearConsoleCapture()
        textElement = self.getTextElement(lang)
        l = 0
        for keys in inputData.split(' '):
            textElement.send_keys(keys)

            capture = self.browser.getConsoleCapture()
            self.assertEqual(capture[-3]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[-3]['arguments'][1], 'keydown', outputData[l])
            self.assertEqual(capture[-2]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[-2]['arguments'][1], 'keypress', outputData[l])
            self.assertEqual(capture[-1]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[-1]['arguments'][1], 'keyup', outputData[l])

            l = l + 1
            self.assertEqual(textElement.get_property('value'), outputData[0:l])

class TextAreaTest(BaseTest, metaclass=TestCase):
    def getTextElement(self, lang):
        return self.browser.find_element_by_css_selector(f'textarea[lang="{lang}"]')

    def clearTextElements(self):
        for textArea in self.browser.find_elements_by_tag_name('textarea'):
            textArea.clear()

class TextInputTest(BaseTest, metaclass=TestCase):
    def getTextElement(self, lang):
        return self.browser.find_element_by_css_selector(f'input[type="text"][lang="{lang}"]')

    def clearTextElements(self):
        for textInput in self.browser.find_elements_by_css_selector('input[type="text"]'):
            textInput.clear()
