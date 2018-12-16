import pandas as pd
import re
import unidecode
import glob
import os
from sklearn import preprocessing
import geopy.distance

de_para_sigla = {'Acre' : 'AC', 
                'Alagoas': 'AL',
                'Amapá': 'AP',
                'Amazonas': 'AM',
                'Bahia': 'BA',
                'Ceará': 'CE',
                'Distrito Federal': 'DF',
                'Espírito Santo': 'ES',
                'Goiás': 'GO',
                'Maranhão': 'MA',
                'Mato Grosso': 'MT',
                'Mato Grosso do Sul': 'MS',
                'Minas Gerais':'MG',
                'Pará': 'PA',
                'Paraíba': 'PB',
                'Paraná': 'PR',
                'Pernambuco': 'PE',
                'Piauí': 'PI',
                'Rio de Janeiro': 'RJ',
                'Rio Grande do Norte': 'RN',
                'Rio Grande do Sul': 'RS',
                'Rondônia': 'RO',
                'Roraima': 'RR',
                'Santa Catarina': 'SC',
                'São Paulo': 'SP',
                'Sergipe': 'SE',
                'Tocantins': 'TO'}


def get_cities():
    # tabela fornecida pelo hackathon com as cidades mais importantes
    cities = pd.read_excel('data/2018 12 12 _ database challenge.xlsx')
    cities = cities.drop('Unnamed: 0', 1)
    cities['Cidades'] = cities['Cidades'].apply(lambda x: re.sub(r'\([^)]*\)', '', x))
    cities['Cidades'] = cities['Cidades'].apply(lambda x: x.strip())
    cities['Cidades'] = cities['Cidades'].apply(lambda x: unidecode.unidecode(x))
    cities['Cidades'] = cities['Cidades'].str.upper()
    
    
    cities = cities.rename(columns={'Cidades': 'city', 'Cód Cidades': 'cod_cidades',
                                    'UF': 'uf', 'Tem malha aerea?':'tem_malha', 'área em KM2': 'area_em_km2',
                                   'Já é atendido pela Loggi?': 'atendido_loggi', 'Distância de Cajamar (km)': 'distancia_cajamar',
                                   'População 2018': 'populacao'}) 
    
    cities['distancia_cajamar'] = cities['distancia_cajamar'].astype(int)
    
    cities['tem_malha'] = cities['tem_malha'].map({'sim': 1, 'não':0})
    
    
    return cities

def get_airports():
    # source: https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat
    # dados de geolocalizacao dos aeroportos
    columns = ['indice', 'airport', 'city', 'country', 'tree', 'codigo', 'latitude_airport', 'longitude_airport', 'colum1', 'colum2', 'colum3', 'colum4', 'colum5', 'colum6']
    airports = pd.read_csv('data/airports.dat.txt', sep=',', names=columns)
    airports['city'] = airports['city'].str.upper()
    airports = airports[airports['country'] == 'Brazil']
    
    airports = airports[['city', 'latitude_airport', 'longitude_airport', 'airport', 'codigo']]
    
    return airports

def get_airport_with_uf(airports, municipios):
    # associando os aeroportos a cada estado.
    dict_duplicated_airports = {'Belém/Brigadeiro Protásio de Oliveira Airport': 'PA',
                                'Val de Cans/Júlio Cezar Ribeiro International Airport': 'PA',
                                'Atlas Brasil Cantanhede Airport': 'RR', 
                                'Cascavel Airport': 'PR',
                                'Campo Grande Airport':'MS',
                                'Cruzeiro do Sul Airport': 'AC',
                                'Lagoa Santa Airport': 'MG',
                                'Plácido de Castro Airport': 'AC',
                                'Tabatinga Airport': 'AM',
                                'Maestro Wilson Fonseca Airport': 'PA',
                                'Iguatu Airport': 'CE',
                                'Brigadeiro Lysias Rodrigues Airport': 'TO',
                                'Santa Maria Airport': 'RS',
                                'Toledo Airport': 'PR',
                                'Santa Terezinha Airport': 'SC',
                                'Valença Airport': 'BA',
                                'Redenção Airport': 'PA',
                                'Humaitá Airport': 'AM',
                                'São Carlos Airport': 'SP',
                                'Canarana Airport': 'MT'}      
    
    airports = airports.merge(municipios, on='city')
    airports_without_duplicated = airports[~airports[['airport', 'city']].duplicated(keep=False)]
    airports_duplicated = airports[airports[['airport', 'city']].duplicated(keep=False)]


    for key in dict_duplicated_airports.keys():
        temp = airports_duplicated[(airports_duplicated['airport'] == key) & (airports_duplicated['UF'] == dict_duplicated_airports[key])]

        airports_without_duplicated = pd.concat([airports_without_duplicated, temp])
        
    return airports_without_duplicated
    
    
