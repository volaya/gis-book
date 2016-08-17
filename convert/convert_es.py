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
        (r"\$(.*?)\$", r"<i>\1</i>"),
        (r"\\iftrue[\s\S]*?\\fi", ""),
        (r"\\iffalse([\s\S]*?)\\fi", r"\1")]
        
exps_post = [(r"\\index\{.*?\}", ""),
        (r"\\pagestyle\{.*?\}",r""),
        (r"\\%", "%"),
        (r"\\_", "_"),
        (r"\\underline\{(.*?)\}", r"<u>\1</u>"),
        (r"\\begin\{intro\}([\s\S]*?)\\end\{intro\}", 
            r'<hr/><p><i>\1</i></p><hr/>'), 
        (r"\url\{(.*?)}", r'<a href="\1">\1</a>'),
        (r"\\begin\{verbatim\}([\s\S]*?)\\end\{verbatim\}", r"<pre>\1</pre>"), 
        (r"\\begin\{quotation\}([\s\S]*?)\\end\{quotation\}", r"<p>\1</p>"), 
        (r"\\begin\{displaymath\}([\s\S]*?)\\end\{displaymath\}", r"\\begin{eqnarray}\1\\end{eqnarray}"), 
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
    path = "html/template_es.html"
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
        s = s.replace(img, (r"<a name='%s'></a><figure><center><img src='../img/%s%s' width='%s%%'>"
            "<figcaption>Figura %s: %s</figcaption></figure></center>" % (label, path, ext, str(size), figNum, caption)))
        s = s.replace("\\ref{%s}" % label, '<a href="#%s">%s</a>' % (label, figNum))

    p = re.compile(r"(\\begin\{table[\S\s]*?\\end\{table.*?\})")
    tables = p.findall(s)
    for table in tables:            
        idx = table.find("Tabla:")
        tablelabel = table[idx:table.find("}", idx)]
        idx = table.find(r"\caption") + 9        
        caption = table[idx:table.find("}\n", idx)]
        try:
            replace = tableshtml[tablelabel] + "<figcaption>%s</figcaption>$$\label{%s}$$" % (caption, tablelabel)
            s = s.replace(table, replace)            
        except Exception, e:
            pass

    for exp, replace in exps_post:
        p = re.compile(exp)
        s = p.sub(replace, s)            

    html = template().replace("[BODY]", s)
    with open(os.path.join("html", name + ".html"), "w") as f:
        f.write(html.decode('iso-8859-1').encode('utf8'))

    return s



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

ebookTemplate = '''<html> 
<head> 
<title>Introducción a los SIG</title> 
</head> 
<body> 
<a name="start"> 
<h2>Introduccion a los SIG</h2></a> </p> 
<p>Copyright © Victor Olaya. 2016</p> 
<p>Versión del %s</p> 
<mbp:pagebreak/>
%s
</body>
</html>'''

if __name__ == '__main__':

    chapterFiles = ["../latex/es/prologo.tex"]
    chapterNames = ["Introduccion", "Historia", "Fundamentos_cartograficos", "Datos", 
    				"Fuentes_datos", "Software", "Bases_datos", "Analisis", "Visualizacion"]
    chapterFiles.extend(["../latex/es/%s/%s.tex" % (n,n) for n in chapterNames])


    chapters = []
    for i, f in enumerate(chapterFiles):
        try:
            chapter = convertFile(f, i + 1)
            chapters.append(chapter)
        except Exception, e:
            traceback.print_exc()
            pass 

    import locale
    locale.setlocale(locale.LC_TIME, "esn")
    fullBook = "<mbp:pagebreak/>".join(chapters)
    with open("html/ebook.html", 'w')  as f:
        text = ebookTemplate % (time.strftime("%x") , fullBook)
        f.write(text)
