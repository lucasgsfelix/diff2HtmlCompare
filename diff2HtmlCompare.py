# MIT License
#
# Copyright (c) 2016 Alex Goodman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import io
import os
import sys
import json
import difflib
import argparse
import pygments
import pdfkit
import webbrowser
import diff_match_patch as dmp_module
from pygments.formatters import HtmlFormatter
from pygments.token import *

# Monokai is not quite right yet
PYGMENTS_STYLES = ["vs", "xcode"] 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html class="no-js">
    <head>
        <!-- 
          html_title:    browser tab title
          reset_css:     relative path to reset css file
          pygments_css:  relative path to pygments css file
          diff_css:      relative path to diff layout css file
          page_title:    title shown at the top of the page. This should be the filename of the files being diff'd
          original_code: full html contents of original file
          modified_code: full html contents of modified file
          jquery_js:     path to jquery.min.js
          diff_js:       path to diff.js
        -->
        <meta charset="utf-8">
        <title>
            %(html_title)s
        </title>
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="mobile-web-app-capable" content="yes">
        <link rel="stylesheet" href="%(reset_css)s" type="text/css">
        <link rel="stylesheet" href="%(diff_css)s" type="text/css">
        <link class="syntaxdef" rel="stylesheet" href="%(pygments_css)s" type="text/css">
    </head>
    <body>
        <div class="" id="topbar">
          <div id="filetitle"> 
            %(page_title)s
          </div>
          <div class="switches">
            <div class="switch">
              <input id="showoriginal" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="showoriginal" data-on="&#10004; Original" data-off="Original"></label>
            </div>
            <div class="switch">
              <input id="showmodified" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="showmodified" data-on="&#10004; Modified" data-off="Modified"></label>
            </div>
            <div class="switch">
              <input id="highlight" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="highlight" data-on="&#10004; Highlight" data-off="Highlight"></label>
            </div>
            <div class="switch">
              <input id="codeprintmargin" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="codeprintmargin" data-on="&#10004; Margin" data-off="Margin"></label>
            </div>
            <div class="switch">
              <input id="dosyntaxhighlight" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="dosyntaxhighlight" data-on="&#10004; Syntax" data-off="Syntax"></label>
            </div>
          </div>
        </div>
        <div id="maincontainer" class="%(page_width)s">
            <div id="leftcode" class="left-inner-shadow codebox divider-outside-bottom">
                <div class="codefiletab">
                    &#10092; Original
                </div>
                <div class="printmargin">
                    01234567890123456789012345678901234567890123456789012345678901234567890123456789
                </div>
                %(original_code)s
            </div>
            <div id="rightcode" class="left-inner-shadow codebox divider-outside-bottom">
                <div class="codefiletab">
                    &#10093; Modified
                </div>
                <div class="printmargin">
                    01234567890123456789012345678901234567890123456789012345678901234567890123456789
                </div>
                %(modified_code)s
            </div>
        </div>
<script src="%(jquery_js)s" type="text/javascript"></script>
<script src="%(diff_js)s" type="text/javascript"></script>
    </body>
</html>
"""


def convert_html_to_pdf(html_content, pdf_path):

    pdfkit.from_string(html_content, pdf_path, options={"enable-local-file-access": True})


def read_json_files(file_path):

    with open(file_path, 'r') as f:

        json_file = json.load(f)

    return json_file


def extract_data_from_json(json_obj, field):

    field_extraction = []

    for line in json_obj:

        # transcription
        field_extraction.append(line['speaker'] + ": " + line[field] + "\n")

    return '\n'.join(field_extraction)


def paint_text(diff, original=False):

    if original:

        html_span = "<span class=\"remove\">"

    else:

        html_span = "<span class=\"add\">"

    
    close_span = "</span>"

    complete_text = "<body><p class=\"text\">"

    for index, (code, text) in enumerate(diff):

        if code == 0:

            complete_text += text

        elif code == -1 and original:

            complete_text += html_span + text + close_span

        elif code == 1 and not original:

            complete_text += html_span + text + close_span


    return complete_text.replace('\n', '<br>') + "</body></p>"


def format(options, file1, file2):


    color_format = """
                      <style type="text/css">
                          p.text {color:black;font-weight:bold;font-family:Calibri;font-size:20}
                          span.add {color:green;font-weight:bold;font-family:Calibri;font-size:20}
                          span.remove {color:red;font-weight:bold;font-family:Calibri;font-size:20}
                      </style>
                      </head>
                    """

    fromlines = read_json_files(file1)
    fromlines = extract_data_from_json(fromlines, 'transcription')

    tolines = read_json_files(file2)
    tolines = extract_data_from_json(tolines, 'transcription')

    dmp = dmp_module.diff_match_patch()

    diff = dmp.diff_main(''.join(fromlines), ''.join(tolines))

    dmp.diff_cleanupSemantic(diff)

    painted_original_code = paint_text(diff, True)

    painted_modified_code = paint_text(diff)


    answers = {
        "html_title":     "Transcript Comparision",
        "reset_css":      os.getcwd() +  "/deps/reset.css",
        "pygments_css":   os.getcwd() + "/deps/codeformats/%s.css" % 'vs',
        "diff_css":       os.getcwd() + "/deps/diff.css",
        "page_title":     "Transcript Comparision",
        "original_code":  color_format + painted_original_code,
        "modified_code":  color_format + painted_modified_code,
        "jquery_js":      os.getcwd() +  "/deps/jquery.min.js",
        "diff_js":        os.getcwd() +  "/deps/diff.js",
        "page_width":     "page-80-width" if False else "page-full-width"
    }

    htmlContents = HTML_TEMPLATE % answers

    return htmlContents

def write(path, htmlContents):
    fh = io.open(path, 'w')
    fh.write(htmlContents)
    fh.close()


def main(file1, file2, outputpath, options):

    output_html = format(options, file1, file2)

    write(outputpath, output_html)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('file1', help='source file to compare ("before" file).')
    parser.add_argument('file2', help='source file to compare ("after" file).')

    args = parser.parse_args()


    outputpath = "index.html"

    main(args.file1, args.file2, outputpath, args)


    with open(outputpath, "r") as file:

        html_source = file.read()



    convert_html_to_pdf(html_source, "output.pdf")

    #makepdf(html_source, 'from_html.pdf')

    #asyncio.get_event_loop().run_until_complete(generate_pdf_from_html(html_source, 'from_html.pdf'))