def get_frotas():
    # source http://www.denatran.gov.br/estatistica/635-frota-2018
    # frota por municipio
    frotas = pd.read_excel('data/frota.xls', skiprows=3)
    frotas = frotas[['UF', 'MUNICIPIO', 'CAMINHAO', 'CAMINHONETE', 'CAMIONETA', 'MOTOCICLETA']]
    
    frotas = frotas.rename(columns={'MUNICIPIO':'city', 'CAMINHAO': 'caminhao',
                                    'CAMINHONETE': 'caminhonete', 'CAMIONETA': 'camioneta',
                                    'MOTOCICLETA': 'motocicleta', 'UF': 'uf'})

    return frotas

def get_municipios():
    # source https://ww2.ibge.gov.br/home/estatistica/populacao/contagem2007/popmunic2007layoutTCU14112007.xls
    municipios = pd.read_excel('data/municipios.xls', skiprows=3)
    municipios = municipios.rename(columns={'Unnamed: 3':'city', 'U.F': 'UF'})[['city', 'UF']]
    municipios['city'] = municipios['city'].str.upper()
    municipios['city'] = municipios['city'].apply(lambda x: unidecode.unidecode(x))
    municipios['city'] = municipios['city'].apply(lambda x: x.replace('*', ''))
    municipios['city'] = municipios['city'].apply(lambda x: x.strip())
    
    return municipios

def get_decolagens():
    # source http://www.anac.gov.br/assuntos/dados-e-estatisticas/mercado-de-transporte-aereo/anuario-do-transporte-aereo/dados-do-anuario-do-transporte-aereo
    # numero de decolagens por municipio
    decolagens = pd.read_excel('data/decolagens.xlsx')
    decolagens = decolagens[~decolagens['Aeroporto'].str.contains('Total')]
    decolagens['Aeroporto'] = decolagens['Aeroporto'].apply(lambda x : x.split("-", maxsplit=1)[0])
    decolagens = decolagens.rename(columns= {'Aeroporto': 'codigo', 'Quantidade de Decolagens': 'quantidade_decolagens'})
    
    return decolagens

def get_gasolina():
    # source http://www.anp.gov.br/precos-e-defesa/234-precos/levantamento-de-precos/4606-infopreco-precos-praticados-pelos-postos-revendedores
    # preco de gasolina por municipio
    gasolina = pd.read_excel('data/infopreco-30-11-2018.xlsx', skiprows=5)
    gasolina_mean = gasolina.groupby(['MUNICÍPIO', 'UF', 'PRODUTO'], as_index=False)['VALOR VENDA'].mean()
    gasolina_mean_pivot = pd.pivot_table(gasolina_mean, values='VALOR VENDA', index=['MUNICÍPIO', 'UF'], columns=['PRODUTO']).reset_index()
    gasolina_mean_pivot = gasolina_mean_pivot.rename(columns={'MUNICÍPIO': 'city', 'UF': 'uf', 'Gasolina C Comum': 'preco_gasolina',
                                                              'Diesel S10': 'preco_diesel_s10'})
    gasolina_mean_pivot = gasolina_mean_pivot[['uf', 'city', 'preco_gasolina', 'preco_diesel_s10']]
    
    gasolina_mean_pivot_uf = gasolina_mean_pivot.groupby('uf', as_index=False).mean()
    
    return gasolina_mean_pivot, gasolina_mean_pivot_uf

