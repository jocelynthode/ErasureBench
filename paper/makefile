# Macro pour la compilation de fichiers LaTeX
# Derni�res modifications : 15 janvier 2016

# -------------------------------------------------------------------------------

# Nom du fichier LaTeX principal

SRC = main

# -------------------------------------------------------------------------------

.PHONY : nobib bib slides clean cleanfinal

# -------------------------------------------------------------------------------

bib:    # With bibTeX
	make clean
	pdflatex -synctex=1 -shell-escape $(SRC).tex
	biber $(SRC)
	pdflatex -synctex=1 -shell-escape $(SRC).tex
	pdflatex -synctex=1 -shell-escape $(SRC).tex
	make clean
	open -a Skim $(SRC).pdf	

nobib:  # Without bibTeX
	make clean
	pdflatex -synctex=1 -shell-escape $(SRC).tex
	pdflatex -synctex=1 -shell-escape $(SRC).tex
	make clean
	open -a Skim $(SRC).pdf	

slides: # For sans serif fonts compiled with lualatex. Better for presentations.
	make clean
	lualatex -synctex=1 --jobname=$(SRC)_p $(SRC).tex
#	lualatex -synctex=1 --jobname=$(SRC)_p $(SRC).tex
	make clean
	lualatex  -synctex=1 "\def\ishandout{1} \input{$(SRC).tex}"
#	lualatex  -synctex=1 "\def\ishandout{1} \input{$(SRC).tex}"
	make clean
	make cleanfinal
	open -a Skim $(SRC)_p.pdf

# -------------------------------------------------------------------------------

# Elimine les fichiers temporaires.

clean:
# Le - permet d'�viter des erreurs si la commande �choue.
	-rm *.log *.aux *.aux *.bbl *.blg *.info *.toc *.lof *.out *.lot *.dvi *.snm *.nav *.log *.aux *.aux *.bbl *.blg *.info *.toc *.lof *.out *.lot *.dvi *.snm *.nav

cleanfinal:
	-rm *.synctex.gz *~ 
	-rm -R auto

# -------------------------------------------------------------------------------
