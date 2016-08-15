#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import os.path
import sys
import fnmatch
import glob
import traceback
import json
import codecs

tableshtml={
"Tabla:PropiedadesVariablesVisuales": r'<table border="1"><col width="11%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /><col width="13%" /></colgroup><thead valign="bottom"><tr class="row-odd"><th class="head">Propiedad</th><th class="head">Posición</th><th class="head">Tamaño</th><th class="head">Forma</th><th class="head">Valor</th><th class="head">Tono</th><th class="head">Textura</th><th class="head">Orientación</th></tr></thead><tbody valign="top"><tr class="row-even"><td>Asociativa</td><td><span class="math">\(\diamondsuit\)</span></td><td>&#8212;</td><td><span class="math">\(\diamondsuit\)</span></td><td>&#8212;</td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td></tr><tr class="row-odd"><td>Selectiva</td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td><td>&#8212;</td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td></tr><tr class="row-even"><td>Ordenada</td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td><td>&#8212;</td><td><span class="math">\(\diamondsuit\)</span></td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td></tr><tr class="row-odd"><td>Cuantitativa</td><td><span class="math">\(\diamondsuit\)</span></td><td><span class="math">\(\diamondsuit\)</span></td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td></tr></tbody></table>'
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
        (r"\\iftrue[\s\S]*?\\fi", ""),
        (r"\\iffalse([\s\S]*?)\\fi", r"\1")]
        
exps_post = [(r"\\index\{.*?\}", ""),
        (r"\\pagestyle\{.*?\}",r""),
        (r"\\%", "%"),
        (r"\\_", "_"),
        (r"\\emph\{(.*?)\}", r"<i>\1</i>"),
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
        (r"\\chapter.*?\{(.*?)\}", ""),
        (r"\\section.*?\{(.*?)\}", r'<h2 id="\1">\1</h2>'),
        (r"\\subsection.*?\{(.*?)\}", r'<h3 id="\1">\1</h3>'),
        (r"\\subsubsection.*?\{(.*?)\}", r'<h4 id="\1">\1</h4>'),
        (r"\\begin\{figure\}.*?\n", "<figure></center>"),
        (r"\\end\{figure\}", "</figure></center>"),
        (r"\\caption\{(.*)\}", r"<figcaption>\1</figcaption>"),
        (r"(\\label\{Fig:.*?\})", r"$$\1$$"),
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
    path = "template.html"
    with open(path) as f:
        s = f.read()
    return s

labelrefs = {}

def convertFile(path):     
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        s = f.read()

    for exp, replace in exps_pre:
        p = re.compile(exp)
        s = p.sub(replace, s) 

    p = re.compile(r"\\chapter.*?\{(.*?)\}")
    title = p.findall(s)[0]
    p = re.compile(r"\\chapterauthor\{(.*?)\}")
    authors = p.findall(s)
    p = re.compile(r"\\cite\{([ \S]*?)\}")
    cites = p.findall(s) 
    for cite in cites:
        rep = "".join(['[<a href="../bib.htm#%s">%s</a>]' % (c.strip(),c.strip()) for c in cite.split(",")])
        s = s.replace(r"\cite{%s}" % cite, rep)
    p = re.compile(r"(\\includegraphics.*?\{.*?\})")
    imgs = p.findall(s)
    for img in imgs:
        f = img[img.find("{")+1:img.rfind("}")]
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
        s = s.replace(img, r"<img src='../img/%s%s' width='%s'>" % (path, ext, str(size) + "%"))
    p = re.compile(r"\\label\{([^:]*?)\}")
    labels = p.findall(s)
    global labelrefs
    for label in labels:
        labelrefs[label] = name
    s = p.sub(r'<a name="\1"></a>', s) 

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
            print e
            pass

    for exp, replace in exps_post:
        p = re.compile(exp)
        s = p.sub(replace, s)            

    html = template().replace("[BODY]", s).replace("[TITLE]", title)
    with open(os.path.join("chapters", name + ".html"), "w") as f:
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
%s
</body>
</html>'''

if __name__ == '__main__':
    try:
    	os.mkdir("chapters")
    except:
    	pass

    chapterNames = ["Introduccion", "Historia", "Fundamentos_cartograficos", "Datos", 
    				"Fuentes_datos", "Software", "Bases_datos", "Analisis", "Visualizacion"]
    chapterFiles = ["../latex/es/%s/%s.tex" % (n,n) for n in chapterNames]

    chapters = []
    for f in chapterFiles:
        try:
            chapter = convertFile(f)
            chapters.append(chapter)
        except Exception, e:
            traceback.print_exc()
            pass 

    chapterHtmlFiles = ["chapters/%s.html" % n for n in chapterNames]
    for path in chapterFiles:
        with open(path) as f:
            s = f.read()
        p = re.compile(r"\\ref\{([^:]*?)\}")
        refs = p.findall(s)
        for ref in refs:
            try:
                s = s.replace(r"\ref{%s}" % ref, '<a href="%s.html#%s">%s</a>' % (labelrefs[ref], ref, ref))
            except KeyError:
                pass
                #print ref
        with open(path, "w") as f:
            f.write(s)

    for chapter in chapters:
    	p = re.compile(r"\\ref\{([^:]*?)\}")
        refs = p.findall(chapter)
        for ref in refs:
            try:
                s = s.replace(r"\ref{%s}" % ref, '<a href="#%s">%s</a>' % (labelrefs[ref], ref, ref))
            except KeyError:
                pass
    fullBook = "<mbp:pagebreak/>".join(chapters)
    with open("chapters/ebook.html", 'w')  as f:
        f.write(ebookTemplate % fullBook)
