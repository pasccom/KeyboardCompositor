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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from .PythonUtils.testdata import TestData
from .ConsoleCapture import captureConsole

import os
import subprocess
import unittest

class ImageMagick:
    programs = {
        'crop':    'convert',
        'compare': 'compare',
    }

    @classmethod
    def checkImageMagick(cls):
        for prog in cls.programs.values():
            imWhich = subprocess.run(['which', prog], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if (imWhich.returncode != 0):
                return False
        return True

    @classmethod
    def crop(cls, src, dest, rect):
        imCrop = subprocess.run([cls.programs['crop'], src, '-crop', f"{rect['width']}x{rect['height']}+{rect['x']}+{rect['y']}", dest])
        return imCrop.returncode == 0

    @classmethod
    def compare(cls, src1, src2, dest):
        imCompare = subprocess.run([cls.programs['compare'], src1, src2, '-metric', 'DSSIM', '-compose', 'clear', dest], stderr=subprocess.PIPE)
        try:
            return float(imCompare.stderr)
        except (ValueError):
            print(imCompare.stderr)

def foreachElement(fun):
    def foreachElementFun(self, *args, **kwArgs):
        try:
            lang = kwArgs['lang']
        except(KeyError):
            lang = args[0]
        try:
            for elementId in [None] + self.__class__.elementIds[lang]:
                with self.subTest(elementId=elementId):
                    kwArgs['elementId'] = elementId
                    fun(self, *args, **kwArgs)
        except(KeyError):
            fun(self, *args, **kwArgs)

    return foreachElementFun

class BrowserTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testDir = os.path.dirname(os.path.abspath(__file__))
        cls.baseDir = os.path.dirname(cls.testDir)

        cls.browser = webdriver.Firefox()
        captureConsole(cls.browser, os.path.join(cls.testDir, 'console_capture.xpi'))
        print(cls.browser.install_addon(os.path.join(cls.baseDir, 'dist', 'keyboard_compositor.xpi'), True))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()

    def setUp(self):
        self.browser = self.__class__.browser

class BaseTest(BrowserTestCase):

    def assertEvent(self, event, eventType, target):
        self.assertEqual(event['type'], eventType)
        self.assertEqual(event['target'], target)
        self.assertEqual(event['originalTarget'], target)
        self.assertEqual(event['explicitOriginalTarget'], target)

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
        [{'lang': "ru", 'keys': k, 'letter': l} for k, l in zip("abcdefgijklmnoprtuvxzè", "абсдефгижклмнопртувхзэ")] +
        [{'lang': "el", 'keys': k, 'letter': l} for k, l in zip("ABGDEZÈIKLMNOPRSTUXW", "ΑΒΓΔΕΖΗΙΚΛΜΝΟΠΡΣΤΥΧΩ")] +
        [{'lang': "el", 'keys': k, 'letter': l} for k, l in zip("abgdezèiklmnoprstuxw", "αβγδεζηικλμνοπρστυχω")],
    afterEach=lambda self: self.clearTextElements())
    @foreachElement
    def testSingleKey(self, lang, keys, letter, elementId=None):
        textElement = self.getTextElement(lang, elementId)
        del self.browser.consoleCapture

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(self.getValue(textElement), letter * i)

        capture = [record for record in self.browser.consoleCapture() if record['arguments'][0].startswith('Key')]
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
    @foreachElement
    def testPrefixComposition(self, lang, keys, letter, elementId=None):
        textElement = self.getTextElement(lang, elementId)
        del self.browser.consoleCapture

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(self.getValue(textElement), letter * i)

        capture = [record for record in self.browser.consoleCapture() if record['arguments'][0].startswith('Key')]
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
        [{'lang': "ru", 'keys': k, 'letter': l} for k, l in dict({"ts": "ц", "tS": "ц", "ch": "ч", "cH": "ч"}).items()] +
        [{'lang': "el", 'keys': k, 'letter': l} for k, l in dict({"TH": "Θ", "Th": "Θ", "KC": "Ξ", "Kc": "Ξ", "PH": "Φ", "Ph": "Φ", "PC": "Ψ", "Pc": "Ψ"}).items()] +
        [{'lang': "el", 'keys': k, 'letter': l} for k, l in dict({"th": "θ", "tH": "θ", "kc": "ξ", "kC": "ξ", "ph": "φ", "pH": "φ", "pc": "ψ", "pC": "ψ", "sc": "ς", "sC": "ς"}).items()] ,
    afterEach=lambda self: self.clearTextElements())
    @foreachElement
    def testSuffixComposition(self, lang, keys, letter, elementId=None):
        textElement = self.getTextElement(lang, elementId)
        del self.browser.consoleCapture

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(self.getValue(textElement), letter * i)

        capture = [record for record in self.browser.consoleCapture() if record['arguments'][0].startswith('Key')]
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
        }).items()],
    afterEach=lambda self: self.clearTextElements())
    @foreachElement
    def testShchaComposition(self, lang, keys, letter, elementId=None):
        textElement = self.getTextElement(lang, elementId)
        del self.browser.consoleCapture

        for i in range(1, 5):
            textElement.send_keys(keys)
            self.assertEqual(self.getValue(textElement), letter * i)

        capture = [record for record in self.browser.consoleCapture() if record['arguments'][0].startswith('Key')]
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
        "Greek (upper)": {
            'lang': "el",
            'inputData': "A B G D E Z È TH I K L M N KC O P R S T U PH X PC W",
            'outputData': "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
        },
        "Greek (lower)": {
            'lang': "el",
            'inputData': "a b g d e z è th i k l m n kc o p r s sc t u ph x pc w",
            'outputData': "αβγδεζηθικλμνξοπρσςτυφχψω"
        },

    }, afterEach=lambda self: self.clearTextElements())
    @foreachElement
    def testAlphabet(self, lang, inputData, outputData, elementId=None):
        textElement = self.getTextElement(lang, elementId)
        del self.browser.consoleCapture

        l = 0
        for keys in inputData.split(' '):
            textElement.send_keys(keys)

            capture = [record for record in self.browser.consoleCapture() if record['arguments'][0].startswith('Key')]
            self.assertEqual(capture[-3]['arguments'][0], f'KeyDown[{lang}]')
            self.assertKeyEvent(capture[-3]['arguments'][1], 'keydown', outputData[l])
            self.assertEqual(capture[-2]['arguments'][0], f'KeyPress[{lang}]')
            self.assertKeyEvent(capture[-2]['arguments'][1], 'keypress', outputData[l])
            self.assertEqual(capture[-1]['arguments'][0], f'KeyUp[{lang}]')
            self.assertKeyEvent(capture[-1]['arguments'][1], 'keyup', outputData[l])

            l = l + 1
            self.assertEqual(self.getValue(textElement), outputData[0:l])

    @TestData(['ru', 'el'])
    @foreachElement
    def testEnter(self, lang, elementId=None):
        textElement = self.getTextElement(lang, elementId)
        del self.browser.consoleCapture

        textElement.send_keys(Keys.ENTER)
        capture = self.browser.consoleCapture()[1:]

        focusEvent = None
        blurEvent = None
        for record in capture:
            if (record['arguments'][0] == f'Blur[{lang}]'):
                if focusEvent is not None:
                    self.fail("Focus event occured before blur event")
                if blurEvent is None:
                    blurEvent = record['arguments'][1]
                else:
                    self.fail("Captured two blur events")
            if (record['arguments'][0] == f'Focus[{lang}]'):
                if blurEvent is None:
                    self.fail("Focus event occured before blur event")
                if focusEvent is None:
                    focusEvent = record['arguments'][1]
                else:
                    self.fail("Captured two focus events")
        self.assertEvent(blurEvent, 'blur', textElement)
        self.assertEvent(focusEvent, 'focus', textElement)

