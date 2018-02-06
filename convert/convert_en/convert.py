#!/usr/bin/python
# -*- coding: cp1252 -*-

import re
import os.path
import sys
import fnmatch
import glob
import traceback
import json
import codecs
import time
import shutil
import zipfile

tableshtml={
"Tabla:PropiedadesVariablesVisuales": r'<table border="1"><col width="11%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /></colgroup><thead valign="bottom"><tr class="row-odd"><th class="head">Propiedad</th><th class="head">Posición</th><th class="head">Tamaño</th><th class="head">Forma</th><th class="head">Valor</th><th class="head">Tono</th><th class="head">Textura</th><th class="head">Orientación</th></tr></thead><tbody valign="top"><tr class="row-even"><td>Asociativa</td><td>&loz;</td><td>&#8212;</td><td>&loz;</td><td>&#8212;</td><td>&loz;</td><td>&loz;</td><td>&loz;</td></tr><tr class="row-odd"><td>Selectiva</td><td>&loz;</td><td>&loz;</td><td>&#8212;</td><td>&loz;</td><td>&loz;</td><td>&loz;</td><td>&loz;</td></tr><tr class="row-even"><td>Ordenada</td><td>&loz;</td><td>&loz;</td><td>&#8212;</td><td>&loz;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td></tr><tr class="row-odd"><td>Cuantitativa</td><td>&loz;</td><td>&loz;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td></tr></tbody></table>'
}

exps_pre = [(r"\\bigskip", ""),
        (r"\\ldots", "&hellip;"),  
        #(r"[\r\n]{2,}",r"<br><br>"),
        (r"\\centering", ""),
        (r"\\par[^t]", ""),
        (r"\\degree", "&deg;"),
        (r"\\noindent", ""),
        (r"\\vspace\{.*?\}", ""),
        (r"\\begin\{center\}", ""),
        (r"\\end\{center\}", ""),
        (r"\\small", ""),
        (r"\\emph\{(.*?)\}", r"<i>\1</i>"),
        (r"\$(.*?)\$", r"<i>\1</i>")]

        
exps_post = [(r"\\index\{.*?\}", ""),
        (r"\\pagestyle\{.*?\}",r""),
        (r"\\%", "%"),
        (r"\\_", "_"),
        (r"\\underline\{(.*?)\}", r"<u>\1</u>"),
        (r"\\footnote\{[\s\S]*?\}", ""),
        (r"\\begin\{itemize\}", "<ul>"),
        (r"\\end\{itemize\}", "</ul>"),
        (r"\\begin\{enumerate\}", "<ol>"),
        (r"\\end\{enumerate\}", "</ol>"),
        (r"\\item", "<li>"),
        (r"\\subitem", ""),
        (r"\\texttt\{(.*?)\}", r"<tt>\1</tt>"), 
        (r"\\textbf\{(.*?)\}", r"<b>\1</b>"),        
        (r"\\chapter.*?\{(.*?)\}", r'<h1 id="\1">\1</h1>'),
        (r"\\section.*?\{(.*?)\}", r'<h2 id="\1">\1</h2>'),
        (r"\\subsection.*?\{(.*?)\}", r'<h3 id="\1">\1</h3>'),
        (r"\\subsubsection.*?\{(.*?)\}", r'<h4 id="\1">\1</h4>'),
        (r"---", "&#8212;"),
        (">>", "&raquo;"),
        ("<<", "&laquo;"),
        (r"([\s\S]*?)[\r\n]{2,}", r"<p>\1</p>"),  
        (r"<p><h",r"<h"),
        (r"(</h.>)</p>",r"\1"),
        (r"<p><pre>", r"<pre>"),
        (r"</pre></p>", r"</pre>"),
        (r"><br><br>",r"><br>"),
        ]


def template():
    path = os.path.join(os.path.dirname(__file__), "html", "template.html")
    with open(path) as f:
        s = f.read()
    return s

def convertFile(path, chapterNum):     
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        s = f.read()

    for exp, replace in exps_pre:
        p = re.compile(exp)
        s = p.sub(replace, s) 

    p = re.compile(r"\\begin\{figure\}[\s\S]*?\\end\{figure\}?")
    imgs = p.findall(s)
    for i, img in enumerate(imgs):
        f = re.search(r"\\includegraphics.*?\{(.*?)\}", img).groups()[0]
        path, ext = os.path.splitext(f)
        if ext == ".pdf":
            ext = ".png"
        path = os.path.basename(path)
        size = img[img.find("["):img.rfind("]")]
        size = "".join([d for d in size if d in "0123456789."])
        try:
            size = float(size) * 100
        except:
            size = 100
        caption = re.search(r"\\caption\{(.*?)\}", img).groups()[0]
        label = re.search(r"\\label\{(.*?)\}", img).groups()[0]
        figNum = "%i.%i" % (chapterNum, i + 1)
        s = s.replace(img, (r"<a name='%s'></a><center><figure><img src='img/%s%s' width='%s%%'/>"
            "<br><figcaption>Figura %s: %s</figcaption></figure></center>" % (label, path, ext, str(size), figNum, caption)))
        s = s.replace("\\ref{%s}" % label, '<a href="#%s">%s</a>' % (label, figNum))

    p = re.compile(r"(\\begin\{table[\S\s]*?\\end\{table.*?\})")
    tables = p.findall(s)
    for tableNum, table in enumerate(tables):  
        idx = table.find("Tabla:")
        tablelabel = table[idx:table.find("}", idx)]
        idx = table.find(r"\caption") + 9        
        caption = table[idx:table.find("}\n", idx)]
        try:
            replace = "<a name='%s'></a>%s<center><figcaption>Cuadro %s: %s</figcaption></center>" % (tablelabel, tableshtml[tablelabel], tableNum + 1, caption)
            s = s.replace(table, replace)
            s = s.replace("\\ref{%s}" % tablelabel, '<a href="#%s">%s</a>' % (label, tableNum))
        except Exception, e:
            pass

    for exp, replace in exps_post:
        p = re.compile(exp)
        s = p.sub(replace, s)            

    html = template().replace("[BODY]", s)
    with open(os.path.join(os.path.dirname(__file__), "html", name + ".html"), "w") as f:
        f.write(html.decode('iso-8859-1').encode('utf8'))

    return s


