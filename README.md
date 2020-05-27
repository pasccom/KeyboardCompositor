REPOSITORY DESCRIPTION
----------------------

This repository contains a WebExtension for Mozilla Firefox, which allows
to type in other languages. It can do prefix and suffix composition, which
enables more flexibility in the mapping than only remapping the keys.

I use it to type Russian phonetically and it greatly the task of typing Cyrillic
letters (at least for me). I use it mainly on Duolingo where it has a small bug:
DuoLingo decomposes the last Cyrillic letter I typed. The simple workaround is to
use punctuation. It seems that Duolingo do not take into account the events
generated by the extension.

It currently allows to type only in Russian language. But it will be extended
to other languages. Also it requires the input field to have the `lang` attribute
set to the right language.

FEATURES
--------

Here is the list of the current features (included in version 0.1)
- Phonetic mapping of Russian Cyrillic alphabet into latin on the text fields with
the `lang` attribute

Ideas I have to extend the functionalities of the page are listed
[below](#future-developments)

FUTURE DEVELOPMENTS
-------------------

Here is the list of ideas I would like to implement
- Allow the user to activate the extension on text fields without the `lang` attribute
(or with other `lang` attribute).
- Allow the user to configure the mapping for a given language.

If you have any other feature you will be interested in, please let me know.
I will be pleased to develop it if I think it is a must have.

If you want to implement extension, also tell me please. Admittedly you
can do what you desire with the code (under the
[licensing constraints](#licensing-information)), but this will avoid double work.


BUILDING
--------

The script [build.sh](https://github.com/pasccom/KeyboardCompositor/blob/master/build.sh)
allows to easily build the extension into an `*.xpi` file.

*NOTE:* If you use the unsigned extension, you have to temporarily load the extension using
Firefox addon debugging page (`about:debugging`).

LICENSING INFORMATION
---------------------
These programs are free software: you can redistribute them and/or modify
them under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

These programs are distributed in the hope that they will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
