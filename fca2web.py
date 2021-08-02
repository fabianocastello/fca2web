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
    global hist, boxp, mcorr, noheader, sep_csv, filecst, dec_csv, sample
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

    max_freq  = st.sidebar.slider('Numero de categorias máximas nas colunas de texto:', 1, 20, max_freq,
    help=tool_tips('max_freq'))
    hist_bins = st.sidebar.slider('Qte de bins no histograma:', 1, 20, hist_bins,
    help=tool_tips('hist_bins'))
    max_dups = st.sidebar.slider('Qte de exemplos de duplicados:', 1, 10, max_dups,
    help=tool_tips('max_dups'))
    sample = st.sidebar.slider('Qte de itens para amostragem:', 1, 10, sample,
    help=tool_tips('sample'))
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
 
    #print(max_freq, hist_bins, max_dups, hist)
 
 
    try:    del uploaded_files
    except: pass
        
        
    titanic =  st.checkbox('Marque para ver uma demonstração (titanic.csv)', value=False,
    help=tool_tips('titanic'))
        
    uploaded_file = st.file_uploader('Informe o arquivo para análise. Acesse a barra lateral (">" à esquerda) para opções.', type =['csv','xls','xlsx'],
                    accept_multiple_files=False, help=tool_tips('uploaded_file'))
    # UploadedFile(id=8, name='xxxxjr5mqz0i.csv', type='application/vnd.ms-excel', size=1211)
    
    # ago/21 - restrito para um arquivo apenas
    if uploaded_file is not None or titanic:
        if titanic: 
            with open('./titanic.csv', 'rb') as base:
                content = base.read()
                with open(os.path.join(datain,"titanic.csv"),"wb") as f:
                    f.write(content)
            hist=True
            boxp = True
            mcorr = True
        else:
            with open(os.path.join(datain,uploaded_file.name),"wb") as f:
                f.write(uploaded_file.getbuffer())
        files = os.listdir(datain)
        if len(files) != 0:
            dfx = [i for i in files if ('XLSX' in i[-4:].upper()) or ('XLS' in i[-3:].upper())]
            dfc = [i for i in files if 'CSV' in i[-3:].upper()] 
            filesToWorkOn = dfx + dfc
            msg_count  = 0
            
            del dfx, dfc, files
            filesToWorkOn = sorted(filesToWorkOn) 
            for name in filesToWorkOn:
                st.markdown(f'''<body><p style="font-size:20px;margin-bottom: -5px;">
                                Analisando <b>{name}</b></p></body>''', unsafe_allow_html=True)
                                
                parâmetros = f'max_freq={max_freq}; hist_bins={hist_bins}; max_dups={max_dups};'+\
                             f'hist={hist}; boxp={boxp}; mcorr={mcorr}; noheader={noheader}; '
                remarks = ''
                sizeKB     = int(round(os.stat(datain+"/"+name).st_size/1024,0))
                                
                analysis(name)
                

            st.markdown(f'''<body><p style="font-size:15px;margin-bottom: -5px;"><br><br><br>
                                <u><i>✅ Para analisar outro arquivo pressione F5</i></u></p></body>''', unsafe_allow_html=True)
    
    st.markdown('''
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
    
    <p style="font-size:20px;margin-bottom: -5px;"><b><i>What's New</i></b></p>
    <p style="font-size:16px;margin-bottom: -5px<span style="font-size:10px ;margin-bottom: -5px;"> 
    <ul style="margin-bottom: -5px;">
      <li>mudança do licenciamento para CC BY 4.0 (jul/21).</li>
      <li>boxplot, customização de colunas, arquivo exemplo e amostragem (ago/21).</li>
    </ul></span><span style="font-size:16px ;line-height: 25px"><br>
   
    <p style="font-size:20px;margin-bottom: -5px;"><b><i>Issues</i> conhecidos</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    Neste momento o único "issue" conhecido é a questão do alinhamento dos resultados no browser, por um problema de fontes de HTML nos navegadores, particulamente referente aos "white spaces". <i>Se vc identificar um problema faça o reporte em  <a target="_blank" href ="http://www.github.com/fabianocastello/fca2web/issues">www.github.com/fabianocastello/fca2web/issues</a></i></p><br>
    
    <p style="font-size:20px;margin-bottom: -5px;"><b>O que está no <i>pipeline</i></b></p>
    <p style="font-size:16px;margin-bottom: -5px<span style="font-size:10px ;margin-bottom: -5px;"> 
    <ul style="margin-bottom: -5px;">
      <li>gerar um arquivo em PDF com a análise consolidada.</li>
      <li>melhorar a formatação de saída dos resultados (em linha com o problema de formatação das "white spaces").</li>
    </ul></span><span style="font-size:16px ;line-height: 25px"><br>
    
    <p style="font-size:20px;margin-bottom: -5px;"><b>Sobre LGPD, GRPR e confidencialidade de dados</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    FCA2 cria containers a partir dos arquivos carregados para tratamento e destrói a informação assim que o processamento é realizado. Nenhuma informação é retida ou enviada para fora do site (exceto tipo do arquivo, tamanho, tempo de processamento e parâmetros, para efeito de gerar estatísticas). Todos os arquivos tempororários geradaos são apagados.</p><br>

    <p style="font-size:20px;margin-bottom: -5px;"><b>Contribuições</b></p>
    <p style="font-size:16px;margin-bottom: -5px;">
    FCA2 é mantido pelo autor com contribuições da comunidade.<br>Thanks: Marcus Pinto, João Victor Mulle, Mateus Ricci, Vivian Sato. <i>Para contribuir com o projeto faça um "fork" a partir do repositório <a target="_blank" href ="http://www.github.com/fabianocastello/fca2web">www.github.com/fabianocastello/fca2web</a></i>.</p><br>
    
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
sample    =  5 #qte de exemplos da coluna 

FC_Auto_Analyser_Version = 'fca2web beta 0.92 (2021AGO01) '

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
    ident = '&nbsp;'*5
    if newline:
        st.markdown(f'''<body><p style="font-size:14px;margin-bottom: -5px;
                    font-family: monospace;"><br></p></body>''', unsafe_allow_html=True)
    msg = msg.replace('  ',' ')
    cut = 100
    if addcont:
        full_msg  = (f'{msgC()} {msg}').strip()
    else:
        full_msg  = (f'{ident+msg}').strip()
    first_msg = full_msg[:cut].replace(' ', '&nbsp;').replace('\n', '<br>')
    rest_msg  = full_msg[cut:].replace(' ', '&nbsp;').replace('\n', '<br>')
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
        if 'csv' in file:
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
                    df = pd.read_csv(datain+"/"+file, encoding ='utf-8', engine='python', sep = separador, header=None, decimal=decimalcsv)
                    for c in df.columns:
                        df.rename({c:f'Coluna{c}'}, axis=1, inplace=True)
                       
                else:
                    df = pd.read_csv(datain+"/"+file, encoding ='utf-8', engine='python',
                                        sep = separador, decimal=decimalcsv)
            except Exception as erro:
                log_write("Erro "+str(erro))
                log_write("Abortando analise "+file+"\n")
                return(-1)
        elif 'xls'in file:
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
        else:
            log_write("Erro identificando xls/csv")
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

    global i
    with st.form("my_form"):
       st.write("Customização de colunas", help=tool_tips('form_custom'))
       for i in range(0,custom.shape[0]):
           col = custom['Coluna'].loc[i]
           exemplos = 'Exemplos: '+('; '.join(
                [str(c) for c in list(df[col].unique()[:3])])).strip()
           s = "custom"+str(i)+"=st.radio(f'Coluna {str(i+1)}: '+'["+custom['Coluna'].loc[i]+"] "+exemplos+\
               "', options=['Texto', 'Numérico(int)', 'Numérico(dec)'], "+\
               "index="+str(opt[custom['Custom'].loc[i]])+")"
           exec(s, globals())

       submitted = st.form_submit_button("Processar alterações")
       if not submitted:
           st.stop()
       else:
            for i in range(0, custom.shape[0]):
                s = "custom.at[i,'Custom'] = custom"+str(i)
                exec(s)
                # if custom['Tipo'].loc[i] != custom['Custom'].loc[i]:
                    # print(i,
                          # custom['Coluna'].loc[i],
                          # custom['Type'].loc[i], 
                          # custom['Tipo'].loc[i], 
                          # custom['Custom'].loc[i])
    
    log_write("### <b>Analisando e convertendo colunas</b>", newline=True) 
    changes = custom[custom.Tipo != custom.Custom].shape[0]    
    log_write(f'{changes} coluna(s) alterada(s)') 
    opt_rename = dict()
    opt_rename['Texto']         = 'Tx'
    opt_rename['Numérico(int)'] = 'Ni'
    opt_rename['Numérico(dec)'] = 'Nd'
    for index, row in custom.iterrows():
        custom.at[index,'Rename'] = opt_rename[row['Tipo']]+'>'+opt_rename[row['Custom']]

    for index, row in custom.iterrows():
        if    row['Custom'] == 'Texto':
               custom.at[index, 'CustomType'] = 'object'
        elif  row['Custom'] == 'Numérico(int)':
               custom.at[index, 'CustomType'] = 'int64'
        elif  row['Custom'] == 'Numérico(dec)':
               custom.at[index, 'CustomType'] = 'float64'
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

            elif row['CustomType'] == 'int64':
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
            else:
                log_write('Tipo não identificado'+row['Coluna'],
                        addcont=True,newline=False)
    return(df)
        
def analysis_df(df,file):
        
        ## MORFOLOGIA
        reg_total = df.shape[0]
        log_write("### <b>Análise de Morfologia</b>", newline=True) 
        log_write(f'{reg_total:,} registros e {df.shape[1]}  colunas') 

        xext = '' ;  xqte = 0
        for x in df.columns:
            if 'object' in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna de texto: [ {xext} ]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas de texto: [ {xext} ]' ) 
              
        xqte_corr = 0
        xext = '' ;  xqte = 0
        for x in df.columns:
            if 'int' in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna numérica (inteiro): [ {xext} ]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas numéricas (inteiro): [ {xext} ]' ) 
        xqte_corr += xqte
    
        xext = '' ;  xqte = 0
        for x in df.columns:
            if 'float' in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna numérica (decimal): [ {xext} ]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas numéricas (decimal): [ {xext} ]' ) 
        xqte_corr += xqte

        xext = '' ;  xqte = 0
        for x in df.columns:
            if not 'object'  in str(df[x].dtype).lower() and\
               not 'int'     in str(df[x].dtype).lower() and\
               not 'float'   in str(df[x].dtype).lower():
                xext = xext + sep(xqte) +x  ; xqte += 1 
        if xqte == 1: 
            log_write(f'1 coluna de outro tipos: [ {xext} ]' ) 
        elif xqte > 1: 
            log_write(f'{xqte} colunas de outros tipos: [ {xext} ]' ) 
        
        
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
                ctmp = ctmp.dropna()
                validos = ctmp_total-nulos
                
                
                log_write(f"{'registros:':<15}{ctmp_total   :>10,}", addcont=False) 
                log_write(f"{'missing:'  :<15}{nulos        :>10,}", addcont=False) 
                log_write(f"{'válidos:'  :<15}{validos      :>10,}", addcont=False) 
                
                ctmp.drop_duplicates(keep='first', inplace = True) 
                ctmp_final = ctmp.shape[0]
                dups       = ctmp_total-nulos-ctmp_final 
                
                log_write(f"{'duplicados:'  :<15}{dups :>10,}", addcont=False) 
                log_write(f"{'categorias:'  :<15}{ctmp_final :>10,}", addcont=False) 
                
                if (ctmp_total-ctmp_final) == 0:
                    log_write(f"categorias = registros, zero duplicados", addcont=False) 
                else:
                    log_write("Freqs  [f.abs] [ f.rel%] [f.acc%] categorias (max="+'{:n})'.format(max_freq), addcont=False)
                    freq     = 0
                    freq_acc = 0
                    for key, value in ctmp_counts.iteritems():
                        if freq <= max_freq:
                            freq += 1
                            freq_acc = freq_acc + (value/ctmp_total)
                            log_write("       ["+'{:>12,.0f}'.format(value)+
                                             "] [ " +'{:>5,.1f}'.format(value/ctmp_total*100) +"%] ["  
                                                    +'{:>5,.1f}'.format(freq_acc*100) +"%] "  
                                             +str(key), addcont=False)   
                                             
                ctmpS = pd.DataFrame(df[~df[x].isnull()][x], columns=[x]).sample(sample)
                log_write(f"Amostra aleatória dos dados ({sample:,} itens):", addcont=False, newline=True) 
                log_write(f"{'; '.join([str(c) for c in ctmpS[x].unique()])}", addcont=False) 
                                             
                ctmpD = pd.DataFrame(df[~df[x].isnull()][x], columns=[x])
                if not dups == 0:
                    dupsTMP = pd.concat(g for _, g in ctmpD.groupby(x) if len(g) > 1)
                    dupsTMP = dupsTMP.groupby(x).size().reset_index()
                    dupsTMP.sort_values(by=[0], ascending=False, inplace = True)
                    dupsTMP.reset_index(drop=True)
                    cont = 0
                    dupsTX = '['
                    for index, row in dupsTMP.iterrows():
                        dupsTX += f'{str(row[x]).strip()}({row[0]}), '
                        cont += 1
                        if cont >= max_dups: break
                    dupsTX = dupsTX.strip()[:-1]+']'
                    log_write(f"Duplicações ({cont:,} exemplos):", addcont=False, newline=True) 
                    log_write(f"{dupsTX}", addcont=False) 


        ## CAMPOS NUMÉRICOS (INTEIROS e DECIMAIS)
        log_write("### Análise das colunas <b>NUMÉRICAS</b> (INTEIROS E DECIMAIS)",newline=True) 
        for x in df.columns:
            if df[x].dtype == np.int64 or df[x].dtype == np.float64:
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
                    log_write(f"{'Registros:'  :<15}{reg_total :>10,}", addcont=False) 
                    log_write(f"{'Missing:'  :<15}{nulos :>10,}", addcont=False) 
                    log_write(f"{'Válidos:'  :<15}{reg_total-nulos :>10,}", addcont=False) 
                    log_write(f"{'Zerados:'  :<15}{zerados :>10,}", addcont=False) 


                    txt = f'{"[Válidos]":>46}{"[Válidos Exc. Zero]" if not z else "":>31}'
                    log_write(txt, addcont=False) 
                                         
                    txt = f'{"Registros:"  :<12}{reg_total-nulos:>30,}'+\
                          f'{ctmpZ.shape[0] if not z else "":>46}' 
                    log_write(txt, addcont=False) 
                                        
                    txt  = 'Soma: {:>30,}'.format(round(ctmp.sum() ,2))
                    txt +=       '{:>35,}'.format(round(ctmpZ.sum(),2)) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    txt  = 'Média: {:>30,}'.format(round(ctmp.describe()[1],2))
                    txt +=       '{:>35,}'.format(round(ctmpZ.describe()[1],2)) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    txt  = 'Desvio: {:>30,}'.format(round(ctmp.describe()[2],2))
                    txt +=       '{:>35,}'.format(round(ctmpZ.describe()[2],2)) if not z else ''
                    log_write(txt, addcont=False) 
                    
                    
                   
                    txt = f'{"Mínimo:"  :<12}{round(ctmp.describe()[3],2):>24,}'
                    txt +=       f'{round(ctmpZ.describe()[3],2):>40,}' if not z else "" 
                    log_write(txt, addcont=False)  
 
                   
                    txt = f'{"Máximo:"  :<12}{round(ctmp.describe()[7],2):>24,}'
                    txt +=       f'{round(ctmpZ.describe()[7],2):>40,}' if not z else ""
                    log_write(txt, addcont=False) 
 
                    txt = f'{"Amplitude:"  :<12}{round(ctmp.describe()[7]-ctmp.describe()[3],2):>24,}'
                    txt +=       f'{round(ctmpZ.describe()[7]-ctmpZ.describe()[6],2):>40,}' if not z else ""
                    log_write(txt, addcont=False) 
 
                    txt = f'{"25%:"  :<12}{round(ctmp.describe()[4],2):>24,}'
                    txt +=       f'{round(ctmpZ.describe()[4],2):>40,}' if not z else ""
                    log_write(txt, addcont=False) 
 
                    txt = f'{"Mediana:"  :<12}{round(ctmp.describe()[5],2):>24,}'
                    txt +=       f'{round(ctmpZ.describe()[5],2):>40,}' if not z else ""
                    log_write(txt, addcont=False) 
 
                    txt = f'{"75%:"  :<12}{round(ctmp.describe()[6],2):>24,}'
                    txt +=       f'{round(ctmpZ.describe()[6],2):>40,}' if not z else ""
                    log_write(txt, addcont=False) 
                    
                    ctmpS = pd.DataFrame(df[~df[x].isnull()][x], columns=[x]).sample(sample)
                    log_write(f"Amostra aleatória dos dados ({sample:,} itens):", addcont=False, newline=True) 
                    log_write(f"{'; '.join([str(c) for c in ctmpS[x].unique()])}", addcont=False) 
       
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
                                 FC_Auto_Analyser_Version+'\n'+'http://github.com/fabianocastello/fca2web',
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
                                 FC_Auto_Analyser_Version+'\n'+'http://github.com/fabianocastello/fca2web',
                                 fontsize=10, ha='left')
                        
                        sns_plot = sns.boxplot(x=grf)
                        sns_plot = sns_plot.set_title("Boxplot de ["+grf.name+"]", {'size': '18'})
                        img_file = file+'_BoxPlot_'+grf.name+'.png'
                        fig = sns_plot.get_figure().savefig(dataout+"/"+img_file)  
                        plt.close()
                        log_write('', addcont=False,newline=True)  

                        image = Image.open(dataout+"/"+img_file)
                        st.image(image, caption=img_file) 


						
                        

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
        if not file == 'titanic.csv':
            ret = post_stat_fca2(file, sizeKB, parâmetros, running_time, remarks)
            if '200' in str(ret):
                log_write(f"Estatística postada: nome={file}, size={sizeKB:,}Kb, param={parâmetros}"+\
                          f", Elap={running_time}, remarks={remarks}",
                            newline=False,addcont=True) 
        log_write("Análise finalizada de "+file, newline=False) 

        st.success('Análise finalizada')
            
        return(0)

    #except Exception as erro:
    #    log_write("\n\n Erro Geral: "+str(erro) + "\n\n") 
    #    return(-2)
       
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
        return("""Arraste o arquivo para ser analisado ou selecione a partir botão "browser". FCA2 aceita arquivos formato CSV e Excel. Se vc tem um arquivo CSV com extensão TXT ou outra, renomeie para que o arquivo seja analisado. A opção de multiplos arquivos foi descontinuada para implantação da customização dos tipos de colunas.""")
    elif widget == 'titanic':
        return("""A base titanic é muito utilizada como exemplo porque é um arquivo pequeno, tem colunas de vários tipos, casos de duplicações e dados ausentes.""")

    return('no tool tip!')

    # global msg_count, max_freq, hist_bins, max_dups
    # global hist, boxp, mcorr, noheader, sep_csv, filecst, dec_csv, sample
    # global UserAgents, runningOn, parâmetros, remarks, sizeKB


run()