def convert():
    src = os.path.join(os.path.dirname(__file__), "img")
    dst = os.path.join(os.path.dirname(__file__), "html", "img")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    chapterFiles = [os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "latex/es/prologo.tex")]
    chapterNames = ["Introduction", "History", "Cartography", "Data", 
                    "Data_sources", "Software", "Databases", "Analysis", "Visualization"]
    chapterFiles.extend([os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 
                        "latex/en/%s/%s.tex" % (n,n)) for n in chapterNames])

    chapters = []
    for i, f in enumerate(chapterFiles):
        try:
            chapter = convertFile(f, i + 1)
            chapters.append(chapter)
        except Exception, e:
            traceback.print_exc()
            pass 


    epub = zipfile.ZipFile(os.path.join(os.path.dirname(__file__), "ebook", "librosig.epub"), 'w')

    epub.writestr("mimetype", "application/epub+zip")

    epub.writestr("META-INF/container.xml", '''<container version="1.0"
               xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
      <rootfiles>
        <rootfile full-path="OEBPS/Content.opf" media-type="application/oebps-package+xml"/>
      </rootfiles>
    </container>''');

    index = '''<package version="2.0"
        xmlns="http://www.idpf.org/2007/opf">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
            <dc:title>Introducción a los SIG</dc:title>
            <dc:creator opf:file-as="Olaya, Víctor" opf:role="aut">Víctor Olaya</dc:creator>
            <dc:language>es</dc:language>        
            <dc:description>Introducción a los Sistemas de Información Geográfica.</dc:description> 
            <meta name="cover" content="cover.jpg" />               
        </metadata>
      <manifest>
        <item id="cover" href="cover.html" media-type="application/xhtml+xml"/> 
        <item id="cover-image" href="cover.jpg" media-type="image/jpeg"/>
        <item id="intro" href="intro.html" media-type="application/xhtml+xml"/>
        %(manifest)s
      </manifest>
      <spine toc="ncx">
        <itemref idref="cover" linear="no"/>
        <itemref idref="intro" />
        %(spine)s
      </spine>
    </package>'''

    cover = '''<html>
              <head>
                <title>Cover</title>
                <style type="text/css"> img { max-width: 100%; } </style>
              </head>
              <body>
                <div id="cover-image">
                  <img src="cover.jpg" alt="Introducción a los SIG"/>
                </div>
              </body>
            </html>'''

    intro = '''<html> 
                <head> 
                <title>Introducción a los SIG</title> 
                </head> 
                <body> 
                <a name="start"> 
                <h2>Introducción a los SIG</h2></a> </p> 
                <p>Copyright © Víctor Olaya. 2016</p> 
                <p>Versión del %s</p> 
                </body>
                </html>'''

    chapterTemplate = '''<html> 
                <head>  
                    <title></title>
                    <link href="base.css" rel="stylesheet" type="text/css" />               
                </head> 
                <body> 
                %s                
                </body>
                </html>'''

    manifest = ""
    spine = ""

    import locale
    try:
        locale.setlocale(locale.LC_TIME, "esn")
    except:
        pass

    epub.write(os.path.join(os.path.dirname(__file__), "ebook", "base.css"), os.path.join('OEBPS', "base.css"))
    epub.write(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "covers", "ebook_es.jpg"), os.path.join('OEBPS', "cover.jpg"))
    epub.writestr('OEBPS/intro.html', (intro % (time.strftime("%x"))).decode('iso-8859-1').encode('utf8'))
    epub.writestr('OEBPS/cover.html', (intro % (time.strftime("%x"))).decode('iso-8859-1').encode('utf8'))       

    for i, html in enumerate(chapters):
        manifest += '<item id="file_%s" href="%s.html" media-type="application/xhtml+xml"/>' % (
                      i+1, i+1)
        spine += '<itemref idref="file_%s" />' % (i+1)
        chapterText = chapterTemplate % html.replace("img/", "")
        epub.writestr('OEBPS/%i.html' % (i+1), chapterText.decode('iso-8859-1').encode('utf8')) 

    for f in os.listdir(src):
        fn = os.path.join(src, f)
        epub.write(fn, os.path.join('OEBPS', f))

    epub.writestr('OEBPS/Content.opf', (index % {
      'manifest': manifest,
      'spine': spine,
    }).decode('iso-8859-1').encode('utf8'))


###############################

def findFiles(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename
                
    
def convertImages():
    for f in findFiles('../latex', '*.pdf'):

        from subprocess import call
        dest = os.path.basename(f)
        dest = os.path.splitext(dest)[0]
        dest = "img/%s.png" % dest
        commands = [r'"Inkscape.exe"', "--export-png=" + dest, f]
        print " ".join(commands)
        #call(commands)

###############################

if __name__ == '__main__':
    convert()