class FlagsTest(BrowserTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.testInput = os.path.join(cls.testDir, 'testInput', cls.__name__)
        cls.testOutput = os.path.join(cls.testDir, 'testOutput', cls.__name__)

        try:
            os.mkdir(cls.testOutput)
        except (FileExistsError):
            pass

    def checkFlag(self, element, lang):
        w = 32 + 3*2 + 1
        h = 32

        self.browser.execute_script("arguments[0].blur();", element)
        self.assertTrue(self.browser.save_screenshot(os.path.join(self.__class__.testOutput, f"testFlag_{lang}.png")))
        self.assertTrue(ImageMagick.crop(os.path.join(self.__class__.testOutput, f"testFlag_{lang}.png"),
                                         os.path.join(self.__class__.testOutput, f"testFlag_{lang}.png"),
                                         {
                                             'width': w,
                                             'height': h,
                                             'x': element.rect['x'] + element.rect['width'] - w,
                                             'y': element.rect['y'] + element.rect['height'] - h
                                         }))

        diff = ImageMagick.compare(os.path.join(self.__class__.testInput, f"testFlag_{lang}.png"),
                                   os.path.join(self.__class__.testOutput, f"testFlag_{lang}.png"),
                                   os.path.join(self.__class__.testOutput, f"testFlag_{lang}_diff.png"))
        self.assertIsNot(diff, None)
        print(f"\nDSSIM for '{lang}' is: {diff} ... ", end='')
        self.assertLessEqual(diff, 0.1)

    @TestData(['ru', 'el'])
    @foreachElement
    @unittest.skipUnless(ImageMagick.checkImageMagick(), 'This test requires ImageMagick')
    def testFlag(self, lang, elementId=None):
        self.checkFlag(self.getTextElement(lang, elementId), lang)

class MessagesTest(BrowserTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print(cls.browser.install_addon(os.path.join(cls.testDir, 'dist', 'kc_test.xpi'), True))

    @TestData(['en', 'fr', 'de', 'ru', 'el'])
    def testGetLang(self, lang):
        element = self.getTextElement(lang)
        ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        self.assertEqual(ans, [lang, None])

    @TestData([
        {'lang': 'en', 'kcLang': 'ru'},
        {'lang': 'fr', 'kcLang': 'ru'},
        {'lang': 'de', 'kcLang': 'ru'},
        {'lang': 'ru', 'kcLang': 'ru'},
        {'lang': 'el', 'kcLang': 'ru'},
        {'lang': 'en', 'kcLang': 'el'},
        {'lang': 'fr', 'kcLang': 'el'},
        {'lang': 'de', 'kcLang': 'el'},
        {'lang': 'ru', 'kcLang': 'el'},
        {'lang': 'el', 'kcLang': 'el'},
    ])
    def testSetLang(self, lang, kcLang):
        element = self.getTextElement(lang)

        ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        self.assertEqual(ans, [lang, None])

        self.browser.execute_script(f"kcTest.sendMessage({{command: 'SET_LANG', lang: '{kcLang}'}}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        self.assertEqual(ans, [lang, kcLang])

        self.browser.execute_script("kcTest.sendMessage({command: 'REMOVE_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        self.assertEqual(ans, [lang, None])

class DynamicFlagsTest(FlagsTest, MessagesTest):

    def setUp(self):
        super(FlagsTest, self).setUp()

    @TestData([
        {'lang': 'en', 'kcLang': 'ru'},
        {'lang': 'fr', 'kcLang': 'ru'},
        {'lang': 'de', 'kcLang': 'ru'},
        {'lang': 'ru', 'kcLang': 'ru'},
        {'lang': 'el', 'kcLang': 'ru'},
        {'lang': 'en', 'kcLang': 'el'},
        {'lang': 'fr', 'kcLang': 'el'},
        {'lang': 'de', 'kcLang': 'el'},
        {'lang': 'ru', 'kcLang': 'el'},
        {'lang': 'el', 'kcLang': 'el'},
    ])
    @unittest.skipUnless(ImageMagick.checkImageMagick(), 'This test requires ImageMagick')
    def testFlagSetLang(self, lang, kcLang):
        element = self.getTextElement(lang)

        ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        self.assertEqual(ans, [lang, None])
        self.checkFlag(element, lang)

        self.browser.execute_script(f"kcTest.sendMessage({{command: 'SET_LANG', lang: '{kcLang}'}}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        self.assertEqual(ans, [lang, kcLang])
        self.checkFlag(element, kcLang)

        self.browser.execute_script("kcTest.sendMessage({command: 'REMOVE_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
        self.assertEqual(ans, [lang, None])
        self.checkFlag(element, lang)

class TextAreaTest(BaseTest, DynamicFlagsTest):
    elementIds = {
        'ru': ['inlineTextArea', 'blockTextArea', 'inlineBlockTextArea'],
        'el': ['inlineTextArea', 'blockTextArea', 'inlineBlockTextArea'],
    }

    def getTextElement(self, lang, elementId=None):
        if elementId is None:
            self.browser.get(os.path.join('file://' + self.__class__.testDir, 'test_mapping.html'))
            element = self.browser.find_element(By.CSS_SELECTOR, f'textarea[lang="{lang}"]')
        else:
            self.browser.get(os.path.join('file://' + self.__class__.testDir, 'test_dynamic.html'))
            element = self.browser.find_element(By.ID, elementId)
            if lang is not None:
                self.browser.execute_script(f"kcTest.sendMessage({{command: 'SET_LANG', lang: '{lang}'}}, arguments[0]).then(arguments[arguments.length - 1]);", element)
                ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
                self.assertEqual(ans, [None, lang])

        self.browser.consoleCapture.depth = 1
        return element

    def getValue(self, element):
        return element.get_property('value')

    def clearTextElements(self):
        for textArea in self.browser.find_elements(By.TAG_NAME, 'textarea'):
            textArea.clear()

class TextInputTest(BaseTest, DynamicFlagsTest):
    elementIds = {
        'ru': ['inlineTextInput'],
        'el': ['inlineTextInput'],
    }

    def getTextElement(self, lang, elementId=None):
        if elementId is None:
            self.browser.get(os.path.join('file://' + self.__class__.testDir, 'test_mapping.html'))
            element = self.browser.find_element(By.CSS_SELECTOR, f'input[type="text"][lang="{lang}"]')
        else:
            self.browser.get(os.path.join('file://' + self.__class__.testDir, 'test_dynamic.html'))
            element = self.browser.find_element(By.ID, elementId)
            if lang is not None:
                self.browser.execute_script(f"kcTest.sendMessage({{command: 'SET_LANG', lang: '{lang}'}}, arguments[0]).then(arguments[arguments.length - 1]);", element)
                ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
                self.assertEqual(ans, [None, lang])

        self.browser.consoleCapture.depth = 1
        return element

    def getValue(self, element):
        return element.get_property('value')

    def clearTextElements(self):
        for textInput in self.browser.find_elements(By.CSS_SELECTOR, 'input[type="text"]'):
            textInput.clear()

class ContentEditableTest(BaseTest, DynamicFlagsTest):
    elementIds = {
        'ru': ['blockEditableDiv', 'inlineBlockEditableDiv'],
        'el': ['blockEditableDiv', 'inlineBlockEditableDiv'],
    }

    def getTextElement(self, lang, elementId=None):
        if elementId is None:
            self.browser.get(os.path.join('file://' + self.__class__.testDir, 'test_mapping.html'))
            element = self.browser.find_element(By.CSS_SELECTOR, f'div[contentEditable="true"][lang="{lang}"]')
        else:
            self.browser.get(os.path.join('file://' + self.__class__.testDir, 'test_dynamic.html'))
            element = self.browser.find_element(By.ID, elementId)
            if lang is not None:
                self.browser.execute_script(f"kcTest.sendMessage({{command: 'SET_LANG', lang: '{lang}'}}, arguments[0]).then(arguments[arguments.length - 1]);", element)
                ans = self.browser.execute_async_script("kcTest.sendMessage({command: 'GET_LANG'}, arguments[0]).then(arguments[arguments.length - 1]);", element)
                self.assertEqual(ans, [None, lang])

        self.browser.consoleCapture.depth = 1
        return element

    def getValue(self, element):
        return element.text

    def clearTextElements(self):
        for editableDiv in self.browser.find_elements(By.CSS_SELECTOR, 'div[contentEditable="true"]'):
            editableDiv.clear()
