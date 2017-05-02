# Aim: rename files from Spanish to English in a folder
library(translateR)
es_en = function(content.vec)
  translate(content.vec = content.vec, source.lang = "es", target.lang = "en", google.api.key = Sys.getenv("GOOGLETRANSLATE"))
# test
es_en("Hola")

# translate directories manually
old_dir = setwd("latex/es/")
d = list.dirs(path = ".", full.names = F)
d_words = gsub(pattern = "_", replacement = " ", x = d)
d_words_en = c(
  "",
  "Analysis",
  "Databases",
  "Data",
  "Data sources",
  "Cartographic fundamentals",
  "History",
  "Introduction",
  "Software",
  "Visualization"
)

# check
cbind(d_words, d_words_en)
d_en = gsub(pattern = " ", replacement = "_", x = d_words_en)

f = list.files(path = ".", pattern = "*.tex", recursive = T)
f_en = f
for(i in 1:length(d)) {
  f_en = gsub(pattern = d[i], replacement = d_en[i], x = f_en)
}

setwd("../en")
for(i in d_en[-1]) {
  dir.create(i)
}
for(i in 1:length(f_en)) {
  file.copy(paste0("../es/", f[i]), f_en[i])
}
file.remove("prologo.tex")
file.remove("Libro_SIG.tex")
setwd(old_dir)

# update figure paths
d
d_refs = paste0(d[-1], "/")
d_ref_new = paste0("../es/", d_refs)
f_en = f_en[!grepl(pattern = "Libro|prolo", x = f_en)]

for(i in seq_along(f_en)) {
  doc = readLines(f_en[i])
  for(j in seq_along(d_refs)) {
    linematches = grep(pattern = d_refs[j], x = doc)
    old_doc = doc[linematches]
    print(old_doc)
    new_doc = gsub(pattern = d_refs[j], replacement = d_ref_new[j], x = old_doc, perl = T)
    print(new_doc)
    doc[linematches] = new_doc
  }
  writeLines(doc, f_en[i])
}
