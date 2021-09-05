import os

import sys
import numpy as np
import requests
import pandas as pd
from pandas import ExcelFile 
from datetime import datetime
from datetime import timedelta
import time, socket
import seaborn as sns
import matplotlib.pyplot as plt
from glob import glob
import textwrap
import socket
from PIL import Image
from random import randrange
import streamlit as st
from streamlit import caching
import base64

#global UserAgents, runningOn, parâmetros, remarks, sizeKB
runningOn =  socket.gethostname()

#USerAgents para post das estatísticas
with open("./UserAgents.cfg",encoding='utf-8') as f:
     UserAgents = f.readlines(); f.close()
UserAgents = [c.replace('\n','').strip() for c in UserAgents]

if not runningOn == 'localhost':
    import configparser
    config_parser = configparser.RawConfigParser()
    config_parser.read('./fca2web.ini')
    url_post_stat  = config_parser.get('RUN', 'url_post_stat')
else:
    url_post_stat = st.secrets["url_post_stat"]

caching.clear_cache()
st.set_page_config(
        page_title="FCA2 - FCastell Auto Analyser")
        
def run():
    global msg_count, max_freq, hist_bins, max_dups
    global hist, boxp, mcorr, noheader, sep_csv, filecst, dec_csv, sampleN
    global UserAgents, runningOn, parâmetros, remarks, sizeKB

    st.markdown(f'''
    <body>
    <p style="font-size:50px;line-height: 25px"><i><b>FCA2</b></i><br>
    <p style="font-size:30px;line-height: 25px"><b>FCastell Auto Analyser</b><br>
    <span style="font-size: 12pt;"><i>{FC_Auto_Analyser_Version} by Fabiano Castello.</i></span>
    </p>
    </body>
    ''', unsafe_allow_html=True)
    
    # COLOCAR PARAMETROS NO SIDEBAR

    hide_streamlit_style = """<style>#MainMenu {visibility: hidden;}
                              footer {visibility: hidden;}
                              </style>"""
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    max_freq  = st.sidebar.slider('Qte máxima de categorias nas colunas de texto:', 1, 20, max_freq,
    help=tool_tips('max_freq'))
    hist_bins = st.sidebar.slider('Qte de bins no histograma:', 1, 20, hist_bins,
    help=tool_tips('hist_bins'))
    max_dups = st.sidebar.slider('Qte máxima de exemplos de duplicados:', 1, 10, max_dups,
    help=tool_tips('max_dups'))
    sampleN = st.sidebar.slider('Qte máxima de itens para amostragem:', 1, 10, sampleN,
    help=tool_tips('sampleN'))
    hist  =  st.sidebar.checkbox('Mostrar histograma?', value=False,
    help=tool_tips('max_dups'))
    boxp  =  st.sidebar.checkbox('Mostrar boxplot?', value=False,
    help=tool_tips('boxp'))
    mcorr =  st.sidebar.checkbox('Mostrar matriz de correlação?', value=False,
    help=tool_tips('mcorr'))
    noheader  =  st.sidebar.checkbox('Marque se o seu arquivo não tem header (cabeçalho)', value=False,
    help=tool_tips('noheader'))
    filecst  =  st.sidebar.checkbox('Marque para customizar colunas', value=False,
    help=tool_tips('filecst'))
    sep_csv  =  st.sidebar.text_input('Definir separador específico para arquivos CSV?', value='',
    help=tool_tips('sep_csv'))
    dec_csv  =  st.sidebar.checkbox('Marque para usar "," em colunas decimais em arquivos CSV(padrão=".")', value=False, help=tool_tips('dec_csv'))
 
    try:    del uploaded_files
    except: pass
        
        
    titanic =  st.checkbox('Marque para ver uma demonstração (titanic)', value=False,
    help=tool_tips('titanic'))
    
    sharing = st.empty()

    
    with st.expander("Considerações sobre formatos de arquivos e campos de data"):
           st.write("""
               FCA2 aceita arquivos formato CSV, Excel, Feather, Pickle e Pickle compactado (gzip). Se vc tem um arquivo CSV com extensão TXT ou outra, renomeie para que o arquivo seja analisado. O limite para análise é de 200Mb. Localmente é possível rodar arquivos até 1Gb, porém arquivos com mais de 200Mb o processamento é lento e todos os recursos são consumidos, a ponto de você achar que sua máquina travou. """)
           st.write("""
               **Em termos técnicos**, arquivos XLS muitas vezes são problemátivos, sempre que possível use XLSX; nos casos de arquivos CSV com problema de tokenização o FCA2 automaticamente tenta carregar usando o engine Python e, no caso de falha, o engine C++; Pickle funciona com protocolos 1 a 4, compactados com gzip ou não. Feather "vanilla" roda bem, mas dependendo da versão de pyarrow instalada não há suporte para lz4 e snappy.""")
           st.write("""
               **Sobre datas**, a partir de setembro de 2021 implementei análise de colunas datetime. Estava fazendo falta e agora está bem completo. No entanto, são raras as situações onde o pandas detecta colunas datetime de forma automática; nestes casos use a customização de colunas. Converter texto em datas é um processo relativamente lento porque são feitos testes por amostragem para vários formatos de datas (por exemplo %Y-%m-%d, %Y%m%d, %d/%m/%Y), e, após o teste, tenta-se a conversão pelo formato que teve menos erros de conversão. Outro ponto, existe uma análise chamada "filling", que considera o range de dias, meses e anos e informa, para todos os ranges, em qual "slots" há dado presente. Última coisa: em todas as análises o formato utilizado é o ISO (YYYY-MM-DD).""")
               
    sharing_message = """
    <body><p style="font-size:14px;line-height:16px"><b>Curtiu o FCA2? Compartilhe!</b></span>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <a href="https://www.facebook.com/sharer/sharer.php?title=FCA2+Análise+exploratória+de+dados+gratuita,+segura+e+colaborativa&u=https://www.fabianocastello.com.br/fca2/"
    style="text-decoration:none" target="_blank"
    class="fa fa-facebook"> </a>&nbsp;
    <a href="https://twitter.com/intent/tweet?text=FCA2+Análise+exploratória+de+dados+gratuita,+segura+e+colaborativa&url=https://www.fabianocastello.com.br/fca2/" 
    style="text-decoration:none" target="_blank"
    class="fa fa-twitter"></a>&nbsp;
    <a href="whatsapp://send?text=FCA2+Análise+exploratória+de+dados+gratuita,+segura+e+colaborativa https://www.fabianocastello.com.br/fca2/" 
    style="text-decoration:none" target="_blank"
    class="fa fa-whatsapp"></a>
    </p></body>
    """
    st.markdown(sharing_message, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader('Informe o arquivo para análise. Acesse a barra lateral (">" à esquerda) para opções. O link para baixar o relatório em formato TXT está no final da análise.', type =['csv','xls','xlsx','feather','pkl','zpkl'],
                    accept_multiple_files=False, help=tool_tips('uploaded_file'))
         
    # UploadedFile(id=8, name='xxx 000 Test Dates Simplificado.xlsx', type='application/vnd.ms-excel', size=1211)
    # ago/21 - restrito para um arquivo apenas
    if uploaded_file is not None or titanic:
        if titanic: 
            with open('./titanic.pkl', 'rb') as base:
                content = base.read()
                with open(os.path.join(datain,"titanic.pkl"),"wb") as f:
                    f.write(content)
            hist=True
            boxp = True
            mcorr = True
        else:
            with open(os.path.join(datain,uploaded_file.name),"wb") as f:
                f.write(uploaded_file.getbuffer())
        files = os.listdir(datain)
        if len(files) != 0:
            dfs = [i for i in files if ('XLSX' in i[-4:].upper()) or 
                                       ('XLS' in i[-3:].upper())  or 
                                       ('CSV' in i[-3:].upper())  or 
                                       ('FEATHER' in i[-7:].upper())  or 
                                       ('PKL' in i[-3:].upper())  or 
                                       ('ZPKL' in i[-4:].upper()) ]
            msg_count  = 0
            filesToWorkOn = sorted(dfs) 
            for name in filesToWorkOn:
                st.markdown(f'''<body><p style="font-size:20px;margin-bottom: -5px;">
                                Analisando <b>{name}</b></p></body>''', unsafe_allow_html=True)
                                
                parâmetros = f'max_freq={max_freq}; hist_bins={hist_bins}; max_dups={max_dups};'+\
                             f'hist={hist}; boxp={boxp}; mcorr={mcorr}; noheader={noheader}; '
                remarks = ''
                sizeKB     = int(round(os.stat(datain+"/"+name).st_size/1024,0))
                
                global output
                output = pd.DataFrame(columns=['TS','Row','Content','NewLine'])
                analysis(name)

    
    st.markdown(f'''
    <body>
    <p style="font-size:30px;margin-bottom: -5px;">
    <br>
    <b>Sobre FCA2</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    FCA2 é um algoritmo criado em Python para análise exploratória básica de dados, que visa trazer <b>produtividade</b> para analistas. De forma automática, o algoritmo trata arquivos em formato csv, xls e xlsx e realiza diversas análises: <span style="font-size:10px ;margin-bottom: -5px;"> 
    <ul style="margin-bottom: -5px;">
      <li>identificação de colunas texto (categóricas), colunas numéricas inteiras e numéricas decimais.</li>
      <li>colunas texto: quantidade de registros, registros ausentes, duplicações e categorias, top "n" categorias.</li>
      <li>colunas numéricas: quantidade de registros, registros zerados, soma total, média, desvio, máximos e mínimos, amplitude, quartis. Mesmas análises para a base descontando os registros zerados, lembrando que zero é diferente de ausente :-).</li>
    </ul></span><span style="font-size:16px ;line-height: 25px"><br>
    Desenvolvido originalmente por Fabiano Castello (<a target="_blank" href ="http://www.fabianocastello.com.br">www.fabianocastello.com.br</a>), é disponibilizado <b>gratuitamente</b> sob licença CC BY 4.0 para a comunidade. O código original está registrado sob DOI <a target="_blank" href ="http://doi.org/10.6084/m9.figshare.9902417">doi.org/10.6084/m9.figshare.9902417</a>. A versão web foi criada em streamlit e está disponível em (<a target="_blank" href ="http://www.github.com/fabianocastello/fca2web">www.github.com/fabianocastello/fca2web</a>). Se você usar esta aplicação em um artigo ou publicação pode incluir a citação "Castello, Fabiano (2019): <i>Python Code: FC Auto Analyser (FCA2)</i>. figshare. Software. https://doi.org/10.6084/m9.figshare.9902417.v1".</span> </p><br>
    
    <p style="font-size:20px;margin-bottom: -5px;"><b><i>What's New @ {FC_Auto_Analyser_Version}</i></b></p>
    <p style="font-size:16px;margin-bottom: -5px<span style="font-size:10px ;margin-bottom: -5px;"> 
    <ul style="margin-bottom: -5px;">
      <li>análises de colunas datetime (set/21).</li>
      <li>links para compartilhar no facebook, twitter e whatsapp (set/21).</li>
      <li>formatos Feather e Pickle (em beta) (ago/21).</li>
      <li>download do relatório da análise em TXT (ago/21).</li>
      <li>melhorias na formatação do relatório (ago/21).</li>
      <li>mudança do licenciamento para CC BY 4.0 (jul/21).</li>
      <li>boxplot, customização de colunas, amostragem e exemplos de duplicados (ago/21).</li>
      <li>tentativa automática de abrir arquivo CSV com engine Python e C (ago/21).</li>
    </ul></span><span style="font-size:16px ;line-height: 25px"><br>
   
    <p style="font-size:20px;margin-bottom: -5px;"><b><i>Issues</i> conhecidos</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    <ul style="margin-bottom: -5px;">
    <li>formatos Feather e Pickle, dependendo da compressão usada no momento da gravação podem apresentar problemas para serem abertos no FCA2.</li>
    <li><i>Se vc identificar um problema faça o reporte em  <a target="_blank" href ="http://www.github.com/fabianocastello/fca2web/issues">www.github.com/fabianocastello/fca2web/issues</a></i>.</li>
    </ul></p><br>
    
    <p style="font-size:20px;margin-bottom: -5px;"><b>O que está no <i>pipeline</i></b></p>
    <p style="font-size:16px;margin-bottom: -5px<span style="font-size:10px ;margin-bottom: -5px;"> 
    <ul style="margin-bottom: -5px;">
      <li>gerar um arquivo em PDF com a análise consolidada, incluindo os gráficos.</li>
      <li>gerar gráficos com informações relevantes, usando seaborn.</li>
      <li>analisar colunas do tipo binário.</li>
      <li>postar estatísticas da utilização.</li>
    </ul></span><span style="font-size:16px ;line-height: 25px"><br>
    
    <p style="font-size:20px;margin-bottom: -5px;"><b>Sobre LGPD, GRPR e confidencialidade de dados</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    FCA2 cria containers a partir dos arquivos carregados para tratamento e destrói a informação assim que o processamento é realizado. Nenhuma informação é retida ou enviada para fora do site (exceto tipo do arquivo, tamanho, tempo de processamento e parâmetros, para efeito de gerar estatísticas). Todos os arquivos tempororários geradaos são apagados.</p><br>

    <p style="font-size:20px;margin-bottom: -5px;"><b>Contribuições</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    FCA2 é mantido pelo autor com contribuições da comunidade.<br>Thanks: Marcus Pinto, João Victor Mulle, Mateus Ricci, Vivian Sato.<br><i>Para contribuir com o código do projeto faça um "fork" a partir do repositório <a target="_blank" href ="http://www.github.com/fabianocastello/fca2web">www.github.com/fabianocastello/fca2web</a>. Para sugerir melhorias, mesmo sem ter a menor noção de como fazer isso na linguagem Python, envie um email para <a href ="mailto:fca2@fabianocastello.com.br?Subject:Contribuição_FCA2">fca2@fabianocastello.com.br</a></i>.</p><br>
    
    <p style="font-size:20px;margin-bottom: -5px;"><b>FCA2 na sua organização</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    FCA2 pode ser instalado num servidor da sua organização por um valor fixo mensal. Para mais informações contate a <a target="_blank" target="_blank" href ="http://www.cdatalab.com.br">cDataLab</a>.</p> 
    </body>
    ''', unsafe_allow_html=True)
    return()

######################################################################
###################################################################### End of Streamlit
######################################################################

#Parâmetros
datain    = "./!data.in"    
dataout   = "./!data.out"   #onde analisador vai gravar os resultados
datalog   = "./!data.log"   #onde o analisador vai gravar os logs do processamento 
datatmp   = "./!data.tmp"   #arquivos temporários. Será limpo após o processamento

max_freq  = 10 #numeros de categorias máximas nos campos texto
hist_bins = 10 #qte de bins no histograma 
max_dups  =  5 #qte de exemplos de duplicados 
sampleN    =  5 #qte de exemplos da coluna 

FC_Auto_Analyser_Version = 'fca2web beta 0.96 (2021SET04) '

#Criando diretórios se inexistentes
dirs = ['!data.tmp','!data.out','!data.log','!data.in']
for d in dirs:
    if not os.path.exists(d):
        os.makedirs(d)
    else:
        files = glob(f'{d}/*')
        for f in files: os.remove(f)
        
def post_stat_fca2(filename, sizeKB, parâmetros, elap,remarks=''):
    
    form_data = { 'entry.525617926' : runningOn,
                  'entry.506775480' : filename,
                  'entry.442023490' : sizeKB,
                  'entry.2027178672': elap,
                  'entry.222084486' : parâmetros,
                  'entry.225285568' : runningOn,
                  'entry.1052496244': remarks }
    return(requests.post(url_post_stat+'/formResponse', data=form_data, headers=
                 {'Referer':url_post_stat+'/viewform',
                  'User-Agent': UserAgents[randrange(len(UserAgents))]}))

global msg_count
msg_count = 0
def msgC():
    global msg_count
    msg_count += 1
    return(str(msg_count).zfill(4))

def log_write(msg, newline=False, addcont=True):
    global output
    ident = '&nbsp;'*5
    if newline:
        st.markdown(f'''<body><p style="font-size:14px;margin-bottom: -5px;
                    font-family: monospace;"><br></p></body>''', unsafe_allow_html=True)
    #msg = msg.replace('  ',' ')
    cut = 105
    msgCstr = msgC() if addcont else None
    if addcont:
        full_msg  = (f'{msgCstr} {msg}').strip()
    else:
        full_msg  = (f'{ident+msg}').strip()
        
    output = output.append({
                   'TS'      : datetime.today(),
                   'Row'     : msgCstr,
                   'Content' : msg,
                   'NewLine' : newline,
                   
                   },ignore_index=True)
                   
                   
    first_msg = full_msg[:cut].replace(' ', '&nbsp;').replace('\n', '<br>')
    first_msg = first_msg.replace('<b>', '83e7b7bc412f20').replace('</b>', '8xe7b7bc412f20B')
    first_msg = first_msg.replace('<', '&#60;').replace('>', '&#62;')
    first_msg = first_msg.replace('83e7b7bc412f20', '<b>').replace('8xe7b7bc412f20B','</b>')
    
    rest_msg  = full_msg[cut:].replace(' ', '&nbsp;').replace('\n', '<br>')
    rest_msg  = rest_msg.replace('<b>', '83e7b7bc412f20').replace('</b>', '8xe7b7bc412f20B')
    rest_msg  = rest_msg.replace('<', '&#60;').replace('>', '&#62;')
    rest_msg  = rest_msg.replace('83e7b7bc412f20', '<b>').replace('8xe7b7bc412f20B','</b>')


    st.markdown(f'''<body><p style="font-size:14px;margin-bottom: -5px;
                    font-family: monospace">
                    {first_msg}</p></body>''', unsafe_allow_html=True)
    if len(rest_msg) > 0:
        msgs = textwrap.wrap(rest_msg, cut)
        for msg in msgs:
            st.markdown(f'''<body><p style="font-size:14px;margin-bottom: -5px;
                    font-family: monospace" >
                    {ident+msg.strip()}</p></body>''', unsafe_allow_html=True) 
    return() #

def sep(ser):
    if ser > 0: return(", ")
    return("")   
    
def analysis(file):
    
    global df,ctmp, ctmp_counts, i, x, xqte_corr  
    global start_time
    if True: #try:
        log_write("Iniciando análise de "+file)
        start_time = time.time()

        # open the file
        if 'csv' in file.lower():
            decimalcsv = ',' if dec_csv else '.'
            try:
                if len(sep_csv.strip()) == 0:
                    f = open(datain+"/"+file,encoding='utf-8')
                    line = f.readline()
                    f.close()
                    semicolon = line.count(";")
                    comma = line.count(",")
                    if semicolon > comma:
                        separador = ";"
                    else:
                        separador = ","
                else:
                    separador = sep_csv.strip()
                log_write("Separador de CSV selecionado [ "+separador+" ]")
                log_write("Parâmetro para leitura de números decimais [ "+decimalcsv+" ]")
                if separador == decimalcsv:
                    st.error('ALERTA!!! separador e parâmetro de decimais identicos. Verifique.')
                if noheader:
                    try:
                        df = pd.read_csv(datain+"/"+file, encoding ='utf-8', engine='python', sep = separador, header=None, decimal=decimalcsv)
                    except Exception as erro:
                        log_write("Erro! Tentando com engine C")
                        df = pd.read_csv(datain+"/"+file, encoding ='utf-8', engine='c', sep = separador, header=None, decimal=decimalcsv)
                        log_write("Base carregada com sucesso")

                    for c in df.columns:
                        df.rename({c:f'Coluna{c}'}, axis=1, inplace=True)
                       
                else:
                    log_write("Abrindo arquivo com engine Python")
                    try:
                        df = pd.read_csv(datain+"/"+file, encoding ='utf-8', engine='python',
                                            sep = separador, decimal=decimalcsv)
                    except Exception as erro:
                        log_write("Erro! Tentando com engine C")
                        df = pd.read_csv(datain+"/"+file, encoding ='utf-8', engine='c',
                                            sep = separador, decimal=decimalcsv)
                        log_write("Base carregada com sucesso")
                                                    
            except Exception as erro:
                log_write("Erro "+str(erro))
                log_write("Abortando analise "+file)
                log_write("Sugestão: verifique se o arquivos está codificado como UTF-8")
                return(-1)
        elif 'xls' in file.lower():
            try:
                if noheader:
                    df = pd.read_excel(datain+"/"+file, header=None)
                    for c in df.columns:
                        df.rename({c:f'Coluna{c}'}, axis=1, inplace=True)
                else:
                    df = pd.read_excel(datain+"/"+file)
                
            except Exception as erro:
                log_write("Erro "+str(erro))
                log_write("Abortando analise "+file+"\n")
                return(-1)
                
        elif 'feather' in file.lower():
            import lz4
            try:
                if noheader:
                    log_write("Feather não tem a opção de carregar sem header")
                df = pd.read_feather(datain+"/"+file)
                
            except Exception as erro:
                log_write("Erro "+str(erro))
                log_write("Abortando analise "+file+"\n")
                return(-1)
                
        elif 'zpkl' in file.lower():
            import gzip, pickle, pickletools
            if noheader:
                log_write("Gzip Pickle não tem a opção de carregar sem header")
            with gzip.open(datain+"/"+file, 'rb') as f:
              df = pickle.Unpickler(f).load()


        elif 'pkl' in file.lower():     
            try:
                import gzip, pickle, pickletools
                if noheader:
                    log_write("Pickle não tem a opção de carregar sem header")
                try:
                    df = pd.read_pickle(datain+"/"+file)
                except:                  
                    import pickle5 as pickle
                    with open(datain+"/"+file, "rb") as fh:
                          df = pickle.load(fh)
                
            except Exception as erro:
                log_write("Erro "+str(erro))
                log_write("Abortando analise "+file+"\n")
                return(-1)
                
        else:
            log_write("Erro identificando arquivo")
            return(-1)
        if filecst:
            df = custom_df(df)
            
        analysis_df(df,file)
        return(None)
        
def custom_df(df):
    custom = pd.DataFrame(columns = ['Índice','Coluna','Type','Tipo','Custom','CustomType'])
    for c in df.columns:
        custom = custom.append({'Coluna': c,
                                'Type'  : df[c].dtype}, ignore_index=True)
    custom['Índice'] = custom.index+1
    for index, row in custom.iterrows():
        if 'Unnamed' in row['Coluna']:
            custom.at[index,'Coluna'] = 'Coluna '+str(index+1)
            df.rename({row['Coluna']:'Coluna '+str(index+1)}, axis=1, inplace=True)
        if    row['Type'] == 'object':
               custom.at[index, 'Tipo'] = 'Texto'
        elif  row['Type'] == 'int64':
               custom.at[index, 'Tipo'] = 'Numérico(int)'
        elif  row['Type'] == 'float64':
               custom.at[index, 'Tipo'] = 'Numérico(dec)'
        else:
               custom.at[index, 'Tipo'] = 'Texto'
    custom['Custom'] = custom['Tipo']        
    opt = dict()
    opt['Texto']         = 0
    opt['Numérico(int)'] = 1
    opt['Numérico(dec)'] = 2
    opt['Datetime'] = 3

    global i
    with st.form("my_form"):
       st.write("Customização de colunas", help=tool_tips('form_custom'))
       for i in range(0,custom.shape[0]):
           col = custom['Coluna'].loc[i]
           exemplos = 'Exemplos: '+('; '.join(
                [str(c) for c in list(df[col].unique()[:3])])).strip()
           s = "custom"+str(i)+"=st.radio(f'Coluna {str(i+1)}: '+'["+custom['Coluna'].loc[i]+"] "+exemplos+\
               "', options=['Texto', 'Numérico(int)', 'Numérico(dec)', 'Datetime'], "+\
               "index="+str(opt[custom['Custom'].loc[i]])+")"
           exec(s, globals())

       submitted = st.form_submit_button("Processar alterações")
       if not submitted:
           st.stop()
       else:
            for i in range(0, custom.shape[0]):
                s = "custom.at[i,'Custom'] = custom"+str(i)
                exec(s)
    
    log_write("### <b>Analisando e convertendo colunas</b>", newline=True) 
    changes = custom[custom.Tipo != custom.Custom].shape[0]    
    log_write(f'{changes} coluna(s) alterada(s)') 
    opt_rename = dict()
    opt_rename['Texto']         = 'Tx'
    opt_rename['Numérico(int)'] = 'Ni'
    opt_rename['Numérico(dec)'] = 'Nd'
    opt_rename['Datetime']      = 'Dt'
    for index, row in custom.iterrows():
        custom.at[index,'Rename'] = opt_rename[row['Tipo']]+'>'+opt_rename[row['Custom']]

    for index, row in custom.iterrows():
        if    row['Custom'] == 'Texto':
               custom.at[index, 'CustomType'] = 'object'
        elif  row['Custom'] == 'Numérico(int)':
               custom.at[index, 'CustomType'] = 'int64'
        elif  row['Custom'] == 'Numérico(dec)':
               custom.at[index, 'CustomType'] = 'float64'
        elif  row['Custom'] == 'Datetime':
               custom.at[index, 'CustomType'] = 'datetime64[ns]'
    for index, row in custom.iterrows():
        if not row['Type'] == row['CustomType']:
            log_write(f"Convertendo [{row['Coluna']}] de [{row['Tipo']}] para [{row['Custom']}]",
                        addcont=True,newline=False)
            if    row['CustomType'] == 'object':
                df[row['Coluna']] = df[row['Coluna']].astype(row['CustomType']) 
                if 'float' in str(row['Type']).lower():
                    df[row['Coluna']] = df[row['Coluna']].apply(lambda x: str(x)[:-2] if str(x)[-2:] == '.0' else x)
                log_write(f"[{row['Coluna']}] renomeada para {row['Coluna']+'('+row['Rename']+')'}.",
                        addcont=False,newline=False)
                df.rename({row['Coluna']:row['Coluna']+'('+row['Rename']+')'}, axis=1, inplace=True)
                
            elif  row['CustomType'] == 'float64':
                NaN_inicial =   df[row['Coluna']].isnull().sum()
                df[row['Coluna']] = pd.to_numeric(df[row['Coluna']], errors='coerce')
                NaN_final =   df[row['Coluna']].isnull().sum()
                if df[row['Coluna']].dtype == row['CustomType']:
                    if NaN_inicial == NaN_final:
                        log_write(f"100% convertido sem erros",
                        addcont=False,newline=False)
                    else:
                        log_write(f"{NaN_final - NaN_inicial:,} erros na conversão (assumidos como missing).",
                                    addcont=False,newline=False)
                    log_write(f"[{row['Coluna']}] renomeada para {row['Coluna']+'('+row['Rename']+')'}.",
                            addcont=False,newline=False)
                    df.rename({row['Coluna']:row['Coluna']+'('+row['Rename']+')'}, axis=1, inplace=True)
                else:
                    log_write(f"*ERRO* convertendo [{row['Coluna']}] de "+\
                          f"[{row['Tipo']}] para [{row['Custom']}] ({df[row['Coluna']].dtype})",
                        addcont=False,newline=False)

            elif row['CustomType'] == 'int64':     ####### INTEIRO
                NaN_inicial =   df[row['Coluna']].isnull().sum()
                df[row['Coluna']] = pd.to_numeric(df[row['Coluna']], errors='coerce')
                df[row['Coluna']] = df[row['Coluna']].apply(lambda x: x if pd.isna(x) else int(x))
                df[row['Coluna']] = df[row['Coluna']].astype(float).astype('Int64')
                NaN_final =   df[row['Coluna']].isnull().sum()
                if df[row['Coluna']].dtype == 'Int64':
                    if NaN_inicial == NaN_final:
                        log_write(f"100% convertido sem erros",
                                    addcont=False,newline=False)
                    else:
                        log_write(f"{NaN_final - NaN_inicial:,} erros na conversão (assumidos como missing).",
                                      addcont=False,newline=False)
                    log_write(f"[{row['Coluna']}] renomeada para {row['Coluna']+'('+row['Rename']+')'}.",
                            addcont=False,newline=False)
                    df.rename({row['Coluna']:row['Coluna']+'('+row['Rename']+')'}, axis=1, inplace=True)
                else:
                    log_write(f"*ERRO* convertendo [{row['Coluna']}] de "+\
                          f"[{row['Tipo']}] para [{row['Custom']}] ({df[row['Coluna']].dtype})",
                        addcont=False,newline=False)
                        
            elif row['CustomType'] == 'datetime64[ns]':  ####### DATETIME
                global sampleD
                try:    
                    sampleD = 50 
                    dfc = df.sample(sampleD)
                except: 
                    sampleD = df.shape[0]
                    dfc = df.sample(sampleD)
                best,taxa = best_format(dfc,row['Coluna'])
                log_write(f'melhor formato "{best}" com {str(100-taxa)}% de erro de conversão', addcont=False,newline=False)    
            
            
                NaN_inicial =   df[row['Coluna']].isnull().sum()
                df[row['Coluna']] = pd.to_datetime(df[row['Coluna']],format=best, errors='coerce')
                df[row['Coluna']] = df[row['Coluna']].apply(lambda x: None if pd.isna(x) else x)
                NaN_final =   df[row['Coluna']].isnull().sum()
                if df[row['Coluna']].dtype == 'datetime64[ns]':
                    if NaN_inicial == NaN_final:
                        log_write(f"100% convertido sem erros",
                                    addcont=False,newline=False)
                    else:
                        log_write(f"{NaN_final - NaN_inicial:,} erros na conversão (assumidos como missing).",
                                      addcont=False,newline=False)
                    log_write(f"[{row['Coluna']}] renomeada para {row['Coluna']+'('+row['Rename']+')'}.",
                            addcont=False,newline=False)
                    df.rename({row['Coluna']:row['Coluna']+'('+row['Rename']+')'}, axis=1, inplace=True)
                else:
                    log_write(f"*ERRO* convertendo [{row['Coluna']}] de "+\
                          f"[{row['Tipo']}] para [{row['Custom']}] ({df[row['Coluna']].dtype})",
                        addcont=False,newline=False)
            else:
                log_write('Tipo não identificado'+row['Coluna'],
                        addcont=True,newline=False)
    return(df)

def validate_format(f, s):
    lenF = len(f) if 'y' in f else len(f)+2
    try:
        tmp = datetime.strptime(str(s)[:lenF], f).date()
    except Exception as e:
        return(0)
    sep = '-' if '-' in f else '/' if '/' in f else ''
    anoL = '2' if 'y' in f else '4'
    ordem = f.replace(sep,'').replace('%','')
    import re
    d1,d2,d3 = [c for c in ordem.replace('m','2').replace('d','2').replace('y',anoL).replace('Y',anoL)]
    string = r'(\d{'+d1+'})'+sep+'(\d{'+d2+'})'+sep+'(\d{'+d3+'})'
    try:
        result = re.findall(string, str(s))
        if len(result) == 0: 
            valid = 0
        else:
            ano = int(result[0][ordem.find('y')])
            mes = int(result[0][ordem.find('m')])
            dia = int(result[0][ordem.find('d')])
            valid = 1 if (mes <=12 and dia <=31) else 0 
    except:
        valid = False
    return(valid)

def best_format(dfc,c):
    formats = [ '%Y-%m-%d', '%Y%m%d'  , '%m/%d/%Y', '%m-%d-%Y', 
                '%d/%m/%Y', '%d-%m-%Y', '%y-%m-%d', '%y%m%d'  , 
                '%m/%d/%y', '%m-%d-%y', '%d/%m/%y', '%d-%m-%y']
    
    if   'int'    in str(dfc[c].dtype).lower():
        dfc[c] = dfc[c].astype(object)
    elif 'float'    in str(df[c].dtype).lower():
        dfc[c] = dfc[c].astype(object)
        dfc[c] = dfc[c].apply(lambda x: str(x).replace('.0',''))
    best = ''; bestN = 0
    d = dfc[~dfc[c].isnull()][c].astype(object).rename('c').to_frame()
    tot = d.shape[0]
    for form in formats:
        check =  d['c'].apply(lambda s: validate_format(form, s) ).sum()
        sample =  d['c'].unique()[:5]
        if check > bestN:
            best = form; bestN = check
        taxa = int(round(check/tot*100,0))
        # print(f'teste de conversão datetime: sample={sampleD} col={c}, form={form}, erros={str(100-taxa)}%')    
    return(best,int(round(bestN/tot*100,0)))
        
        
def analysis_df(df,file):

    if True: #try:
    
        ## MORFOLOGIA
        reg_total = df.shape[0]
        log_write("### <b>Análise de Morfologia</b>", newline=True) 
        log_write(f'{reg_total:,} registros e {df.shape[1]}  colunas') 

        xext = '' ;  xqte = 0
        for x in df.columns:
            if 'object' in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna de texto: [{xext}]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas de texto: [{xext}]' ) 
              
        xqte_corr = 0
        xext = '' ;  xqte = 0
        for x in df.columns:
            if 'int' in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna numérica (inteiro): [{xext}]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas numéricas (inteiro): [{xext}]' ) 
        xqte_corr += xqte
    
        xext = '' ;  xqte = 0
        for x in df.columns:
            if 'float' in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna numérica (decimal): [{xext}]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas numéricas (decimal): [{xext}]' ) 
        xqte_corr += xqte

        xext = '' ;  xqte = 0
        for x in df.columns:
            if 'datetime' in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna datetime: [{xext}]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas datetime: [{xext}]' ) 
        xqte_corr += xqte

        xext = '' ;  xqte = 0
        for x in df.columns:
            if not 'object'    in str(df[x].dtype).lower() and\
               not 'datetime'  in str(df[x].dtype).lower() and\
               not 'int'       in str(df[x].dtype).lower() and\
               not 'float'     in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna de outro tipos: [ {xext} ]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas de outros tipos: [ {xext} ]' ) 
        
        dtp = []
        for c in df.columns:
            dtp.append(str(df[c].dtype))
        dtp = ';'.join(set(dtp))
        log_write(f'dtypes detalhados: {dtp}.' ) 
        
        ## CAMPOS TEXTO
        log_write("### Análise das colunas tipo <b>TEXTO</b>", newline=True) 
        for x in df.columns:
            if df[x].dtype == np.object:
                xext = xext + sep(xqte) +x  ; xqte += 1 
                log_write(str(xqte)+") "+ x + " ["+x.upper()+"]",newline=True) 
                ctmp = df[x]
                ctmp_counts = ctmp.value_counts()
                ctmp_total = reg_total
                nulos = ctmp.isna().sum() 
                ctmp = ctmp.dropna().reset_index(drop=True)  #CHECK OTHERS
                validos = ctmp_total-nulos
                
                nodups = ctmp.drop_duplicates(keep='first') 
                ctmp_final = nodups.shape[0]
                dups       = ctmp_total-nulos-ctmp_final 

                
                log_write(f"{'registros:  ':<15}{ctmp_total :>10,}", addcont=False,newline=True) 
                log_write(f"{'missing:    ':<15}{nulos      :>10,}", addcont=False) 
                log_write(f"{'válidos:    ':<15}{validos    :>10,}", addcont=False) 
                log_write(f"{'duplicados: ':<15}{dups       :>10,}", addcont=False) 
                log_write(f"{'categorias: ':<15}{ctmp_final :>10,}", addcont=False) 
                if (ctmp_total-ctmp_final) == 0:
                    log_write(f"categorias = registros, zero duplicados", addcont=False,newline=True)  
                else:
                    log_write("[       f.abs] [f.rel%] [f.acc%] categorias (max="+'{:n})'.format(max_freq), addcont=False,newline=True) 
                    freq     = 0
                    freq_acc = 0
                    for key, value in ctmp_counts.iteritems():
                        key2show = str(key) if len(str(key))<= 35 else str(key)[:35]+'\\' 
                        if freq <= max_freq:
                            freq += 1
                            freq_acc = freq_acc + (value/ctmp_total)
                            log_write(
                                    "["    +'{:>12,.0f}'.format(value)+
                                    "] ["  +'{:>5,.1f}'.format(value/ctmp_total*100)+
                                    "%] [" +'{:>5,.1f}'.format(freq_acc*100) +"%] "  
                                           +key2show, addcont=False)
                                             
                base_dup = pd.DataFrame(
                           df[~df[x].isnull()][x], columns=[x])
                sampleN1 = sampleN if base_dup.shape[0] > sampleN else base_dup.shape[0]
                ctmpS = base_dup.sample(sampleN1)
                log_write(f"Amostra aleatória dos dados (max={sampleN1:,}):", addcont=False, newline=True) 
                log_write(f"[{']['.join([str(c) for c in ctmpS[x].unique()])}]", addcont=False) 
                                             
                ctmpD = pd.DataFrame(df[~df[x].isnull()][x], columns=[x])
                if not dups == 0:
                    dupsTMP = pd.concat(g for _, g in ctmpD.groupby(x) if len(g) > 1)
                    dupsTMP = dupsTMP.groupby(x).size().reset_index()
                    dupsTMP.sort_values(by=[0], ascending=False, inplace = True)
                    dupsTMP.reset_index(drop=True)
                    cont = 0
                    dupsTX = '['
                    for index, row in dupsTMP.iterrows():
                        dupsTX += f'{str(row[x]).strip()}({row[0]:,})]['
                        cont += 1
                        if cont >= max_dups: break
                    dupsTX = dupsTX.strip()[:-1]
                    log_write(f"Duplicações ({cont:,} exemplos):", addcont=False, newline=True) 
                    log_write(f"{dupsTX}", addcont=False) 


        ## CAMPOS NUMÉRICOS (INTEIROS e DECIMAIS)
        log_write("### Análise das colunas <b>NUMÉRICAS</b> (INTEIROS E DECIMAIS)",newline=True) 
        for x in df.columns:
            #if df[x].dtype == np.int64 or df[x].dtype == np.float64:
            if 'int'   in  str(df[x].dtype) or\
               'float' in  str(df[x].dtype):
                xqte += 1 
                tipo = '[INTEIRO]' if df[x].dtype == np.int64 else '[DECIMAL]'
                log_write(str(xqte)+") "+ x + " ["+x.upper()+f"] {tipo}",newline=True) 
    
                if df[x].sum() == 0:   
                    log_write("  <b>Todos os valores zerados</b>") 
                else:
                        
                    ctmp = df[x]
                    nulos = ctmp.isna().sum() 
                    ctmpZ = ctmp[ctmp != 0]
                    ctmpZ = ctmpZ.dropna()
                    ctmpZEXC = ctmp[ctmp == 0]
                    zerados = ctmpZEXC.shape[0]
                    z = True if zerados == 0 else False
                    log_write(f"{'registros:':<18}{reg_total :>10,}", addcont=False,newline=True) 
                    log_write(f"{'missing:'  :<18}{nulos :>10,}", addcont=False) 
                    log_write(f"{'válidos:'  :<18}{reg_total-nulos :>10,}", addcont=False) 
                    log_write(f"{'zerados:'  :<18}{zerados :>10,}", addcont=False) 

                    txt = f'{"[válidos]":>35}{"  [válidos exc. zero]" if not z else "":>20}'.rstrip()
                    log_write(txt, addcont=False,newline=True) 
                                         
                    txt  =  'registros:'.ljust(18)
                    txt +=  ' {:>13,}   '.format(reg_total-nulos)
                    txt +=  ' {:>17,}   '.format(ctmpZ.shape[0]) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    txt  =  'soma:'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.sum() ,2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.sum(),2)) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    txt  =  'média:'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[1],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[1],2)) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    txt  =  'desvio:'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[2],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[2],2)) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    txt  =  'médiana (Q2):'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.median(),2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.median(),2)) if not z else ''
                    
                    log_write(txt, addcont=False) 
                    txt  =  'mínimo:'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[3],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[3],2)) if not z else ''
                    log_write(txt, addcont=False) 
                   
                    txt  =  'máximo:'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[7],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[7],2)) if not z else ''
                    log_write(txt, addcont=False) 
 
                    txt  =  'amplitude:'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[7]-ctmp.describe()[3],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[7]-ctmpZ.describe()[3],2)) if not z else ''
                    log_write(txt, addcont=False) 
 
                    txt  =  '25% (Q1):'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[4],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[4],2)) if not z else ''
                    log_write(txt, addcont=False) 

                    txt  =  '50% (Q2):'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[5],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[5],2)) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    txt  =  '75% (Q3):'.ljust(18)
                    txt +=  ' {:>16,.2f}'.format(round(ctmp.describe()[6],2))
                    txt +=  ' {:>20,.2f}'.format(round(ctmpZ.describe()[6],2)) if not z else ''
                    log_write(txt, addcont=False) 
                    ############################### QTE RECORDS
                    txt  =  'registros<Q1:'.ljust(18)
                    txt +=  ' {:>13,}'.format((ctmp < ctmp.describe()[4]).sum())
                    txt +=  ' {:>20,}'.format((ctmp < ctmpZ.describe()[4]).sum()) if not z else ''
                    log_write(txt, addcont=False) 
                    txt  =  'registros<Q2:'.ljust(18)
                    txt +=  ' {:>13,}'.format((ctmp < ctmp.describe()[5]).sum())
                    txt +=  ' {:>20,}'.format((ctmp < ctmpZ.describe()[5]).sum()) if not z else ''
                    log_write(txt, addcont=False) 
                    txt  =  'registros>Q2:'.ljust(18)
                    txt +=  ' {:>13,}'.format((ctmp > ctmp.describe()[5]).sum())
                    txt +=  ' {:>20,}'.format((ctmp > ctmpZ.describe()[5]).sum()) if not z else ''
                    log_write(txt, addcont=False) 
                    txt  =  'registros>Q3:'.ljust(18)
                    txt +=  ' {:>13,}'.format((ctmp > ctmp.describe()[6]).sum())
                    txt +=  ' {:>20,}'.format((ctmp > ctmpZ.describe()[6]).sum()) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    base_dup = pd.DataFrame(
                           df[~df[x].isnull()][x], columns=[x])
                    sampleN1 = sampleN if base_dup.shape[0] > sampleN else base_dup.shape[0]
                    ctmpS = base_dup.sample(sampleN1)
                    ctmpS = pd.DataFrame(df[~df[x].isnull()][x], columns=[x]).sample(sampleN1)
                    log_write(f"Amostra aleatória dos dados (max={sampleN1:,}):", addcont=False, newline=True) 
                    log_write(f"[{']['.join([f'{c:,}' for c in ctmpS[x].unique()])}]", addcont=False) 
       
                    if hist:
                        grf = df[x].dropna()    
                        grfINFO = grf.describe()
                        max_height = (np.histogram(grf, bins=hist_bins)[0].max())
                        max_lenght = (grfINFO[7]- grfINFO[3])
                        sns.set_style("whitegrid")
                        plt.figure(figsize=(11.7, 8.27))
                        plt.xlim(grfINFO[3].round(0), grfINFO[7].round(0))
                        plt.ylim(0, max_height*1.1)
                        
                        plt.text(0.03*max_lenght,-0.09*max_height,
                                 FC_Auto_Analyser_Version+'\n'+'https://www.fabianocastello.com.br/fca2',
                                 fontsize=10, ha='left')
                        
                        sns_plot = sns.distplot(grf, bins=hist_bins, kde=False, color="purple", 
                                     axlabel=False, rug=True)
                        sns_plot = sns_plot.set_title("histograma de ["+grf.name+"]", {'size': '18'})
                        img_file = file+'_HIST_'+grf.name+'.png'
                        fig = sns_plot.get_figure().savefig(dataout+"/"+img_file)  #pdf: trocar sufixo
                        plt.close()
                        log_write('', addcont=False,newline=True)  

                        image = Image.open(dataout+"/"+img_file)
                        st.image(image, caption=img_file) 
						
                    if boxp:
                        grf = df[x].dropna()    
                        grfINFO = grf.describe()
                        max_height = (np.histogram(grf, bins=hist_bins)[0].max())
                        max_lenght = (grfINFO[7]- grfINFO[3])
                        sns.set_style("whitegrid")

                        plt.figure(figsize=(11.7, 8.27))
                        plt.xlim(grfINFO[3].round(0), grfINFO[7].round(0))
                        plt.ylim(0, max_height*1.1)
                        
                        plt.text(0.03*max_lenght,-0.09*max_height,
                                 FC_Auto_Analyser_Version+'\n'+'https://www.fabianocastello.com.br/fca2',
                                 fontsize=10, ha='left')
                        
                        sns_plot = sns.boxplot(x=grf)
                        sns_plot = sns_plot.set_title("Boxplot de ["+grf.name+"]", {'size': '18'})
                        img_file = file+'_BoxPlot_'+grf.name+'.png'
                        fig = sns_plot.get_figure().savefig(dataout+"/"+img_file)  
                        plt.close()
                        log_write('', addcont=False,newline=True)  

                        image = Image.open(dataout+"/"+img_file)
                        st.image(image, caption=img_file) 

        ## CAMPOS DATETIME #XPTO
        log_write("### Análise das colunas tipo <b>DATA</b> (em beta!)", newline=True) 
        for x in df.columns:
            if str(df[x].dtype) == 'datetime64[ns]':
                xext = xext + sep(xqte) +x  ; xqte += 1 
                log_write(str(xqte)+") "+ x + " ["+x.upper()+"]",newline=True) 
                df[x] = df[x].apply(lambda x: x.date())
                ctmp = df[x]
                ctmp_counts = ctmp.value_counts()
                ctmp_total = reg_total
                nulos = ctmp.isna().sum() 
                ctmp = ctmp.dropna().reset_index(drop=True)  #CHECK OTHERS
                validos = ctmp_total-nulos
                ctmp_final = ctmp.shape[0]
                nodups = ctmp.drop_duplicates(keep='first') 
                ctmp_final = nodups.shape[0]
                dups       = ctmp_total-nulos-ctmp_final 
                
                log_write(f"{'registros:  ':<15}{ctmp_total :>10,}", addcont=False,newline=True) 
                log_write(f"{'missing:    ':<15}{nulos      :>10,}", addcont=False) 
                log_write(f"{'válidos:    ':<15}{validos    :>10,}", addcont=False) 
                log_write(f"{'duplicados: ':<15}{dups       :>10,}", addcont=False) 
                log_write(f"{'categorias: ':<15}{ctmp_final :>10,}", addcont=False) 
                if (ctmp_total-ctmp_final) == 0:
                    log_write(f"categorias = registros, zero duplicados", addcont=False,newline=True)  
                else:
                    log_write("[       f.abs] [f.rel%] [f.acc%] categorias (max="+'{:n})'.format(max_freq), addcont=False,newline=True) 
                    freq     = 0
                    freq_acc = 0
                    for key, value in ctmp_counts.iteritems():
                        key = key.strftime('%Y-%m-%d')
                        key2show = str(key) if len(str(key))<= 35 else str(key)[:35]+'\\' 
                        if freq <= max_freq:
                            freq += 1
                            freq_acc = freq_acc + (value/ctmp_total)
                            log_write(
                                    "["    +'{:>12,.0f}'.format(value)+
                                    "] ["  +'{:>5,.1f}'.format(value/ctmp_total*100)+
                                    "%] [" +'{:>5,.1f}'.format(freq_acc*100) +"%] "  
                                           +key2show, addcont=False)
                                           

                    min_ = ctmp.min()
                    max_ = ctmp.max()
                    cal = pd.DataFrame({'c': pd.date_range(min_, max_)})\
                                       ['c'].apply(lambda x: x.date()).to_list()
                    ampl = len(cal)
                    mean = min_+timedelta(days=int(ampl))/2
                    filling  = len(list(set(cal) & set(ctmp)))
                    fillingP = 0 if ampl==0 else int(round(filling/ampl*100,0))

                    quartis = list(ctmp.astype('datetime64[ns]').quantile([.25, .5, .75]))
                    Q1,Q2,Q3 = quartis[0].date(),quartis[1].date(),quartis[2].date()

                    #filling meses
                    calM = pd.DataFrame({'c': pd.period_range(min_, max_, freq="M")})
                    calM['Year']    = calM['c'].apply(lambda x: str(x.year))
                    calM['Period']  = calM['c'].apply(lambda x: f'{x.year}-{str(x.month).zfill(2)}')
                    cal_meses  = sorted(set(calM['Period'].to_list()))
                    ctmp_meses = sorted(set([f'{x.year}-{str(x.month).zfill(2)}' for x in ctmp]))
                    amplM      = len(cal_meses)
                    fillingM   = len(set(cal_meses) & set(ctmp_meses))
                    fillingMP  = 0 if ampl==0 else int(round(fillingM/amplM*100,0))


                    #filling Years
                    cal_years  = sorted(set(calM['Year'].to_list()))
                    ctmp_years = sorted(set([f'{x.year}' for x in ctmp]))
                    amplY      = len(cal_years)
                    fillingY   = len(set(cal_years) & set(ctmp_years))
                    fillingYP  = 0 if ampl==0 else int(round(fillingY/amplY*100,0))
                    
                    log_write(f"Stats (Ano-Mês-Dia)", addcont=False,newline=True)                     
                    log_write( 'mais antiga:'.ljust(18) +f' {min_}'.rjust(13), addcont=False) 
                    log_write( 'mais recente:'.ljust(18)+f' {max_}'.rjust(13), addcont=False) 
                    log_write( 'data média:'.ljust(18)+f' {mean}'.rjust(13), addcont=False) 
                    
                    log_write( 'amplitude:'.ljust(18)+f' {ampl:,}'.rjust(13)+\
                             ( 'dias' if ampl>1 else 'dia').rjust(7), addcont=False) 
                    log_write( 'filling (dias):'.ljust(18)+f' {filling:,}/{ampl:,}'.rjust(13)+\
                              f'{fillingP}%'.rjust(7), addcont=False) 
                    log_write( 'filling (meses):'.ljust(18)+f' {fillingM:,}/{amplM:,}'.rjust(13)+\
                              f'{fillingMP}%'.rjust(7), addcont=False) 
                    log_write( 'filling (anos):'.ljust(18)+f' {fillingY:,}/{amplY:,}'.rjust(13)+\
                              f'{fillingYP}%'.rjust(7), addcont=False) 


                    txt  = f"""{'Q1;~registros:'.ljust(18)}{str(Q1).rjust(13)}"""
                    txt += f"""{'{:>10,}'.format((ctmp < Q1).sum())}|{'{:<10,}'.format((ctmp > Q1).sum())}"""
                    log_write(txt, addcont=False)
                    txt  = f"""{'Q2;~registros:'.ljust(18)}{str(Q2).rjust(13)}"""
                    txt += f"""{'{:>10,}'.format((ctmp < Q2).sum())}|{'{:<10,}'.format((ctmp > Q2).sum())}"""
                    log_write(txt, addcont=False)
                    txt  = f"""{'Q3;~registros:'.ljust(18)}{str(Q3).rjust(13)}"""
                    txt += f"""{'{:>10,}'.format((ctmp < Q3).sum())}|{'{:<10,}'.format((ctmp > Q3).sum())}"""
                    log_write(txt, addcont=False)

                    log_write(f"Distribuição visual (D=dados no período)", addcont=False,newline=True)                     
                    meses = list(enumerate(['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                                            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'], start=1))
                    l = ' '*5 #linha para formatar
                    for n,m in meses:
                        l += m.rjust(4)
                    l += 'Regs'.rjust(10)
                    log_write(f"{l}", addcont=False) 
                    for ano in cal_years:
                        l = f'{ano}'.ljust(5)
                        for m in meses:
                            periodo = f'{ano}-{str(m[0]).zfill(2)}'
                            if periodo in cal_meses:
                                l += 'D '.rjust(4) if periodo in ctmp_meses else '- '.rjust(4)
                            else:
                                l += ''.rjust(4)
                        recs = (pd.to_datetime(ctmp).dt.year == int(ano)).sum()
                        l += f'{recs:,}'.rjust(10)+ ' ' + barra_ast(recs/len(ctmp),10)
                        log_write(f"{l}", addcont=False) 

                    base_dup = pd.DataFrame(
                               df[~df[x].isnull()][x], columns=[x])

                    sampleN1 = sampleN if base_dup.shape[0] > sampleN else base_dup.shape[0]
                    ctmpS = base_dup.sample(sampleN1)
                    log_write(f"Amostra aleatória dos dados (max={sampleN1:,}):", addcont=False, newline=True) 
                    log_write(f"[{']['.join([c.strftime('%Y-%m-%d') for c in ctmpS[x].unique()])}]", addcont=False) 
                                                 
                    ctmpD = pd.DataFrame(df[~df[x].isnull()][x], columns=[x])
                    if not dups == 0:
                        dupsTMP = pd.concat(g for _, g in ctmpD.groupby(x) if len(g) > 1)
                        dupsTMP = dupsTMP.groupby(x).size().reset_index()
                        dupsTMP.sort_values(by=[0], ascending=False, inplace = True)
                        dupsTMP.reset_index(drop=True)
                        cont = 0
                        dupsTX = '['
                        for index, row in dupsTMP.iterrows():
                            dupsTX += f'{row[x].strftime("%Y-%m-%d").strip()}({row[0]:,})]['
                            cont += 1
                            if cont >= max_dups: break
                        dupsTX = dupsTX.strip()[:-1]
                        log_write(f"Duplicações ({cont:,} exemplos):", addcont=False, newline=True) 
                        log_write(f"{dupsTX}", addcont=False) 
						

                        

        ## CORRELAÇÃO ENTRE VARIÁVEIS NUMÉRICAS
        if mcorr:
            log_write("### Matriz de Correlação de Variáveis Numéricas",newline=True) 
            if not xqte_corr == 0:
                sns.set_style("whitegrid")
                plt.figure(figsize=(11.7, 8.27))
                plt.text(0.05, 2.2, FC_Auto_Analyser_Version+'\n'+'http://github.com/fabianocastello/fca2web',
                         fontsize=10, ha='left')
                sns_corr = sns.heatmap(df.corr())
                sns_corr = sns_corr.set_title("Matriz de Correlação de Variáveis Numéricas", {'size': '18'})
                sns_corr.get_figure().savefig(dataout+"/"+file+' CORR.png')
                plt.close()
                log_write('', addcont=False,newline=True)  
                image = Image.open(dataout+"/"+file+' CORR.png')
                img_file = file+'_CORR.png'
                st.image(image, caption=img_file)                        
            else:
                log_write('Não foram identificadas variáveis numéricas')
       
        running_time = str(int(round( (time.time() - start_time)/60,0)) )+'min'
       
        log_write(f"Running time: {running_time}", newline=True,addcont=True) 
        
        #post statísticas
        if not file == 'titanic.pkl':
            ret = post_stat_fca2(file, sizeKB, parâmetros,
                                 running_time, f" dtypes = {dtp}".strip())
            if '200' in str(ret):
                log_write(f"Estatística postada: nome={file}, size={sizeKB:,}Kb, "+\
                          f"dtypes = {dtp}, param={parâmetros}"+\
                          f", Elap={running_time}, remarks={remarks}",
                            newline=False,addcont=True) 
        log_write("Análise finalizada de "+file, newline=False) 
        
        dump_output(output)
        with open('./!data.out/Report.txt', 'r', encoding = 'utf-8') as f:
            txt = f.read()
        download_filename = f'{datetime.today().strftime("%Y-%m-%d_%Hh%Mm")}_FCA2_{file}.txt'
        csv = txt
        b64 = base64.b64encode(txt.encode()).decode()  # some strings <-> bytes conversions necessary here
        #href = f'<a href="data:file/txt;base64,{b64}" download="myfilename.txt">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
        href = f'<a href="data:file/txt;base64,{b64}" download="{download_filename}"><br>Clique para baixar {download_filename}<br></a>'
        st.markdown(href, unsafe_allow_html=True)

        
        

        st.success('Análise finalizada')
            
        return(0)

    # except Exception as erro:
       # log_write("\n\n Erro Geral: "+str(erro) + "\n\n") 
       # return(-2)
       
