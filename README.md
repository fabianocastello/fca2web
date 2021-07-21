## Versão na web: http://www.fabianocastello.com.br/fca2

# FCA2web FC Auto Analyser v0.9 beta (jul/21)

(no English version - sorry!)

FCA2 é um algoritmo criado originalmente em Python para análise exploratória básica de dados, que visa trazer produtividade para analistas. De forma automática, o algoritmo trata arquivos em formato csv, xls e xlsx e realiza diversas análises:

__ identificação de campos texto, campos numéricos inteiros e números decimais.

__ campos texto: quantidade de registros, duplicações e de categorias, top "n" categorias.

__ campos numéricos: quantidade de registros, registros zerados, soma total, média, desvio, máximos e mínimos, amplitude, quartis. Mesmas descrições para a base descontando os registros zerados.


Desenvolvido originalmente por Fabiano Castello (www.fabianocastello.com.br), é disponibilizado sob licença GNL3.0 para toda a comunidade. A versão web foi criada em streamlit (www.github.com/fabianocastello/fca2web), e o código original em Python também está disponível (www.github.com/fabianocastello/fca2). FCA2 é disponibilizado em beta: use por seu próprio risco. O código original está registrado sob DOI doi.org/10.6084/m9.figshare.9902417. A versão atual conta com contribuições de Marcos Pinto.

## Sobre LGPD, GRPR e confidencialidade de dados

FCA2 cria containers a partir dos arquivos carregados para tratamento e destrói a informação assim que o processamento é realizado. Nenhuma informação é retida ou enviada para fora do site. Todos os arquivos tempororários geradaos são apagados.

## Problemas & Melhorias

Vamos trabalhar para melhorar cada vez mais o aplicativo. Neste momento o único "issue" conhecido é a questão do alinhamento dos resultados no browser, por um problema de fontes de HTML nos navegadores, particulamente referente aos "white spaces".

## FCA2 na sua organização

FCA2 pode ser instalado num servidor da sua organização por um valor fixo mensal. Para mais informações contate a cDataLab.

## NOTAS 

__ FCA2web analisa arquivos CSV, XLS e XLSX.
__ No caso de várias pastas em arquivos xls ou xlsx o FCA2 analisará a primeira delas.

__ Vírgula "," ou ponto e vírgula ";" em arquivos CSV: o FCA2 conta o número de ocorrências de cada tipo na primeira linha do arquivo, e considera como separador o maior número de ocorrências


## EM DESENVOLVIMENTO (por prioridade)

__ Ajustar o alinhamento (talvez usando a apresentação dos dados em tabelas).

__ Colocar todas as informações juntas em um PDF para download.

__ Inserir data labels nos histogramas.