def get_area_urbana():
    # source https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Brasil_por_%C3%A1rea_urbana
    # area urbana por municipio
    area_urbana = pd.read_excel('data/urbana.xlsx')
    area_urbana = area_urbana[['Município', 'Unidade federativa', 'Área urbana (km²)']]
    area_urbana['Unidade federativa'] = area_urbana['Unidade federativa'].str.replace('Pará Pará', 'Pará')
    area_urbana['Unidade federativa'] = area_urbana['Unidade federativa'].str.replace('Bahia Bahia', 'Bahia')
    area_urbana['Unidade federativa'] = area_urbana['Unidade federativa'].map(de_para_sigla)
    
    area_urbana['Município'] = area_urbana['Município'].apply(lambda x: unidecode.unidecode(x))
    area_urbana['Município'] = area_urbana['Município'].str.upper()
    
    area_urbana = area_urbana.rename(columns={'Unidade federativa': 'uf', 'Município': 'city',
                                              'Área urbana (km²)': 'area_urbana'})
    
    return area_urbana

def get_geo_municipios():
    # https://github.com/kelvins/Municipios-Brasileiros
    # geolocalizacao por municpio
    geo_municipios = pd.read_csv('data/municipios_geolocalizacao.csv')
    geo_municipios = geo_municipios.rename(columns={'nome_municipio': 'city'})
    
    geo_municipios['city'] = geo_municipios['city'].apply(lambda x: unidecode.unidecode(x))
    geo_municipios['city'] = geo_municipios['city'].str.upper()
    
    return geo_municipios[['city', 'uf', 'latitude', 'longitude']]

def get_pib_municipio():
    # https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Brasil_por_PIB
    # pib por municpio
    pib_municipio = pd.read_excel('data/pib_municipio.xlsx', header=None)
    pib_municipio = pib_municipio.rename(columns={0:'city', 1:'uf', 2:'pib'})
    pib_municipio['pib'] = pib_municipio['pib'].apply(lambda x: str(x).strip().replace(" ", ""))
    pib_municipio['pib'] = pib_municipio['pib'].astype(float)
    
    pib_municipio['uf'] = pib_municipio['uf'].str.replace('Pará Pará', 'Pará')
    pib_municipio['uf'] = pib_municipio['uf'].str.replace('Bahia Bahia', 'Bahia')
    pib_municipio['uf'] = pib_municipio['uf'].map(de_para_sigla)
    
    pib_municipio['city'] = pib_municipio['city'].apply(lambda x: unidecode.unidecode(x))
    pib_municipio['city'] = pib_municipio['city'].str.upper()
    
    return pib_municipio

def get_sinistros():
    # http://www2.susep.gov.br/menuestatistica/RankRoubo/menu1.asp
    # numero de roubos de carga. 
    sinistros = pd.DataFrame()

    for file in glob.glob("data/sinistros/*.xlsx"):
        temp_dataframe = pd.read_excel(file)
        temp_dataframe['uf'] = os.path.basename(file).replace('.xlsx', '')

        sinistros = pd.concat([sinistros, temp_dataframe])
        
    sinistros['uf'] = sinistros['uf'].map(de_para_sigla)
    sinistros = sinistros[sinistros['Modelo'].str.contains('CAMINHOES')]
    
    ## calculating weighted mean
    sinistros['sum_veiculos'] = sinistros.groupby('uf')['Veículos Expostos'].transform(sum)
    sinistros['factor'] = sinistros['(*) Índice de Roubos/Furtos (%)'] * sinistros['Veículos Expostos']
    sinistros['factor_sum'] = sinistros.groupby('uf')['factor'].transform(sum)
    sinistros['weighted_mean'] = sinistros['factor_sum'] / sinistros['sum_veiculos']
    sinistros.sort_values('weighted_mean', ascending=False)

    sinistros_mean = sinistros.groupby('uf', as_index=False)['weighted_mean'].first()
    sinistros_mean.sort_values('weighted_mean', ascending=False)
    sinistros_mean = sinistros_mean.rename(columns={'weighted_mean': 'indice_roubo'})

    return sinistros_mean

def get_idh_renda():
    # http://www.atlasbrasil.org.br/2013/pt/ranking
    # idh de renda por municipio
    idh = pd.read_csv('data/idh.csv', encoding='latin-1', sep=';', skiprows=1)
    idh['city'], idh['uf'] = idh['Nome'].str.split('(', 1).str
    idh['uf'] = idh['uf'].str.replace(')', '')
    idh['city'] = idh['city'].apply(lambda x: x.strip())
    idh['city'] = idh['city'].apply(lambda x: unidecode.unidecode(x))
    idh['city'] = idh['city'].str.upper()
    
    idh = idh.rename(columns={'IDHM Renda (2010)': 'idh_renda'})
    
    return idh[['city', 'uf', 'idh_renda']]