def tool_tips(widget):
    if    widget == 'max_freq':
        return("""Nas colunas de texto são apresentadas as principais categorias, com suas frequencias e as frequencias acumuladas. Este parâmetro define o número máximos de categorias apresentadas.""")
    elif widget == 'hist_bins':
        return("""Para campos numéricos há opção de apresentar histogramas. Este parâmetro define o número de separações do histograma.""")
    elif widget == 'max_dups':
        return("""Nas colunas de texto são identificadas quantas duplicações existem na coluna. Este parâmetro define quantos exemplos duplicados são apresentados (em ordem decrescente de quantidade de duplicações. O número entre parênteses que aparece no resulta é a quantidade de itens duplicados.""")
    elif widget == 'hist':
        return("""Mostrar (ou suprimir) o histograma de colunas numéricas.""")
    elif widget == 'max_dups':
        return("""Mostrar (ou suprimir) o boxplot de colunas numéricas.""")
    elif widget == 'mcorr':
        return("""Mostrar (ou suprimir) a correlação das colunas numéricas.""")
    elif widget == 'noheader':
        return("""Existem arquivos que não tem o cabeçalho com o nome das colunas na primeira linha e, nestes casos, o FCA2 assume automaticamente a primeira linha como o nome das colunas. Marque esta opção para informar que o arquivo não tem cabeçalho e o FCA2 nomeará as colunas como 1,2,3, etc)""")
    elif widget == 'filecst':
        return("""O Python infere o tipo de dado da coluna baseado na análise dos dados da coluna. Existem situações, como por exemplo códigos (ex.: códigos de produto 1, 2, 3) que são variáveis categóricas mas que são interpretadas como numéricas. Para ter uma análise correta, marque esta opção e mude conforme sua conveniência o tipo da coluna para texto ou numérica (numeros inteiros ou decimais).""")
    elif widget == 'sep_csv':
        return("""FCA2 identifica automaticamente se o separador em arquivos CSV é "," ou ";". Há casos, no entanto, onde o separador é outro caracter, como por exemplo "|". Informe o caracter aqui para forçar a separação.""")
    elif widget == 'dec_csv':
        return("""FCA2 utiliza como base para os números decimais o ponto, mas existem casos onde o decimal é uma vírgula. Note que se o separador e o parâmetro de decimal forem iguais o FCA2 realizará a análise, mas dará um alerta para verificar.""")
    elif widget == 'uploaded_file':
        return("""Arraste o arquivo para ser analisado ou selecione a partir botão "browser". Veja as observações com considerações sobre o tipo dos arquivos. A opção de multiplos arquivos foi descontinuada para implantação da customização dos tipos de colunas.""")
    elif widget == 'titanic':
        return("""A base titanic é muito utilizada como exemplo porque é um arquivo pequeno, tem colunas de vários tipos, casos de duplicações e dados ausentes.""")

    return('no tool tip!')

    # global msg_count, max_freq, hist_bins, max_dups
    # global hist, boxp, mcorr, noheader, sep_csv, filecst, dec_csv, sampleN
    # global UserAgents, runningOn, parâmetros, remarks, sizeKB

def dump_output(output):
    with open('./!data.out/Report.txt', 'w', encoding = 'utf-8') as fout:
        col = 70
        fout.write(f"\n{FC_Auto_Analyser_Version}\nhttps://www.fabianocastello.com.br/fca2\n")
        fout.write(f"Análise exploratória de dados gratuita,\nsegura e colaborativa. Compartilhe!\n{'-'*col}\n\n")
        for index, row in output.iterrows():
            if row['NewLine']: fout.write('\n')
            first_line = True
            x = row['Content'].replace('<b>','').replace('</b>','')
            chunks, chunk_size = len(x), col
            line = ' '*4 if str(row['Row']) == 'nan' else\
                   ' '*4 if str(row['Row']) == 'None' else row['Row']
            for i in range(0, chunks, chunk_size):
                chunk = x[i:i+chunk_size]+('' if i+col>chunks else '\\')
                fout.write(f"""{line if first_line else ' '*4} {chunk}\n""")
                first_line = False
    return
    
def barra_ast(p,s, char=chr(42)):
    """ p = percentual; s = size em caracteres; char=caracter (default asterisco) """
    if p<=1:
        barra = (char*int(round(p*s,0)))
    else:
        barra=char*int(s)
    return(barra)



run()

